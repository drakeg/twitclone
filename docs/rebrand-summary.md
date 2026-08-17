# Ripple rebrand summary

The public-facing application is now branded **Ripple**. The internal
`twitclone` Python package and GitHub repository name remain unchanged to avoid
an unrelated namespace migration.

The same change set also replaces deprecated `datetime.utcnow()` calls in the
reported runtime/test paths and timestamp model defaults while preserving the
existing naive-UTC database contract.
