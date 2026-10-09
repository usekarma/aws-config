"""Local configuration contracts. No AWS imports, credentials or network I/O."""

import ipaddress
import base64
import json
import os
from pathlib import Path
import re

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
FORMATS = FormatChecker()


@FORMATS.checks("cidr", raises=ValueError)
def cidr(value):
    if not isinstance(value, str):
        return True
    ipaddress.ip_network(value, strict=True)
    return True


def no_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key: " + key)
        value[key] = item
    return value


def load_json(path):
    return json.loads(
        Path(path).read_text(),
        object_pairs_hook=no_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError("invalid JSON number " + value)
        ),
    )


def schema_validate(value, schema_name, label):
    schema = load_json(ROOT / "schemas" / (schema_name + ".schema.json"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema, format_checker=FORMATS).iter_errors(value))
    if errors:
        # Do not echo rejected values; configuration may contain secrets.
        error = errors[0]
        location = "/".join(map(str, error.absolute_path)) or "<root>"
        raise ValueError(f"{label}: {location}: schema rule {error.validator} failed")


def lambda_declarations(value):
    declarations = list(value.get("functions", {}).values())
    if "ingest_function" in value:
        declarations.append(value["ingest_function"])
    return declarations


def validate_lambda_metadata(value):
    for declaration in lambda_declarations(value):
        if ("src_type" in declaration) != ("src_nickname" in declaration):
            raise ValueError("Lambda source type and nickname must be paired")
        artifact = declaration.get("artifact")
        if isinstance(artifact, dict):
            digest = artifact["source_code_hash"]
            decoded = base64.b64decode(digest, validate=True)
            if len(decoded) != 32 or base64.b64encode(decoded).decode() != digest:
                raise ValueError("Lambda source_code_hash must be canonical base64 SHA-256")
            if not artifact["s3_object_version"].strip():
                raise ValueError("Lambda artifact version must be explicit")


def validate_deployment_readiness(value, component):
    """Local publication gate, independent of AWS approval and artifact availability."""
    if component not in ("lambda", "iot-digital-twin"):
        return
    if component == "iot-digital-twin" and "ingest_function" not in value:
        raise ValueError("Deployment blocked: missing Lambda declaration")
    declarations = lambda_declarations(value)
    if not declarations:
        raise ValueError("Deployment blocked: missing Lambda declaration")
    for declaration in declarations:
        if "planning_dependencies" in declaration:
            raise ValueError("Deployment blocked: unresolved Lambda planning dependencies")
        schema_validate(declaration, "lambda-declaration", "deployment readiness")
    validate_lambda_metadata(value)
    if component == "iot-digital-twin":
        validate_iot_lambda(value, ready=True)


def validate_iot_lambda(value, ready=False):
    declaration = value.get("ingest_function")
    if declaration is None:
        return  # Legacy v1 remains representable; readiness requires a declaration.
    env = declaration.get("environment", {})
    dependencies = declaration.get("planning_dependencies", [])
    if (
        declaration["runtime"] != "python3.12"
        or declaration["handler"] != "app.lambda_handler"
        or declaration["log_retention_days"] != value["cloudwatch_log_retention_days"]
        or value["device_id"] != value["thing_name"]
        or value["mqtt_topic"] != f"devices/{value['device_id']}/telemetry"
        or env.get("EXPECTED_DEVICE_ID") != value["thing_name"]
        or env.get("LATEST_STATE_TABLE") != value["latest_state_table_name"]
        or env.get("MAX_CLOCK_SKEW_SECONDS") != str(value["max_clock_skew_seconds"])
        or any(
            value[key] is not True
            for key in (
                "device_certificate_authoritative",
                "device_id_is_data_only",
                "reject_device_authored_offline",
                "connectivity_state_server_derived",
                "server_replay_and_stale_enforcement",
                "least_privilege_iam",
                "no_broad_permission_fallback",
            )
        )
    ):
        raise ValueError("IoT Lambda runtime, identity, retention or trust contract mismatch")
    if (ready or "trusted_principal" not in dependencies) and not env.get(
        "EXPECTED_PRINCIPAL", ""
    ).strip():
        raise ValueError("IoT Lambda trusted principal is unresolved")
    if (
        declaration.get("artifact") is not None
        and Path(declaration["artifact"]["s3_key"]).name != "iot-digital-twin-ingest.zip"
    ):
        raise ValueError("IoT Lambda requires the merged ingestion package")


def validate_config(path, value):
    path = Path(path)
    if path.parts[0] not in ("iac", "account_environments"):
        return
    if path.parts[0] == "account_environments":
        schema_validate(value, "account-environment", path)
        if value["name"] != path.stem or not (ROOT / "iac" / value["environment"]).is_dir():
            raise ValueError(f"{path}: binding name/environment does not match repository")
        return
    if len(path.parts) != 5 or path.name != "config.json":
        raise ValueError(f"{path}: expected iac/environment/component/nickname/config.json")
    _, env, component, nickname, _ = path.parts
    if not re.fullmatch(r"[a-z0-9-]+", component) or not re.fullmatch(r"[a-zA-Z0-9_-]+", nickname):
        raise ValueError(f"{path}: invalid component/nickname")
    schema_validate(value, component, path)
    validate_lambda_metadata(value)
    if component == "iot-digital-twin":
        validate_iot_lambda(value)
    bindings = [load_json(p)["environment"] for p in (ROOT / "account_environments").glob("*.json")]
    if env not in bindings:
        raise ValueError(f"{path}: environment has no local account binding")
    if "AWS_IAC_DIR" in os.environ:
        module = Path(os.environ["AWS_IAC_DIR"]) / "components" / component
        if not (module / "header.tf").is_file():
            raise ValueError(f"{path}: sibling component is not deployable")
    dependencies = {
        "vpc_nickname": "vpc",
        "s3_bucket_nickname": "s3-bucket",
        "ecs_cluster_nickname": "ecs-cluster",
        "cognito_sso_nickname": "cognito-sso",
    }
    objects = [value] + lambda_declarations(value)
    for obj in objects:
        for key, target in dependencies.items():
            if (
                key in obj
                and not (ROOT / "iac" / env / target / obj[key] / "config.json").is_file()
            ):
                raise ValueError(f"{path}: {key}: no matching config in environment {env}")
        if "src_type" in obj or "src_nickname" in obj:
            if not all(
                isinstance(obj.get(k), str) and re.fullmatch(r"[a-zA-Z0-9_-]+", obj[k])
                for k in ("src_type", "src_nickname")
            ):
                raise ValueError(f"{path}: source type/nickname must be paired valid names")
            if not (
                ROOT / "iac" / env / obj["src_type"] / obj["src_nickname"] / "config.json"
            ).is_file():
                raise ValueError(f"{path}: source dependency config is missing")
