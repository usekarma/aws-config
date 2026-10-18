import copy
import json
from pathlib import Path
import unittest

from config_validation import schema_validate, validate_deployment_readiness

ROOT = Path(__file__).resolve().parents[1]


class BootstrapContractTests(unittest.TestCase):
    def config(self):
        return json.loads((ROOT / "examples/m1-operational-bootstrap.json").read_text())

    def test_bootstrap_does_not_require_invented_role_arn(self):
        validate_deployment_readiness(self.config(), "iot-digital-twin")

    def test_bootstrap_wrong_account_rejected(self):
        config = self.config()
        config["expected_account"] = "111111111111"
        with self.assertRaises(ValueError):
            validate_deployment_readiness(config, "iot-digital-twin")

    def test_bootstrap_bound_role_rejected(self):
        config = self.config()
        config["cloudformation_role_arn"] = "arn:aws:iam::623155450153:role/uncreated"
        with self.assertRaises(ValueError):
            schema_validate(config, "iot-digital-twin", "bootstrap")

    def test_stage_two_unverified_handler_rejected(self):
        config = self.config()
        config.update(
            deployment_stage="operational",
            cloudformation_role_arn="arn:aws:iam::623155450153:role/iot-digital-twin-operational-m1-cloud-control",
        )
        with self.assertRaises(ValueError):
            validate_deployment_readiness(config, "iot-digital-twin")

    def test_stage_two_requires_complete_bindings(self):
        config = copy.deepcopy(self.config())
        config.update(deployment_stage="operational", awscc_request_tags_verified=True)
        with self.assertRaises(ValueError):
            validate_deployment_readiness(config, "iot-digital-twin")
