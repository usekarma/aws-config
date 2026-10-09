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
