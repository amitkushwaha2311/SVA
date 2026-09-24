"""
Simple Python package for SVA test fixture.
"""


def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


def greet(name: str) -> str:
    """Return a greeting string."""
    if not name:
        raise ValueError("name cannot be empty")
    return f"Hello, {name}!"


class Calculator:
    """A simple calculator class."""

    def __init__(self) -> None:
        self._history: list[int] = []

    def add(self, a: int, b: int) -> int:
        result = a + b
        self._history.append(result)
        return result

    def history(self) -> list[int]:
        return list(self._history)
