"""Direct-message input validation."""

MESSAGE_CONTENT_MAX_LENGTH = 500


def validate_message_content(content):
    if content is None or not content.strip():
        return "Message content is required."
    if len(content) > MESSAGE_CONTENT_MAX_LENGTH:
        return f"Message content exceeds {MESSAGE_CONTENT_MAX_LENGTH} characters."
    return None


__all__ = ["MESSAGE_CONTENT_MAX_LENGTH", "validate_message_content"]
