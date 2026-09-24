# Sprint 21 — Author-Controlled Post Lifecycle

**Status:** Completed.

## Goal

Give authors safe, understandable control over the lifecycle of their own original posts without weakening ownership, moderation, conversation-history, or topic-integrity boundaries.

## Story 21.1 — Owner-only original post editing

**Status:** Completed in PR #267.

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

## Story 21.2 — Owner-requested original post removal

**Status:** Completed in PR #268.

- Let only the authenticated owner remove a published original post.
- Reuse Ripple's existing soft-removal fields rather than physically deleting the post row.
- Record `removed_by_id` as the author and `removal_reason` as `Removed by author.` so author removal remains distinguishable from moderation enforcement.
- Immediately hide the original from the timeline, post detail, reply thread, bookmarks, repost/quote visibility, new reporting/context creation, and other normal public surfaces that already respect `is_removed`.
- Preserve existing replies, quotes, repost rows, bookmarks, notifications, community-context records, moderation reports, and other relational history.
- Leave pending moderation reports pending; author removal does not mean a report was upheld or dismissed.
- Exclude future scheduled posts from this published-post removal path.
- Explain the historical-retention behavior to the author before removal.

### Acceptance criteria

- Anonymous users are redirected to login.
- Non-owners receive HTTP 403.
- Owner removal sets `is_removed`, `removed_at`, `removed_by_id`, and the author-specific removal reason.
- Removed posts disappear from normal public post/timeline/thread/bookmark surfaces.
- Existing replies, quotes, reposts, bookmarks, notifications, community context, and reports remain persisted.
- Pending reports are not silently resolved.
- Future scheduled posts remain outside this removal flow.
- Only owners see the removal control.
- Tests cover authorization, soft-removal state, public hiding, relational preservation, moderation-state preservation, and scheduled-post boundaries.

## Story 21.3 — Legacy TODO reconciliation

**Status:** Completed in PR #269.

- Convert the root `TODO.md` from a competing backlog into a historical-status document.
- Point all new work to `docs/ROADMAP.md` and the active sprint records.
- Mark already-delivered legacy items as completed rather than continuing to advertise them as pending.
- Preserve genuinely deferred ideas as non-commitments unless they are promoted into a numbered sprint.
- Keep AWS production activation explicitly separate from roadmap inclusion and spend authorization.
- Retain the historical origin of the old "Twitter Clone" wording without treating it as current product specification.

### Acceptance criteria

- `TODO.md` no longer presents delivered features as unfinished.
- The file names the roadmap/sprint/ADR hierarchy as the source of truth.
- Password recovery, profiles, search, notifications, PostgreSQL readiness, CI/deployment contracts, and the UI refresh are recognized as delivered.
- Social login and real-time/WebSocket notifications are identified as deferred ideas rather than silently promised work.
- AWS activation remains explicitly conditional on separate authorization.
- Sprint 21 is identified as the current active development record.

## Story 21.4 — Post edit-history decision

**Status:** Completed by decision in this closeout.

Ripple will not add full revision-history persistence for ordinary original-post edits at this time.

Durable collaborative resources have explicit revision models because exact edit provenance is part of their product purpose. Original posts are short conversational artifacts. Sprint 21 already preserves post identity, original publish time, moderation/removal state, related responses, and a visible `Edited` timestamp. No current moderation, portability, API, or user-facing contract requires reconstructing every prior wording.

Adding post revisions now would introduce new retention, privacy, moderation, export, and UI obligations without a demonstrated product requirement.

### Revisit criteria

A future sprint may introduce post edit history only if at least one concrete requirement needs prior wording, such as:

- moderation review that must compare historical text;
- a public/user-visible revision history product decision;
- portability requirements for previous post versions;
- legal/privacy retention rules that explicitly require revision capture; or
- quote/reply editing semantics that cannot be made understandable without version provenance.

Until then, `edited_at` remains the intentional post-edit history contract.

## Sprint outcome

Sprint 21 delivered author-controlled lifecycle behavior for published original posts while preserving historical integrity. Authors can edit post text under owner-only authorization, viewers can see that a post was edited, text-derived mentions/topics are reconciled safely, and authors can soft-remove posts without cascading away replies, quotes, bookmarks, notifications, community context, or moderation records.

The legacy root TODO was also reconciled so the numbered roadmap and sprint/ADR records remain the single source of truth.

## Definition of done

Completed. Original-post editing and removal now have explicit authorization, visibility, preservation, and history semantics. Full post revision storage remains deliberately deferred until a concrete product or compliance requirement justifies it.

## Boundary

Sprint 21 does not permit editing another user's content, rewrite moderation history, silently alter existing responses, or physically delete relational history without an explicit lifecycle decision.
