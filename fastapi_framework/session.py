import random
import string
from typing import Union, Callable, Coroutine, Type, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.requests import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .redis import redis_dependency


async def fetch_session_id(request: Request) -> None:
    if not hasattr(request.state, "session_id"):
        request.state.session_id = request.cookies.get("SESSION_ID")


async def generate_session_id() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=100))


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


class SessionNotExists(Exception):
    pass


class Session:
    model: Type[BaseModel]
    default_data: BaseModel
    session_id_callback: Union[Callable[[Request], None], Callable[[Request], Coroutine]]
    generate_session_id_callback: Union[Callable[[], str], Callable[[], Coroutine]]

    def __init__(
        self,
        app: FastAPI,
        model: Type[BaseModel],
        default_data: BaseModel,
        session_id_callback: Union[Callable[[Request], None], Callable[[Request], Coroutine]] = fetch_session_id,
        generate_session_id_callback: Union[Callable[[], str], Callable[[], Coroutine]] = generate_session_id,
        middleware: Union[
            Callable[["Session", Request, RequestResponseEndpoint], Response],
            Callable[["Session", Request, RequestResponseEndpoint], Coroutine],
        ] = session_middleware,
    ) -> None:
        app.add_middleware(BaseHTTPMiddleware, dispatch=middleware)
        self.model = model
        self.default_data = default_data
        self.session_id_callback = session_id_callback
        self.generate_session_id_callback = generate_session_id_callback

    async def fetch_session_id(self, request: Request) -> None:
        result: Union[None, Coroutine] = self.session_id_callback(request)
        if isinstance(result, Coroutine):
            await result

    async def session_exists(self, request: Request) -> bool:
        return getattr(request.state, "session_id") is not None

    async def create_session(self) -> str:
        result: Union[str, Coroutine] = self.generate_session_id_callback()
        session_id: str
        if isinstance(result, Coroutine):
            session_id = await result
        else:
            session_id = result
        await (await redis_dependency()).set(f"session:id:{session_id}", self.default_data.json())
        return session_id

    async def add_session_id(self, response: Response, session_id: str) -> Response:
        response.set_cookie("SESSION_ID", session_id)
        return response

    async def update_session(self, request: Request, data: BaseModel) -> None:
        await (await redis_dependency()).set(f"session:id:{request.state.session_id}", data.json())

    async def get_data(self, request: Request) -> BaseModel:
        raw_data: str = await (await redis_dependency()).get(f"session:id:{request.state.session_id}")
        if raw_data is None:
            raise SessionNotExists()
        data: BaseModel = self.model.parse_raw(raw_data)
        return data
