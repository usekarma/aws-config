# IoT digital-twin sandbox desired state

Status: draft / review-only, not deployed

## Purpose

This document explains the desired-state contract for the sandbox prototype described in the iot-digital-twin application repo. The configuration intentionally represents the required behavior and resource names without creating AWS resources or writing secrets to Git.

The config lives at:

- `iac/dev/iot-digital-twin/core2-aws-001/config.json`

It is intended to be consumed by the future `aws-iac` component that owns the sandbox implementation for the prototype.

## Contract and consumption model

The repository pattern is:

- `account_environments/<binding-name>.json` selects the environment binding
- `iac/<environment>/<component>/<nickname>/config.json` holds the desired state for that instance
- `aws-iac` reads the config values through its standard `TF_COMPONENT`, `TF_NICKNAME`, `TF_REGION`, and `TF_ACCOUNT_ID` contract
- the Terraform module then resolves the AWS resources and publishes runtime metadata under `/runtime`

In this repo, the design intent is that a future `aws-iac` module named `iot-digital-twin` or a composite IoT/TwinMaker module will consume this config. The desired state names are the stable logical names the module will resolve to actual AWS resources after human approval.

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

- the exact AWS account binding to use for the sandbox (`usekarma-dev-dev` is the current safe default assumption, but this must be confirmed)
- the final AWS region for the actual sandbox account
- whether the eventual `aws-iac` implementation uses a dedicated `iot-digital-twin` component or a small composition of existing modules
- any final TwinMaker property mapping names after the live demo contract is reviewed

## Validation

Local validation uses the repository’s schema checks and `scripts/validate_config.py` flow. This config is intentionally a review-only planning artifact and does not imply deployment authorization.

## No AWS mutation

This file is desired state only. It does not create resources, publish SSM values, generate device certificates, or mutate AWS infrastructure.
