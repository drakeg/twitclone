# Ripple API Webhook Contract

## Status

Webhook delivery is **contract-only** in Sprint 16 Story 16.5. Ripple defines the event envelope, signing, replay, retry, idempotency, privacy, and operational boundaries here, but does not yet persist subscriber endpoints or send outbound HTTP requests.

That separation is intentional: no background delivery infrastructure, paid queue, new AWS resource, or recurring third-party cost is authorized by this story.

## Initial event set

The first allow-listed event is:

- `post.created` — emitted only for a globally public ordinary post after successful persistence.

Future event types require an explicit contract addition. Private messages, moderation actions, billing/verification state, credentials, email addresses, admin state, entitlement state, inferred traits, and Ripple Space-scoped content are not part of the initial webhook surface.

## Event envelope

Every event uses a versioned envelope:

```json
{
  "id": "evt_...",
  "type": "post.created",
  "version": "v1",
  "occurred_at": "2026-09-14T03:30:00Z",
  "data": {}
}
```

`id` is the consumer idempotency key. Consumers must treat repeated delivery of the same event ID as the same event rather than a second action.

## Canonical body and signatures

Ripple signs the exact UTF-8 request body using HMAC-SHA-256 over:

```text
<unix_timestamp>.<raw_body>
```

The signature header format is:

```text
t=<unix_timestamp>,v1=<hex_digest>
```

Receivers should:

1. read the raw body before JSON re-serialization;
2. reject timestamps outside a five-minute replay window;
3. compute HMAC-SHA-256 with the endpoint secret;
4. compare digests using a constant-time comparison;
5. accept any valid `v1` signature while a secret rotation overlap is active;
6. deduplicate by event `id`.

Ripple's contract helper supports multiple `v1` values specifically so a future sender can overlap old/new secrets during rotation without disabling verification.

## Retry contract

The bounded proposed retry schedule is:

- 1 minute
- 5 minutes
- 30 minutes
- 2 hours
- 6 hours

A future delivery worker must stop retrying after the bounded schedule unless a later story explicitly changes the policy. Redirects must not silently expand the destination trust boundary. Network timeouts, retryable HTTP statuses, terminal statuses, and operator replay require implementation evidence before delivery is activated.

## Privacy and destination safety

Before subscriber endpoints can be enabled, Ripple must add explicit controls for:

- HTTPS-only destinations outside local development;
- SSRF protection and destination validation;
- DNS/IP revalidation where appropriate;
- blocked loopback, link-local, private-network, and cloud metadata destinations unless explicitly authorized for a controlled deployment;
- encrypted-at-rest endpoint secrets;
- secret rotation without exposing previous raw secrets;
- least-data event payloads;
- endpoint ownership/authorization checks;
- bounded delivery logs and retention;
- removal/disable behavior that stops new deliveries.

The webhook system must never become a back door around API visibility rules.

## Delivery persistence decision

Ripple should use an outbox/delivery-record design when delivery is activated:

- create the event record in the same transactional boundary as the source mutation or an equivalent reliable outbox step;
- persist one delivery attempt state per endpoint/event;
- never rely on an in-process fire-and-forget HTTP call after a database commit;
- retain stable event IDs across retries;
- record bounded attempt metadata without retaining unnecessary response bodies or secrets;
- make retries idempotent and safe across worker restarts.

No such tables or workers are introduced in Story 16.5 because outbound delivery is not yet activated.

## Cost and operations boundary

The current decision requires **no new paid service and no AWS activation**. A future implementation may use Ripple's existing worker/container pattern first. Any managed queue, notification service, additional EC2 capacity, or third-party webhook platform requires separate cost review and explicit authorization.

## Activation gate

Outbound webhooks remain disabled until a future change includes all of the following evidence:

- subscriber ownership and authorization model;
- endpoint/secret persistence and migration;
- SSRF and destination validation tests;
- reliable outbox semantics;
- worker retry/idempotency tests;
- secret rotation tests;
- delivery disable/delete lifecycle;
- privacy and retention policy;
- observability without secret leakage;
- recovery/replay procedure;
- measured operational/cost impact;
- explicit authorization for any new recurring spend.
