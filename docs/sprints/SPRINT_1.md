# Sprint 1 — Secure, Reproducible Development Baseline

## Sprint goal

Make TwitClone safe and predictable to install, configure, start, and validate in a local development environment without redesigning application behavior.

## User/project value

A contributor can clone the repository, configure it without editing secrets into source files, install a supported dependency set, initialize the database, and run a basic automated validation.

## In scope

1. Environment-based application configuration
2. Removal of hard-coded secrets
3. Example environment file and configuration documentation
4. Supported Python version declaration
5. Deliberate dependency reconciliation and security review
6. Database initialization and migration guidance
7. Minimal automated smoke tests
8. GitHub Actions workflow for install and test validation
9. Review and disposition plan for stale Snyk pull requests

## Out of scope

- Application factory or blueprint refactor
- New user-facing features
- Timeline redesign
- Scheduler architecture replacement
- Production deployment
- Media-storage redesign

## Ordered backlog

### 1. Externalize configuration

- Read the secret key, database URL, upload directory, and scheduler enablement from environment-backed configuration.
- Provide safe development defaults only where appropriate.
- Fail clearly when a required production secret is absent.

### 2. Document environment setup

- Add `.env.example` without real secrets.
- Document each variable and local startup procedure.
- Ensure `.env` and local data remain ignored.

### 3. Reconcile dependencies

- Identify direct versus transitive packages.
- Update vulnerable or unsupported packages as a tested set.
- Remove unnecessary direct pins where appropriate.
- Confirm Flask-Migrate, Flask-SQLAlchemy, APScheduler, and tzlocal are installed consistently.

### 4. Establish database workflow

- Determine whether migration history exists and should be restored or regenerated.
- Stop ignoring migration files once a valid baseline is established.
- Document database creation, upgrade, and reset procedures.

### 5. Add smoke tests

- Application module imports without starting unsafe background work during tests.
- The public index route responds successfully.
- Registration/login configuration can be initialized against a temporary database.

### 6. Add CI

- Run on pull requests and pushes to `main`.
- Install the supported Python version and dependencies.
- Run the smoke-test suite.

## Acceptance criteria

- [ ] No real or placeholder secret is hard-coded as the active application secret
- [ ] `.env.example` documents all supported local settings
- [ ] A clean checkout can be installed using documented commands
- [ ] The supported Python version is declared
- [ ] Direct dependencies install without resolver warnings
- [ ] Known dependency vulnerabilities are reviewed and documented
- [ ] Database initialization and migrations are reproducible
- [ ] At least one automated route smoke test passes locally
- [ ] GitHub Actions runs the test suite on pull requests
- [ ] No new user-facing behavior is intentionally introduced
- [ ] README and architecture documentation reflect the completed baseline

## Testing approach

- Use an isolated temporary SQLite database
- Disable or safely isolate the scheduler under tests
- Verify configuration precedence and secret handling
- Verify installation in CI from a clean environment
- Run a basic HTTP client test against public application routes

## Risks and mitigations

- **Dependency upgrades may break behavior:** upgrade in small groups and run smoke tests after each group.
- **Missing migration history may complicate schema setup:** inventory the existing schema before generating a baseline.
- **Scheduler import behavior may interfere with tests:** add a configuration switch without performing the larger Sprint 2 refactor.
- **Historical Snyk PRs may conflict:** replace them with one tested dependency change rather than merging them sequentially.

## Documentation impact

Update README setup instructions, architecture configuration notes, dependency decisions, database workflow, test commands, and CI behavior.
