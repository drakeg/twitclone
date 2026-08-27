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

**Status:** In implementation.

Add a visible Check facts / Add context action to posts. A submission is a request for evidence-backed community context, not an immediate declaration that the post is false.

### Foundation acceptance criteria

- Signed-in users can open Check facts / Add context from a post detail page.
- A submission identifies the specific claim, explains proposed context/correction, and includes a valid http/https supporting source URL.
- New submissions remain pending and are not shown publicly as accepted context.
- Fact context is reviewed separately from Community Standards moderation.
- Admins see pending fact-context work from the main Admin page and can review a dedicated queue.
- Approval requires an explicit nuanced outcome: Additional context, Disputed claim, Outdated information, or Supported correction.
- Accepted context appears visually separate from the author's words and includes a link to the supporting source.
- Submitters are notified of approval/rejection; the original author is notified when reviewed context is published on their post.
- Reviewer identity, review time, notes, status, and outcome remain auditable in persistence.
- A single submitter cannot unilaterally publish a false-information label.
- No paid fact-checking API, AI moderation service, external analytics service, or AWS infrastructure is required.

### Follow-on work

- Define community-review eligibility and consensus rules so accepted context need not depend permanently on administrators alone.
- Add source-quality and duplicate/context-merging controls based on actual usage.
- Consider notifying prior reposters/interactors when meaningful accepted context is attached later.
- Consider an author-visible correction/update workflow that complements rather than replaces community context.

## Story 9.5 — Conversation health controls

Give authors understandable controls for managing their own discussion after publication, such as closing a conversation to new responses or marking that the original question has been answered. These controls must not erase existing responses or bypass moderation/audit requirements.

## Later differentiation candidates

- Topic-based reputation earned from constructive contributions rather than raw follower count
- Collaborative resource posts that communities can maintain over time
- Quiet/relationship-first feed modes that do not rank primarily by velocity or controversy
- Community-created topic guides and durable knowledge collections
- Local/community coordination tools with privacy-preserving location granularity
- A true threaded-reply model if Ripple's conversation design benefits from it
