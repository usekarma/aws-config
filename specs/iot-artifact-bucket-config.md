# IoT prototype artifact bucket desired-state publication proposal

Status: IAM prerequisite merged; validated desired state ready for human merge
and publication review. No publication or workload apply is authorized.
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

The earlier planning-role probe was AccessDenied and is now historical. After
the approved IAM maintenance, postflight reported GetParameter permitted;
ParameterNotFound. A fresh restricted-role read during this finalization also
returned ParameterNotFound. This is authorization/absence evidence at those reads,
not a published value or a guarantee against a later concurrent publication.
Immediately before authorization, the human publisher must inspect again using
a verified publication-capable profile, preserve any existing value/version/hash
for recovery, verify local/payload hashes and stop for explicit approval. Do not use AdministratorAccess for workload plans.
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

## Completed minimal IAM prerequisite — historical delta

The original policy granted binding/runtime reads and the initial config probe
returned AccessDenied. The minimal resource-only delta was reviewed in aws-iac
PR #13, planned against the same retained owner (0 creates, 1 update, 0 deletes),
sealed and applied by the human with explicit saved-plan mutation approval.
Read-only postflight returned GetParameter permitted; ParameterNotFound.
PR #13 is merged on aws-iac/main at
e579a8573051e8d0ef023e893aab69f7851d960e. The approved effective additional grant
was only (original 24 actions unchanged):

```json
{
  "Effect": "Allow",
  "Action": "ssm:GetParameter",
  "Resource": "arn:aws:ssm:us-east-1:623155450153:parameter/iac/s3-bucket/iot-digital-twin-artifacts/config"
}
```

The delta is deployed and its declarative revision is now on aws-iac/main. No
further IAM change is requested by this config PR. Normal planning must continue
using strall-dev-plan; never fall back to AdministratorAccess. The SSM-backed
workload plan remains a separate post-publication step, not performed here.

## Prepared post-publication normal plan

The IAM prerequisite is satisfied. Only after separately approved publication
and exact-value/version postflight:

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
At initial preparation, read-only STS/preflight succeeded and the config probe
was AccessDenied. That finding is historical after the human IAM maintenance.
During this finalization, a fresh read confirmed authorization with ParameterNotFound.
No SSM publication, normal SSM-backed workload plan or deployment occurred.

## Publication profile options and mandatory pre-approval review

No publication profile is selected by the agent. Local configuration identifies:

- strall-dev: configured account 623155450153, role AdministratorAccess. This is
  an existing human publication candidate, not a verified/selected writer; the
  human must verify actual STS identity and effective publication permissions.
- strall-dev-plan: same account, IaCPlanReadOnly; read-only and never a publisher.

No dedicated scoped publisher is currently identified. If the human has one,
independently verify it rather than inventing/configuring a new profile here.
Other-account profiles are not options for this target. The publisher requires
binding/config GetParameter plus PutParameter on the one target ARN. No elevated
profile is used for workload planning. Merge readiness is separate from selecting
and approving the publication identity/operation.

Before any write, the human must follow this read-only preparation sequence:

1. Set CONFIG_PUBLICATION_PROFILE to the independently selected existing writer.
2. Verify STS account exactly 623155450153 and binding dev / strall-com-dev.
3. Inspect the exact config parameter using that profile. ParameterNotFound means
   no existing-value backup is needed then; AccessDenied/other errors stop review.
4. If it exists, save the full GetParameter response privately (umask 077, ignored
   artifacts/). Record parameter version/type, raw value SHA-256 and recovery file
   location. Never paste its value in chat/PR. Preserve the prior value before
   approving Overwrite=True; publisher concurrency is not version-conditional.
5. Verify the local file equals the approved declaration/commit and these hashes:
   file SHA-256 6b11e56bbd2f60d559dfad21333078750bb22290b55dea53bf8c72501241f72f;
   serialized Value SHA-256
   19392f2a293fd6f9165e1dcc4baeae47916f1a57e0d05949a7078ce2526a90bc.
6. STOP for explicit human approval of the exact profile/account/path/hash and
   existing-value/overwrite consequences. Only afterward use the publication
   command above with AGENT_MODE=0 and AWS_MUTATION_APPROVED=1.

Prepared read-only inspection commands (human-selected profile; NOT publication):

```bash
: "${CONFIG_PUBLICATION_PROFILE:?Select and verify the existing human publisher}"
aws sts get-caller-identity --profile "$CONFIG_PUBLICATION_PROFILE" \
  --region us-east-1 --no-cli-pager
# Require account 623155450153. Inspect binding privately and require dev/strall-com-dev.
aws ssm get-parameter --profile "$CONFIG_PUBLICATION_PROFILE" \
  --region us-east-1 --name /iac/s3-bucket/iot-digital-twin-artifacts/config \
  --query '{Name:Parameter.Name,Version:Parameter.Version,Type:Parameter.Type}' \
  --no-cli-pager
# If present, capture the full response privately before approving overwrite.
```

For an existing value, exact private capture/hash commands from aws-config root:

```bash
set -euo pipefail
umask 077
mkdir -p artifacts
publication_review_dir=$(mktemp -d "$PWD/artifacts/publication-preflight.XXXXXX")
aws ssm get-parameter --profile "$CONFIG_PUBLICATION_PROFILE" \
  --region us-east-1 --name /iac/s3-bucket/iot-digital-twin-artifacts/config \
  --no-cli-pager > "$publication_review_dir/prior-parameter.json"
python3 - "$publication_review_dir/prior-parameter.json" <<'PY_REVIEW'
import hashlib,json,pathlib,sys
p=json.loads(pathlib.Path(sys.argv[1]).read_text())["Parameter"]
print(json.dumps({"version":p["Version"],"type":p["Type"],"value_sha256":hashlib.sha256(p["Value"].encode()).hexdigest()}))
PY_REVIEW
```

If any read fails, stop; do not infer absence or write using a fallback identity.
Recheck immediately before publication if review ages or concurrent writers exist.
The fresh restricted read found no parameter, so no old value was captured by the
agent; the human writer's immediate check remains required. No bucket deployment,
ZIP upload, IAM amendment, binding/schema/guard edit or SSM write is performed.

## Finalization verification

Against aws-iac/main at e579a8573051e8d0ef023e893aab69f7851d960e, the local
implementation tree was verified identical. Full aws-config verification/test
suites pass: 37 tests with four existing IaC-only skips, all 26 configs/bindings
validated, selected deployment-ready validation and exact publisher load/proposal
comparison passed. Both reviewed input hashes are unchanged. No publisher/guard,
schema, binding or unrelated config changed; only this documentation was updated.
A fresh restricted STS/preflight/read verified account/binding and ParameterNotFound.
No write-capable profile was selected, no prior value existed at that read, and
no SSM publication or workload deployment occurred. Final-head CI is checked
before marking ready for human merge review; merge itself is not write approval.
