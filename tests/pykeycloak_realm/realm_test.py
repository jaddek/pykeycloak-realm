from unittest.mock import patch

import pytest

from pykeycloak_realm.config import RealmBuilderConfig
from pykeycloak_realm.realm import main


class TestRealmMain:
    @patch("pykeycloak_realm.realm.export")
    @patch(
        "sys.argv",
        ["realm.py", "--from-realm", "test-template", "--to-realm", "test-output"],
    )
    def test_main_success(self, mock_export):
        main()
        mock_export.assert_called_once()
        _, args = mock_export.call_args
        assert args["from_template"] == "test-template"
        assert args["to_file"] == "test-output"
        assert isinstance(args["config"], RealmBuilderConfig)

    @patch("pykeycloak_realm.realm.export")
    @patch(
        "sys.argv",
        ["realm.py", "--from-realm", "prod-template", "--to-realm", "prod-output"],
    )
    def test_main_success_with_different_args(self, mock_export):
        main()
        mock_export.assert_called_once()
        _, args = mock_export.call_args
        assert args["from_template"] == "prod-template"
        assert args["to_file"] == "prod-output"
        assert isinstance(args["config"], RealmBuilderConfig)

    @patch("sys.argv", ["realm.py"])
    def test_main_missing_arguments(self):
        with pytest.raises(SystemExit):
            main()

    @patch("sys.argv", ["realm.py", "--from-realm", "test-template"])
    def test_main_missing_to_realm(self):
        """Test without --to-realm"""
        with pytest.raises(SystemExit):
            main()

    @patch("sys.argv", ["realm.py", "--to-realm", "test-output"])
    def test_main_missing_from_realm(self):
        """Test without --from-realm"""
        with pytest.raises(SystemExit):
            main()
