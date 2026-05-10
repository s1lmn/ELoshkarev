from __future__ import annotations

import unittest
from unittest.mock import patch

from src.db import __main__


class TestMain(unittest.TestCase):
    @patch("src.db.__main__.run")
    def test_main_calls_run(self, run_mock) -> None:
        __main__.main()
        run_mock.assert_called_once_with()
