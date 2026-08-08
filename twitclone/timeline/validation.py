"""Validation rules shared by timeline post workflows."""

POST_CONTENT_LIMIT = 144


def validate_post_content(content, *, post_type):
    """Return a user-facing validation error, or ``None`` when valid."""
    if content is None or not content.strip():
        return f"{post_type} content is required."
    if len(content) > POST_CONTENT_LIMIT:
        return f"{post_type} content exceeds {POST_CONTENT_LIMIT} characters."
    return None


__all__ = ["POST_CONTENT_LIMIT", "validate_post_content"]
