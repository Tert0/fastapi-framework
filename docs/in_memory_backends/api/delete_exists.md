# Delete and Exists
## Delete
You can Delete Keys with
```python
await redis.delete("my_key")
```
## Exists
You can check if a Key exists
```python
await redis.exists("this_exists")  # True
await redis.exists("this_dont_exists")  # False
```