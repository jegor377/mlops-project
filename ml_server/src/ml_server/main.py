from src.ml_server.dependencies.settings import get_settings
from src.ml_server.app import create_app


settings = get_settings()
app = create_app(settings)
