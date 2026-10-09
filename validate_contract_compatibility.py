"""Compatibility import shim for the contract validator.

Tests and CI expect the module to be importable directly from the repository root,
while the implementation remains under scripts/ for normal Python package layout.
"""

from scripts.validate_contract_compatibility import (
    check_compatibility,
    main,
    validate_compatibility,
    validate_contract_compatibility,
)

__all__ = [
    "check_compatibility",
    "main",
    "validate_compatibility",
    "validate_contract_compatibility",
]
