# IoT prototype artifact bucket desired-state publication proposal

Status: validated proposal awaiting human publication review; normal planning
blocked on a separate minimal read-only IAM grant. No publication/apply authorized.
Owner/reviewer: strall / requesting human.

## Goal and exact target

Represent the already-reviewed, merged aws-iac bucket proposal as desired state
using the existing aws-config layout and publisher. File:
`iac/dev/s3-bucket/iot-digital-twin-artifacts/config.json`.
Account 623155450153, us-east-1, dev, binding strall-com-dev, prefix /iac,
component s3-bucket, nickname iot-digital-twin-artifacts. Destination:
`/iac/s3-bucket/iot-digital-twin-artifacts/config`.

The declaration is copied exactly from merged aws-iac/main's
examples/iot-artifact-bucket.strall-dev.json. It retains versioning, AES256,
BucketOwnerEnforced, all public-access blocks, force_destroy=false, existing tags
and purpose. No website/public policy/expiration is added. Existing schema accepts
all fields; no schema, guard, binding or publisher is changed. Production config,
Lambda declarations/artifacts, IoT resources and existing runtime metadata remain
out of scope. Bucket has not been deployed and ZIP has not been uploaded.

## Consequential publication boundary

The normal scripts/deploy.sh -> deploy_config.py publisher chooses dev from the
verified live binding and uses PutParameter Type=String, Tier=Standard,
Overwrite=True. Publication affects subsequent Terraform desired inputs; it is
an AWS mutation requiring separate human approval of the exact file/commit/hash
and target. Git review/merge does not authorize it. AGENT_MODE=1 blocks publishing
regardless of inherited acknowledgements. Agents never unset that flag to write.

The planning-role read probe was AccessDenied. This does NOT prove the parameter
is absent. Before authorizing overwrite, the human publisher must use a verified
publication-capable profile to inspect the current parameter/version privately
(or record genuine ParameterNotFound), preserve any existing value for recovery,
and review the proposed change. Do not use AdministratorAccess for workload plans.
The publication profile requires GetParameter on binding/config and PutParameter
on the exact config ARN; publication does not change /iac/environment or runtime.

## Exact human publication command — prepared, not executed

The verified publication-capable profile has not been supplied for this task.
Set CONFIG_PUBLICATION_PROFILE to the human-selected profile for account
623155450153, verify STS account and binding, inspect/preserve current config, and
approve the exact proposal before the following existing publisher command:

```bash
cd /home/ted/dev/aws-config
. .venv/bin/activate
: "${CONFIG_PUBLICATION_PROFILE:?Set the independently verified publication profile}"
AGENT_MODE=0 AWS_MUTATION_APPROVED=1 \
AWS_PROFILE="$CONFIG_PUBLICATION_PROFILE" AWS_REGION=us-east-1 \
EXPECTED_AWS_ACCOUNT=623155450153 EXPECTED_ENVIRONMENT=dev \
EXPECTED_BINDING=strall-com-dev IAC_PREFIX=/iac \
bash scripts/deploy.sh s3-bucket iot-digital-twin-artifacts
```

This is a human command only. No specific elevated profile is guessed or selected;
the restricted strall-dev-plan profile cannot publish. The publisher verifies STS
and the live binding itself before writes. Review metadata and exact serialized
payload/file SHA-256 are prepared privately under ignored artifacts/; no old
SSM value or raw cloud evidence is committed.

## Minimal normal-planning IAM delta — separate approval, not implemented

The deployed reviewed IaCPlanReadOnly policy grants GetParameter only on the
binding and runtime, not this config path. A live strall-dev-plan probe confirmed
no identity-based Allow for the exact requested resource. Required additional
statement (no other action/resource or wildcard change):

```json
{
  "Effect": "Allow",
  "Action": "ssm:GetParameter",
  "Resource": "arn:aws:ssm:us-east-1:623155450153:parameter/iac/s3-bucket/iot-digital-twin-artifacts/config"
}
```

This is a proposed delta for an independently reviewed owner-context permission
set change, not an edit to the existing role/policy or an execution command.
Preserve the original 24-action policy and all existing grants. No IAM mutation
or normal plan is performed here; never fall back to AdministratorAccess.

## Prepared post-publication normal plan

Only after separately approved publication, exact-value/version postflight and
approval/provisioning of the minimal read grant:

```bash
cd /home/ted/dev/aws-iac
export AGENT_MODE=1 AWS_PROFILE=strall-dev-plan AWS_REGION=us-east-1
export EXPECTED_AWS_ACCOUNT=623155450153 EXPECTED_ENVIRONMENT=dev
export EXPECTED_BINDING=strall-com-dev IAC_PREFIX=/iac
umask 077
aws sts get-caller-identity --profile strall-dev-plan --region us-east-1 --no-cli-pager
# Require account 623155450153 and AWSReservedSSO_IaCPlanReadOnly_ role.
bash scripts/preflight.sh
bash scripts/plan.sh s3-bucket iot-digital-twin-artifacts
```

No --plan-config override. Expect only six creates: bucket, versioning, ownership,
public-access block, encryption and runtime SSM parameter. Zero changes/deletes/
replacements/drift. Exact bucket 623155450153-iot-digital-twin-artifacts and reviewed
controls must remain. Abort on account/role/binding/backend mismatch, denied reads
or unexpected actions/resources. Privately generate fresh plan/evidence; old
unpublished-proposal plans are historical. No apply is authorized.

## Validation, preservation and recovery

Run AWS_IAC_DIR=../aws-iac make verify, make test, validate_config.py (all configs
and deployment-ready check for this instance), publisher load_config offline,
exact merged-proposal comparison and git diff --check. Preserve schema and
mutation-blocking tests. No actual SSM state or configuration evidence is invented.
The active binding's config_branch=dev is existing metadata; the publisher reads
this approved local checkout and does not switch branches. Do not alter the binding.

After approved publication, read back GetParameter with the approved reader and
compare parsed JSON with the reviewed local file; record SSM version and raw-value
hash privately. Existing scripts/postflight.py supports exact SSM comparison.
An existing previous config must be backed up before overwrite. Rollback is a
separately approved publication of the prior value followed by a fresh reviewed
IaC plan; it does not restore deleted objects. No workload downtime, logging,
backup or storage change occurs until later separately approved execution.

## Local outcomes

AWS_IAC_DIR=../aws-iac make verify and make test pass: 37 tests, four existing
IaC-only skips. All 26 bindings/configs validate, the specific declaration passes
deployment-ready validation, and the actual publisher load_config returns exactly
the merged aws-iac proposal. No schemas, bindings, guard or evidence code changed.
File SHA-256: 6b11e56bbd2f60d559dfad21333078750bb22290b55dea53bf8c72501241f72f.
Serialized publisher payload SHA-256:
19392f2a293fd6f9165e1dcc4baeae47916f1a57e0d05949a7078ce2526a90bc.
These hashes identify proposed local input only, not a published SSM value.
Read-only STS and preflight succeeded; the exact config-path permission probe was
AccessDenied. No parameter absence, publication, IAM update, normal SSM-backed plan
or workload execution is claimed.
