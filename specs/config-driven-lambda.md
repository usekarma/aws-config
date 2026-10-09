# Config-driven Lambda desired state

Status: prepared for local verification; no deployment approval

Scope: aws-config only, dev/iot-digital-twin/core2-aws-001 and additive Lambda
schema/publication validation. No AWS operations, artifact publication, other-repo
edits, production config edits, commits or pushes. Exact account/profile/binding
remain unconfirmed; no live plan or resource changes are part of this task.

Inspected aws-iac feature/config-driven-lambda: contracts/lambda-declaration-v1.schema.json,
contracts/aws-config-compatibility.json, scripts/check_lambda_declarations.py,
components/lambda and components/iot-digital-twin. Runtime environment inspected
in aws-lambda/iot-digital-twin-ingest/domain.py and README.md. Existing IoT sizing
is 512 MB / 30 seconds in aws-iac main's previous ingestion resource; desired
log retention remains 14 days. Motion thresholds match runtime defaults.

Preserve contract v1 through optional additive properties. Existing declarations
remain locally valid; publication readiness explicitly requires the complete new
consumer contract. Production legacy declarations need a separate migration before
publication to the new consumer; this task does not select artifacts for them.

IoT uses the consumer's ingest_function property and ingest_lambda_name, rather
than duplicating the standalone functions map. Declare artifact: null with
planning_dependencies: [artifact_publication, trusted_principal]. No artifact
coordinates or principal identity are guessed. Certificate/Thing authority,
payload-as-data, rejection of device OFFLINE, server-derived connectivity and
server-side replay/staleness enforcement remain required. IAM stays in aws-iac.

Acceptance: deterministic valid/invalid declaration tests, immutable metadata
checks, exact IoT runtime/environment tests, planning/publication rejection before
AWS session creation, legacy validation, make verify, make test, local schema
validation and explicit sibling compatibility/consumer checks. Consumer rejection
of the unresolved IoT declaration is expected and required. No provider validation
is applicable because no Terraform is edited here.

Recovery: discard/review the local diff; no live state or data is affected. A future
publisher must supply reviewed immutable metadata and trusted principal, remove
planning_dependencies, pass both repositories' validators and obtain concrete
human approval before SSM publication/deployment. Artifact availability and content
remain unverified by schema validation. TwinMaker and existing cross-repo readiness
gaps remain separate. Logs/alarms/cost/backup/postflight: N/A to this offline edit;
review these before live deployment. No plan/evidence values are created.

Verification on 2026-10-09: make verify, AWS_IAC_DIR=../aws-iac make verify and
make test passed (36 tests, four existing IaC-entrypoint-only skips). Ruff lint and
format checks passed. Local schema CLI validated 25 configs/bindings. Contract
compatibility CLI confirmed v1 support. Explicit local sibling schema equality and
validator calls accepted complete synthetic standalone/IoT declarations and rejected
the actual unresolved IoT config; the readiness CLI also rejected it as expected.
Sibling checkout HEAD d0d1ac568d015b64bf4b9337022ab56ea99fb502 is on
feature/config-driven-lambda with existing uncommitted implementation changes;
validation used that working tree, not a claim that HEAD contains those changes.
No aws-iac or aws-lambda edits were made. Branch is ready for coordinated PR review
as planning desired state; live publication/deployment remains blocked.
