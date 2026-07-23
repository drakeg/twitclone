# Product Roadmap

This roadmap is intentionally incremental. Sprint scope may be refined as the repository is tested, but a sprint's goal and acceptance criteria should remain stable once implementation begins.

## Sprint 0 — Project foundation and assessment

**Goal:** Establish the project baseline, working agreements, architecture record, and prioritized backlog.

**Deliverables:**

- Rebuilt README
- Product vision and roadmap
- Agile process and Definition of Done
- Current architecture assessment
- Sprint 0 and Sprint 1 plans
- GitHub backlog issues

## Sprint 1 — Secure, reproducible development baseline

**Goal:** Make the existing application safe and predictable to install and run locally.

**Planned outcomes:**

- Remove hard-coded secrets and environment-specific configuration
- Add an example environment file and configuration documentation
- Establish supported Python version and reproducible setup commands
- Reconcile and update direct dependencies deliberately
- Add a minimal application smoke test
- Add baseline CI for installation and tests
- Document database initialization and migration behavior

## Sprint 2 — Application structure and test foundation

**Goal:** Reduce risk by separating concerns without changing user-visible behavior.

**Planned outcomes:**

- Introduce an application factory
- Separate configuration, extensions, models, and route modules
- Ensure scheduler startup is controlled and test-safe
- Establish unit and integration test conventions
- Add tests for authentication and basic timeline access

## Sprint 3 — Core timeline and post reliability

**Goal:** Make the primary posting and timeline workflows consistent and well-tested.

**Planned outcomes:**

- Validate post creation and length rules
- Clarify post, repost, and quote data behavior
- Correct timeline ordering and scheduled-post visibility
- Add pagination
- Add tests for authorization and ownership boundaries

## Sprint 4 — Social interactions and notifications

**Goal:** Harden follows, likes, bookmarks, messaging, and notifications.

**Planned outcomes:**

- Prevent duplicate relationship records
- Define notification lifecycle and read behavior
- Harden direct-message authorization and input handling
- Add interaction-focused tests

## Sprint 5 — Media, polls, and scheduling

**Goal:** Secure and stabilize advanced content capabilities.

**Planned outcomes:**

- Validate upload type, extension, size, and generated filenames
- Separate original and thumbnail handling
- Enforce one vote per user at the database level
- Clarify poll expiration behavior
- Make scheduled-post processing reliable outside the web process

## Sprint 6 — Deployment and operations readiness

**Goal:** Prepare a documented, low-cost deployment path.

**Planned outcomes:**

- Add production WSGI serving guidance
- Add health checks and structured logging
- Select a production database and migration procedure
- Document backups, restores, media storage, and rollback
- Add containerization only when it simplifies operations without creating unnecessary cost
- Publish a deployment cost estimate before infrastructure is implemented

## Future backlog

Potential work after stabilization:

- Accessibility review
- Account recovery and email verification
- Moderation and reporting tools
- API design
- Search improvements
- Theme and responsive UI refinement
- Optional federation feasibility study
