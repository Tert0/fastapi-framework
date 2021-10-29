# Initialize

You have to initialize the Session System.

```python
from fastapi import FastAPI
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
```