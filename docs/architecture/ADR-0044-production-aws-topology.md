# ADR-0044: Low-cost AWS production topology

- Status: Accepted for implementation planning; no resources authorized
- Date: 2026-08-23
- Sprint: 8
- Story: 8.1

## Context

Ripple's original AWS backlog assumed a single Amazon Lightsail host and local
SQLite/media. The application has since established stronger production
contracts:

- managed PostgreSQL 18 is required in production (ADR-0033);
- exactly one scheduled worker must run independently of the web process;
- production media must use private S3-compatible object storage;
- migrations run as an explicit release task;
- deployment preflight, backup/restore, rollback, and release evidence are launch
  gates;
- secrets must remain outside source, images, logs, and Terraform outputs.

The deployment target must therefore be re-selected from the current product,
not from the original TwitClone assumptions.

## Decision

Use a small, conventional AWS VPC topology for the initial low-traffic launch:

1. **One ARM64 EC2 `t4g.small` application host** in a public subnet.
   - Run the reverse proxy/TLS endpoint, one Gunicorn web service, and exactly
     one scheduled-worker service on this host.
   - Run database migrations and `deployment-preflight` as one-shot release
     commands, never as web startup side effects.
   - Use an Elastic IP only when a stable IPv4 address is required for DNS and
     release operations.
2. **One private, Single-AZ RDS PostgreSQL 18 `db.t4g.micro` instance** for the
   initial low-traffic launch.
   - RDS is not publicly accessible.
   - Its security group accepts PostgreSQL only from the application host's
     security group.
   - Storage encryption and automated backups are enabled.
   - Multi-AZ remains an explicit later reliability/cost upgrade rather than a
     launch requirement.
3. **One private S3 bucket** for live media.
   - Block all public access.
   - Enable default encryption and versioning.
   - Give the EC2 instance a least-privilege IAM instance role rather than
     storing long-lived S3 access keys on disk.
   - Prefer an S3 gateway VPC endpoint so application-to-S3 access does not
     require a NAT Gateway.
4. **A minimal VPC** with:
   - one public application subnet;
   - two private database subnets in distinct Availability Zones so RDS has a
     valid DB subnet group;
   - one Internet Gateway;
   - no NAT Gateway at launch;
   - security groups that expose only HTTP/HTTPS publicly and restrict SSH to an
     explicitly approved administration source if SSH is enabled at all.
5. **DNS/TLS**:
   - Route 53 may host DNS when desired, but domain registration is outside this
     story;
   - terminate HTTPS on the application host with a lightweight reverse proxy
     and an automated public certificate flow, avoiding an Application Load
     Balancer at launch.

## Why EC2 instead of Lightsail

Lightsail remains inexpensive and was the correct original hypothesis, but the
current Ripple architecture benefits from standard EC2/VPC controls:

- EC2 supports an IAM instance profile for temporary application credentials,
  avoiding long-lived AWS access keys for S3;
- RDS can remain private in the same VPC without a Lightsail-to-default-VPC
  peering dependency;
- security groups, subnet groups, VPC endpoints, and Terraform ownership remain
  conventional and explicit;
- the topology can later add a load balancer, second application instance,
  Multi-AZ RDS, or managed deployment service without migrating away from a
  Lightsail-specific network boundary.

The added EC2 public-IPv4 and EBS charges are accepted because the overall
low-traffic estimate remains modest and the security/operational boundary is
cleaner.

## Cost decision

Pricing was reviewed on 2026-08-23 for `us-east-1`. This is a planning estimate,
not authorization to purchase resources.

The expected base is approximately **$31-$35/month** before taxes, domain
registration, backup growth, logs/monitoring, email delivery, and usage
overages. The estimate assumes roughly:

- EC2 `t4g.small`: about $12.26/month on demand;
- one in-use public IPv4 address: about $3.65/month;
- a small gp3 root volume: roughly $1-$2/month;
- RDS PostgreSQL `db.t4g.micro`: about $11.68/month compute plus minimum gp3
  storage;
- low-volume S3 Standard media: normally well under $1/month at launch;
- Route 53 hosted zone, if used: $0.50/month plus queries.

Do not rely on this estimate for an apply. Re-run a dated AWS Pricing Calculator
estimate immediately before provisioning and record every non-zero resource.

Current public pricing references:

- https://aws.amazon.com/ec2/pricing/on-demand/
- https://aws.amazon.com/vpc/pricing/
- https://aws.amazon.com/rds/postgresql/pricing/
- https://aws.amazon.com/s3/pricing/
- https://aws.amazon.com/route53/pricing/

## Terraform implementation boundary

A later Sprint 8 story may implement this decision under `infra/terraform`.
Terraform must:

- keep resource declarations in `main.tf`, inputs in `variables.tf`, and outputs
  in `outputs.tf`;
- pin Terraform and AWS provider versions;
- make Region, environment/name prefix, instance type, DB instance type, storage
  sizes, CIDRs, and optional DNS configurable;
- never place database passwords, Flask secrets, Stripe secrets, or access keys
  in Terraform outputs or source control;
- default optional paid resources such as load balancers, NAT Gateways,
  CloudFront, Multi-AZ RDS, and extra application hosts to disabled;
- tag resources consistently and expose only non-secret operational outputs;
- include `terraform fmt -check` and `terraform validate` in validation;
- document destroy behavior and identify state that must be backed up before
  destroy.

## Deployment shape

The initial host may run the existing container image/process contracts through
a production Compose file or equivalent system-service wrapper. It must preserve
these logical process boundaries even though web and worker share one VM:

- release/migration job: one shot;
- web: one Gunicorn service;
- scheduled worker: exactly one service;
- reverse proxy: one host-level or containerized service.

The database and media bucket remain independent durable services. Container and
host filesystems are not the production system of record for application data.

## Launch and upgrade gates

Before public traffic is enabled:

- complete the manual Sprint 7 assistive-technology/zoom evidence disposition;
- obtain explicit approval for the dated monthly AWS estimate;
- provision infrastructure only through the approved Terraform path;
- migrate/verify media in the private bucket;
- verify RDS backups plus an independent encrypted logical backup;
- rehearse restore against isolated resources;
- run migrations and `deployment-preflight` successfully;
- verify health endpoints, login, timeline reads, media retrieval, scheduled
  worker behavior, and Stripe webhook reachability;
- record release-readiness evidence and the rollback decision.

## Rejected alternatives

### Single Lightsail VM with local PostgreSQL

Cheaper, but violates ADR-0033's managed-PostgreSQL decision and weakens the
independent recovery boundary.

### Lightsail VM plus Lightsail managed database

Operationally simple, but the smallest database bundle has weaker encryption
characteristics than desired and the larger encrypted bundle pushes the base
cost above this EC2/RDS design. Lightsail also provides a less convenient
identity boundary for accessing general AWS services than an EC2 instance role.

### ECS/Fargate, Application Load Balancer, and managed NAT Gateway

Technically sound but introduces fixed monthly cost and operational surface that
are not justified by current traffic or availability requirements.

### Multi-AZ RDS at launch

Improves availability but approximately doubles the database compute/storage
footprint. Add it when availability requirements or measured business value
justify the recurring cost.

## Consequences

- Ripple gets a small but conventional AWS architecture that can grow without a
  platform migration.
- The initial application host remains a single failure domain; this is accepted
  for a low-traffic launch and must be disclosed in release readiness.
- The database is managed but initially Single-AZ.
- No load balancer or NAT Gateway is required at launch.
- Actual provisioning remains blocked until a later implementation PR and
  explicit spend authorization.
