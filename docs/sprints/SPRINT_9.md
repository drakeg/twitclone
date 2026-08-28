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

### Foundation — completed

- Signed-in users can open Check facts / Add context from a post detail page.
- Submissions identify the claim, proposed context/correction, and a valid http/https supporting source URL.
- New submissions remain pending and unpublished until reviewed.
- Fact context is separate from Community Standards moderation.
- Admins have a dedicated auditable review queue.
- Approval requires Additional context, Disputed claim, Outdated information, or Supported correction.
- Accepted context is visually separate from the author's words and links to its source.
- Submitters and post authors receive review notifications.
- A single submitter cannot unilaterally publish a false-information label.

### Community consensus — completed

- Community reviewers must have a verified email and have accepted the current Community Standards.
- Submitters and original post authors cannot review the submission.
- Each eligible reviewer may submit only one independent assessment per context item.
- Assessments are Additional context, Disputed claim, Outdated information, Supported correction, or Not enough evidence.
- Automatic publication requires at least three independent reviews and at least two-thirds agreement on the same publishable outcome.
- Lack of consensus leaves the submission pending for additional reviews or admin oversight; disagreement does not silently suppress or label the original post.
- Consensus publication stores an auditable summary and notifies the submitter and original post author.
- Admin review remains available for unresolved cases and future appeals.

### Reviewer quality — in implementation

- Reviewer reputation is derived from assessment history rather than stored as a mutable score.
- The record tracks total assessments, resolved assessments, assessments aligned with the eventual published outcome, and outcome-agreement rate.
- Only approved submissions with an explicit final outcome count toward agreement metrics; pending work cannot inflate reputation.
- Reviewers see their own transparent record and a plain-language level such as New reviewer, Developing reviewer, Established reviewer, or Strong review record.
- Reputation is not based on follower count, paid status, popularity, or inferred political viewpoint.
- Reputation is informational in this slice and does not silently give a reviewer extra voting weight.

### Follow-on work

- Use demonstrated reviewer history for carefully designed anti-brigading safeguards only after the reputation metrics have real-world history and are explainable to users.
- Add source-quality and duplicate/context-merging controls based on actual usage.
- Add an appeal/correction path for context that was previously published.
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
