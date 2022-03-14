import random
from unittest.mock import ANY
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock

from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi_framework import RAMBackend
from fastapi_framework.session import (
    fetch_session_id,
    generate_session_id,
    session_middleware,
    Session,
    SessionNotExists,
)


class TestSession(IsolatedAsyncioTestCase):
    async def test_fetch_session_id_without_session_id(self):
        request = MagicMock()
        del request.state.session_id
        request.cookies.get.return_value = "TEST_SESSION_ID"

        await fetch_session_id(request)

        request.cookies.get.assert_called_with("SESSION_ID")
        self.assertEqual(request.state.session_id, "TEST_SESSION_ID")

    async def test_fetch_session_id_with_session_id(self):
        request = MagicMock()
        request.state.session_id = "TEST_SESSION_ID"
        request.cookies.get.return_value = "FAKE_TEST_SESSION_ID"

        await fetch_session_id(request)

        request.cookies.get.assert_not_called()
        self.assertEqual(request.state.session_id, "TEST_SESSION_ID")

    async def test_generate_session_id(self):
        random.seed(1)

        session_id = await generate_session_id()

        self.assertEqual(
            session_id,
            "i0VpEBOWfbZAVaBSo63bbH6xnAbnBEoonCrbZINl91huSS6AZPsK20FKcpXzkIRPxBFWGyEbcR8KykF8VH1oF7JCqH7aWY2TYGIA",
        )

    async def test_session_middleware_with_new_session(self):
        session_system = AsyncMock()

        session_system.session_exists.return_value = False
        session_system.create_session.return_value = "TEST_GENERATED_SESSION_ID"

        request = MagicMock()
        call_next = AsyncMock()

        response = MagicMock()

        call_next.return_value = response

        session_system.add_session_id.return_value = response

        middleware_response = await session_middleware(session_system, request, call_next)

        session_system.fetch_session_id.assert_called_once_with(request)
        session_system.create_session.assert_called_once()
        call_next.assert_called_once_with(request)
        session_system.add_session_id.assert_called_once_with(response, "TEST_GENERATED_SESSION_ID")
        self.assertEqual(middleware_response, response)

    async def test_session_middleware_with_old_session(self):
        session_system = AsyncMock()

        session_system.session_exists.return_value = True

        request = MagicMock()
        call_next = AsyncMock()

        response = MagicMock()

        call_next.return_value = response

        session_system.add_session_id.return_value = response

        middleware_response = await session_middleware(session_system, request, call_next)

        session_system.fetch_session_id.assert_called_once_with(request)
        session_system.create_session.assert_not_called()
        call_next.assert_called_once_with(request)
        session_system.add_session_id.assert_not_called()
        self.assertEqual(middleware_response, response)

    async def test_create_session_system(self):
        app = MagicMock()
        model = BaseModel
        default_data = BaseModel()

        session = Session(app, model, default_data)

        app.add_middleware.assert_called_once_with(BaseHTTPMiddleware, dispatch=ANY)
        self.assertEqual(session.model, model)
        self.assertEqual(session.default_data, default_data)
        self.assertEqual(session.session_id_callback, fetch_session_id)
        self.assertEqual(session.generate_session_id_callback, generate_session_id)

    async def test_middleware_wrapper(self):
        app = MagicMock()
        request = MagicMock()
        call_next = AsyncMock()
        session_middleware_mock = MagicMock()
        session_middleware_mock.return_value = MagicMock()

        session = Session(app, BaseModel, BaseModel(), middleware=session_middleware_mock)

        middleware = app.add_middleware.call_args[1]["dispatch"]

        await middleware(request, call_next)

        session_middleware_mock.assert_called_once_with(session, request, call_next)

    async def test_middleware_wrapper_async(self):
        app = MagicMock()
        request = MagicMock()
        call_next = AsyncMock()
        session_middleware_mock = AsyncMock()
        session_middleware_mock.return_value = MagicMock()

        session = Session(app, BaseModel, BaseModel(), middleware=session_middleware_mock)

        middleware = app.add_middleware.call_args[1]["dispatch"]

        await middleware(request, call_next)

        session_middleware_mock.assert_called_once_with(session, request, call_next)

    async def test_fetch_session_id(self):
        request = MagicMock()
        session = MagicMock()
        session.session_id_callback.return_value = None

        await Session.fetch_session_id(session, request)

        session.session_id_callback.assert_called_once_with(request)

    async def test_fetch_session_id_async(self):
        request = MagicMock()
        session = AsyncMock()
        session.session_id_callback.return_value = None

        await Session.fetch_session_id(session, request)

        session.session_id_callback.assert_called_once_with(request)

    async def test_session_exists_with_existing_session_id(self):
        request = MagicMock()
        request.state.session_id = "TEST_SESSION_ID"

        session = AsyncMock()

        exists = await Session.session_exists(session, request)

        self.assertEqual(exists, False)

    @patch("fastapi_framework.session.redis_dependency", new_callable=AsyncMock)
    async def test_session_exists_with_existing_session(self, redis_dependency_mock: AsyncMock):
        ram_backend = RAMBackend()
        redis_dependency_mock.return_value = ram_backend

        request = MagicMock()
        request.state.session_id = "TEST_SESSION_ID"
        await ram_backend.set("session:id:TEST_SESSION_ID", "data")

        session = AsyncMock()

        exists = await Session.session_exists(session, request)

        self.assertEqual(exists, True)

    async def test_session_exists_without_existing_session_id(self):
        request = MagicMock()
        request.state.session_id = None
        session = AsyncMock()

        exists = await Session.session_exists(session, request)

        self.assertEqual(exists, False)

    @patch("fastapi_framework.session.redis_dependency", new_callable=AsyncMock)
    async def test_create_session(self, redis_dependency_mock: AsyncMock):
        ram_backend = RAMBackend()
        redis_dependency_mock.return_value = ram_backend

        session = AsyncMock()
        session.session_expire = 10**10
        session.generate_session_id_callback = MagicMock()
        session.generate_session_id_callback.return_value = "TEST_GENERATED_SESSION"
        session.default_data.json = MagicMock()
        session.default_data.json.return_value = '{"default": "data"}'

        session_id = await Session.create_session(session)

        self.assertEqual(session_id, "TEST_GENERATED_SESSION")
        self.assertEqual(await ram_backend.exists(f"session:id:{session_id}"), True)
        self.assertEqual(await ram_backend.get(f"session:id:{session_id}"), b'{"default": "data"}')

    @patch("fastapi_framework.session.redis_dependency", new_callable=AsyncMock)
    async def test_create_session_async(self, redis_dependency_mock: AsyncMock):
        ram_backend = RAMBackend()
        redis_dependency_mock.return_value = ram_backend

        session = AsyncMock()
        session.session_expire = 10**10
        session.generate_session_id_callback.return_value = "TEST_GENERATED_SESSION"
        session.default_data.json = MagicMock()
        session.default_data.json.return_value = '{"default": "data"}'

        session_id = await Session.create_session(session)

        self.assertEqual(session_id, "TEST_GENERATED_SESSION")
        self.assertEqual(await ram_backend.exists(f"session:id:{session_id}"), True)
        self.assertEqual(await ram_backend.get(f"session:id:{session_id}"), b'{"default": "data"}')

    async def test_add_session_id(self):
        session = AsyncMock()
        session.session_expire = 0
        response = MagicMock()

        new_response = await Session.add_session_id(session, response, "TEST_SESSION_ID")

        response.set_cookie.assert_called_once_with("SESSION_ID", "TEST_SESSION_ID", httponly=True)
        self.assertEqual(new_response, response)

    @patch("fastapi_framework.session.redis_dependency", new_callable=AsyncMock)
    async def test_update_session(self, redis_dependency_mock: AsyncMock):
        ram_backend = RAMBackend()
        redis_dependency_mock.return_value = ram_backend

        session = AsyncMock()
        session.session_expire = 10**10
        request = MagicMock()
        request.state.session_id = "TEST_SESSION_ID"
        data = MagicMock()
        data.json.return_value = '{"new": "data"}'

        await Session.update_session(session, request, data)

        self.assertEqual(await ram_backend.get("session:id:TEST_SESSION_ID"), b'{"new": "data"}')

    @patch("fastapi_framework.session.redis_dependency", new_callable=AsyncMock)
    async def test_get_data(self, redis_dependency_mock: AsyncMock):
        ram_backend = RAMBackend()
        redis_dependency_mock.return_value = ram_backend
        await ram_backend.set("session:id:TEST_SESSION_ID", "TEST_DATA")

        request = MagicMock()
        request.state.session_id = "TEST_SESSION_ID"
        session = AsyncMock()
        session.model.parse_raw = MagicMock()
        session.model.parse_raw.return_value = BaseModel()

        data = await Session.get_data(session, request)

        self.assertEqual(data, BaseModel())
        session.model.parse_raw.assert_called_once_with(b"TEST_DATA")

    @patch("fastapi_framework.session.redis_dependency", new_callable=AsyncMock)
    async def test_get_data_without_session(self, redis_dependency_mock: AsyncMock):
        ram_backend = RAMBackend()
        redis_dependency_mock.return_value = ram_backend

        request = MagicMock()
        request.state.session_id = "TEST_SESSION_ID_DONT_EXISTS"
        session = AsyncMock()

        with self.assertRaises(SessionNotExists):
            await Session.get_data(session, request)
