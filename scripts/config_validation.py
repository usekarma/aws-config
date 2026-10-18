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
    if component == "iot-digital-twin":
        schema_validate(value, component, "simulator readiness")
        if value.get("mode") == "operational-telemetry":
            if value.get("deployment_stage") == "service-role-bootstrap":
                if (
                    value.get("expected_account") != "623155450153"
                    or value.get("region") != "us-east-1"
                    or "planning_dependencies" in value
                    or value.get("expected_principal") is None
                ):
                    raise ValueError("Deployment blocked: unresolved bootstrap identity/target")
                return
            if value.get("deployment_stage") == "operational" and not value.get(
                "awscc_request_tags_verified"
            ):
                raise ValueError("Deployment blocked: AWSCC request-tag behavior unverified")
            if "planning_dependencies" in value or any(
                value[k] is None
                for k in (
                    "region",
                    "expected_account",
                    "expected_principal",
                    "cloudformation_role_arn",
                )
            ):
                raise ValueError("Deployment blocked: unresolved operational bindings")
            if value["cloudformation_role_arn"].split(":")[4] != value["expected_account"]:
                raise ValueError("Deployment blocked: CloudFormation role account mismatch")
            return
        if "planning_dependencies" in value or any(
            value[key] is None
            for key in ("artifact", "active_session", "expected_principal", "region")
        ):
            raise ValueError("Deployment blocked: unresolved simulator bindings")
        artifact = value["artifact"]
        digest = artifact["source_code_hash"]
        decoded = base64.b64decode(digest, validate=True)
        if len(decoded) != 32 or base64.b64encode(decoded).decode() != digest:
            raise ValueError("Simulator artifact hash must be canonical base64 SHA256")
        return
    if component != "lambda":
        return
    declarations = lambda_declarations(value)
    if not declarations:
        raise ValueError("Deployment blocked: missing Lambda declaration")
    for declaration in declarations:
        if "planning_dependencies" in declaration:
            raise ValueError("Deployment blocked: unresolved Lambda planning dependencies")
        schema_validate(declaration, "lambda-declaration", "deployment readiness")
    validate_lambda_metadata(value)


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
