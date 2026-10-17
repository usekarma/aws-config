import copy
import json
import unittest
from pathlib import Path

import config_validation as validation

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = "iot-digital-twin"


class SimulatorContractTests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads(
            (ROOT / "iac/dev/iot-digital-twin/atom-lite-001/config.json").read_text()
        )

    def test_canonical_discovery_rejects_retired_core2(self):
        archived = ROOT / "archive/core2/core2-aws-001/config.json"
        value = json.loads(archived.read_text())
        with self.assertRaises(ValueError):
            validation.validate_config("iac/dev/iot-digital-twin/core2-aws-001/config.json", value)
        with self.assertRaises(ValueError):
            validation.validate_deployment_readiness(value, COMPONENT)
        self.assertFalse((ROOT / "iac/dev/iot-digital-twin/core2-aws-001").exists())
        self.assertFalse((ROOT / "iac/dev/iot-digital-twin-simulator").exists())

    def resolved(self):
        value = copy.deepcopy(self.value)
        value.pop("planning_dependencies")
        value.update(
            region="us-east-1",
            active_session="a" * 32,
            expected_principal="synthetic-principal",
            artifact={
                "s3_bucket": "synthetic-bucket",
                "s3_key": "iot-digital-twin-simulator.zip",
                "s3_object_version": "synthetic-version",
                "source_code_hash": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
            },
        )
        return value

    def test_draft_is_valid_but_publication_blocked(self):
        validation.schema_validate(self.value, COMPONENT, "synthetic draft")
        with self.assertRaises(ValueError):
            validation.validate_deployment_readiness(self.value, COMPONENT)

    def test_resolved_shape_requires_explicit_bindings(self):
        value = self.resolved()
        validation.validate_deployment_readiness(value, COMPONENT)
        for field in ("artifact", "active_session", "expected_principal", "region"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validation.validate_deployment_readiness(value | {field: None}, COMPONENT)

    def test_names_and_security_inputs_rejected(self):
        value = self.resolved()
        for invalid in (
            value | {"project": "iot-interview-demo"},
            value | {"policy": {}},
            value | {"active_session": True},
            value | {"tags": {"Project": "wrong"}},
            value | {"artifact": value["artifact"] | {"s3_key": "iot-digital-twin-ingest.zip"}},
        ):
            with self.assertRaises(ValueError):
                validation.schema_validate(invalid, COMPONENT, "invalid fixture")


if __name__ == "__main__":
    unittest.main()
