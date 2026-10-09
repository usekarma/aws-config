import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import config_validation as validation


class SchemaTests(unittest.TestCase):
    def test_all_current_configs_and_bindings(self):
        paths = list((validation.ROOT / "iac").rglob("config.json"))
        paths += list((validation.ROOT / "account_environments").glob("*.json"))
        for path in paths:
            with self.subTest(path=path):
                validation.validate_config(
                    path.relative_to(validation.ROOT), validation.load_json(path)
                )

    def test_wrong_type_unknown_key_missing_required_and_dependency(self):
        path = Path("iac/prod/clickhouse/usekarma-dev/config.json")
        original = validation.load_json(validation.ROOT / path)
        for edit in (
            {"ebs_size_gb": "500"},
            {"ebs_size_gb": True},
            {"vpc_nickname": "missing"},
            {"typo_key": True},
            {"allowed_cidrs": ["not-cidr"]},
        ):
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validation.validate_config(path, original | edit)
        value = copy.deepcopy(original)
        del value["vpc_nickname"]
        with self.assertRaises(ValueError):
            validation.validate_config(path, value)

    def test_custom_domain_and_lambda_limits(self):
        with self.assertRaises(ValueError):
            validation.schema_validate(
                {
                    "content_bucket_prefix": "x",
                    "cloudfront_comment": "x",
                    "enable_custom_domain": True,
                },
                "serverless-site",
                "fixture",
            )
        with self.assertRaises(ValueError):
            validation.schema_validate({"functions": {"f": {"timeout": 901}}}, "lambda", "fixture")

    def test_errors_do_not_echo_values(self):
        with self.assertRaises(ValueError) as error:
            validation.schema_validate(
                {"bucket_name": "x", "SECRET_VALUE": "SECRET_VALUE"}, "s3-bucket", "fixture"
            )
        self.assertNotIn("SECRET_VALUE", str(error.exception))
