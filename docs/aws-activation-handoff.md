# AWS activation handoff checklist

This checklist is the boundary between Ripple's completed repository-side AWS
implementation and any future live AWS activation.

Nothing in this document authorizes AWS spend. Do not run a real Terraform plan
or apply until the required credentials, cost review, approvals, and evidence
are in place.

## Repository-side controls already complete

The repository already provides and tests:

- ADR-0044 low-cost AWS topology and Terraform under `infra/terraform`;
- private RDS, private encrypted/versioned S3, S3 gateway endpoint, IAM instance
  profile, restricted PostgreSQL ingress, and opt-in DNS/Multi-AZ/budget alerts;
- mocked Terraform plan coverage plus exact resource/cost inventory checks;
- real-plan JSON policy validation with explicit approval for conditional
  resources;
- guarded apply of the exact reviewed binary plan with SHA-256 verification;
- post-apply idempotence verification using `terraform plan -detailed-exitcode`;
- same-day UTC cost-review enforcement before apply;
- immutable host bootstrap and container release artifacts;
- one-shot migration/preflight jobs, separate web/worker processes, and rollback;
- independent encrypted logical database backup and media backup workflow;
- isolated restore rehearsal workflow;
- Stripe webhook reachability check;
- read-only and authoritative launch-readiness gates.

## Live activation prerequisites

Before generating a real AWS plan:

- [ ] Explicit AWS activation/spend approval has been recorded outside the repo.
- [ ] Intended AWS account and Region are confirmed with the approved credential chain.
- [ ] Terraform state location, encryption, versioning, access, and backup are approved.
- [ ] Exact release SHA and `host_bootstrap_ref` are selected.
- [ ] Production secrets are available from an approved runtime source.
- [ ] Same-day AWS pricing and cost assumptions are reviewed.
- [ ] Optional resources are explicitly decided: Route 53, Multi-AZ RDS, AWS cost budget.
- [ ] If budget alerts are enabled, the notification subscriber can complete any required verification.

## Real plan review

From `infra/terraform`, after the prerequisites above:

```bash
terraform init
terraform fmt -check
terraform validate
terraform test

terraform plan -out=/secure/path/ripple.tfplan
terraform show -json /secure/path/ripple.tfplan > /secure/path/ripple-plan.json
python ../../scripts/validate-terraform-plan.py /secure/path/ripple-plan.json
sha256sum /secure/path/ripple.tfplan
```

If any conditional resource is approved, pass its exact Terraform address with
`--allow-conditional`. Do not apply a plan that has not passed this policy
review.

## Apply boundary

Only after explicit spend authorization:

```bash
export RIPPLE_AWS_SPEND_AUTHORIZED=true
export RIPPLE_REVIEWED_PLAN=/secure/path/ripple.tfplan
export RIPPLE_REVIEWED_PLAN_SHA256='<recorded-sha256>'
export RIPPLE_COST_REVIEW_DATE="$(date -u +%F)"

bash ../../scripts/apply-reviewed-terraform-plan.sh
```

A successful apply is not sufficient by itself. The wrapper must also report a
clean post-apply plan.

## Post-provisioning evidence

After infrastructure exists, complete and record:

- [ ] RDS is private and reachable only through the intended application path.
- [ ] S3 media is private, encrypted, versioned, and accessible through the app role.
- [ ] Production environment file is rendered without exposing secrets.
- [ ] Migration job succeeds.
- [ ] Deployment preflight succeeds.
- [ ] Web health endpoints pass.
- [ ] Login, timeline, and representative media retrieval pass.
- [ ] Exactly one scheduled worker is running correctly.
- [ ] Stripe webhook public reachability check passes.
- [ ] Independent database/media backup completes and artifacts are verified.
- [ ] Isolated restore rehearsal completes within the documented RPO/RTO.
- [ ] Backup alert path is tested.
- [ ] Manual NVDA/VoiceOver and 200%/400% zoom evidence is complete.
- [ ] Release-readiness record is prepared and approved.

Then run:

```bash
bash scripts/check-aws-launch-readiness.sh launch
```

Public traffic remains blocked until the authoritative launch gate passes.

## What remains intentionally unproven before activation

Without live AWS resources, the repository cannot truthfully prove:

- the real Terraform plan against the target account;
- successful provisioning and re-plan idempotence;
- actual RDS network reachability;
- actual S3/IAM access behavior;
- backup and restore against live infrastructure;
- public HTTPS and Stripe webhook reachability;
- the real monthly bill.

Those are activation evidence items, not missing repository code.
