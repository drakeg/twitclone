# Legacy Flask Secret Removal

## Status

The legacy `app.py` module no longer contains a hard-coded or fallback Flask signing key. All supported startup paths require `SECRET_KEY` to be supplied outside source control.

## Why this matters

Flask uses `SECRET_KEY` to sign session cookies and CSRF-related data. A predictable key allows an attacker to forge trusted client-side data. Placeholder values are therefore unsafe even when they were originally intended only for development.

## Required local setup

Generate a unique local key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Export it before running Flask, migrations, or tests outside the repository-provided test environment:

```bash
export SECRET_KEY='generated-value'
```

Do not add the generated value to `.env.example`, source files, test fixtures intended for production, shell history shared with others, or committed Terraform variables.

## Startup behavior

Both of these paths now require validated environment configuration:

```bash
python application.py
```

```bash
python app.py
```

The supported path remains `application.py` / `application:application`. Direct `app.py` execution is retained only as a transitional compatibility path during Sprint 2.

## Scheduler behavior

The legacy scheduler starts only when:

```bash
SCHEDULER_ENABLED=true
```

Tests and multi-process web workers should set it to `false`. A later Sprint 2 story will move scheduler ownership out of the monolith entirely.

## Rotation

Rotate `SECRET_KEY` immediately if a real deployment ever used either historical placeholder value. Rotation invalidates existing signed sessions, so users will need to sign in again.

## AWS deployment

The AWS deployment must inject the value at runtime. Terraform must not place the plaintext value in committed files, plans, outputs, user-data logs, or repository variables. The final storage mechanism will be selected in the infrastructure sprint based on cost and operational simplicity.

## Verification

Run:

```bash
python -m pytest tests/test_config.py tests/test_legacy_security.py
```

The regression tests verify that known placeholder values are absent, direct import fails without an external key, and disabling the scheduler prevents background startup.
