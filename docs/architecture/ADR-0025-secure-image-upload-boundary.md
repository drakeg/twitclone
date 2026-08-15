# ADR-0025: Secure image-upload boundary

- Status: Accepted
- Date: 2026-08-14
- Sprint: 5
- Story: 5.1

## Context

Tweet uploads previously trusted the client filename, accepted arbitrary bytes,
and imposed no size limit. Extension sanitization alone cannot establish that a
file is an image or prevent collisions between users choosing the same name.

## Decision

- Accept PNG, JPEG, and GIF uploads only.
- Require the extension, submitted MIME type, and Pillow-detected image format
  to agree.
- Verify image content before writing it to disk.
- Reject uploads larger than 5 MB.
- Generate a random 128-bit hexadecimal basename while retaining the validated
  lowercase extension.
- Preserve the existing thumbnail filename stored on Tweet records.

## Consequences

- Arbitrary and mislabeled files are rejected before database or file writes.
- Client filenames can no longer collide or influence server paths.
- Valid upload URLs and thumbnail rendering remain compatible.
- Original and thumbnail lifecycle separation remains Story 5.2.

## Guardrails

- New accepted formats require an explicit extension, MIME, and decoded-format
  mapping plus regression coverage.
- Upload limits must be enforced while reading, not only from client headers.
