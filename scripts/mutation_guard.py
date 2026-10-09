"""Shared approval/identity guard for SSM writes, including direct Python entrypoints."""

import json
import os
import re
import boto3


def approved_session(require_binding=True):
    if os.environ.get("AGENT_MODE", "0") != "0":
        raise SystemExit("Agent mode blocks all SSM publishing, including acknowledged operations")
    if os.environ.get("AWS_MUTATION_APPROVED") != "1":
        raise SystemExit(
            "Human approval required; operator must acknowledge with AWS_MUTATION_APPROVED=1"
        )
    required = (
        "AWS_PROFILE",
        "AWS_REGION",
        "EXPECTED_AWS_ACCOUNT",
        "EXPECTED_ENVIRONMENT",
        "EXPECTED_BINDING",
    )
    if any(not os.environ.get(key) for key in required):
        raise SystemExit("Set " + ", ".join(required) + " before any AWS mutation")
    if not re.fullmatch(r"[0-9]{12}", os.environ["EXPECTED_AWS_ACCOUNT"]):
        raise SystemExit("Invalid expected account ID")
    if not re.fullmatch(r"[a-z]{2}(-[a-z]+)+-[0-9]+", os.environ["AWS_REGION"]):
        raise SystemExit("Invalid AWS region")
    if not re.fullmatch(r"(/[a-zA-Z0-9_-]+)+", os.environ.get("IAC_PREFIX", "/iac")):
        raise SystemExit("Invalid IAC_PREFIX")
    for key in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_SECURITY_TOKEN",
        "AWS_WEB_IDENTITY_TOKEN_FILE",
        "AWS_ROLE_ARN",
        "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
        "AWS_CONTAINER_CREDENTIALS_FULL_URI",
    ):
        if os.environ.get(key):
            raise SystemExit("Unset " + key + "; use only the named profile")
    session = boto3.Session(
        profile_name=os.environ["AWS_PROFILE"], region_name=os.environ["AWS_REGION"]
    )
    if session.client("sts").get_caller_identity()["Account"] != os.environ["EXPECTED_AWS_ACCOUNT"]:
        raise SystemExit("AWS account mismatch; refusing write")
    if require_binding:
        parameter = session.client("ssm").get_parameter(
            Name=f"{os.getenv('IAC_PREFIX', '/iac')}/environment", WithDecryption=False
        )
        binding = json.loads(parameter["Parameter"]["Value"])
        if (
            binding.get("name") != os.environ["EXPECTED_BINDING"]
            or binding.get("environment") != os.environ["EXPECTED_ENVIRONMENT"]
        ):
            raise SystemExit("Environment binding mismatch; refusing write")
    return session


def check_local_binding(binding):
    if binding.get("name") != os.environ.get("EXPECTED_BINDING") or binding.get(
        "environment"
    ) != os.environ.get("EXPECTED_ENVIRONMENT"):
        raise SystemExit("Local binding differs from approved target")
