from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    NestedSecretsSettingsSource,
)
from pydantic import (
    BaseModel,
    PostgresDsn,
)
from typing import Literal


class SMTPCredentials(BaseModel):
    username: str
    password: str


class SMTPSettings(BaseModel):
    host: str = 'smtp.example.com'
    port: int = 1025
    from_email_address: str
    credentials: SMTPCredentials | None = None
    security: Literal[
        "none",
        "starttls",
        "tls",
    ] = "none"


class GoogleOAuth2Credentials(BaseModel):
    client_id: str
    client_secret: str


class Settings(BaseSettings):
    env: Literal[
        'development',
        'staging',
        'production'
    ] = 'development'
    hostname: str
    frontend_hostname: str
    oauth_state_session_secret_key: str
    db_uri: PostgresDsn
    load_model: bool
    pool_size: int = 5
    max_overflow: int = 10
    email_verification_expire_hours: int = 24
    smtp: SMTPSettings
    session_expire_hours: int = 24
    password_reset_expire_hours: int = 1
    pat_count_limit: int = 50
    google_oauth2_creds: GoogleOAuth2Credentials

    model_config = SettingsConfigDict(
        env_file='.env',
        secrets_dir='/run/secrets',
        secrets_nested_delimiter='__',
        env_nested_delimiter='__',
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            NestedSecretsSettingsSource(file_secret_settings),
        )

    @property
    def async_db_uri(self) -> str:
        return str(self.db_uri).replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        ).replace(
            "postgres://",
            "postgresql+asyncpg://",
            1,
        )
