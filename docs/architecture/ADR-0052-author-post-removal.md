# ADR-0052: Author-requested original post removal

- Status: Accepted
- Date: 2026-09-23
- Sprint: 21
- Story: 21.2

## Context

Ripple already uses soft removal for moderation: original posts retain their database row and carry `is_removed`, `removed_at`, `removed_by_id`, and `removal_reason`. Original posts are also referenced by replies, quotes, reposts, bookmarks, notifications, moderation reports, community context, analytics, and portability data.

Physical deletion would cascade or orphan parts of that history and could make moderation/review records impossible to interpret. Author-requested removal also has different semantics from an admin determining that content violated Community Standards.

## Decision

Author-requested removal uses the existing soft-removal state.

For a published original post, the authenticated owner may request removal. Ripple then sets:

- `is_removed = true`;
- `removed_at` to the current UTC time;
- `removed_by_id` to the author; and
- `removal_reason = "Removed by author."`.

The post is immediately excluded from normal public surfaces that honor `is_removed`.

Ripple does **not** cascade-delete dependent records. Existing replies, quotes, repost rows, bookmarks, notifications, community-context records, moderation reports, and similar relational history remain persisted.

Pending moderation reports remain pending. Author removal is not treated as proof that a report was upheld, and it does not dismiss a report either. An administrator may still review the retained moderation record under the existing moderation process.

Future scheduled posts are outside this published-post removal path.

## Consequences

### Positive

- Authors can withdraw their own published content.
- Public visibility changes immediately without destroying relational history.
- Existing moderation/audit records remain interpretable.
- Author removal remains distinguishable from admin enforcement.
- The existing portability export can continue representing removed authored content and removal metadata.

### Constraints

- A removed original post and its dependent public conversation are no longer reachable through normal public post/thread surfaces.
- Retained dependent rows are historical records, not a promise that their original public presentation remains available.
- Media-file retention/deletion is not changed by this story.
- Restore/undo behavior is not introduced.

## Follow-up

If Ripple later exposes tombstones, author restore, retention expiration, or physical erasure workflows, those features must define their effects on moderation evidence, community context, replies/quotes, exports, media storage, and legal/privacy retention separately.
