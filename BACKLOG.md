# Prioritized backlog

This file summarizes ready and deferred work. Detailed product history remains in
`docs/ROADMAP.md`; GitHub issues remain the executable tracker.

| Priority | Item | Source | Status |
| --- | --- | --- | --- |
| P0 | Keep CI/build/test pipelines green | GitHub Actions | Continuous |
| P0 | Maintain Mad Mallard governance docs, verified README badges, and CI standards validation | Standards | Implemented; continuous |
| P1 | Preserve the completed AWS activation handoff and zero-spend boundary | Issue #16 / PR #368 | Implemented; live evidence still gated |
| P1 | Review and merge safe dependency updates after green CI | Renovate / Issue #22 | Continuous; current queue cleared |
| P1 | Complete manual NVDA/VoiceOver and 200%/400% zoom evidence before public launch | Sprint 7/25 launch gate | Awaiting manual evidence |
| P1 | Complete real AWS plan/apply/idempotence/network/backup/restore evidence | Issue #16 | Blocked on explicit spend authorization |
| P1 | Validate SMB member-community wedge with operator dashboard pilot | Issue #372 | MVP/demo launcher ready; local network-pool fix in review |
| P1 | Run real prospect interviews and test $49–$79/month hosted-community pricing hypothesis | Issue #372 | Ready; no validation claimed |
| P2 | Add release automation only after the first meaningful release candidate and license decision | RELEASES.md | Backlog |
| P2 | Resolve repository license intentionally; do not infer one from placeholder text | Owner decision | Blocked on consequential legal choice |

## Commercialization decision rule

Prioritize work that can plausibly save an SMB/community operator time, reduce
administrative cost/risk, or enable paid membership/community revenue. Before
building a large feature, state the target buyer, painful workflow, expected
measurable benefit, competitor/alternative, and price hypothesis. Treat all such
items as hypotheses until validated with real prospects or customers.
