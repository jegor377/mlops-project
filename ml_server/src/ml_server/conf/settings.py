import os


class Settings:
    def __init__(self):
        raw_uri = os.getenv("DB_URI", "")
        self.hostname = os.getenv("HOSTNAME")
        self.db_uri = raw_uri.replace("postgresql://", "postgresql+asyncpg://")
        self.load_model = os.getenv("LOAD_MODEL", "false").lower() == "true"
        self.pool_size = 5
        self.max_overflow = 10
        self.email_verification_expire_hours = 24
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.example.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        self.smtp_use_credentials = os.getenv("SMTP_USE_CREDENTIALS", "true").lower() == "true"
        self.smtp_validate_certs = os.getenv("SMTP_VALIDATE_CERTS", "true").lower() == "true"
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM")
        self.smtp_starttls = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
        self.smtp_ssl_tls = os.getenv("SMTP_SSL_TLS", "false").lower() == "true"