#!/usr/bin/env python3

import json
import pathlib
import sys
from decimal import Decimal, InvalidOperation

CONTRACT_PATH = pathlib.Path("governance/steady_state_costs.json")


def fail(message):
    print(f"❌ {message}")
    sys.exit(1)


def money(value, field_name):
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError):
        fail(f"{field_name} must be a decimal-compatible value")
    if amount < 0:
        fail(f"{field_name} must be non-negative")
    return amount


def load_contract():
    if not CONTRACT_PATH.exists():
        fail(f"Missing contract: {CONTRACT_PATH}")
    try:
        return json.loads(CONTRACT_PATH.read_text())
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {CONTRACT_PATH}: {exc}")


def validate_safety(contract):
    criteria = contract.get("acceptance_criteria", {})
    if criteria.get("account_for_all_recurring_spend") is not True:
        fail("account_for_all_recurring_spend must be true")
    if money(criteria.get("max_unattributed_usd"), "max_unattributed_usd") != Decimal("0.00"):
        fail("max_unattributed_usd must be exactly 0.00")
    if criteria.get("remediation_mode") != "proposal_only":
        fail("remediation_mode must be proposal_only")
    if criteria.get("allow_destructive_actions") is not False:
        fail("allow_destructive_actions must be false")


def validate_target(target, seen_ids, seen_environments):
    target_id = target.get("id")
    account_environment = target.get("account_environment")

    if not target_id or target_id in seen_ids:
        fail(f"Target id is missing or duplicated: {target_id!r}")
    seen_ids.add(target_id)

    if not account_environment or account_environment in seen_environments:
        fail(f"account_environment is missing or duplicated: {account_environment!r}")
    seen_environments.add(account_environment)

    env_path = pathlib.Path("account_environments") / f"{account_environment}.json"
    if not env_path.exists():
        fail(f"Missing account environment for {target_id}: {env_path}")

    try:
        env_config = json.loads(env_path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {env_path}: {exc}")

    if env_config.get("name") != account_environment:
        fail(f"Environment name mismatch in {env_path}")
    if env_config.get("environment") != "prod":
        fail(f"Steady-state target {target_id} must bind to a prod environment")

    roots = target.get("config_roots")
    if not roots:
        fail(f"Target {target_id} must declare at least one config_root")
    for root in roots:
        config_path = pathlib.Path(root) / "config.json"
        if not config_path.exists():
            fail(f"Missing declared config root for {target_id}: {config_path}")

    return money(target.get("monthly_target_usd"), f"{target_id}.monthly_target_usd")


def main():
    contract = load_contract()

    if contract.get("schema_version") != 1:
        fail("schema_version must be 1")
    if contract.get("currency") != "USD":
        fail("currency must be USD")

    validate_safety(contract)

    targets = contract.get("targets")
    if not isinstance(targets, list) or not targets:
        fail("targets must be a non-empty list")

    seen_ids = set()
    seen_environments = set()
    calculated_total = sum(
        (validate_target(target, seen_ids, seen_environments) for target in targets),
        Decimal("0.00"),
    )
    declared_total = money(contract.get("combined_monthly_target_usd"), "combined_monthly_target_usd")

    if calculated_total != declared_total:
        fail(
            f"Target sum {calculated_total:.2f} does not match "
            f"combined_monthly_target_usd {declared_total:.2f}"
        )

    print(f"✅ Valid steady-state cost contract: {CONTRACT_PATH}")
    for target in targets:
        print(f"   {target['id']}: ${Decimal(target['monthly_target_usd']):.2f}/month")
    print(f"   combined: ${declared_total:.2f}/month")
    print("   unaccounted recurring spend allowed: $0.00")
    print("   remediation: proposal only; destructive actions disabled")


if __name__ == "__main__":
    main()
