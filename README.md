# AWS configuration

Versioned environment bindings and non-secret deployment inputs for
[`aws-iac`](https://github.com/usekarma/aws-iac). Part of
[Adage](https://github.com/usekarma/adage).

This repository **writes configuration to AWS Systems Manager Parameter Store**.
It does not apply Terraform, but publishing SSM changes can affect the next IaC
deployment. Publishing and environment binding changes require human approval.

## Repository map and interaction

- `account_environments/<binding-name>.json`: named account environment metadata.
  Actual bindings include `usekarma-dev-prod`, `usekarma-dev-dev`, `strall-com-prod`
  and `strall-com-dev`; these files do not contain AWS account IDs.
- `iac/<environment>/<component>/<nickname>/config.json`: per-instance inputs.
- `scripts/define_account_environment.py`: writes `${IAC_PREFIX:-/iac}/environment`.
- `scripts/deploy_config.py` / `scripts/deploy.sh`: select the live binding's
  environment, load local JSON and overwrite `/<component>/<nickname>/config`.
- `scripts/validate_config.py`: existing single-instance JSON syntax check.
- `scripts/validate_account_environment.py`: read-only local/live binding comparison.
- `AGENTS.md`, `specs/`, `docs/`, `scripts/verify.sh`, `tests/`: agent workflow and gates.

`aws-iac` owns Terraform resource definitions and Terragrunt state organization.
It reads `/config` and writes `/runtime` metadata to resolve dependencies through SSM.
Use the same IAC_PREFIX (default /iac) across both repos. Current publishers do not
clone the binding's repo/branch or enforce strict/drift flags; Git review is a human
process and IAM must enforce allowed writes. A committed config is not AWS approval.

## Validate and prepare

Read [AGENTS.md](AGENTS.md), [the workflow](docs/agent-workflow.md), and
[the destructive policy](docs/destructive-operations.md). Use
[specs/TEMPLATE.md](specs/TEMPLATE.md) for resource, security, migration or cleanup
work. A short PR description is enough for a small documentation edit.

Prerequisites for local gates: Bash, Git, Python 3.12+ and hash-locked verification tools.
Existing AWS Python tools additionally need boto3 installed in the operator's environment.

```bash
./scripts/verify.sh
AWS_IAC_DIR=../aws-iac ./scripts/verify.sh
python3 scripts/validate_config.py --config clickhouse/usekarma-dev
```

Verification makes no AWS calls: all JSON, duplicate-key rejection, binding field
types, config structure/tags, Python/shell syntax, changed shell lint, credential
patterns and mocked safety tests. The optional sibling path checks component names.
It validates explicit per-component JSON schemas, bindings and local dependencies.
See schemas/README.md for optional fields and extension rules.
CI runs this gate without cloud credentials or deployment steps.

## Preflight and approval

Confirm the account ID and target with the owner; never infer environment from nickname:
ClickHouse `usekarma-dev` is under **prod**.

```bash
export AWS_PROFILE=prod-karma
export AWS_REGION=us-east-1
export EXPECTED_AWS_ACCOUNT='<confirmed-12-digit-account-id>'
export EXPECTED_ENVIRONMENT=prod
export EXPECTED_BINDING=usekarma-dev-prod
./scripts/preflight.sh
```

Preflight checks STS account and exact SSM environment binding. Prepare a private
comparison of the current parameter with the proposed local JSON; record the old
version/value securely for recovery. Changes to inputs should also be evaluated
with the affected aws-iac component and its plan. Keep production and dev separate.

After explicit approval of the exact config/target, the **human operator** sets
`AWS_MUTATION_APPROVED=1` and uses the existing publisher CLI:
`./scripts/deploy.sh clickhouse usekarma-dev` or
`python3 scripts/deploy_config.py --component clickhouse --nickname usekarma-dev`.
These commands overwrite SSM, including when called directly through Python.
The shared guard checks approval, STS identity, named profile/region and binding.
An agent must not set the acknowledgement to authorize itself.

## New or changed account binding

The actual command is `python3 scripts/define_account_environment.py --env
usekarma-dev-prod` (supply the binding filename stem, not just prod). It requires
the same explicit expected target and human acknowledgement. For first-time setup,
the existing SSM binding cannot be checked, so the guard checks STS identity and
the local file's exact name/environment instead. Changing an existing binding
is consequential and needs explicit review of the old and new values. Use IAC_PREFIX
or `--param-name` to select the parameter; there is no `--prefix` option in this script.

## Postflight and recovery

Privately compare the published parameter with the approved JSON and record its
SSM version. `python3 scripts/validate_account_environment.py --env usekarma-dev-prod`
checks the binding against its local file. In AGENT_MODE=1, read_config prints only parameter version/hash after preflight,
and binding comparisons suppress values. Human read tools can print full config:
do not paste secret-bearing output into logs/chat. Verify downstream plans, preserved
resources and health as appropriate. Restore an older SSM value only after approval;
then generate a new IaC plan. A config rollback does not restore deleted data.

SPEC → inspect → implement → verify → plan/review → **human approval** → publish/apply
→ read-only postflight → observe. See [the illustrative cleanup spec](specs/clickhouse-cleanup.example.md)
for the boundary between config preparation and destructive execution in aws-iac.

## Agent-first commands and evidence

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-dev.lock
export AGENT_MODE=1
make verify
make test
make demo
```

The lock targets Python 3.12/Linux x86_64. Terraform/Terragrunt remain separate
prerequisites in aws-iac. Agent mode blocks mutation even with inherited approval.
The legacy deploy default remains apply for human compatibility; agents use explicit
planning/validation. See [architecture assessment](docs/architecture-assessment.md)
and [evidence, postflight and metrics](docs/evidence-and-evaluation.md).
Raw plans and generated evidence belong in ignored artifacts/ or another private path.
