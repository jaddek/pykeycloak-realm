from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class RealmBuilderConfig:
    template_export_dir_path: str | None = field(
        default_factory=lambda: os.getenv("KEYCLOAK_BUILDER_EXPORT_PATH", "./data/realms/export")
    )

    template_dir_path: str | None = field(
        default_factory=lambda: os.getenv("KEYCLOAK_BUILDER_TEMPLATES_PATH", "./data/realms/templates")
    )

    template_file_suffix: str | None = field(
        default_factory=lambda: os.getenv("KEYCLOAK_BUILDER_TEMPLATES_FILE_SUFFIX", ".realm.yml")
    )

    realm_file_suffix: str | None = field(
        default_factory=lambda: os.getenv("KEYCLOAK_BUILDER_REALM_FILE_SUFFIX", ".realm.json")
    )

    overwrite_existing_realm: bool | None = field(
        default_factory=lambda: os.getenv("KEYCLOAK_OVERWRITE_EXISTING_REALM", "True") == "True"
    )

    def get_realm_filename(self, filename: str) -> Path:
        return Path(self.template_export_dir_path) / f"{filename}{self.realm_file_suffix}"

    def __post_init__(self):
        if self.template_export_dir_path:
            self.template_export_dir_path = str(Path(self.template_export_dir_path).resolve())

        if self.template_dir_path:
            self.template_dir_path = str(Path(self.template_dir_path).resolve())

        missing = []

        if not self.template_export_dir_path:
            missing.append("template_export_dir_path")

        if not self.template_dir_path:
            missing.append("template_dir_path")

        if not self.template_file_suffix:
            missing.append("template_file_suffix")

        if not self.realm_file_suffix:
            missing.append("realm_file_suffix")

        if self.overwrite_existing_realm == "":
            missing.append("overwrite_existing_realm")

        if missing:
            raise ValueError(f"RealmBuilderConfig missing required fields: {', '.join(missing)}")
