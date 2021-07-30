# Config
The `Config` Module is a simple "Config Parser".

## Example

```python
from fastapi_framework import Config


class MyConfig(Config):
    name: str
    version: str = "v1"
    timestamp: int


print(MyConfig.name)
print(MyConfig.version)
print(MyConfig.timestamp)
```
Content of `config.yaml`:
```yaml
name: My cool Name
timestamp: 123456789
```
Result:
```
My cool Name
v1
123456789
```
As you can see if the `version` Config isn't set it will have the default value!

!!! attention
    All Config Items must have a type hint!

!!! tip
    You can define `CONFIG_PATH` to set the Path of the File

With `CONFIG_TYPE` you can set the File Type e.g. `yaml`, `json` and `toml`