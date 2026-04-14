from src.ml_server.conf.settings import Settings
from src.ml_server.app import create_app


settings = Settings()
app = create_app(settings)
