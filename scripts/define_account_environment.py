#!/usr/bin/env python3

import argparse
import json
import pathlib
from mutation_guard import approved_session, check_local_binding
from config_validation import load_json, schema_validate
import sys
import os


def get_prefix():
    return os.getenv("IAC_PREFIX", "/iac")


def load_environment_config(file_path):
    value = load_json(file_path)
    schema_validate(value, "account-environment", file_path)
    if value["name"] != pathlib.Path(file_path).stem:
        raise SystemExit("Binding name must match filename")
    return value


def write_environment_param(env_dict, param_name=f"{get_prefix()}/environment"):
    session = approved_session(require_binding=False)
    check_local_binding(env_dict)
    ssm = session.client("ssm")
    print(f"Writing parameter {param_name} to SSM Parameter Store...")
    ssm.put_parameter(
        Name=param_name,
        Value=json.dumps(env_dict, separators=(",", ":")),
        Type="String",
        Overwrite=True,
        Tier="Standard",
    )
    print("Environment parameter set successfully.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True, help="Environment name (e.g. dev, prod)")
    parser.add_argument(
        "--path",
        default=str(pathlib.Path(__file__).resolve().parents[1] / "account_environments"),
        help="Path to environment files",
    )
    parser.add_argument(
        "--param-name", default=f"{get_prefix()}/environment", help="Parameter Store name to write"
    )
    args = parser.parse_args()

    file_path = pathlib.Path(args.path) / f"{args.env}.json"
    if not file_path.exists():
        print(f"Environment file not found: {file_path}")
        sys.exit(1)

    env_config = load_environment_config(file_path)
    write_environment_param(env_config, param_name=args.param_name)


if __name__ == "__main__":
    main()
