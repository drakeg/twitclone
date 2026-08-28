# Sprint 9 — Intentional Conversations

## Goal

Differentiate Ripple from conventional microblogging by helping people state what kind of interaction they want and by rewarding constructive participation rather than maximizing conflict or raw engagement.

## Product hypothesis

A social network can produce better conversations when participants understand the author's intent before responding. Ripple should make conversational expectations visible, lightweight, and understandable without turning every post into a rules form.

## Guardrails

- Conversation intent is available to free accounts; it is not a premium safety feature.
- Intent does not override Ripple Community Standards.
- Conversation cues are descriptive by default, not hidden enforcement mechanisms.
- Future controls must remain understandable and must not silently hide or suppress lawful, respectful speech.
- No AI moderation service, third-party analytics, or new infrastructure is required for this sprint.

## Story 9.1 — Conversation intent

**Status:** Completed.

Authors may optionally label a post as Open conversation, Looking for answers, Advice wanted, Support wanted, Respectful debate welcome, or Just sharing. Existing posts default to Open conversation.

## Story 9.2 — Respectful response expectations

**Status:** Completed.

The Quote flow repeats the original author's intent and gives response guidance appropriate to that intent without hard-blocking respectful participation. Ripple currently has no registered public threaded-reply route; threaded replies remain a separate future capability.

## Story 9.3 — Constructive contribution signals

**Status:** Completed.

Helpful, Thoughtful, and Useful context signals recognize contribution quality without collapsing participation into a single popularity score. Users can toggle distinct signals on other people's posts, while database constraints prevent duplicate same-signal awards.

## Story 9.4 — Community fact checks and context

**Status:** Completed.

Ripple now has an evidence-backed community context workflow with admin review, independent community consensus, transparent reviewer history, and an auditable appeal/correction path. A context submission never directly labels the original post false, published context remains visually separate from the author's words, and later revisions or withdrawals preserve the original review history.

### Completed capabilities

- Signed-in users can submit a specific claim, proposed context/correction, and supporting http/https source.
- New submissions remain pending and unpublished until review.
- Admin review is available separately from Community Standards moderation.
- Eligible community reviewers can independently assess pending context; submitters and original post authors cannot review their own item.
- Automatic publication requires at least three independent reviews and at least two-thirds agreement on the same publishable outcome.
- Reviewer quality is derived transparently from resolved assessment history and is not based on followers, paid status, popularity, or inferred political viewpoint.
- Any signed-in user can appeal published context with a reason, new evidence, or suggested revision.
- Appeal resolution can uphold, revise, or withdraw context without deleting the original submission, assessments, or appeal trail.
- Published context includes source links and remains separate from the original author's text.

### Follow-on candidates

- Add source-quality and duplicate/context-merging controls based on actual usage.
- Consider notifying prior reposters/interactors when meaningful accepted context is attached later.
- Consider an author-visible correction/update workflow that complements rather than replaces community context.
- Use demonstrated reviewer history for stronger anti-brigading safeguards only after real-world review history exists and the rules remain explainable.

## Story 9.5 — Conversation health controls

**Status:** In implementation.

Give authors understandable controls for managing the state of their own discussion after publication without erasing prior participation.

### Current slice

- Every post has an effective conversation state of Open / Unresolved unless the author changes it; no backfill is required for existing posts.
- Authors can close a conversation to new quote responses and later reopen it.
- Closing a conversation does not delete or hide existing quote responses.
- Closed state is enforced server-side so old or direct quote URLs cannot bypass the author's choice.
- Authors can mark a conversation Answered / Resolved and later clear that status.
- Open/closed and resolved status are visible on post detail.
- Only the post author can change conversation health state.
- Repost, bookmark, fact-context, constructive-contribution, and moderation/reporting behavior remain unaffected by closing a conversation.

### Follow-on candidates

- Show health state consistently in timeline cards, profiles, search, and hashtag results.
- Decide whether resolved questions should optionally suppress response prompts without fully closing the conversation.
- Add an author-visible history of state changes if real-world use shows a need for a stronger audit trail.
- Revisit threaded replies separately if Ripple adds a true reply model in a later sprint.

## Later differentiation candidates

- Topic-based reputation earned from constructive contributions rather than raw follower count
- Collaborative resource posts that communities can maintain over time
- Quiet/relationship-first feed modes that do not rank primarily by velocity or controversy
- Community-created topic guides and durable knowledge collections
- Local/community coordination tools with privacy-preserving location granularity
- A true threaded-reply model if Ripple's conversation design benefits from it
