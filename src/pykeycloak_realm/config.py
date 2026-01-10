import os
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path


@dataclass
class RealmBuilderConfig:
    _template_export_dir_path: str | PathLike[str] = field(
        default_factory=lambda: os.getenv(
            "KEYCLOAK_BUILDER_EXPORT_PATH", "./data/realms/export"
        )
    )

    _template_dir_path: str | PathLike[str] = field(
        default_factory=lambda: os.getenv(
            "KEYCLOAK_BUILDER_TEMPLATES_PATH", "./data/realms/templates"
        )
    )

    template_file_suffix: str = field(
        default_factory=lambda: os.getenv(
            "KEYCLOAK_BUILDER_TEMPLATES_FILE_SUFFIX", ".realm.yml"
        )
    )

    realm_file_suffix: str = field(
        default_factory=lambda: os.getenv(
            "KEYCLOAK_BUILDER_REALM_FILE_SUFFIX", ".realm.json"
        )
    )

    overwrite_existing_realm: bool = field(
        default_factory=lambda: os.getenv("KEYCLOAK_OVERWRITE_EXISTING_REALM", "True")
        == "True"
    )

    def get_realm_filename(self, filename: str) -> Path:
        return (
            Path(self._template_export_dir_path) / f"{filename}{self.realm_file_suffix}"
        )

    @property
    def template_export_dir_path(self) -> str:
        return str(Path(self._template_export_dir_path).resolve())

    @property
    def template_dir_path(self) -> str:
        return str(Path(self._template_dir_path).resolve())

    def __post_init__(self) -> None:
        missing = []

        if not self._template_export_dir_path:
            missing.append("template_export_dir_path")

        if not self._template_dir_path:
            missing.append("template_dir_path")

        if not self.template_file_suffix:
            missing.append("template_file_suffix")

        if not self.realm_file_suffix:
            missing.append("realm_file_suffix")

        if missing:
            raise ValueError(
                f"RealmBuilderConfig missing required fields: {', '.join(missing)}"
            )
