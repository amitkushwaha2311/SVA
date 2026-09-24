"""Tests for mypackage.utils — SVA test fixture."""

import pytest
from src.mypackage.utils import add, greet, Calculator


def test_add_positive():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-1, -2) == -3


def test_greet_valid():
    assert greet("Alice") == "Hello, Alice!"


def test_greet_empty_raises():
    with pytest.raises(ValueError, match="name cannot be empty"):
        greet("")


class TestCalculator:
    def test_add(self):
        calc = Calculator()
        assert calc.add(10, 5) == 15

    def test_history(self):
        calc = Calculator()
        calc.add(1, 2)
        calc.add(3, 4)
        assert calc.history() == [3, 7]
