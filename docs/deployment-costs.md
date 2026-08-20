# Initial deployment cost estimate

This estimate is a planning baseline, not purchasing authorization. Prices were
checked on 2026-08-20 and must be rechecked immediately before provisioning.
Taxes, a domain, transactional email, external monitoring, support, and usage
overages are excluded.

## Reference low-traffic topology

DigitalOcean is used only as a concrete pricing reference; Ripple's operational
contracts remain provider-neutral.

| Component | Assumption | Estimated monthly cost (USD) |
| --- | --- | ---: |
| Web | One 1 GiB shared App Platform container | $10.00 |
| Scheduled worker | One 512 MiB shared App Platform container | $5.00 |
| PostgreSQL | One 1 GiB managed PostgreSQL node with minimum storage | $15.15 |
| Media | One Spaces subscription, including 250 GiB storage and 1 TiB outbound transfer | $5.00 |
| Independent backup allowance | Small logical dumps and media copies within included capacity or a separate low-cost destination | $0–$5.00 |
| **Expected base total** | Before optional services and overages | **$35.15–$40.15/month** |

Current first-party pricing references:

- [App Platform pricing](https://docs.digitalocean.com/products/app-platform/details/pricing/)
- [Managed database pricing](https://www.digitalocean.com/pricing/managed-databases)
- [Spaces pricing](https://docs.digitalocean.com/products/spaces/details/pricing/)

The two application containers preserve Ripple's required separation between
the web process and exactly one scheduled worker. The migration command runs as
a one-shot release job and should incur only its short runtime charge.

## Cost boundaries

Do not provision paid infrastructure until the object-storage adapter and the
restore rehearsal in [`operations.md`](operations.md) are complete. Before
approval, capture a dated provider estimate and set budget alerts at 80% and
100% of the approved monthly amount.

Costs increase when:

- web or worker memory is insufficient and containers are resized;
- availability requirements add database standby nodes or multiple web instances;
- media or application transfer exceeds included allowances;
- retained object versions and independent backups increase stored bytes;
- log retention, email delivery, monitoring, a domain, or support plans are added.

The minimum topology is suitable only for a low-traffic launch. It is not highly
available: the single database node, web instance, and worker each have a
service interruption boundary. Scale only from measured load and a revised cost
estimate.
