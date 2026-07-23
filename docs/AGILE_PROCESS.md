# Agile Delivery Process

## Working model

TwitClone uses small, outcome-focused sprints. Each sprint should produce a demonstrable improvement and leave the repository in a usable state.

## Sprint planning

Every sprint plan must include:

- Sprint goal
- User or project value
- Scope and explicit exclusions
- Ordered backlog items
- Acceptance criteria
- Risks and dependencies
- Documentation impact
- Testing approach

## Branch and pull-request conventions

- Use one dedicated branch per sprint or independently reviewable backlog item.
- Prefer branch names such as `sprint/1-secure-baseline` or `feature/issue-12-description`.
- Keep unrelated changes out of the branch.
- Open pull requests as drafts while implementation is in progress.
- The pull-request description should identify the sprint, summarize changes, list validation performed, note risks, and reference issues.
- Prefer squash merging unless preserving individual commits provides meaningful history.

## Backlog item format

Each implementation issue should include:

- Problem statement
- Intended outcome
- Scope
- Acceptance criteria
- Test expectations
- Documentation expectations
- Dependencies or blockers

## Definition of Ready

A backlog item is ready when:

- The problem and expected outcome are clear.
- Acceptance criteria are testable.
- Dependencies and likely files or components are understood.
- Security, data migration, compatibility, and operating-cost impacts have been considered.
- The item is small enough to complete and review independently.

## Definition of Done

An item is done only when applicable criteria are satisfied:

- Acceptance criteria are met.
- Code follows the agreed structure and avoids unrelated changes.
- Automated tests are added or updated and pass.
- Database migrations are included and reviewed when models change.
- Security-sensitive input and authorization paths are tested.
- User-facing, developer, architecture, and operations documentation are updated.
- Configuration examples are updated without committing secrets.
- The pull request explains validation, risks, and rollback considerations.
- No unresolved blocking review comments remain.

## Sprint review

At the end of each sprint:

1. Demonstrate the completed behavior.
2. Compare results against acceptance criteria.
3. Record incomplete items and return them to the backlog rather than silently extending scope.
4. Update architecture and operating documentation.
5. Record known defects, technical debt, and decisions.

## Retrospective

Document briefly:

- What worked
- What caused rework or delay
- What should change in the next sprint
- Whether sprint size was appropriate

## Change-control principles

- The current repository state is the source of truth.
- Changes are delta-based and targeted.
- Existing behavior is not redesigned accidentally during cleanup.
- Security and dependency changes are validated rather than merged solely because an automated tool proposed them.
- Infrastructure and managed services require a current and projected monthly cost estimate before implementation.
