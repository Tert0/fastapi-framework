# Custom Callbacks and Middleware

## `session_id_callback`

This callback is used to fetch the session id from the user.

### Function Signature
```python
from fastapi.requests import Request

async def session_id_callback(request: Request) -> None:
    pass
```
or
```python
from fastapi.requests import Request

def session_id_callback(request: Request) -> None:
    pass
```

### Type
```python
from typing import Union, Callable, Coroutine
from fastapi.requests import Request

session_id_callback: Union[Callable[[Request], None], Callable[[Request], Coroutine]]
```

### Standard Implementation

```python
from fastapi.requests import Request

async def fetch_session_id(request: Request) -> None:
    if not hasattr(request.state, "session_id"):
        request.state.session_id = request.cookies.get("SESSION_ID")
```

!!! important
    Make sure that only the `Make sure that only the "test" part is changed.` part is changed.

## `generate_session_id_callback`

This callback is used to generate a new session id.

### Function Signature
```python
async def generate_session_id() -> str:
    pass
```
or
```python
def generate_session_id() -> str:
    pass
```

### Type
```python
from typing import Union, Callable, Coroutine

generate_session_id_callback: Union[Callable[[], str], Callable[[], Coroutine]]
```

### Standard Implementation

```python
import random
import string

async def generate_session_id() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=100))
```

!!! note
    The Session ID Entropy should be `64 Bits` or bigger.
    
    Source: [OWASP Cheatsheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#session-id-entropy)

## Middleware

### Function Signature

```python
from fastapi.requests import Request
from fastapi.responses import Response
from starlette.middleware.base import RequestResponseEndpoint

async def session_middleware(
    session_system: "Session", request: Request, call_next: RequestResponseEndpoint
) -> Response:
    pass
```

### Type

```python
from typing import Union, Callable, Coroutine
from fastapi.requests import Request
from fastapi.responses import Response
from starlette.middleware.base import RequestResponseEndpoint

middleware: Union[
            Callable[["Session", Request, RequestResponseEndpoint], Response],
            Callable[["Session", Request, RequestResponseEndpoint], Coroutine],
        ]
```

### Standard Implementation

```python
from typing import Optional
from fastapi.requests import Request
from fastapi.responses import Response
from starlette.middleware.base import RequestResponseEndpoint


async def session_middleware(
    session_system: "Session", request: Request, call_next: RequestResponseEndpoint
) -> Response:
    session_id: Optional[str] = None
    await session_system.fetch_session_id(request)
    if not await session_system.session_exists(request):
        session_id = await session_system.create_session()

        request.state.session_id = session_id

    response: Response = await call_next(request)

    if session_id:
        response = await session_system.add_session_id(response, session_id)
    return response
```
