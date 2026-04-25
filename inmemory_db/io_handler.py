"""Classes related to console input and output."""

from __future__ import annotations

from typing import Protocol


class IOHandler(Protocol):
    """Protocol for user input and output operations."""

    def input(self, prompt: str) -> str:
        """Read a string from the user."""

    def output(self, message: str) -> None:
        """Display a string to the user."""


class ConsoleIO:
    """Standard console implementation of input and output."""

    def input(self, prompt: str) -> str:
        return input(prompt)

    def output(self, message: str) -> None:
        print(message)
