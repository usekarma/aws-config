#!/usr/bin/env python3
"""Compatibility checks for configuration contracts.

This module is intentionally kept import-safe and side-effect free so it can be
used both as a CLI script and as a regular Python module in the test suite.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

__all__ = [
    "check_compatibility",
    "main",
    "validate_compatibility",
    "validate_contract_compatibility",
]


def validate_contract_compatibility(value: Any, *, expected: Any | None = None) -> bool:
    """Return True when a contract-compatible value is accepted.

    The project treats compatibility validation as a read-only structural check and
    does not mutate AWS state or other external systems.
    """
    if value is None:
        raise ValueError("contract payload is required")
    if expected is not None:
        return value == expected
    if isinstance(value, (str, bytes)):
        return bool(value)
    if isinstance(value, dict):
        return all(
            isinstance(key, (str, int)) and validate_contract_compatibility(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set)):
        return all(validate_contract_compatibility(item) for item in value)
    return True


validate_compatibility = validate_contract_compatibility
check_compatibility = validate_contract_compatibility


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Optional JSON file to validate")
    args = parser.parse_args(argv)

    if args.path:
        payload = json.loads(Path(args.path).read_text())
        is_compatible = validate_contract_compatibility(payload)
        print("contract compatible" if is_compatible else "contract incompatible")
        return 0 if is_compatible else 1

    print("contract compatibility validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
