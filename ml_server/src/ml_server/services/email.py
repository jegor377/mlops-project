from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from datetime import datetime

from src.ml_server.conf.settings import Settings


def _make_mailer(settings: Settings) -> FastMail:
    mail_config = ConnectionConfig(
        MAIL_USERNAME=settings.smtp_username,
        MAIL_PASSWORD=settings.smtp_password,
        MAIL_FROM=settings.smtp_from,
        MAIL_PORT=settings.smtp_port,
        MAIL_SERVER=settings.smtp_host,
        MAIL_STARTTLS=settings.smtp_starttls,
        MAIL_SSL_TLS=settings.smtp_ssl_tls,
        USE_CREDENTIALS=settings.smtp_use_credentials,
        VALIDATE_CERTS=settings.smtp_validate_certs,
    )
    return FastMail(mail_config)


async def send_verification_email(
    recipient: EmailStr, verify_url: str, settings: Settings
) -> None:
    message = MessageSchema(
        subject="Verify your email address",
        recipients=[recipient],
        body=(
            f"<p>Thanks for registering. Click the link below to activate your account:</p>"
            f'<p><a href="{verify_url}">{verify_url}</a></p>'
            f"<p>This link expires in {settings.email_verification_expire_hours} hour(s).</p>"
        ),
        subtype=MessageType.html,
    )
    await _make_mailer(settings).send_message(message)


async def send_password_reset_email(
    recipient: EmailStr, reset_url: str, settings: Settings
) -> None:
    message = MessageSchema(
        subject="Reset your password",
        recipients=[recipient],
        body=(
            f"<p>We received a request to reset your Volta password.</p>"
            f'<p><a href="{reset_url}">Reset password</a></p>'
            f"<p>This link expires in {settings.password_reset_expire_hours} hour(s).</p>"
            f"<p>If you didn't request this, you can safely ignore this email.</p>"
        ),
        subtype=MessageType.html,
    )
    await _make_mailer(settings).send_message(message)


async def send_pat_creation_email(
    recipient: EmailStr,
    pat_name: str,
    scopes: list[str],
    expires_in_days: int | None,
    expires_at: datetime,
    settings: Settings
) -> None:
    message = MessageSchema(
        subject="Your new Personal Access Token",
        recipients=[recipient],
        body=(
            f"<p>A new Personal Access Token (PAT) has been created for your account.</p>"
            f"<p><strong>Name:</strong> {pat_name}</p>"
            f"<p><strong>Scopes:</strong> {', '.join(scopes)}</p>"
            f"<p><strong>Expires in:</strong> {f'{expires_in_days} days' if expires_in_days is not None else 'Never'}</p>"
            f"<p><strong>Expiration date:</strong> {expires_at if expires_at else 'Never'}</p>"
            f"<p>If you didn't create this token, please revoke it immediately from your account settings.</p>"
        ),
        subtype=MessageType.html,
    )
    await _make_mailer(settings).send_message(message)


async def send_pat_revocation_email(
    recipient: EmailStr, pat_name: str, settings: Settings
) -> None:
    message = MessageSchema(
        subject="Personal Access Token Revoked",
        recipients=[recipient],
        body=(
            f"<p>Your Personal Access Token (PAT) named '{pat_name}' has been revoked.</p>"
            f"<p>If you didn't revoke this token, please check your account security settings immediately.</p>"
        ),
        subtype=MessageType.html,
    )
    await _make_mailer(settings).send_message(message)
