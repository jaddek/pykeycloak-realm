#!/usr/bin/env python3

import json
import logging
from pathlib import Path

import yaml

from pykeycloak_realm.config import RealmBuilderConfig

logger = logging.getLogger(__name__)


def template_load(template_name: str, template_suffix: str, templates_path: str) -> dict:
    if not template_name.endswith(template_suffix):
        template_name += template_suffix

    file_path = Path(templates_path) / template_name
    file_path = file_path.resolve()

    if not file_path.is_file():
        raise FileNotFoundError(f"Preset file does not exist: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data


def write_to_realm_import_file(
        realm_data: dict,
        target_file: Path,
        overwrite: bool = False
) -> None:
    if target_file.exists():
        if not overwrite:
            logger.error(f"File exists and overwrite not allowed: {target_file}")
            raise FileExistsError(f"{target_file} already exists")

    json_content = json.dumps(realm_data, indent=2)

    try:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(json_content)
        logger.info(f"Export completed: {target_file}")
    except Exception as e:
        logger.exception(f"Error writing JSON file {target_file}: {e}")
        raise


class RealmTransformer:
    def __init__(self, template: dict):
        self.template = template
        self.realm = template.get("realm", {})
        self.env_config = template.get("envs", {})

    def inject_client_secrets(self, client: dict):
        client_env = self.env_config.get(client.get("clientId"))
        if not client_env:
            return

        if "id" in client_env:
            client["id"] = client_env["id"]
        if "secret" in client_env:
            client["secret"] = client_env["secret"]

    @staticmethod
    def transform_authorization(client: dict):
        auth_cfg = client.get("authorizationSettings")
        if not auth_cfg:
            return

        for policy in auth_cfg.get("policies", []):
            name = policy.get("name", "")
            if not name.startswith("policy_role__"): # realm system_role or uma should be skipped
                continue
            config = policy.get("config")
            if not config:
                continue
            roles_json = {"roles": json.dumps(config.get("roles", []))}
            policy["config"] = {**config, **roles_json}

    def apply_transformations(self):
        for client in self.realm.get("clients", []):
            self.inject_client_secrets(client)
            self.transform_authorization(client)

        for client in self.env_config.get("clients", []):
            cid_alias = client.get("cid_alias") #ot_cid
            cid = client.get("cid")

            if not all([cid_alias, cid]):
                logger.info(f"Skip transformation for client {client.get('cn')} cid_alias or cid is empty")
                continue

            json_str = json.dumps(self.realm)
            json_str = json_str.replace(f"${cid_alias}", cid)
            self.realm = json.loads(json_str)

        return self



def create_realm_config_file(template_name: str, config: RealmBuilderConfig) -> dict:
    template = template_load(
        template_name=template_name,
        template_suffix=config.template_file_suffix,
        templates_path=config.template_dir_path

    )
    transformer = RealmTransformer(template).apply_transformations()

    return transformer.realm


def export(from_template: str, to_file: str, config: RealmBuilderConfig):
    realm_data = create_realm_config_file(
        template_name=from_template,
        config=config
    )

    write_to_realm_import_file(
        realm_data=realm_data,
        target_file=config.get_realm_filename(to_file),
        overwrite=config.overwrite_existing_realm
    )
