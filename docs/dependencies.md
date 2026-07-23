# Dependency Management

## Supported runtime

TwitClone currently targets **Python 3.12**. The repository-level `.python-version` file is the source of truth for local tooling and the initial AWS deployment.

## Dependency files

- `requirements.txt` is the current reproducible runtime lock set.
- `requirements-dev.txt` adds development and test tooling on top of the runtime set.
- `scripts/verify_dependencies.py` verifies the supported Python version and imports the packages used directly by the application.

Install and verify with:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/verify_dependencies.py
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

## Reconciliation decision

Several automated security pull requests were merged on July 23, 2026. Their resulting versions are preserved in `requirements.txt` rather than replaced by a second speculative upgrade.

The file is organized into:

1. Runtime framework dependencies used directly by the Flask application.
2. Explicit application/runtime packages.
3. Transitive packages retained as exact pins after automated security updates.
4. A documented Snyk security override for `zipp`.

This organization does not claim that every transitive pin must remain forever. It records why each class of dependency is present until CI and clean-environment testing provide enough evidence to simplify the lock set safely.

## Upgrade procedure

1. Create a dedicated dependency branch from the latest `main`.
2. Change one coherent dependency group at a time.
3. Install into a clean Python 3.12 virtual environment.
4. Run `python scripts/verify_dependencies.py`.
5. Run the full automated test suite once Issue #13 is complete.
6. Record vulnerability scan results and any compatibility decisions in the PR.
7. Do not merge multiple overlapping bot PRs without reconciling the final combined result.

## Security bot policy

Dependabot, Mend, Renovate, and Snyk findings are inputs to the engineering process, not automatic proof that a change is safe for this application. Security PRs should be reviewed for:

- overlapping version changes;
- direct versus transitive package intent;
- compatibility with Python 3.12;
- compatibility with Flask and its extensions;
- successful clean installation;
- successful application tests and startup checks.

## Future improvement

After CI and application tests are established, the project should evaluate generating a locked runtime file from a smaller direct-dependency input file. That change should be handled as a separate story so the generated workflow, update process, and security tooling remain understandable.
