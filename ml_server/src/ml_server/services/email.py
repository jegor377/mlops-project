from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

from src.ml_server.conf.settings import Settings


async def send_verification_email(recipient: EmailStr, verify_url: str, settings: Settings) -> None:
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

    mailer = FastMail(mail_config)
    
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
    await mailer.send_message(message)