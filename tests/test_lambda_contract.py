"""Deterministic desired-state and publication boundary tests; no AWS calls."""

import base64
import copy
from pathlib import Path
import sys
import subprocess
from unittest import mock
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import config_validation as validation
import deploy_config


IOT_PATH = Path("iac/dev/iot-digital-twin/core2-aws-001/config.json")


def declaration():
    # Synthetic unit-test coordinates only; never desired state or publication evidence.
    return {
        "runtime": "python3.12",
        "handler": "app.lambda_handler",
        "memory_size": 512,
        "timeout": 30,
        "log_retention_days": 14,
        "artifact": {
            "s3_bucket": "synthetic-test-bucket",
            "s3_key": "test/iot-digital-twin-ingest.zip",
            "s3_object_version": "synthetic-version",
            "source_code_hash": base64.b64encode(bytes(32)).decode(),
        },
    }


class LambdaContractTests(unittest.TestCase):
    def setUp(self):
        self.iot = validation.load_json(validation.ROOT / IOT_PATH)

    def test_complete_declaration(self):
        value = {"functions": {"iot-digital-twin-ingest": declaration()}}
        validation.schema_validate(value, "lambda", "fixture")
        validation.validate_deployment_readiness(value, "lambda")

    def test_publisher_import_and_config_loading_do_not_load_aws_dependencies(self):
        # A fresh interpreter avoids dependencies cached by other tests.
        # Use an explicit script path rather than relying on the suite's PYTHONPATH.
        script = """
import sys
sys.path.insert(0, 'scripts')
import deploy_config
try:
    deploy_config.load_config('dev', 'iot-digital-twin', 'core2-aws-001')
except ValueError as error:
    assert 'Deployment blocked' in str(error)
else:
    raise AssertionError('Unresolved declaration accepted')
assert 'mutation_guard' not in sys.modules
assert 'boto3' not in sys.modules
assert 'botocore' not in sys.modules
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=validation.ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_embedded_schemas_match_pinned_contracts(self):
        complete = validation.load_json(validation.ROOT / "schemas/lambda-declaration.schema.json")
        planning = validation.load_json(validation.ROOT / "schemas/lambda-planning.schema.json")
        standalone = validation.load_json(validation.ROOT / "schemas/lambda.schema.json")
        iot = validation.load_json(validation.ROOT / "schemas/iot-digital-twin.schema.json")
        self.assertEqual(iot["properties"]["ingest_function"]["oneOf"], [complete, planning])
        self.assertEqual(
            standalone["properties"]["functions"]["additionalProperties"]["then"]["oneOf"],
            [complete, planning],
        )

    def test_invalid_types_and_required_fields(self):
        for key in ("runtime", "handler", "memory_size", "timeout", "log_retention_days"):
            value = declaration()
            value[key] = []
            with self.subTest(key=key), self.assertRaises(ValueError):
                validation.schema_validate({"functions": {"f": value}}, "lambda", "fixture")
        for key in declaration()["artifact"]:
            value = declaration()
            del value["artifact"][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                validation.validate_deployment_readiness({"functions": {"f": value}}, "lambda")
        for key in declaration():
            value = declaration()
            del value[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                validation.validate_deployment_readiness({"functions": {"f": value}}, "lambda")

    def test_hash_and_mutable_versions(self):
        for digest in ("bad", "a" * 44, "A" * 42 + "B=", "A" * 43 + "=\n"):
            value = declaration()
            value["artifact"]["source_code_hash"] = digest
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                validation.validate_deployment_readiness({"functions": {"f": value}}, "lambda")
        for version in ("latest", "null", "", "   "):
            value = declaration()
            value["artifact"]["s3_object_version"] = version
            with self.subTest(version=version), self.assertRaises(ValueError):
                validation.validate_deployment_readiness({"functions": {"f": value}}, "lambda")

    def test_iot_planning_declaration(self):
        value = self.iot["ingest_function"]
        self.assertEqual(self.iot["ingest_lambda_name"], "iot-digital-twin-ingest")
        self.assertEqual(value["runtime"], "python3.12")
        self.assertEqual(value["handler"], "app.lambda_handler")
        self.assertEqual((value["memory_size"], value["timeout"]), (512, 30))
        self.assertEqual(value["log_retention_days"], 14)
        self.assertIsNone(value["artifact"])
        self.assertEqual(
            value["planning_dependencies"], ["artifact_publication", "trusted_principal"]
        )
        self.assertEqual(
            value["environment"],
            {
                "EXPECTED_DEVICE_ID": "core2-aws-001",
                "LATEST_STATE_TABLE": "iot-digital-twin-latest-state",
                "MAX_CLOCK_SKEW_SECONDS": "10",
                "ACCEL_MOTION_THRESHOLD_G": "0.15",
                "GYRO_MOTION_THRESHOLD_DPS": "5",
            },
        )
        validation.validate_config(IOT_PATH, self.iot)
        with self.assertRaisesRegex(ValueError, "unresolved Lambda planning dependencies"):
            validation.validate_deployment_readiness(self.iot, "iot-digital-twin")

    def test_planning_cannot_hide_fake_artifacts_or_typos(self):
        for edit in (
            {"artifact": {}},
            {"artifact": declaration()["artifact"]},
            {"planning_dependencies": []},
            {"planning_dependencies": ["typo"]},
        ):
            value = copy.deepcopy(self.iot)
            value["ingest_function"].update(edit)
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validation.validate_config(IOT_PATH, value)

    def test_iot_ready_and_trust_mismatch(self):
        value = copy.deepcopy(self.iot)
        runtime = declaration()
        runtime["environment"] = self.iot["ingest_function"]["environment"] | {
            "EXPECTED_PRINCIPAL": "synthetic-test-principal",
        }
        value["ingest_function"] = runtime
        validation.validate_config(IOT_PATH, value)
        validation.validate_deployment_readiness(value, "iot-digital-twin")
        for edit in (
            {"device_id_is_data_only": False},
            {"thing_name": "other"},
            {"mqtt_topic": "devices/other/telemetry"},
            {"cloudwatch_log_retention_days": 30},
        ):
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validation.validate_config(IOT_PATH, value | edit)
        del runtime["environment"]["EXPECTED_PRINCIPAL"]
        with self.assertRaisesRegex(ValueError, "trusted principal"):
            validation.validate_config(IOT_PATH, value)

    def test_no_credentials_or_policy_in_migration(self):
        # Exact environment allowlist above also detects unreviewed secret inputs.
        forbidden = (
            "password",
            "secret",
            "token",
            "credential",
            "access_key",
            "private_key",
            "policy",
            "account_id",
        )

        def inspect(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    self.assertFalse(any(word in key.lower() for word in forbidden), key)
                    inspect(item)
            elif isinstance(value, list):
                for item in value:
                    inspect(item)
            elif isinstance(value, str):
                self.assertNotRegex(value, r"(?:AKIA|ASIA)[A-Z0-9]{16}|-----BEGIN|\b\d{12}\b")

        inspect(self.iot)
        value = declaration() | {"iam_policy": {}}
        with self.assertRaises(ValueError):
            validation.schema_validate({"functions": {"f": value}}, "lambda", "fixture")

    def test_publication_blocks_before_aws_session(self):
        with mock.patch.object(deploy_config, "approved_session") as session:
            with self.assertRaisesRegex(ValueError, "Deployment blocked"):
                deploy_config.write_param("/iac/iot-digital-twin/core2-aws-001/config", self.iot)
            session.assert_not_called()
        with self.assertRaisesRegex(ValueError, "Deployment blocked"):
            deploy_config.load_config("dev", "iot-digital-twin", "core2-aws-001")

    def test_legacy_v1_remains_valid_but_requires_migration_for_readiness(self):
        for path in (validation.ROOT / "iac/prod/lambda").glob("*/config.json"):
            value = validation.load_json(path)
            validation.validate_config(path.relative_to(validation.ROOT), value)
            with self.assertRaises(ValueError):
                validation.validate_deployment_readiness(value, "lambda")
        legacy_iot = copy.deepcopy(self.iot)
        del legacy_iot["ingest_function"]
        validation.validate_config(IOT_PATH, legacy_iot)
        with self.assertRaisesRegex(ValueError, "missing Lambda declaration"):
            validation.validate_deployment_readiness(legacy_iot, "iot-digital-twin")
