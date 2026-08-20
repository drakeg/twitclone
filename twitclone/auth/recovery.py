"""Password-recovery token and email helpers."""

from email.message import EmailMessage
import hashlib
import smtplib
import ssl

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


RESET_SALT = "ripple-password-reset"


def _password_fingerprint(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()


def generate_reset_token(email: str, password_hash: str) -> str:
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(
        {"email": email, "password": _password_fingerprint(password_hash)},
        salt=RESET_SALT,
    )


def verify_reset_token(token: str) -> dict[str, str] | None:
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        payload = serializer.loads(
            token,
            salt=RESET_SALT,
            max_age=current_app.config["PASSWORD_RESET_MAX_AGE_SECONDS"],
        )
        if not isinstance(payload, dict) or set(payload) != {"email", "password"}:
            return None
        return payload
    except (BadSignature, SignatureExpired):
        return None


def reset_token_matches_password(payload: dict[str, str], password_hash: str) -> bool:
    return payload["password"] == _password_fingerprint(password_hash)


def send_recovery_email(*, recipient: str, username: str, reset_url: str) -> None:
    subject = "Recover your Ripple account"
    body = (
        f"Your Ripple username is: {username}\n\n"
        "Use the link below to choose a new password. The link expires automatically.\n\n"
        f"{reset_url}\n\n"
        "If you did not request account recovery, you can ignore this message."
    )

    if current_app.config["MAIL_SUPPRESS_SEND"]:
        current_app.logger.warning(
            "account_recovery_email_suppressed recipient=%s username=%s reset_url=%s",
            recipient,
            username,
            reset_url,
        )
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    message["To"] = recipient
    message.set_content(body)

    host = current_app.config["MAIL_SERVER"]
    port = current_app.config["MAIL_PORT"]
    timeout = current_app.config["MAIL_TIMEOUT_SECONDS"]

    if current_app.config["MAIL_USE_SSL"]:
        with smtplib.SMTP_SSL(host, port, timeout=timeout, context=ssl.create_default_context()) as smtp:
            _login_if_configured(smtp)
            smtp.send_message(message)
        return

    with smtplib.SMTP(host, port, timeout=timeout) as smtp:
        if current_app.config["MAIL_USE_TLS"]:
            smtp.starttls(context=ssl.create_default_context())
        _login_if_configured(smtp)
        smtp.send_message(message)


def _login_if_configured(smtp) -> None:
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    if username and password:
        smtp.login(username, password)
