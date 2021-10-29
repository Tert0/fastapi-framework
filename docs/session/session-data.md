# Session Data

## Get Data
You can get the Session Data with the `Session.get_data` dependency.
```python
from fastapi import FastAPI, Depends
from fastapi_framework import Session
from fastapi_framework.session import fetch_session_id, generate_session_id, session_middleware
from pydantic import BaseModel


class SessionData(BaseModel):
    username: str
    age: int


app = FastAPI()

session = Session(
    app,  # FastAPI App
    SessionData,  # Pydantic Model
    SessionData(
        username="test_user",
    ),  # Default Data
    session_id_callback=fetch_session_id,  # Fetch Session ID Callback
    generate_session_id_callback=generate_session_id,  # Session ID Generator
    middleware=session_middleware,  # Session System Middleware
    session_expire=60 * 60 * 24,  # Session Expire Time in Seconds
)

@app.get("/")
async def route(data: SessionData = Depends(session.get_data)):
    return data.json()
```

## Update Data
You can update the Session Data with `Session.update_session`.
```python
from fastapi import FastAPI, Depends
from fastapi.requests import Request
from fastapi_framework import Session
from fastapi_framework.session import fetch_session_id, generate_session_id, session_middleware
from pydantic import BaseModel


class SessionData(BaseModel):
    username: str
    age: int


app = FastAPI()

session = Session(
    app,  # FastAPI App
    SessionData,  # Pydantic Model
    SessionData(
        username="test_user",
    ),  # Default Data
    session_id_callback=fetch_session_id,  # Fetch Session ID Callback
    generate_session_id_callback=generate_session_id,  # Session ID Generator
    middleware=session_middleware,  # Session System Middleware
    session_expire=60 * 60 * 24,  # Session Expire Time in Seconds
)

@app.post("/{value}")
async def route(request: Request, value: str, data: SessionData = Depends(session.get_data)):
    data.key = value
    await session.update_session(request, data)
    return "Done"
```
