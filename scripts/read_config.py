#!/usr/bin/env python3

import argparse
import boto3
import json
import sys
import os
from pathlib import Path
import subprocess
import hashlib


def read_param(name):
    ssm = boto3.Session(
        profile_name=os.environ.get("AWS_PROFILE"), region_name=os.environ.get("AWS_REGION")
    ).client("ssm")
    try:
        response = ssm.get_parameter(Name=name, WithDecryption=False)
        value = response["Parameter"]["Value"]
        if os.environ.get("AGENT_MODE") == "1":
            print(
                json.dumps(
                    {
                        "name": name,
                        "version": response["Parameter"]["Version"],
                        "sha256": hashlib.sha256(value.encode()).hexdigest(),
                    }
                )
            )
            return
        try:
            parsed = json.loads(value)
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError:
            print(value)
    except ssm.exceptions.ParameterNotFound:
        print(f"❌ Parameter not found: {name}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error retrieving parameter: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="Parameter name (e.g. /iac/environment)")
    args = parser.parse_args()
    if os.environ.get("AGENT_MODE") == "1":
        subprocess.run(["bash", str(Path(__file__).resolve().parent / "preflight.sh")], check=True)
        if not args.name.startswith(os.environ.get("IAC_PREFIX", "/iac") + "/"):
            parser.error("Parameter must be under reviewed IAC_PREFIX")
    read_param(args.name)


if __name__ == "__main__":
    main()
