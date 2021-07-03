from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi_framework.database import select, filter_by, exists, delete, db


class TestDatabase(IsolatedAsyncioTestCase):
    @patch("fastapi_framework.database.sa_select")
    async def test_select(self, sa_select: MagicMock):
        model = MagicMock()

        result = select(model)

        sa_select.assert_called_with(model)
        self.assertEqual(result, sa_select())

    @patch("fastapi_framework.database.select")
    async def test_filter_by(self, select_patch: MagicMock):
        model = MagicMock()
        filters = {
            "param1": MagicMock(),
            "param2": MagicMock(),
            "param3": MagicMock(),
            "param4": MagicMock(),
            "param5": MagicMock(),
        }

        result = filter_by(model, **filters)

        select_patch.assert_called_once_with(model)
        select_patch().filter_by.assert_called_once_with(**filters)
        self.assertEqual(select_patch().filter_by(), result)

    @patch("fastapi_framework.database.sa_exists")
    async def test_exists(self, sa_exists: MagicMock):
        model = MagicMock()
        filters = {
            "param1": MagicMock(),
            "param2": MagicMock(),
            "param3": MagicMock(),
            "param4": MagicMock(),
            "param5": MagicMock(),
        }

        result = exists(model, **filters)

        sa_exists.assert_called_once_with(model, **filters)
        self.assertEqual(result, sa_exists())

    @patch("fastapi_framework.database.sa_delete")
    async def test_delete(self, sa_delete: MagicMock):
        model = MagicMock()

        result = delete(model)

        sa_delete.assert_called_once_with(model)
        self.assertEqual(result, sa_delete())

    @patch("fastapi_framework.database.db._session")
    async def test_add_row(self, async_session_patch: AsyncMock):
        row = MagicMock()
        await db.add(row)
        async_session_patch.add.assert_called_with(row)
