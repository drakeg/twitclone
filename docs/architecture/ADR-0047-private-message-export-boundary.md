# ADR-0047: Private-message export boundary

## Status

Accepted.

## Context

Both participants possess the content of a direct-message exchange, but a portability export must not become a side channel for another account's private profile data, read activity, or deletion choices. Ripple already models deletion per participant: deleting a message removes it from that participant's view while the other participant may retain it.

## Decision

- Advance `ripple-portable-export` to version 2 when adding direct messages.
- Export a message only when the requester is its sender or receiver and has not deleted it from their own view.
- Export stable message ID, sent/received direction, the other participant's username, content, and timestamp.
- Do not export read state, either deletion flag, participant email, verification, entitlements, or other profile/account metadata.
- Do not reveal whether the other participant retained or deleted the message.
- Keep messages ordered by timestamp and stable ID.
- Preserve the existing application behavior that physically deletes a message after both participants delete it.

## Consequences

- A requester receives the same private-message content still available to them in Ripple.
- A user's own deletion choice is honored by their export.
- One participant may retain a message after the other deletes it, matching the established per-participant deletion contract.
- The export is not a transcript of another account's activity and cannot be used to infer read or deletion behavior.
