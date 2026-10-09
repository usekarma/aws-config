import json
import tempfile
import unittest
from pathlib import Path

from validate_contract_compatibility import check_compatibility


class ContractCompatibilityTests(unittest.TestCase):
    def make_repo_pair(self, config_version=1, supported=None):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        config = root / "aws-config"
        iac = root / "aws-iac"
        (config / "contracts").mkdir(parents=True)
        (iac / "contracts").mkdir(parents=True)
        (config / "contracts" / "config-contract.json").write_text(
            json.dumps({"contract_name": "aws-config", "contract_version": config_version})
        )
        (iac / "contracts" / "aws-config-compatibility.json").write_text(
            json.dumps(
                {
                    "contract_name": "aws-config",
                    "supported_contract_versions": supported or [1],
                }
            )
        )
        return temp, config, iac

    def test_supported_version_passes(self):
        temp, config, iac = self.make_repo_pair()
        self.addCleanup(temp.cleanup)
        self.assertEqual(check_compatibility(config, iac), 1)

    def test_unsupported_version_fails(self):
        temp, config, iac = self.make_repo_pair(config_version=2, supported=[1])
        self.addCleanup(temp.cleanup)
        with self.assertRaisesRegex(ValueError, "does not support aws-config contract version 2"):
            check_compatibility(config, iac)

    def test_missing_iac_declaration_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / "aws-config"
            iac = root / "aws-iac"
            (config / "contracts").mkdir(parents=True)
            iac.mkdir()
            (config / "contracts" / "config-contract.json").write_text(
                json.dumps({"contract_name": "aws-config", "contract_version": 1})
            )
            with self.assertRaisesRegex(ValueError, "Missing contract file"):
                check_compatibility(config, iac)


if __name__ == "__main__":
    unittest.main()
