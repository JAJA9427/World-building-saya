"""Backwards compatible entry point delegating to the new CLI."""
from __future__ import annotations

import sys
from typing import Sequence

from .cli import main as cli_main


def main(argv: Sequence[str] | None = None) -> int:
    return cli_main(argv)


if __name__ == "__main__":  # pragma: no cover - module execution
    sys.exit(main())
