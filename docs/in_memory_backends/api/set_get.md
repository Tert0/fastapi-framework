# Set and Get
You can set Values with
```python
await redis.set("my_key", "a value")
```
and get them with
```python
print(await redis.get("my_key"))
#  a value
```
`GET` will return `None` if the key doesn't exist or is expired.

The `SET` Command has some other Arguments
```python
expire_seconds = 5
expire_milliseconds = 555
await redis.set(key="my_key", value="a value", expire=expire_seconds, pexpire=expire_milliseconds, exists=RAMBackend.SET_IF_EXIST)
```
- key: The Redis Key
- value: The Value
- expire: The Expire time in Seconds
- pexpire: The Expire time in Milliseconds
- exists: Exist Conditions