# Define an account environment binding

`define_account_environment.py` writes or overwrites an SSM String parameter.
It is a consequential AWS mutation requiring explicit human approval.
Read [the repository workflow](../docs/agent-workflow.md) first.

Set AWS_PROFILE, AWS_REGION, EXPECTED_AWS_ACCOUNT, EXPECTED_ENVIRONMENT and
EXPECTED_BINDING to independently confirmed values. After approval, the human
operator acknowledges it with AWS_MUTATION_APPROVED=1. The script verifies STS
identity and compares the local binding's exact name/environment before writing.
First-time creation cannot check an existing SSM binding; review the old value
when changing an existing binding.

Use the actual binding filename stem, for example:
`python3 scripts/define_account_environment.py --env usekarma-dev-prod`.
This loads `account_environments/usekarma-dev-prod.json` and publishes it to
`${IAC_PREFIX:-/iac}/environment`. `--path` selects another local binding directory;
`--param-name` explicitly selects a different reviewed parameter path. There is
no `--prefix` option; set IAC_PREFIX before starting the process.

The checked-in files contain name, environment, repository/branch references
and policy metadata. These flags are not enforced by the current publisher.
IAM must restrict writes, especially to production binding parameters.

After approved publication, run the read-only comparison:
`python3 scripts/validate_account_environment.py --env usekarma-dev-prod`.
Do not paste live binding/config output containing sensitive values into chat/logs.
An agent may prepare and verify changes but cannot authorize or execute the write.
