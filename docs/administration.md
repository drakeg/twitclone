# Administration

Ripple does not create an administrator account automatically. Create the user
through normal registration first, then promote that existing account by its
email address.

## Promote an existing user

With the local Docker Compose application running, use:

```bash
docker compose exec web flask --app application make-super-admin user@example.com
```

Replace `user@example.com` with the account's exact email address. A successful
command prints:

```text
@username is now a Ripple super-admin.
```

Without Docker, activate the project's virtual environment, export the same
configuration used by the application, and run:

```bash
flask --app application make-super-admin user@example.com
```

The command sets both the administrator and super-administrator flags. The user
can then sign in normally and open `/admin`. Running it again for the same user
is safe and leaves the account promoted.

If no account has that email address, the command exits with:

```text
No user found with email user@example.com.
```

The command must run against the same `DATABASE_URL` as the intended Ripple
environment. For production, run it as an authenticated one-shot administrative
task using production secrets; do not place the database URL or other secrets in
shell history, source control, screenshots, or support messages. Record who
approved and performed every production role change.

There is currently no supported CLI command for removing administrator access.
Do not edit production data manually without a reviewed revocation procedure.
