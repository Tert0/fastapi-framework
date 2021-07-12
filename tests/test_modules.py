from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from fastapi_framework.modules import check_dependencies
from fastapi_framework import modules


class TestModules(IsolatedAsyncioTestCase):
    @patch.object(modules, "disabled_modules", [])
    async def test_check_dependencies_no_disabled(self):
        check_dependencies()

    @patch.object(modules, "disabled_modules", ["database"])
    async def test_check_dependencies_redis_disabled(self):
        self.assertRaises(Exception, check_dependencies)

    @patch.object(modules, "disabled_modules", ["redis", "rate_limit", "jwt_auth"])
    async def test_check_dependencies_disabled_all_depends_on_redis(self):
        check_dependencies()
