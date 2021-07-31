# Config
The `Config` Module is a simple "Config Parser".

## Example

```python
from fastapi_framework import Config, ConfigField


class MyConfig(Config):
    name: str = ConfigField()
    version: str = ConfigField("v1.0")
    timestamp: int = ConfigField(name="_timestamp")


print(MyConfig.name)
print(MyConfig.version)
print(MyConfig.timestamp)
```
Content of `config.yaml`:
```yaml
name: My cool Name
_timestamp: 123456789
```
Result:
```
My cool Name
v1
123456789
```
As you can see if the `version` Config isn't set it will have the default value!

You can use another Key for the Config as the Variables name by setting `name`
 to the Name

!!! tip
    Config Fields can have a Type Hint and will get converted to this type

!!! tip
    You can define `CONFIG_PATH` to set the Path of the File

!!! tip
    You can define `CONFIG_TYPE` to set the File Type e.g. `yaml`, `json` and `toml`