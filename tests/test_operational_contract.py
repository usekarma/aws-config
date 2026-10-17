import copy
import unittest
from pathlib import Path

import config_validation as validation


class OperationalContractTests(unittest.TestCase):
    def test_explicit_draft_and_complete_bindings(self):
        path = Path("iac/dev/iot-digital-twin/operational-demo/config.json")
        value = validation.load_json(validation.ROOT / path)
        validation.validate_config(path, value)
        with self.assertRaisesRegex(ValueError, "Deployment blocked"):
            validation.validate_deployment_readiness(value, "iot-digital-twin")
        ready = copy.deepcopy(value)
        del ready["planning_dependencies"]
        ready.update(
            region="us-east-1",
            expected_account="000000000000",
            expected_principal="a" * 64,
            cloudformation_role_arn="arn:aws:iam::000000000000:role/synthetic",
        )
        validation.validate_deployment_readiness(ready, "iot-digital-twin")
        for change in [
            {"topic": "arbitrary"},
            {"observation_count": True},
            {"policy": {}},
            {"artifact": {}},
            {"expected_principal": "wrong"},
        ]:
            with self.assertRaises(ValueError):
                validation.validate_config(path, ready | change)
        with self.assertRaises(ValueError):
            validation.validate_deployment_readiness(
                ready | {"expected_account": "111111111111"}, "iot-digital-twin"
            )
