# ADR-0026: Original and thumbnail image storage

- Status: Accepted
- Date: 2026-08-15
- Sprint: 5
- Story: 5.2

## Context

Tweet records stored only a thumbnail filename even though upload processing
also retained an original file. The implicit filename convention made the
original undiscoverable from the data model and could leave partial files when
thumbnail creation failed.

## Decision

- Add nullable `Tweet.original_image` metadata through a reversible migration.
- Keep `Tweet.image` as the rendered thumbnail field for compatibility.
- Store paired `original_<token>.<ext>` and `thumb_<token>.<ext>` files.
- Remove both files if processing fails before the Tweet is committed.
- Provide a Docker Compose development path that migrates automatically and
  persists the SQLite database and uploads in one named volume.

## Consequences

- New uploads have explicit original and thumbnail identities.
- Existing Tweet rows and templates continue to work without data backfill.
- Failed processing does not leave orphaned partial files.
- `docker compose up --build` provides a reproducible local test path.

## Guardrails

- Rendering continues to use thumbnails unless a feature explicitly requests
  originals.
- Destructive media cleanup must validate exact filenames and ownership.
