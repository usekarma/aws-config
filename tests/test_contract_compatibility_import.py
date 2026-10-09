import importlib


def test_contract_compatibility_imports_from_root_and_scripts():
    root_module = importlib.import_module("validate_contract_compatibility")
    script_module = importlib.import_module("scripts.validate_contract_compatibility")

    assert (
        root_module.validate_contract_compatibility is script_module.validate_contract_compatibility
    )
    assert callable(root_module.main)
    assert callable(script_module.main)
