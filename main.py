from __future__ import annotations

import argparse
from pathlib import Path

from inmemory_db import ConsoleInterface, CsvFileDatabase, InMemoryDatabase, JsonFileDatabase


def build_database(backend: str, data_dir: str | None = None):
    if backend == "memory":
        return InMemoryDatabase()

    storage_path = Path(data_dir) if data_dir else Path("data") / backend
    if backend == "json":
        return JsonFileDatabase(storage_path)
    if backend == "csv":
        return CsvFileDatabase(storage_path)

    raise ValueError(f"Неизвестный backend: {backend}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Запуск консольной СУБД.")
    parser.add_argument(
        "--backend",
        choices=("memory", "json", "csv"),
        default="memory",
        help="Тип хранилища данных.",
    )
    parser.add_argument(
        "--data-dir",
        help="Каталог для файлового backend. Для memory не используется.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    database = build_database(args.backend, args.data_dir)
    interface = ConsoleInterface(database=database)
    interface.run()


if __name__ == "__main__":
    main()
