from __future__ import annotations

import unittest
from unittest.mock import patch

import main


class MainTests(unittest.TestCase):
    def test_main_runs_console_interface_with_memory_backend_by_default(self) -> None:
        with patch("main.InMemoryDatabase") as database_mock, patch(
            "main.ConsoleInterface"
        ) as interface_mock:
            main.main([])

        database_mock.assert_called_once_with()
        interface_mock.assert_called_once_with(database=database_mock.return_value)
        interface_mock.return_value.run.assert_called_once_with()

    def test_main_builds_json_backend_with_custom_directory(self) -> None:
        with patch("main.JsonFileDatabase") as database_mock, patch(
            "main.ConsoleInterface"
        ) as interface_mock:
            main.main(["--backend", "json", "--data-dir", "./data/json"])

        database_mock.assert_called_once_with(main.Path("./data/json"))
        interface_mock.assert_called_once_with(database=database_mock.return_value)

    def test_main_builds_csv_backend_with_default_directory(self) -> None:
        with patch("main.CsvFileDatabase") as database_mock, patch(
            "main.ConsoleInterface"
        ) as interface_mock:
            main.main(["--backend", "csv"])

        database_mock.assert_called_once_with(main.Path("data") / "csv")
        interface_mock.assert_called_once_with(database=database_mock.return_value)
