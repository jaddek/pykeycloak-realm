from pathlib import Path

import pytest

from pykeycloak_realm.config import RealmBuilderConfig


class TestRealmBuilderConfig:
    def test_default_initialization(self, monkeypatch):
        """Test with initial data"""
        # Clear environment variables to ensure defaults are used
        monkeypatch.delenv("KEYCLOAK_BUILDER_EXPORT_PATH", raising=False)
        monkeypatch.delenv("KEYCLOAK_BUILDER_TEMPLATES_PATH", raising=False)
        monkeypatch.delenv("KEYCLOAK_BUILDER_TEMPLATES_FILE_SUFFIX", raising=False)
        monkeypatch.delenv("KEYCLOAK_BUILDER_REALM_FILE_SUFFIX", raising=False)
        monkeypatch.delenv("KEYCLOAK_OVERWRITE_EXISTING_REALM", raising=False)

        # Act
        config = RealmBuilderConfig()

        # Assert
        assert config._template_export_dir_path == "./data/realms/export"
        assert config._template_dir_path == "./data/realms/templates"
        assert config.template_file_suffix == ".realm.yml"
        assert config.realm_file_suffix == ".realm.json"
        assert config.overwrite_existing_realm is True

    def test_initialization_with_custom_values(self):
        # Act
        config = RealmBuilderConfig(
            _template_export_dir_path="/custom/export",
            _template_dir_path="/custom/templates",
            template_file_suffix=".yaml",
            realm_file_suffix=".json",
            overwrite_existing_realm=False,
        )

        # Assert
        assert config._template_export_dir_path == "/custom/export"
        assert config._template_dir_path == "/custom/templates"
        assert config.template_file_suffix == ".yaml"
        assert config.realm_file_suffix == ".json"
        assert config.overwrite_existing_realm is False

    def test_get_realm_filename(self, monkeypatch):
        # Clear environment variables to ensure consistent behavior
        monkeypatch.delenv("KEYCLOAK_BUILDER_EXPORT_PATH", raising=False)

        # Arrange
        config = RealmBuilderConfig(
            _template_export_dir_path="./output", realm_file_suffix=".realm.json"
        )

        # Act
        filename = config.get_realm_filename("my_realm")

        # Assert
        expected = Path("./output/my_realm.realm.json")
        assert filename == expected

    def test_path_resolution_in_post_init(self, tmp_path, monkeypatch):
        # Clear environment variables to ensure consistent behavior
        monkeypatch.delenv("KEYCLOAK_BUILDER_EXPORT_PATH", raising=False)
        monkeypatch.delenv("KEYCLOAK_BUILDER_TEMPLATES_PATH", raising=False)

        # Arrange
        custom_path = tmp_path / "custom" / "path"
        custom_path.mkdir(parents=True)

        # Act
        config = RealmBuilderConfig(
            _template_export_dir_path=str(custom_path),
            _template_dir_path=str(custom_path / "templates"),
        )

        # Assert
        assert config.template_export_dir_path == str(custom_path.resolve())
        assert config.template_dir_path == str((custom_path / "templates").resolve())

    def test_environment_variables_override_defaults(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("KEYCLOAK_BUILDER_EXPORT_PATH", "/env/export")
        monkeypatch.setenv("KEYCLOAK_BUILDER_TEMPLATES_PATH", "/env/templates")
        monkeypatch.setenv("KEYCLOAK_BUILDER_TEMPLATES_FILE_SUFFIX", ".env.yml")
        monkeypatch.setenv("KEYCLOAK_BUILDER_REALM_FILE_SUFFIX", ".env.json")
        monkeypatch.setenv("KEYCLOAK_OVERWRITE_EXISTING_REALM", "False")

        # Act
        config = RealmBuilderConfig()

        # Assert
        # Use the property that resolves the path
        assert config._template_export_dir_path == "/env/export"
        assert config._template_dir_path == "/env/templates"
        assert config.template_file_suffix == ".env.yml"
        assert config.realm_file_suffix == ".env.json"
        assert config.overwrite_existing_realm is False

    def test_environment_variables_true_boolean(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("KEYCLOAK_OVERWRITE_EXISTING_REALM", "True")

        # Act
        config = RealmBuilderConfig()

        # Assert
        assert config.overwrite_existing_realm is True

    def test_environment_variables_false_boolean(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("KEYCLOAK_OVERWRITE_EXISTING_REALM", "False")

        # Act
        config = RealmBuilderConfig()

        # Assert
        assert config.overwrite_existing_realm is False

    def test_missing_required_fields(self, monkeypatch):
        # Clear environment variables to ensure proper validation
        monkeypatch.delenv("KEYCLOAK_BUILDER_EXPORT_PATH", raising=False)
        monkeypatch.delenv("KEYCLOAK_BUILDER_TEMPLATES_PATH", raising=False)

        # Act & Assert
        with pytest.raises(
            ValueError, match="RealmBuilderConfig missing required fields"
        ):
            RealmBuilderConfig(
                _template_export_dir_path=None,
                _template_dir_path=None,
                template_file_suffix=None,
                realm_file_suffix=None,
                overwrite_existing_realm=None,
            )

    def test_partial_missing_fields(self, monkeypatch):
        # Clear environment variables to ensure proper validation
        monkeypatch.delenv("KEYCLOAK_BUILDER_EXPORT_PATH", raising=False)
        monkeypatch.delenv("KEYCLOAK_BUILDER_TEMPLATES_PATH", raising=False)

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="missing required fields: template_export_dir_path, template_dir_path",
        ):
            RealmBuilderConfig(
                _template_export_dir_path=None,
                _template_dir_path=None,
                template_file_suffix=".suffix",
                realm_file_suffix=".suffix",
                overwrite_existing_realm=True,
            )

    def test_valid_config_creation(self, monkeypatch):
        # Clear environment variables to ensure consistent behavior
        monkeypatch.delenv("KEYCLOAK_BUILDER_EXPORT_PATH", raising=False)
        monkeypatch.delenv("KEYCLOAK_BUILDER_TEMPLATES_PATH", raising=False)

        # Act
        config = RealmBuilderConfig(
            _template_export_dir_path="./valid/export",
            _template_dir_path="./valid/templates",
            template_file_suffix=".valid.yml",
            realm_file_suffix=".valid.json",
            overwrite_existing_realm=True,
        )

        # Assert
        assert config._template_export_dir_path == "./valid/export"
        assert config._template_dir_path == "./valid/templates"
        assert config.template_file_suffix == ".valid.yml"
        assert config.realm_file_suffix == ".valid.json"
        assert config.overwrite_existing_realm is True
