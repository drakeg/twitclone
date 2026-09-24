# ADR-0051: Owner-only original post editing

- Status: Accepted
- Date: 2026-09-23
- Sprint: 21
- Story: 21.1

## Context

Ripple historically allowed authors to create original posts but not edit or delete them. ADR-0020 explicitly deferred owner-only mutations until a separate product story could define the authorization and history semantics.

Post text now participates in more than presentation: mentions can create notifications and hashtags create derived topic associations. Editing therefore cannot be implemented as an unrestricted column update without reconciling those derived behaviors.

## Decision

Allow an authenticated author to edit only the text of their own original `Tweet`.

A successful edit:

- requires the persisted post owner to match `current_user`;
- reuses the existing Tweet content validation and 144-character limit;
- preserves the original author, publish timestamp, image, explicit topics, conversation intent/state, and existing responses;
- records `edited_at` only when the text actually changes;
- refreshes hashtag-derived topic associations from the new text while preserving explicit author-selected topics; and
- notifies only newly added valid @mentions.

Removed posts are not editable. Quote, reply, poll, image, scheduling, and destructive removal behavior are outside this story.

## Why no full edit history yet

A visible edit timestamp communicates that the text changed while avoiding a larger persistence/privacy contract before there is evidence that version-by-version post history is required. If later product behavior depends on exact historical wording, a separate story must define retention, visibility, moderation, and export semantics before adding edit revisions.

## Consequences

### Positive

- Authors can correct ordinary mistakes without recreating a post.
- Ownership remains server-authoritative.
- Existing replies/quotes continue to reference the same post identity.
- Mention recipients are not spammed by unchanged mentions.
- Topic-derived metadata does not become stale after hashtag edits.
- Viewers can see that a post was edited.

### Constraints

- Editing does not change the original publish timestamp.
- Editing does not replace or remove attached media.
- Explicit topics are preserved unless the author uses the dedicated topic-control workflow.
- Editing is limited to original posts; other content types need separate semantics.

## Follow-up

Owner-requested removal was defined separately in ADR-0052 and implemented through soft removal.

Full post revision-history persistence remains deferred. Durable collaborative resources retain revisions because provenance is intrinsic to that product surface; ordinary posts retain only a visible `edited_at` marker unless a future moderation, portability, compliance, or user-facing requirement needs prior wording.
