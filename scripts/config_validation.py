"""Local configuration contracts. No AWS imports, credentials or network I/O."""

import ipaddress
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
    objects = [value] + list(value.get("functions", {}).values())
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
