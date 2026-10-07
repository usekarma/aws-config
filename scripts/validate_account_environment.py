#!/usr/bin/env python3

import argparse
import json
import boto3
import pathlib
import sys
import os
import subprocess


def get_prefix():
    return os.getenv("IAC_PREFIX", "/iac")


def fetch_param(param_name=f"{get_prefix()}/environment"):
    ssm = boto3.Session(
        profile_name=os.environ.get("AWS_PROFILE"), region_name=os.environ.get("AWS_REGION")
    ).client("ssm")
    result = ssm.get_parameter(Name=param_name, WithDecryption=False)
    return json.loads(result["Parameter"]["Value"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", help="Expected environment name (e.g. dev)")
    parser.add_argument(
        "--param-name", default=f"{get_prefix()}/environment", help="Parameter Store path"
    )
    args = parser.parse_args()

    if os.environ.get("AGENT_MODE") == "1":
        subprocess.run(
            ["bash", str(pathlib.Path(__file__).resolve().parent / "preflight.sh")], check=True
        )
        if args.param_name != f"{get_prefix()}/environment":
            parser.error("Use reviewed IAC_PREFIX for agent binding checks")
    live = fetch_param(args.param_name)
    env_name = args.env or live.get("name")

    expected_path = (
        pathlib.Path(__file__).resolve().parents[1] / "account_environments" / f"{env_name}.json"
    )
    if not expected_path.exists():
        print(f"Missing local file: {expected_path}")
        sys.exit(1)

    with open(expected_path) as f:
        expected = json.load(f)

    if live == expected:
        print("✅ Environment parameter matches local file.")
    else:
        print("❌ Mismatch between environment parameter and local file.")
        if os.environ.get("AGENT_MODE") != "1":
            print("Live value:", json.dumps(live, indent=2))
            print("Expected: ", json.dumps(expected, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
