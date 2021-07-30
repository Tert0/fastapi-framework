from unittest import TestCase
from unittest.mock import patch, MagicMock, mock_open
from fastapi_framework.config import Config


class TestConfig(TestCase):
    test_yaml_config_data = "some_data: a value"
    test_json_config_data = "{\"some_data\": \"a value\"}"
    test_toml_config_data = "some_data = \"a value\""
    test_yaml_config_with_typing_data = "items:\n  - an item\n  - an other item"

    @patch("builtins.open", mock_open(read_data=test_yaml_config_data))
    def test_yaml_config(self):
        class MyConfig(Config):
            some_data: str = "test"
            some_other_data: str = "default value"

        self.assertEqual(MyConfig.some_data, "a value")
        self.assertEqual(MyConfig.some_other_data, "default value")

    @patch("builtins.open", mock_open(read_data=test_json_config_data))
    def test_json_config(self):
        class MyConfig(Config):
            CONFIG_PATH = "config.json"
            CONFIG_TYPE = "json"

            some_data: str
            some_other_data: str = "default value"

        self.assertEqual(MyConfig.some_data, "a value")
        self.assertEqual(MyConfig.some_other_data, "default value")

    @patch("builtins.open", mock_open(read_data=test_toml_config_data))
    def test_toml_config(self):
        class MyConfig(Config):
            CONFIG_PATH = "config.toml"
            CONFIG_TYPE = "toml"

            some_data: str
            some_other_data: str = "default value"

        self.assertEqual(MyConfig.some_data, "a value")
        self.assertEqual(MyConfig.some_other_data, "default value")

    @patch("builtins.open", mock_open(read_data=test_yaml_config_data))
    def test_yaml_config_with_blocked_name(self):
        class MyConfig(Config):
            CONFIG_PATH: str = "config.yaml"
            CONFIG_TYPE: str = "yaml"

            some_data: str
            some_other_data: str = "default value"

        self.assertEqual(MyConfig.some_data, "a value")
        self.assertEqual(MyConfig.some_other_data, "default value")

    @patch("builtins.open", mock_open(read_data=test_yaml_config_data))
    def test_config_type_dont_exists(self):
        with self.assertRaises(Exception):
            class MyConfig(Config):
                CONFIG_TYPE = "type doesn't exists"

                some_data: str
                some_other_data: str = "default value"

    @patch("builtins.open", mock_open(read_data=test_yaml_config_with_typing_data))
    def test_yaml_config_with_typing(self):
        from typing import List

        class MyConfig(Config):
            items: List

        self.assertEqual(MyConfig.items, ["an item", "an other item"])
