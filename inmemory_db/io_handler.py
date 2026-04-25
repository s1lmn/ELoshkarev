from __future__ import annotations

from typing import Protocol


class IOHandler(Protocol):

    def input(self, prompt: str) -> str:
        """Прочитать строку от пользователя"""

    def output(self, message: str) -> None:
        """Отобразить пользователю строку"""


class ConsoleIO:

    def input(self, prompt: str) -> str:
        return input(prompt)

    def output(self, message: str) -> None:
        print(message)
