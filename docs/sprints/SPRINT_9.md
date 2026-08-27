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

**Status:** In implementation.

Introduce positive feedback that is meaningfully different from a generic Like: Helpful, Thoughtful, and Useful context.

### Acceptance criteria

- A signed-in user can add or remove each constructive signal on another user's post.
- Authors cannot award constructive signals to their own posts.
- A user may award more than one distinct signal when appropriate, but cannot duplicate the same signal on the same post.
- Signals remain separate categories rather than being collapsed into a single engagement/popularity score.
- Post detail explains the purpose of the signals.
- Database constraints enforce valid signal values and per-user/per-post/per-signal uniqueness.
- Automated tests cover toggling, self-signaling, invalid signals, and presentation.

## Story 9.4 — Community fact checks and context

**Status:** Planned.

Add a visible Check facts / Add context action to posts. A submission is a request for evidence-backed community context, not an immediate declaration that the post is false.

### Product direction

- Context submissions identify the claim being checked, explain the proposed context/correction, and cite supporting source links.
- Candidate outcomes should support nuance such as Additional context, Disputed claim, Outdated information, and Supported correction rather than forcing every claim into True/False.
- A single submitter cannot unilaterally place a false-information label on another user's post.
- Review/publishing rules must be explicit and auditable before community context is displayed as accepted context.
- Accepted context should remain visually distinct from moderation actions and from the original author's words.
- Future work may notify people who previously reposted/interacted with a post when meaningful accepted context is later attached.
- Initial implementation should remain self-hosted/container-friendly and must not require paid fact-checking APIs, AI services, or AWS infrastructure.

## Story 9.5 — Conversation health controls

Give authors understandable controls for managing their own discussion after publication, such as closing a conversation to new responses or marking that the original question has been answered. These controls must not erase existing responses or bypass moderation/audit requirements.

## Later differentiation candidates

- Topic-based reputation earned from constructive contributions rather than raw follower count
- Collaborative resource posts that communities can maintain over time
- Quiet/relationship-first feed modes that do not rank primarily by velocity or controversy
- Community-created topic guides and durable knowledge collections
- Local/community coordination tools with privacy-preserving location granularity
- A true threaded-reply model if Ripple's conversation design benefits from it
