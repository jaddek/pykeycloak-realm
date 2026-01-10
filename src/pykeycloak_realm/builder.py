#!/usr/bin/env python3

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from pykeycloak_realm.config import RealmBuilderConfig

logger = logging.getLogger(__name__)

JsonDict = dict[str, Any]


def template_load(
    template_name: str,
    template_suffix: str,
    templates_path: str,
) -> JsonDict:
    name = (
        template_name
        if template_name.endswith(template_suffix)
        else f"{template_name}{template_suffix}"
    )

    file_path = (Path(templates_path) / name).resolve()

    if not file_path.is_file():
        raise FileNotFoundError(f"Preset file does not exist: {file_path}")

    with file_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def write_to_realm_import_file(
    realm_data: JsonDict,
    target_file: Path,
    overwrite: bool = False,
) -> None:
    if target_file.exists() and not overwrite:
        raise FileExistsError(f"{target_file} already exists")

    try:
        target_file.write_text(
            json.dumps(realm_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Export completed: %s", target_file)
    except OSError:
        logger.exception("Error writing JSON file %s", target_file)
        raise


def deep_replace(value: Any, replacements: dict[str, str]) -> Any:
    match value:
        case str():
            return replacements.get(value, value)

        case list():
            return [deep_replace(v, replacements) for v in value]

        case dict():
            return {
                replacements.get(k, k): deep_replace(v, replacements)
                for k, v in value.items()
            }

        case _:
            return value


class RealmTransformer:
    def __init__(self, template: JsonDict):
        self.realm: JsonDict = template.get("realm", {})
        self.envs: JsonDict = template.get("envs", {})

    def apply(self) -> JsonDict:
        realm = self._inject_client_secrets(self.realm)
        realm = self._transform_authorizations(realm)
        realm = self._replace_aliases(realm)
        return realm

    def _inject_client_secrets(self, realm: JsonDict) -> JsonDict:
        env_clients_list = self.envs.get("clients", [])
        # Convert list to dictionary for easier lookup by clientId
        env_clients = {
            client.get("clientId"): client
            for client in env_clients_list
            if client.get("clientId")
        }

        clients = [
            client
            | {
                k: env_clients[client["clientId"]][k]
                for k in ("id", "secret")
                if client.get("clientId") in env_clients
                and k in env_clients[client["clientId"]]
            }
            for client in realm.get("clients", [])
        ]

        return realm | {"clients": clients}

    @staticmethod
    def _transform_authorizations(realm: JsonDict) -> JsonDict:
        def transform_client(client: JsonDict) -> JsonDict:
            auth = client.get("authorizationSettings")
            if not auth:
                return client

            policies = [
                (
                    policy
                    if not (
                        policy.get("name", "").startswith("policy_role__")
                        and policy.get("config")
                    )
                    else policy
                    | {
                        "config": policy["config"]
                        | {"roles": json.dumps(policy["config"].get("roles", []))}
                    }
                )
                for policy in auth.get("policies", [])
            ]

            return client | {"authorizationSettings": auth | {"policies": policies}}

        return realm | {
            "clients": [transform_client(c) for c in realm.get("clients", [])]
        }

    def _replace_aliases(self, realm: JsonDict) -> JsonDict:
        replacements = {
            f"${c['cid_alias']}": c["cid"]
            for c in self.envs.get("clients", [])
            if c.get("cid_alias") and c.get("cid")
        }

        if not replacements:
            return realm

        return deep_replace(realm, replacements)  # type: ignore[no-any-return]


def create_realm_config_file(
    template_name: str, config: RealmBuilderConfig
) -> dict[str, Any]:
    template = template_load(
        template_name=template_name,
        template_suffix=config.template_file_suffix,
        templates_path=config.template_dir_path,
    )

    return RealmTransformer(template).apply()


def export(from_template: str, to_file: str, config: RealmBuilderConfig) -> None:
    realm_data = create_realm_config_file(template_name=from_template, config=config)

    write_to_realm_import_file(
        realm_data=realm_data,
        target_file=config.get_realm_filename(to_file),
        overwrite=config.overwrite_existing_realm,
    )
