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

The EC2 resource is wired to the same container-first deployment artifacts used outside AWS. First-boot user data runs `deploy/bootstrap-host.sh`, which installs Docker, installs and checksum-verifies a pinned Docker Compose release, creates the Ripple runtime directories, and copies `compose.production.yaml`, Caddy configuration, the production environment example, and deployment wrapper from an exact Git commit SHA.

## Toolchain

- Terraform `>= 1.15.0, < 1.16.0`
- HashiCorp AWS provider `6.60.0`
- Amazon Linux 2023 ARM64 application host
- Docker from the Amazon Linux 2023 package repository
- Docker Compose `5.4.0`, checksum-verified during host bootstrap

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

Before any future apply, `host_bootstrap_ref` must be set to the exact 40-character Git commit SHA containing the deployment artifacts to install on EC2. Terraform intentionally blocks EC2 creation when that value is missing. This prevents a production host from booting against mutable `main` or an unknown deployment definition.

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

## Host bootstrap boundary

`deploy/bootstrap-host.sh` is designed for Amazon Linux 2023 and runs as EC2 user data. It is idempotent at the operating-system/runtime level and performs only host preparation:

1. installs Docker and starts/enables the Docker service;
2. installs Docker Compose `5.4.0` for ARM64 and verifies the published SHA-256 checksum;
3. prepares `/opt/ripple`, `/var/lib/ripple`, and locked-down `/etc/ripple` paths;
4. downloads deployment files from the exact `host_bootstrap_ref` Git commit;
5. records the installed deployment ref and Compose version under `/var/lib/ripple`.

It does **not** create application secrets, a production environment file, database credentials, Stripe credentials, AWS access keys, DNS records, container registries, or application containers. `/etc/ripple/ripple.env` must be populated separately before `scripts/deploy-production.sh deploy` is used.

No AWS resource is required to review or test this contract. The bootstrap script and Terraform references are covered by repository regression tests, while Terraform CI continues to run formatting and validation without an apply.

## State

This story intentionally starts with local Terraform state because no shared/team backend has been authorized. State files and local tfvars are ignored by Git.

Before any production apply, decide where the state will be kept, how it will be encrypted/backed up, and who can access it. Do not put Terraform state in this repository.

## Secrets boundary

Terraform does not create or output Flask, Stripe, or application secrets. The RDS master password is supplied as the sensitive `db_password` input and must come from a secure runtime source such as an environment variable.

The EC2 bootstrap user data contains only the deployment Git SHA and the checked-in bootstrap script. It does not embed `DATABASE_URL`, `SECRET_KEY`, Stripe credentials, AWS access keys, or the contents of `/etc/ripple/ripple.env`.

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
