# Sets
## smembers
With `smembers` you can get all Members of an Set.
```python
await redis.smembers("my_set")  # {"item1", "item2"}
```
## sadd
With `sadd` you can add an Item to a Set.
```python
await redis.sadd("my_set", "item1")
```
## srem
With `srem` you can remove an Item from a Set.
```python
await redis.srem("my_set", "item1")
```