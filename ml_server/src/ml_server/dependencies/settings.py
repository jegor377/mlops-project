from functools import lru_cache

from src.ml_server.conf.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()
