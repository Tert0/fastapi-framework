# Expires
## Set Expire Time
You can set the Expire time in Seconds or Milliseconds with
```python
await redis.expire("my_key", 5) # 5 Seconds
await redis.pexpire("my_key", 1200) # 1200 Milliseconds => 1.2 Seconds
```
## Get Expire Time
You can get the Expire tim of a Key with
```python
await redis.ttl("my_key")  # 5
await redis.pttl("my_key")  # 1200
await redis.pttl("this_key_dont_exists")  # -2
await redis.pttl("expired_key")  # -1
```
- TTL Returns the Seconds
- PTTL Returns the Milliseconds
- If the Key doesn't exists it will return -2
- If the Key is expired it will return -1