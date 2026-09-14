"""Load configuration from backend/.env, independent of the working directory."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / '.env', extra='ignore')

    app_name: str = '途间 · 智能旅行助手'
    llm_api_key: SecretStr = SecretStr('')
    llm_model_id: str = 'deepseek-v4-flash'
    llm_base_url: str = 'https://api.deepseek.com'
    llm_timeout: float = Field(default=90, gt=0)
    amap_api_key: SecretStr = SecretStr('')
    database_url: SecretStr = SecretStr('')
    unsplash_access_key: SecretStr = SecretStr('')
    host: str = '127.0.0.1'
    port: int = 8000
    cors_origins: str = 'http://localhost:5173,http://127.0.0.1:5173'

    def validate_required(self) -> None:
        missing = [name for name in ('llm_api_key', 'amap_api_key', 'database_url')
                   if not getattr(self, name).get_secret_value()]
        if missing:
            raise ValueError('请在 backend/.env 配置：' + ', '.join(missing))

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(',') if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
