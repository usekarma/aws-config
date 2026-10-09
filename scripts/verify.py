#!/usr/bin/env python3
"""Non-destructive repository checks. No AWS calls or remote backend initialization."""

import argparse
import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)


def run(args, **kwargs):
    print("+ " + " ".join(map(str, args)), flush=True)
    subprocess.run(args, check=True, **kwargs)


def git_paths(*args):
    return set(subprocess.check_output(["git", *args], text=True).splitlines())


def no_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key: " + key)
        value[key] = item
    return value


def load_json(path):
    return json.loads(
        path.read_text(),
        object_pairs_hook=no_duplicates,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError("invalid JSON number " + x)),
    )


def validate_config(path, value):
    import config_validation

    config_validation.ROOT = ROOT
    config_validation.validate_config(path, value)


def provider_validate(component):
    modules = (
        sorted((ROOT / "components").iterdir())
        if component == "all"
        else [ROOT / "components" / component]
    )
    if not re.fullmatch(r"[a-z0-9-]+", component):
        raise ValueError("Invalid component")
    for module in modules:
        if not module.is_dir() or not list(module.glob("*.tf")):
            if component == "all":
                continue
            raise ValueError("No Terraform module: " + component)
        with tempfile.TemporaryDirectory(prefix="iac-validate-") as scratch:
            shutil.copytree(
                module,
                scratch,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(".terraform", "*.tfstate", "*.tfstate.*"),
            )
            env = os.environ.copy()
            for key in list(env):
                if key.startswith("TF_CLI_ARGS"):
                    del env[key]
            env.update(
                AWS_EC2_METADATA_DISABLED="true",
                TF_IN_AUTOMATION="true",
                TF_DATA_DIR=str(Path(scratch) / ".terraform"),
            )
            run(
                ["terraform", "init", "-backend=false", "-input=false", "-no-color"],
                cwd=scratch,
                env=env,
            )
            run(["terraform", "validate", "-no-color"], cwd=scratch, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--terraform",
        metavar="COMPONENT",
        help="provider validation in a disposable copy; use all for all modules",
    )
    args = parser.parse_args()
    base = os.environ.get("VERIFY_BASE_REF", "origin/main")
    run(["git", "rev-parse", "--verify", base])
    files = git_paths("ls-files") | git_paths("ls-files", "--others", "--exclude-standard")
    changed = (
        git_paths("diff", "--name-only", f"{base}...HEAD")
        | git_paths("diff", "--name-only", "HEAD")
        | git_paths("ls-files", "--others", "--exclude-standard")
    )
    files = sorted(p for p in files if Path(p).is_file())
    for tool in ("bash", "shellcheck") + (
        ("terraform", "terragrunt") if (ROOT / "terragrunt.hcl").exists() else ()
    ):
        if not shutil.which(tool):
            raise ValueError(f"Required tool missing: {tool}; see docs/agent-workflow.md")
    secret = re.compile(
        r"(?:AKIA|ASIA)[A-Z0-9]{16}|gh[pousr]_"
        + r"[A-Za-z0-9]{36,}|-----BEGIN "
        + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    )
    legacy_fmt = 0
    for name in files:
        path = Path(name)
        try:
            content = path.read_text()
        except UnicodeDecodeError:
            continue
        if secret.search(content):
            raise ValueError(f"Possible credential in {name}; value withheld")
        if path.suffix == ".py":
            ast.parse(content, filename=name)
        if path.suffix == ".json":
            value = load_json(path)
            validate_config(path, value)
        if path.suffix == ".sh":
            run(["bash", "-n", name])
            if name in changed:
                run(["shellcheck", "--severity=warning", name])
        if path.suffix == ".tf":
            result = subprocess.run(
                ["terraform", "fmt", "-check", "-diff", name], capture_output=True, text=True
            )
            if result.returncode not in (0, 3) or (result.returncode and name in changed):
                print(result.stdout, result.stderr)
                raise ValueError(f"Terraform syntax/changed-file formatting failed: {name}")
            legacy_fmt += result.returncode == 3
    if (ROOT / "terragrunt.hcl").exists():
        run(["terragrunt", "hcl", "fmt", "--check", "--file", "terragrunt.hcl"])
        run(["terragrunt", "hcl", "validate"])
        print(f"Unchanged Terraform files with legacy formatting differences: {legacy_fmt}")
    python_changed = sorted(
        name for name in changed if name.endswith(".py") and Path(name).is_file()
    )
    if python_changed:
        run(["ruff", "check", *python_changed])
        run(["ruff", "format", "--check", *python_changed])
    if (ROOT / "terragrunt.hcl").exists():
        from static_security import check

        check(base)
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    run(["git", "diff", "--check", base])
    if args.terraform:
        if not (ROOT / "components").is_dir():
            raise ValueError("--terraform is available only in aws-iac")
        provider_validate(args.terraform)
    print("Repository verification passed. No AWS calls or Terraform state writes performed.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, SyntaxError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"Verification FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
