"""Type definitions for truthfulness evaluation."""

from typing import Literal

# Type definitions
Verdict = Literal["SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO", "UNVERIFIABLE"]
