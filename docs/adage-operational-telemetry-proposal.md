# Proposed operational telemetry configuration handoff

Design only. Companion specification: iot-digital-twin/docs/adage-operational-telemetry-experiment.md.
Existing aws-config #8 / aws-iac #16 are open coordinated consolidation work; this
proposal does not alter their declarations or claim they are merged/deployed.
Core2 is retired. ATOM remains the physical device; the first producer is local Python.

Reuse account_environments bindings, strict schemas/readiness, /iac/component/nickname/config
and /runtime discovery. Do not copy credentials into JSON, Terraform state or evidence.
Canonical Terraform component remains iot-digital-twin; suggested new configuration
instance is iac/dev/iot-digital-twin/operational-demo/config.json, separate from atom-lite-001.
Its state is iot-digital-twin/operational-demo/terraform.tfstate. A separate nickname
is an independently bounded instance of the same component, not a new component.
Region/profile/account/binding must be verified, not inferred from dev directory naming.

Proposed fields, not deployed declarations:
- explicit mode=operational-telemetry; project=iot-digital-twin; experiment=operational-telemetry;
- asset allowlist (M1 one, M2 five), severity property type INTEGER, epoch/sequence later;
- topic/property mappings derived from allowlisted asset IDs under one fixed namespace;
- model revision, bounded run duration/rate/count and synthetic=true;
- sitewise dependency nickname, Grafana dependency nickname only for M2;
- operational retention intent, budget threshold, error-log retention and ownership.

Prefer a closed, disjoint schema branch for explicit operational mode, preserving the
existing durable simulator declaration unchanged. Reject mixed ingestion/reset shapes,
unknown aliases, unsupported data types, bool integers, unlimited run duration and
credentials/IAM documents. Existing contract v1 compatibility must be tested; any
breaking change requires a version increment plus aws-iac compatibility support first.
Do not merely relabel the old Core2 schema or relax readiness to accept incomplete inputs.

SiteWise reusable capability can own asset models/assets/mappings; proposed dependency
runtime exports exact asset/property IDs and aliases, region and schema version.
Managed Grafana reusable capability exports workspace ID/URL, region and role identity;
local tool separately imports a versioned dashboard after approval. No secret API token
in runtime metadata. Consumers verify dependency account/region/IDs against live inventory.
SSM values are discovery metadata, not ownership or authority evidence.

Tests before implementation claims: schema accepts complete synthetic declared intent,
rejects unresolved deployment bindings, invalid topic/asset/property relationships,
unknown/secret fields and unsupported retention; missing/wrong-region dependency rejected;
old atom-lite-001 durable declaration stays valid; stale Core2 is not active;
SSM publication stays blocked without explicit approval. No values or config files are
added in this PR, so generic schema validation is not evidence of the future contract.

Dependencies: approved resource inventory, local producer certificate lifecycle,
existing canonical consolidation, SiteWise capability and backend ownership, Grafana
identity-provider/workspace decision. Storage configuration is account-level: do not
turn a per-instance retention preference into an automatic PutStorageConfiguration call.
Existing artifact bucket/state/security controls remain separately owned and untouched.
Future Kinesis/Snowflake fields stay out of this schema until their contracts are reviewed.

M1 acceptance: 20 local-produced severity points independently read from SiteWise,
19/20 visible within 10 seconds and all within 60 seconds; measured live only after
separate approval. M2 adds a five-asset managed dashboard and freshness indication.
Estimate: bounded M1 few runs under $1 excluding shared costs; small daily M2 around
$15–25/month with editor/viewer/optional automation-license assumptions, $30 alert
proposal. Alert is not a cap. Use current [SiteWise](https://aws.amazon.com/iot-sitewise/pricing/),
[IoT](https://aws.amazon.com/iot-core/pricing/) and [Grafana](https://aws.amazon.com/grafana/pricing/)
rates for the actual plan. Local tests are not proof of live permission or resource absence.
