#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.diagnostics import collect_runtime_diagnostics, format_runtime_diagnostics


def main() -> None:
    print(format_runtime_diagnostics(collect_runtime_diagnostics()))


if __name__ == "__main__":
    main()
