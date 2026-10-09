# Configuration contracts

Draft 2020-12 per-component schemas are consumed by jsonschema, pinned in
requirements-dev.lock. Binding names/environments and local component dependencies
are checked additionally in scripts/config_validation.py. Publication validates
before SSM writes too. Duplicate keys, NaN/Infinity, unknown top-level fields,
wrong constrained types, malformed CIDRs and missing required inputs fail.
Errors identify file/field/rule without echoing rejected values.

These are maintained contracts, not a universal AWS schema. Existing inputs and
optional direct config accesses were inspected in aws-iac. Free-form connector_config,
root_records and some optional complex fields remain open structures; Lambda function
objects are constrained. Optional fields labeled "type not constrained yet" need a
component-focused schema/test extension before relying on their validation. Defaults
and AWS semantics still require provider validation and live plans. A valid config
can expose networking or destroy data; it is never execution approval.

To add a field/component: inspect its actual Terraform consumer, add its property
and nested constraints to that component schema, add valid/invalid test cases, then
run make verify and sibling-repo validation. New component configs without a schema
fail closed. Components with no current configs need a schema before first use.
Dependency checks intentionally require desired config in the same environment; an
externally supplied runtime dependency requires a reviewed contract extension.

Lambda contract v1 now accepts immutable declarations matching the inspected
aws-iac `feature/config-driven-lambda` consumer. `lambda-declaration.schema.json`
is the pinned consumer shape: runtime, handler, memory_size, timeout,
log_retention_days, artifact (s3_bucket, s3_key, s3_object_version,
source_code_hash), optional environment and paired source/VPC discovery metadata.
Hash validation additionally requires canonical base64 encoding of 32 SHA-256 bytes.
IAM documents are forbidden by the declaration's closed properties.

Standalone functions use their `functions` map key as service name. IoT uses
`ingest_lambda_name` plus `ingest_function`, as the actual consumer requires.
`lambda-planning.schema.json` permits `artifact: null` only with explicit
`planning_dependencies` including `artifact_publication`; `trusted_principal`
records missing runtime identity without storing certificate material or guessing
that a Thing name equals an IoT principal. Planning objects are review inputs,
not consumer-ready declarations. Publisher loading and writing both enforce
readiness. Use `scripts/validate_config.py --deployment-ready` for the offline gate.

This is additive v1: legacy declarations and IoT configs without ingest_function
remain representable under the local schema. Any new artifact, retention or planning
field selects the strict new Lambda shape. Legacy declarations fail readiness until
migrated; current production configs are deliberately unchanged. Version support
alone does not establish per-config readiness. No aws-iac version-list change is
required; its existing validator intentionally rejects incomplete planning objects.
Keep the embedded declaration/planning shapes in the component schemas synchronized
with the standalone schema files when extending the contract.
