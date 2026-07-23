# Sprint 0 — Project Foundation and Assessment

## Sprint goal

Create a trustworthy starting point for renewed development by documenting the product, current architecture, delivery process, roadmap, and first implementation sprint.

## Value

The repository can be resumed without guessing at priorities, quality expectations, or architectural direction. Future work will be delivered as focused, documented increments.

## In scope

- Assess repository metadata, recent commits, open pull requests, dependencies, documentation, and major architectural risks
- Rebuild the README
- Document product vision, roadmap, architecture, and Agile process
- Create a prioritized GitHub backlog
- Prepare Sprint 1 with testable acceptance criteria

## Out of scope

- Changing application behavior
- Refactoring application code
- Updating dependencies
- Closing or merging automated security PRs
- Deploying infrastructure

## Acceptance criteria

- [x] README explains the project, status, setup direction, roadmap, and security warning
- [x] Product vision and non-goals are documented
- [x] Current architecture and known risks are documented
- [x] Agile workflow, Definition of Ready, and Definition of Done are documented
- [x] Roadmap identifies stabilization and delivery sequence
- [x] Sprint 1 has a documented goal, scope, tasks, and acceptance criteria
- [ ] Backlog issues are created and linked
- [ ] Sprint 0 pull request is reviewed and merged

## Repository observations

- The latest application state includes hashtags, bookmarks, image uploads, polls, scheduled posts, and related UI work.
- The README was not usable and required replacement.
- Application code currently concentrates many responsibilities in one module.
- A hard-coded application secret and development configuration are present.
- Five open automated Snyk pull requests overlap on `requirements.txt`; their warning text is inconsistent with the current dependency file, so they should not be merged blindly.
- No project issues existed when Sprint 0 began.

## Risks

- The application may not install or run cleanly on a current Python version until Sprint 1 validates dependencies.
- Migrations are ignored by the current `.gitignore`, which may leave schema history unavailable.
- Existing behavior is broad but lightly tested, making large refactors risky.

## Sprint review checklist

- Review all new documents for accuracy
- Confirm roadmap ordering
- Confirm Sprint 1 scope remains limited to baseline security and reproducibility
- Merge only documentation and planning changes

## Retrospective prompts

- Was the existing behavior discoverable from repository history?
- Are issues sized small enough for review?
- Should stale automated PRs be closed during Sprint 1 or handled in a separate maintenance item?
