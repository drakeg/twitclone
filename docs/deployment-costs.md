# Initial deployment cost estimate

This estimate is a planning baseline, not purchasing authorization. Prices were
rechecked on 2026-08-23 and must be rechecked immediately before provisioning.
Taxes, a domain, transactional email, external monitoring, support, and usage
overages are excluded.

## Selected low-traffic AWS topology

Sprint 8 Story 8.1 selects the architecture in
[`ADR-0044-production-aws-topology.md`](architecture/ADR-0044-production-aws-topology.md):

- one `t4g.small` EC2 application host for the reverse proxy, web process, and
  exactly one scheduled worker;
- one private Single-AZ RDS PostgreSQL 18 `db.t4g.micro` database;
- one private, encrypted, versioned S3 bucket for media;
- one public IPv4 address for the application host;
- no Application Load Balancer, NAT Gateway, CloudFront distribution, or second
  application instance at launch;
- Route 53 DNS only if needed.

This keeps the database and media on managed durable boundaries while avoiding
fixed-cost components that current traffic does not justify.

## Planning estimate for `us-east-1`

| Component | Assumption | Estimated monthly cost (USD) |
| --- | --- | ---: |
| Application host | EC2 `t4g.small`, Linux, on demand | ~12.26 |
| Public IPv4 | One in-use address, 730 hours | ~3.65 |
| Root storage | Small gp3 EC2 volume | ~1–2 |
| PostgreSQL compute | RDS PostgreSQL `db.t4g.micro`, Single-AZ, on demand | ~11.68 |
| PostgreSQL storage | Minimum practical gp3 allocation | ~2–3 |
| Media | Low-volume S3 Standard storage and requests | <1 initially |
| DNS | One Route 53 hosted zone, if used | 0.50 plus queries |
| **Expected base total** | Before backups, domain, observability, email, and overages | **~31–35/month** |

The exact RDS storage minimum, snapshot retention beyond included allowances,
S3 request/transfer volume, CloudWatch usage, and DNS query volume can move the
actual number. Record a dated AWS Pricing Calculator estimate before apply.

Current public pricing references:

- https://aws.amazon.com/ec2/pricing/on-demand/
- https://aws.amazon.com/vpc/pricing/
- https://aws.amazon.com/rds/postgresql/pricing/
- https://aws.amazon.com/s3/pricing/
- https://aws.amazon.com/route53/pricing/

## Why the estimate changed

The earlier planning baseline used DigitalOcean as a provider-neutral example at
approximately $35.15-$40.15/month. Ripple now has enough production contracts to
make an AWS decision directly.

The original Lightsail-only hypothesis is also no longer the preferred target.
A standard EC2 host provides an IAM instance role for temporary S3 credentials
and connects naturally to a private RDS database in the same VPC. That makes the
security and Terraform boundary cleaner while keeping the expected low-traffic
cost in approximately the same range as the prior provider-neutral estimate.

## Explicitly excluded launch components

The following are not part of the launch baseline and must not be provisioned
without a revised estimate and explicit approval:

- Application Load Balancer
- NAT Gateway
- Multi-AZ RDS
- a second application host
- CloudFront/CDN
- ElastiCache/Redis
- ECS/Fargate or EKS
- paid third-party monitoring/support plans

The VPC design should use an S3 gateway endpoint rather than a NAT Gateway for
private S3 routing where applicable.

## Cost boundaries

No paid infrastructure is authorized by this document or ADR-0044. Before any
apply:

1. recheck all AWS prices for the selected Region;
2. capture the Terraform plan and a dated monthly cost estimate;
3. identify every resource with a non-zero recurring charge;
4. set an approved monthly ceiling and alerting plan;
5. obtain explicit authorization to provision.

Costs increase when:

- the EC2 or database instance is resized;
- RDS is changed to Multi-AZ;
- retained database snapshots and independent backups grow;
- media storage/request/transfer volume grows;
- CloudWatch log/metric retention increases;
- a load balancer, NAT Gateway, CDN, email service, or additional application
  host is introduced.

The selected topology is intentionally not highly available. The single EC2
host and Single-AZ database each remain service-interruption boundaries. Scale
only from measured load, recovery evidence, business requirements, and a revised
cost estimate.
