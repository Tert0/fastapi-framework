from typing import Dict, Any

from fastapi_framework import disabled_modules

CONFIG_BLOCKLIST = ["CONFIG_PATH", "CONFIG_TYPE"]
CONFIG_FILE_PATH_DEFAULT = "config.yaml"
CONFIG_TYPE_DEFAULT = "yaml"


class ConfigMeta(type):
    def __new__(mcs, name, bases, dct):
        config_entries: Dict[str, Any] = {}
        config_class = super().__new__(mcs, name, bases, dct)
        if "config" in disabled_modules:
            return config_class
        annotations: Dict = dct.get("__annotations__", {})

        for annotation in annotations.keys():
            if annotation in CONFIG_BLOCKLIST:
                continue
            value = dct.get(annotation)
            config_entries[annotation] = (value, annotations.get(annotation))

        config_file_path = dct.get("CONFIG_PATH") or CONFIG_FILE_PATH_DEFAULT
        config_type = dct.get("CONFIG_TYPE") or CONFIG_TYPE_DEFAULT

        with open(config_file_path, "r") as file:
            data: str = file.read()

        config: Dict

        if config_type.lower() == "yaml":
            import yaml
            config = yaml.load(data, Loader=yaml.CLoader)
        elif config_type.lower() == "json":
            import json
            config = json.loads(data)
        elif config_type.lower() == "toml":
            import toml
            config = toml.loads(data)
        else:
            raise Exception(f"Config Type '{config_type}' is not Supported")

        del data

        config = config or {}
        print(config)
        print(config_entries)
        for key in config_entries.keys():
            if key in config.keys():
                entry_type = config_entries.get(key)[1]
                if entry_type.__module__ == "typing":
                    entry_type = entry_type.__origin__
                value = entry_type(config[key]) if config[key] is not None else None
                setattr(config_class, key, value)
            else:
                value = config_entries.get(key)[0]
                setattr(config_class, key, value)

        return config_class


class Config(metaclass=ConfigMeta):
    pass
