# Secret handling

TwitClone must receive secrets from the runtime environment. Real secrets must never be committed to Git, copied into Terraform variables files, stored in images, or written into GitHub Actions workflow source.

## Current required secret

`SECRET_KEY` signs Flask sessions and CSRF tokens. It must be a long, random value and must be different between development, testing, and production.

Generate a value locally with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Export it for a local shell session:

```bash
export SECRET_KEY='paste-generated-value-here'
```

For AWS deployment, the value will be supplied outside Terraform source and outside the repository. The final storage mechanism will be documented with the AWS architecture before deployment.

## Rotation

Changing `SECRET_KEY` invalidates existing signed sessions and CSRF tokens. Users will need to sign in again. Rotate immediately if a real production value is ever committed, logged, or otherwise exposed.

## Values previously committed

The repository contained two predictable placeholder values:

- `your_secret_key` in the legacy `app.py` initialization path
- `development-only-change-me` as the former development fallback in `config.py`

Neither value should ever be used as a real secret. The environment-backed configuration now refuses to start without `SECRET_KEY`.

## Startup paths

The supported WSGI entry point is `application.py`. The compatibility `app.py` module also imports `Config` and validates the same environment-backed configuration; neither startup path contains a built-in application secret.

Prefer `application.py` / `application:application` for documented local and production workflows so configuration, application-factory behavior, and deployment instructions stay aligned.
