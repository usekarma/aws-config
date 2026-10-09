# IoT digital-twin sandbox desired state

Status: draft / review-only, not deployed

## Purpose

This document explains the desired-state contract for the sandbox prototype described in the iot-digital-twin application repo. The configuration intentionally represents the required behavior and resource names without creating AWS resources or writing secrets to Git.

The config lives at:

- `iac/dev/iot-digital-twin/core2-aws-001/config.json`

It is consumed by the `aws-iac` IoT component on `feature/config-driven-lambda` once deployment dependencies are resolved and approved.

## Contract and consumption model

The repository pattern is:

- `account_environments/<binding-name>.json` selects the environment binding
- `iac/<environment>/<component>/<nickname>/config.json` holds the desired state for that instance
- `aws-iac` reads the config values through its standard `TF_COMPONENT`, `TF_NICKNAME`, `TF_REGION`, and `TF_ACCOUNT_ID` contract
- the Terraform module then resolves the AWS resources and publishes runtime metadata under `/runtime`

The inspected `aws-iac` component named `iot-digital-twin` consumes this config. The desired state names are the stable logical names the module will resolve to actual AWS resources after human approval.

## Security and trust model encoded in config

The configuration is intentionally designed to preserve the prototype trust boundaries from the application contract:

- the certificate / IoT Thing identity remains authoritative
- payload `device_id` is treated as telemetry data, not a trust anchor
- the MQTT topic is scoped to a single device namespace
- stale and replayed data are rejected server-side
- device-authored `OFFLINE` is rejected
- connectivity state is server-derived
- IAM remains least-privilege with no broad fallback permissions

No certificate private key, PEM, AWS credential, token, password, or secret value is stored in this configuration.

## Environment decision

The config has been placed under the `dev` environment because the repo has a non-production binding available and the project must not silently default to a production target. This is still a planning artifact and the exact deploy binding must be confirmed by the human owner before any live publication.

Unresolved values requiring human decision before deployment:

- the exact AWS account binding to use for the sandbox (no binding is assumed)
- the final AWS region for the actual sandbox account
- remaining IoT/TwinMaker implementation and operational readiness gaps
- any final TwinMaker property mapping names after the live demo contract is reviewed

## Validation

Local validation uses the repository’s schema checks and `scripts/validate_config.py` flow. This config is intentionally a review-only planning artifact and does not imply deployment authorization.

## No AWS mutation

This file is desired state only. It does not create resources, publish SSM values, generate device certificates, or mutate AWS infrastructure.

## Config-driven ingestion declaration

- `aws-lambda` owns runtime code and produces the package.
- `aws-config` owns the desired Lambda declaration.
- `aws-iac` owns Lambda resources, IAM and integrations.

The inspected `aws-iac` branch `feature/config-driven-lambda` consumes
`ingest_function` alongside the existing `ingest_lambda_name`. The declaration is
Python 3.12 / `app.lambda_handler`, 512 MB, 30 seconds and 14-day logs. Sizing
preserves the previous aws-iac IoT resource values; retention preserves this config.
Environment includes EXPECTED_DEVICE_ID, LATEST_STATE_TABLE, MAX_CLOCK_SKEW_SECONDS,
ACCEL_MOTION_THRESHOLD_G and GYRO_MOTION_THRESHOLD_DPS. The two thresholds use the
runtime's documented defaults (0.15 g and 5 degrees/second). The runtime derives the
expected topic from EXPECTED_DEVICE_ID; no unused topic environment key is added.

`artifact: null` and `planning_dependencies: [artifact_publication,
trusted_principal]` make deployment dependencies explicit. EXPECTED_PRINCIPAL is
intentionally absent until its exact authoritative IoT `principal()` value is
reviewed. The Thing name is not substituted for that value. Immutable S3 bucket,
key, object version and base64 SHA-256 must come from a separately authorized
publisher; aws-config never generates or guesses them. After review, replace null
with all four artifact fields, supply EXPECTED_PRINCIPAL, and remove
planning_dependencies. The consumer also requires the ZIP basename
`iot-digital-twin-ingest.zip`.

Local schema validation permits planning inputs. The explicit readiness command
below and SSM publisher reject this config. The sibling consumer also rejects it,
so live deployment remains blocked. Passing readiness later does not verify
artifact availability/content or grant deployment approval.

```bash
export AGENT_MODE=1
python3 scripts/validate_config.py --environment dev \
  --config iot-digital-twin/core2-aws-001 --deployment-ready
```

Contract v1 is preserved as an additive extension; production legacy Lambda configs
remain locally valid and need a separate immutable-artifact migration before
publication to the new consumer. No matching aws-iac compatibility version bump is
needed. Resolve binding/region, trusted principal, artifact publication and existing
TwinMaker/integration readiness separately before live deployment.
