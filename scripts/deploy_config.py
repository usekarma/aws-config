#!/usr/bin/env python3

import argparse
import json
import pathlib
from mutation_guard import approved_session
import sys
import os

get_prefix = lambda: os.getenv("IAC_PREFIX", "/iac")

def get_environment_metadata(param_name=None):
    ssm = approved_session().client("ssm")
    param_name = param_name or f"{get_prefix()}/environment"
    try:
        response = ssm.get_parameter(Name=param_name, WithDecryption=False)
        metadata = json.loads(response["Parameter"]["Value"])
        if "environment" not in metadata:
            sys.exit(f"❌ Missing 'environment' field in environment parameter: {param_name}")
        return metadata
    except Exception as e:
        sys.exit(f"❌ Failed to load environment parameter {param_name}: {e}")

def load_config(env_type, component, nickname):
    config_file = pathlib.Path(__file__).resolve().parents[1] / "iac" / env_type / component / nickname / "config.json"
    if not config_file.exists():
        sys.exit(f"❌ Missing config file: {config_file}")
    return json.loads(config_file.read_text())

def write_param(param_name, config_data):
    ssm = approved_session().client("ssm")
    try:
        ssm.put_parameter(
            Name=param_name,
            Value=json.dumps(config_data, separators=(",", ":")),
            Type="String",
            Overwrite=True,
            Tier="Standard"
        )
        print(f"✅ Deployed config to {param_name}")
    except Exception as e:
        sys.exit(f"❌ Failed to deploy parameter {param_name}: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", required=True, help="Component name (e.g. serverless-site)")
    parser.add_argument("--nickname", required=True, help="Nickname or instance name (e.g. karma-api)")
    args = parser.parse_args()

    metadata = get_environment_metadata()
    env_type = metadata["environment"]  # e.g., "dev" or "prod"

    param_name = f"{get_prefix()}/{args.component}/{args.nickname}/config"
    config = load_config(env_type, args.component, args.nickname)
    write_param(param_name, config)

if __name__ == "__main__":
    main()
