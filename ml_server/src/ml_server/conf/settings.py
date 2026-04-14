import os


class Settings:
    def __init__(self):
        raw_uri = os.getenv("DB_URI", "")
        self.db_uri = raw_uri.replace("postgresql://", "postgresql+asyncpg://")
        self.load_model = os.getenv("LOAD_MODEL", "false").lower() == "true"
        self.pool_size = 5
        self.max_overflow = 10
