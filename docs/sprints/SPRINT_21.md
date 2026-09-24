# Sprint 21 — Author-Controlled Post Lifecycle

**Status:** In implementation.

## Goal

Give authors safe, understandable control over the lifecycle of their own original posts without weakening ownership, moderation, conversation-history, or topic-integrity boundaries.

## Story 21.1 — Owner-only original post editing

**Status:** In implementation.

- Allow only the authenticated owner to edit the text of an original post.
- Keep the original publish timestamp, author, image, explicit topics, conversation intent/state, and existing responses unchanged.
- Record an `edited_at` timestamp only when text actually changes.
- Show a visible `Edited` marker on the post detail and timeline.
- Reuse the existing 144-character server-side validation and browser constraint.
- Refresh hashtag-derived topic associations from the edited text while preserving explicit author-selected topics.
- Notify only users newly added through @mentions; existing mentions must not receive duplicate notifications.
- Treat removed posts as unavailable for editing.
- Do not add quote/reply/poll editing in this story.

### Acceptance criteria

- Anonymous users are redirected to login before editing.
- A non-owner receives HTTP 403 for both the edit form and submission.
- Valid owner edits change only the intended text-derived state and set `edited_at`.
- Invalid edits return HTTP 400 and do not mutate the post.
- Submitting unchanged text does not mark the post edited.
- Original publish time, author, and media remain unchanged.
- Newly added mentions are notified once; existing mentions are not re-notified.
- Explicit topics survive an edit while stale/new hashtag-derived topics are removed/added deterministically.
- Owners see an edit control and all viewers see the `Edited` marker after a real edit.
- Regression tests cover authorization, validation, no-op behavior, metadata preservation, mentions, and topic integrity.

## Planned follow-up stories

- Define owner-requested post removal semantics, including how existing replies, quotes, bookmarks, notifications, moderation records, and community context remain interpretable.
- Evaluate whether edit history beyond the visible edited timestamp is necessary before allowing edits to quote/reply content.
- Reconcile the legacy root `TODO.md` against delivered functionality and the numbered roadmap.

## Boundary

Sprint 21 does not permit editing another user's content, rewrite moderation history, silently alter existing responses, or physically delete relational history without an explicit lifecycle decision.
