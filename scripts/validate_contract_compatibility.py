#!/usr/bin/env python3
"""Verify that aws-iac explicitly supports this aws-config contract version."""

import argparse
import json
from pathlib import Path


def load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError as exc:
        raise ValueError(f"Missing contract file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def check_compatibility(aws_config_dir, aws_iac_dir):
    config_contract = load_json(Path(aws_config_dir) / "contracts" / "config-contract.json")
    iac_compatibility = load_json(
        Path(aws_iac_dir) / "contracts" / "aws-config-compatibility.json"
    )

    if config_contract.get("contract_name") != "aws-config":
        raise ValueError("aws-config contract_name must be aws-config")
    if iac_compatibility.get("contract_name") != "aws-config":
        raise ValueError("aws-iac compatibility contract_name must be aws-config")

    version = config_contract.get("contract_version")
    if not isinstance(version, int) or version < 1:
        raise ValueError("aws-config contract_version must be a positive integer")

    supported = iac_compatibility.get("supported_contract_versions")
    if not isinstance(supported, list) or not supported or any(
        not isinstance(item, int) or item < 1 for item in supported
    ):
        raise ValueError("supported_contract_versions must be a non-empty list of positive integers")
    if version not in supported:
        raise ValueError(
            f"aws-iac does not support aws-config contract version {version}; supports {supported}"
        )
    return version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aws-config-dir", required=True, type=Path)
    parser.add_argument("--aws-iac-dir", required=True, type=Path)
    args = parser.parse_args()
    version = check_compatibility(args.aws_config_dir, args.aws_iac_dir)
    print(f"aws-config contract version {version} is supported by aws-iac")


if __name__ == "__main__":
    main()
