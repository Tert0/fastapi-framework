# Increase and Decrease
You can Increase and Decrease Int Values.
```python
await redis.incr("my_key") # my_key + 1
```
```python
await redis.decr("my_key") # my_key - 1
```
The Functions will raise a `ValueError` if the Key is not an Int.

If the Key doesn't exists it will set the Key to `1` or `-1`