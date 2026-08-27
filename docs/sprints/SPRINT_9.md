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

**Status:** In implementation.

Add lightweight pre-response context so people quoting a post see the author's stated intent at the moment they respond. Higher-boundary intents such as Support wanted or Just sharing receive a stronger reminder of the author's expectation, while Open conversation, Questions, Advice, and Debate receive context appropriate to that intent.

Ripple's current public response mechanism is Quote. The repository contains a legacy `reply.html` template but no registered public threaded-reply route, so Story 9.2 does not pretend threaded replies exist or silently add a new response model. Threaded replies remain a separate future product capability.

### Acceptance criteria

- The Quote screen visibly repeats the original author's intent before the response field.
- Support wanted and Just sharing clearly call out the stronger conversational boundary.
- Open conversation remains permissive and does not imply extra restrictions.
- Advice, Question, and Respectful debate intents receive useful response guidance.
- Intent guidance remains visible after quote validation errors.
- The guidance is associated with the response field for assistive technology.
- No intent label hard-blocks a respectful quote response.

## Story 9.3 — Constructive contribution signals

**Status:** Next.

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
- A true threaded-reply model if Ripple's conversation design benefits from it
