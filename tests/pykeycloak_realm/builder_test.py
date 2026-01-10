import json
from unittest.mock import patch

import pytest
import yaml

# Импорты из тестируемого модуля
from pykeycloak_realm.builder import (
    RealmTransformer,
    create_realm_config_file,
    deep_replace,
    export,
    template_load,
    write_to_realm_import_file,
)
from pykeycloak_realm.config import RealmBuilderConfig


class TestTemplateLoad:
    def test_template_load_success(self, tmp_path):
        # Arrange
        template_data = {"realm": {"name": "test-realm"}, "envs": {"clients": []}}
        template_file = tmp_path / "test.realm.yml"
        template_file.write_text(yaml.dump(template_data))

        # Act
        result = template_load(
            template_name="test",
            template_suffix=".realm.yml",
            templates_path=str(tmp_path),
        )

        # Assert
        assert result == template_data

    def test_template_load_with_suffix_in_name(self, tmp_path):
        # Arrange
        template_data = {"realm": {"name": "test-realm"}}
        template_file = tmp_path / "test.realm.yml"
        template_file.write_text(yaml.dump(template_data))

        # Act
        result = template_load(
            template_name="test.realm.yml",
            template_suffix=".realm.yml",
            templates_path=str(tmp_path),
        )

        # Assert
        assert result == template_data

    def test_template_load_file_not_found(self, tmp_path):
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Preset file does not exist"):
            template_load(
                template_name="nonexistent",
                template_suffix=".realm.yml",
                templates_path=str(tmp_path),
            )

    def test_template_load_empty_file(self, tmp_path):
        # Arrange
        template_file = tmp_path / "empty.realm.yml"
        template_file.write_text("")

        # Act
        result = template_load(
            template_name="empty",
            template_suffix=".realm.yml",
            templates_path=str(tmp_path),
        )

        # Assert
        assert result == {}

    def test_template_load_invalid_yaml(self, tmp_path):
        # Arrange
        template_file = tmp_path / "invalid.realm.yml"
        template_file.write_text("invalid: yaml: content: [")

        # Act & Assert
        with pytest.raises(yaml.YAMLError):
            template_load(
                template_name="invalid",
                template_suffix=".realm.yml",
                templates_path=str(tmp_path),
            )


class TestWriteToRealmImportFile:

    def test_write_to_realm_import_file_success(self, tmp_path):
        # Arrange
        realm_data = {"realm": "test-realm", "clients": []}
        target_file = tmp_path / "test-realm.json"

        # Act
        write_to_realm_import_file(realm_data, target_file)

        # Assert
        assert target_file.exists()
        written_data = json.loads(target_file.read_text())
        assert written_data == realm_data

    def test_write_to_realm_import_file_overwrite_false(self, tmp_path):
        # Arrange
        realm_data = {"realm": "test-realm"}
        target_file = tmp_path / "existing.json"
        target_file.write_text("existing content")

        # Act & Assert
        with pytest.raises(FileExistsError, match="already exists"):
            write_to_realm_import_file(realm_data, target_file, overwrite=False)

    def test_write_to_realm_import_file_overwrite_true(self, tmp_path):
        # Arrange
        realm_data = {"realm": "new-realm"}
        target_file = tmp_path / "existing.json"
        target_file.write_text("existing content")

        # Act
        write_to_realm_import_file(realm_data, target_file, overwrite=True)

        # Assert
        written_data = json.loads(target_file.read_text())
        assert written_data == realm_data

    @patch("pykeycloak_realm.builder.logger")
    def test_write_to_realm_import_file_os_error(self, mock_logger, tmp_path):
        # Arrange
        realm_data = {"realm": "test-realm"}
        target_file = tmp_path / "readonly" / "test.json"

        # Act & Assert
        with pytest.raises(OSError):
            write_to_realm_import_file(realm_data, target_file)

        mock_logger.exception.assert_called_once()

    def test_write_to_realm_import_file_unicode_content(self, tmp_path):
        # Arrange
        realm_data = {"realm": "тест-realm", "description": "Описание с unicode"}
        target_file = tmp_path / "unicode.json"

        # Act
        write_to_realm_import_file(realm_data, target_file)

        # Assert
        written_data = json.loads(target_file.read_text(encoding="utf-8"))
        assert written_data == realm_data


class TestDeepReplace:

    def test_deep_replace_string_replacement(self):
        # Arrange
        value = "old_value"
        replacements = {"old_value": "new_value"}

        # Act
        result = deep_replace(value, replacements)

        # Assert
        assert result == "new_value"

    def test_deep_replace_string_no_replacement(self):
        # Arrange
        value = "unchanged_value"
        replacements = {"old_value": "new_value"}

        # Act
        result = deep_replace(value, replacements)

        # Assert
        assert result == "unchanged_value"

    def test_deep_replace_list(self):
        # Arrange
        value = ["old_value", "unchanged", "old_value"]
        replacements = {"old_value": "new_value"}

        # Act
        result = deep_replace(value, replacements)

        # Assert
        assert result == ["new_value", "unchanged", "new_value"]

    def test_deep_replace_dict_keys_and_values(self):
        # Arrange
        value = {"old_key": "old_value", "unchanged_key": "unchanged_value"}
        replacements = {"old_key": "new_key", "old_value": "new_value"}

        # Act
        result = deep_replace(value, replacements)

        # Assert
        expected = {"new_key": "new_value", "unchanged_key": "unchanged_value"}
        assert result == expected

    def test_deep_replace_nested_structure(self):
        # Arrange
        value = {"level1": {"level2": ["old_value", {"nested_key": "old_value"}]}}
        replacements = {"old_value": "new_value"}

        # Act
        result = deep_replace(value, replacements)

        # Assert
        expected = {"level1": {"level2": ["new_value", {"nested_key": "new_value"}]}}
        assert result == expected

    def test_deep_replace_non_string_types(self):
        # Arrange
        value = {"number": 42, "boolean": True, "null": None}
        replacements = {"old_value": "new_value"}

        # Act
        result = deep_replace(value, replacements)

        # Assert
        assert result == {"number": 42, "boolean": True, "null": None}


class TestRealmTransformer:

    @pytest.fixture
    def sample_template(self):
        return {
            "realm": {
                "realm": "test-realm",
                "clients": [
                    {"clientId": "test-client", "name": "Test Client"},
                    {
                        "clientId": "auth-client",
                        "name": "Auth Client",
                        "authorizationSettings": {
                            "policies": [
                                {
                                    "name": "policy_role__admin",
                                    "config": {"roles": ["admin", "user"]},
                                },
                                {
                                    "name": "regular_policy",
                                    "config": {"setting": "value"},
                                },
                            ]
                        },
                    },
                ],
            },
            "envs": {
                "clients": [
                    {
                        "clientId": "test-client",
                        "id": "client-uuid-123",
                        "secret": "client-secret-456",  # noqa s105
                        "cid_alias": "${test_client_id}",
                        "cid": "real-client-id",
                    }
                ]
            },
        }

    def test_realm_transformer_init(self, sample_template):
        # Act
        transformer = RealmTransformer(sample_template)

        # Assert
        assert transformer.realm == sample_template["realm"]
        assert transformer.envs == sample_template["envs"]

    def test_realm_transformer_init_missing_keys(self):
        # Arrange
        template = {}

        # Act
        transformer = RealmTransformer(template)

        # Assert
        assert transformer.realm == {}
        assert transformer.envs == {}

    def test_inject_client_secrets(self, sample_template):
        # Arrange
        transformer = RealmTransformer(sample_template)

        # Act
        result = transformer._inject_client_secrets(transformer.realm)

        # Assert
        test_client = next(
            c for c in result["clients"] if c["clientId"] == "test-client"
        )
        assert test_client["id"] == "client-uuid-123"
        assert test_client["secret"] == "client-secret-456"  # noqa s105

        auth_client = next(
            c for c in result["clients"] if c["clientId"] == "auth-client"
        )
        assert "id" not in auth_client
        assert "secret" not in auth_client

    def test_inject_client_secrets_no_env_clients(self):
        """Тест внедрения секретов когда нет env клиентов"""
        # Arrange
        template = {"realm": {"clients": [{"clientId": "test-client"}]}, "envs": {}}
        transformer = RealmTransformer(template)

        # Act
        result = transformer._inject_client_secrets(transformer.realm)

        # Assert
        assert result["clients"][0] == {"clientId": "test-client"}

    def test_transform_authorizations(self, sample_template):
        """Тест трансформации авторизаций"""
        # Arrange
        transformer = RealmTransformer(sample_template)

        # Act
        result = transformer._transform_authorizations(transformer.realm)

        # Assert
        auth_client = next(
            c for c in result["clients"] if c["clientId"] == "auth-client"
        )
        policies = auth_client["authorizationSettings"]["policies"]

        role_policy = next(p for p in policies if p["name"] == "policy_role__admin")
        assert role_policy["config"]["roles"] == '["admin", "user"]'

        regular_policy = next(p for p in policies if p["name"] == "regular_policy")
        # Regular policy should remain unchanged (not matching the pattern)
        assert (
            "roles" not in regular_policy["config"]
        )  # Should not have roles key added
        assert (
            regular_policy["config"]["setting"] == "value"
        )  # Original config should remain

    def test_transform_authorizations_no_auth_settings(self):
        # Arrange
        template = {"realm": {"clients": [{"clientId": "simple-client"}]}, "envs": {}}
        transformer = RealmTransformer(template)

        # Act
        result = transformer._transform_authorizations(transformer.realm)

        # Assert
        assert result["clients"][0]["clientId"] == "simple-client"

    def test_replace_aliases(self, sample_template):
        """Тест замены алиасов"""
        # Arrange
        template_with_aliases = {
            "realm": {
                "name": "test-realm",
                "clients": [
                    {
                        "clientId": "test-client",
                        "name": "Test Client",
                        "some_field": "$test_client_id_alias",
                    }
                ],
            },
            "envs": {
                "clients": [
                    {
                        "clientId": "test-client",
                        "id": "client-uuid-123",
                        "secret": "client-secret-456",
                        "cid_alias": "test_client_id_alias",
                        "cid": "real-client-id",
                    }
                ]
            },
        }
        transformer = RealmTransformer(template_with_aliases)

        # Act
        result = transformer._replace_aliases(transformer.realm)

        # Assert
        test_client = result["clients"][0]
        assert test_client["some_field"] == "real-client-id"

    def test_replace_aliases_no_replacements(self):
        """Тест замены алиасов когда нет замен"""
        # Arrange
        template = {"realm": {"some_key": "some_value"}, "envs": {}}
        transformer = RealmTransformer(template)

        # Act
        result = transformer._replace_aliases(transformer.realm)

        # Assert
        assert result == transformer.realm

    def test_replace_aliases_multiple_replacements(self):
        """Тест замены нескольких алиасов"""
        # Arrange
        template = {
            "realm": {
                "$first_alias": "resolved_first",
                "$second_alias": "resolved_second",
                "name": "$first_alias",
                "clients": [{"clientId": "$first_alias", "name": "$second_alias"}],
            },
            "envs": {
                "clients": [
                    {
                        "clientId": "client1",
                        "cid_alias": "first_alias",
                        "cid": "resolved_first",
                    },
                    {
                        "clientId": "client2",
                        "cid_alias": "second_alias",
                        "cid": "resolved_second",
                    },
                ]
            },
        }
        transformer = RealmTransformer(template)

        # Act
        result = transformer._replace_aliases(transformer.realm)

        # Assert
        assert result["name"] == "resolved_first"
        assert result["resolved_first"] == "resolved_first"
        assert result["resolved_second"] == "resolved_second"
        assert result["clients"][0]["clientId"] == "resolved_first"
        assert result["clients"][0]["name"] == "resolved_second"

    def test_replace_aliases_nested_structure(self):
        """Тест замены алиасов во вложенной структуре"""
        # Arrange
        template = {
            "realm": {
                "nested": {"deep": {"value": "$nested_alias"}},
                "$nested_alias": "nested_resolved",
                "$array_alias": "array_resolved",
                "array": ["$array_alias", "static", "$nested_alias"],
            },
            "envs": {
                "clients": [
                    {
                        "clientId": "test",
                        "cid_alias": "nested_alias",
                        "cid": "nested_resolved",
                    },
                    {
                        "clientId": "test2",
                        "cid_alias": "array_alias",
                        "cid": "array_resolved",
                    },
                ]
            },
        }
        transformer = RealmTransformer(template)

        # Act
        result = transformer._replace_aliases(transformer.realm)

        # Assert
        assert result["nested"]["deep"]["value"] == "nested_resolved"
        assert result["nested_resolved"] == "nested_resolved"
        assert result["array_resolved"] == "array_resolved"
        assert result["array"][0] == "array_resolved"
        assert result["array"][2] == "nested_resolved"

    def test_apply_method(self, sample_template):
        """Тест метода apply который применяет все трансформации"""
        # Arrange
        transformer = RealmTransformer(sample_template)

        # Act
        result = transformer.apply()

        # Assert
        # Should have applied all transformations
        test_client = next(
            c for c in result["clients"] if c["clientId"] == "test-client"
        )
        assert test_client["id"] == "client-uuid-123"
        assert test_client["secret"] == "client-secret-456"  # noqa s105


class TestCreateRealmConfigFile:
    """Тесты для функции create_realm_config_file"""

    def test_create_realm_config_file_success(self, tmp_path):
        """Тест успешного создания конфига realm"""
        # Arrange
        template_data = {"realm": {"name": "test-realm"}, "envs": {"clients": []}}
        template_file = tmp_path / "test.realm.yml"
        template_file.write_text(yaml.dump(template_data))

        config = RealmBuilderConfig(
            _template_dir_path=str(tmp_path), template_file_suffix=".realm.yml"
        )

        # Act
        result = create_realm_config_file("test", config)

        # Assert
        assert result["name"] == "test-realm"

    def test_create_realm_config_file_with_transformations(self, tmp_path):
        """Тест создания конфига realm с трансформациями"""
        # Arrange
        template_data = {
            "realm": {
                "name": "transform-test-realm",
                "clients": [{"clientId": "test-client", "name": "Test Client"}],
            },
            "envs": {
                "clients": [
                    {
                        "clientId": "test-client",
                        "id": "client-uuid-123",
                        "secret": "client-secret-456",
                        "cid_alias": "${test_client_id}",
                        "cid": "real-client-id",
                    }
                ]
            },
        }
        template_file = tmp_path / "transform.realm.yml"
        template_file.write_text(yaml.dump(template_data))

        config = RealmBuilderConfig(
            _template_dir_path=str(tmp_path), template_file_suffix=".realm.yml"
        )

        # Act
        result = create_realm_config_file("transform", config)

        # Assert
        assert result["name"] == "transform-test-realm"
        # Check that transformations were applied
        test_client = next(
            c for c in result["clients"] if c["clientId"] == "test-client"
        )
        assert test_client["id"] == "client-uuid-123"
        assert test_client["secret"] == "client-secret-456"  # noqa s105

    def test_create_realm_config_file_template_not_found(self, tmp_path):
        """Тест обработки отсутствующего шаблона"""
        # Arrange
        config = RealmBuilderConfig(
            _template_dir_path=str(tmp_path), template_file_suffix=".realm.yml"
        )

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Preset file does not exist"):
            create_realm_config_file("nonexistent", config)


class TestExport:
    """Тесты для функции export"""

    def test_export_success(self, tmp_path):
        """Тест успешного экспорта"""
        # Arrange
        template_data = {
            "realm": {"name": "export-test-realm"},
            "envs": {"clients": []},
        }
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "test.realm.yml"
        template_file.write_text(yaml.dump(template_data))

        export_dir = tmp_path / "export"
        export_dir.mkdir()

        config = RealmBuilderConfig(
            _template_dir_path=str(template_dir),
            _template_export_dir_path=str(export_dir),
            template_file_suffix=".realm.yml",
            realm_file_suffix=".realm.json",
        )

        # Act
        export("test", "output", config)

        # Assert
        output_file = export_dir / "output.realm.json"
        assert output_file.exists()
        content = json.loads(output_file.read_text())
        assert content["name"] == "export-test-realm"

    def test_export_overwrite_behavior(self, tmp_path):
        # Arrange
        template_data = {
            "realm": {"name": "export-test-realm"},
            "envs": {"clients": []},
        }
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "test.realm.yml"
        template_file.write_text(yaml.dump(template_data))

        export_dir = tmp_path / "export"
        export_dir.mkdir()

        # Create existing file
        existing_file = export_dir / "output.realm.json"
        existing_file.write_text('{"existing": "content"}')

        config = RealmBuilderConfig(
            _template_dir_path=str(template_dir),
            _template_export_dir_path=str(export_dir),
            template_file_suffix=".realm.yml",
            realm_file_suffix=".realm.json",
            overwrite_existing_realm=True,
        )

        # Act
        export("test", "output", config)

        # Assert
        content = json.loads(existing_file.read_text())
        assert content["name"] == "export-test-realm"
