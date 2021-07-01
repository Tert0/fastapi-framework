import logging
from unittest import TestCase
from unittest.mock import MagicMock, patch
from fastapi_framework.logger import logging_formatter, get_logger


class LoggerTest(TestCase):
    def test_logging_format(self):
        self.assertIsInstance(logging_formatter, logging.Formatter)
        self.assertEqual("[%(asctime)s] [%(levelname)s] %(message)s", logging_formatter._fmt)

    @patch("logging.getLogger")
    def test_get_logger(self, getLogger_patch: MagicMock):
        name = "logger_name"

        result = get_logger(name)

        getLogger_patch.assert_called_with(name)
        self.assertEqual(result, getLogger_patch())
