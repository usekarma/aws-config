#!/usr/bin/env python3
"""Validate per-component configuration locally, with no AWS calls."""

import argparse
import re
import sys

from config_validation import ROOT, load_json, validate_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", help="Component/nickname; omit to validate all bindings/configs"
    )
    parser.add_argument("--environment", help="Explicit local environment filter")
    args = parser.parse_args()
    if args.config and not re.fullmatch(r"[a-z0-9-]+/[a-zA-Z0-9_-]+", args.config):
        parser.error("--config must be component/nickname")
    if args.environment and not re.fullmatch(r"[a-zA-Z0-9_-]+", args.environment):
        parser.error("Invalid environment")
    files = list((ROOT / "account_environments").glob("*.json")) if not args.config else []
    files += list(
        (ROOT / "iac").glob(f"{args.environment or '*'}/{args.config or '*/*'}/config.json")
    )
    if not files:
        raise ValueError("No matching configuration found")
    for path in sorted(files):
        validate_config(path.relative_to(ROOT), load_json(path))
    print(f"Validated {len(files)} configuration/binding files against local contracts.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
