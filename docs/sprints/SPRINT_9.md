# Sprint 9 — Intentional Conversations

## Goal

Differentiate Ripple from conventional microblogging by helping people state what kind of interaction they want and by rewarding constructive participation rather than maximizing conflict or raw engagement.

## Product hypothesis

A social network can produce better conversations when participants understand the author's intent before responding. Ripple should make conversational expectations visible, lightweight, and understandable without turning every post into a rules form.

## Guardrails

- Conversation intent is available to free accounts; it is not a premium safety feature.
- Intent does not override Ripple Community Standards.
- Story 9.1 is descriptive, not an enforcement mechanism.
- Future controls must remain understandable and must not silently hide or suppress lawful, respectful speech.
- No AI moderation service, third-party analytics, or new infrastructure is required for this sprint.

## Story 9.1 — Conversation intent

**Status:** In implementation.

Authors may optionally label a post as:

- Open conversation
- Looking for answers
- Advice wanted
- Support wanted
- Respectful debate welcome
- Just sharing

Existing posts default to Open conversation. The selected intent is visible in the timeline and post-detail view. Unknown or missing form values safely fall back to Open conversation.

### Acceptance criteria

- Posting remains as easy as before; Open conversation is the default.
- Intent is persisted separately from the mature tweet schema.
- Existing posts require no backfill and render as Open conversation.
- Reposts preserve the original post's intent cue.
- Quotes do not inherit the original author's intent as though it belonged to the quoting user.
- Automated tests cover persistence, fallback, timeline/detail rendering, and composer choices.

## Story 9.2 — Respectful response expectations

Add lightweight pre-response context so people replying/quoting can see the author's stated intent at the moment they respond. For higher-boundary intents such as Support wanted or Just sharing, Ripple should remind the responder of the expectation without preventing legitimate respectful participation by default.

## Story 9.3 — Constructive contribution signals

Introduce positive feedback that is meaningfully different from a generic Like. Candidate signals include Helpful, Thoughtful, and Useful context. The implementation must resist becoming another popularity counter and should emphasize contribution quality over follower size.

## Story 9.4 — Conversation health controls

Give authors understandable controls for managing their own discussion after publication, such as closing a conversation to new responses or marking that the original question has been answered. These controls must not erase existing replies or bypass moderation/audit requirements.

## Later differentiation candidates

These are candidates for future sprints rather than commitments inside Sprint 9:

- Topic-based reputation earned from constructive contributions rather than raw follower count
- Collaborative resource posts that communities can maintain over time
- Quiet/relationship-first feed modes that do not rank primarily by velocity or controversy
- Community-created topic guides and durable knowledge collections
- Local/community coordination tools with privacy-preserving location granularity
