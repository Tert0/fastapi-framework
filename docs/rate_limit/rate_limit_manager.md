# Rate Limit Manager
To use the Raid Limit Feature you have to initialise the Rate Limit Manager.
```python
from fastapi_framework import RateLimitManager, redis_dependency
await redis_dependency.init()
await RateLimitManager.init(await redis_dependency())
```
You can set

- `get_uuid`
- `callback`

## `get_uuid` Setting
Callback function that returns a UUID used for Identification.

Example:
```python
from fastapi import Request
async def default_get_uuid(request: Request) -> str:
    """Default getter for UUID working with Users IP"""
    return f"{request.client.host}"
```
## `callback`
Callback function that will be called when a User gets Raid Limited and tries it again.

Example:
```python
from fastapi import HTTPException
from typing import Dict
async def default_callback(headers: Dict):
    """Default Error Callback when get Raid Limited"""
    raise HTTPException(429, detail="Too Many Requests", headers=headers)
```
You should return the Headers to the users