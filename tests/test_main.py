"""Tests for the application entry point."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import main


class MainTests(unittest.TestCase):
    def test_main_runs_console_interface(self) -> None:
        with patch("main.ConsoleInterface") as interface_mock:
            main.main()

        interface_mock.assert_called_once_with()
        interface_mock.return_value.run.assert_called_once_with()
