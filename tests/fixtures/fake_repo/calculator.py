"""A tiny calculator module used as internal-verification ground truth.

The docstrings and signatures here are deliberately concrete so that
documentation claims can be checked against real code.
"""

from pydantic import BaseModel


class Operation(BaseModel):
    """A validated pair of integer operands."""

    a: int
    b: int


def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b
