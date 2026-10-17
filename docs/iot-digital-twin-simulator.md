# ATOM Lite simulator declaration within iot-digital-twin

Canonical project: iot-digital-twin. Experiment: atom-lite-simulator. Deployment
component: iot-digital-twin-simulator, nickname atom-lite-001, environment dev.
The existing iot-digital-twin/core2-aws-001 declaration is unchanged.

This declaration matches aws-iac PR #16 and aws-lambda PR #2 after their naming update.
SSM path is /iac/iot-digital-twin-simulator/atom-lite-001/config; artifact basename is
iot-digital-twin-simulator.zip. Project/Experiment/Environment tags are constrained.
The model revision is the reviewed pinned source; artifact, principal, fresh active
session and target region remain null with explicit planning_dependencies. Account/
profile/binding remain unresolved; no deployment target is inferred from dev naming.

Schema validation permits this draft. Deployment readiness and publisher loading
reject it until all dependencies are independently resolved and planning_dependencies
removed. A resolved shape is not AWS approval or verification of artifact availability.
No actual values, certificates, IAM/policy documents or placeholders are fabricated.

Review/migration: adopt the renamed component in aws-iac, resolve and record immutable
artifact metadata from a separately authorized publisher, independently verify exact
principal and sandbox binding, then review a saved plan. Approve AWS writes separately.
The first real integration test additionally requires an EXISTING approved PK/SK sandbox
table, scoped operator permissions, exact ZIP/model digest, target identity and explicit
approval of synthetic session writes. It sends no MQTT and retains rows for approved
cleanup. No publication, permissions change or resource/device operation occurred here.
