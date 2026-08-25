# Ripple production Terraform

This directory implements Sprint 8 ADR-0044's low-cost AWS topology. It is infrastructure-as-code only; merging this configuration does **not** authorize or perform `terraform apply`.

## Selected topology

- one ARM64 EC2 `t4g.small` application host in a public subnet;
- one private Single-AZ RDS PostgreSQL 18 `db.t4g.micro` instance;
- one private, encrypted, versioned S3 media bucket;
- one IAM instance role granting only the media-bucket access Ripple needs;
- one S3 gateway VPC endpoint;
- one stable public IPv4 address;
- optional Route 53 DNS;
- no NAT Gateway, load balancer, CDN, second app host, or Multi-AZ database by default.

Application bootstrap, reverse-proxy/TLS configuration, container deployment, and secret delivery are later Sprint 8 stories. This story establishes the network and durable-service boundary only.

## Toolchain

- Terraform `>= 1.15.0, < 1.16.0`
- HashiCorp AWS provider `6.60.0`

## Authentication

Use normal AWS CLI/Terraform credential discovery such as a local profile, SSO, or an assumed role. Do not place AWS access keys in `.tf` or `.tfvars` files.

Confirm the intended account before planning:

```bash
aws sts get-caller-identity
```

## Safe validation workflow

From `infra/terraform`:

```bash
terraform init -backend=false
terraform fmt -check
terraform validate
```

For a real AWS plan, first review the dated cost estimate and obtain the required planning credentials. Supply the database password only at runtime:

```bash
export TF_VAR_db_password='replace-with-a-long-random-secret'
terraform plan
```

Do not save a binary plan containing secrets unless its storage and retention are explicitly secured. `db_password` is marked sensitive for CLI display, but Terraform state/plan data can still contain sensitive values.

**Do not run `terraform apply` without explicit spend authorization.**

## Inputs

Copy `terraform.tfvars.example` to an untracked `terraform.tfvars` only for non-secret customization. The committed example intentionally contains no credentials.

Notable defaults:

- `us-east-1`
- `t4g.small` EC2
- `db.t4g.micro` RDS PostgreSQL 18
- 20 GiB encrypted gp3 EC2 root volume
- 20 GiB encrypted gp3 RDS storage
- RDS deletion protection enabled
- final RDS snapshot required on destroy
- SSH disabled
- Route 53 disabled
- Multi-AZ RDS disabled

## State

This story intentionally starts with local Terraform state because no shared/team backend has been authorized. State files and local tfvars are ignored by Git.

Before any production apply, decide where the state will be kept, how it will be encrypted/backed up, and who can access it. Do not put Terraform state in this repository.

## Secrets boundary

Terraform does not create or output Flask, Stripe, or application secrets in this story. The RDS master password is supplied as the sensitive `db_password` input and must come from a secure runtime source such as an environment variable.

A later deployment story must define how the application receives `DATABASE_URL`, `SECRET_KEY`, Stripe credentials, and any other runtime secrets without committing them or exposing them through Terraform outputs.

## Destroy safety

The live media bucket has `prevent_destroy = true`. RDS deletion protection is also enabled by default and `db_skip_final_snapshot` defaults to `false`.

A production destroy therefore requires deliberate preparation:

1. verify independent database and media backups;
2. record the restore path and release evidence;
3. disable RDS deletion protection deliberately;
4. choose/verify the final database snapshot behavior;
5. remove or deliberately override the media-bucket destroy protection only after media is safely preserved;
6. run and review `terraform plan -destroy` before any destroy action.

Never use destroy as an application reset mechanism.

## Cost boundary

ADR-0044 currently estimates roughly $31-$35/month before backup growth, domain registration, observability, transactional email, taxes, and overages. Recheck AWS pricing immediately before any apply. Optional fixed-cost components must remain disabled unless separately justified and authorized.
