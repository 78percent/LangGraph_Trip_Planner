"""Load configuration from backend/.env, independent of the working directory."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]  #不管你从哪个目录启动 Python，我都准确去 backend/.env 找配置。


class Settings(BaseSettings):  #BaseSettings是 专门用来读取环境变量 / .env 的 Pydantic 模型
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / '.env', extra='ignore')

    app_name: str = '途间 · 智能旅行助手'    # agent参数配置
    llm_api_key: SecretStr = SecretStr('')
    llm_model_id: str = 'deepseek-v4-flash'
    llm_base_url: str = 'https://api.deepseek.com'
    llm_timeout: float = Field(default=90, gt=0)
    amap_api_key: SecretStr = SecretStr('')
    database_url: SecretStr = SecretStr('')
    unsplash_access_key: SecretStr = SecretStr('')  #SecretStr 从env 读数据，密文打印
    host: str = '127.0.0.1'
    port: int = 8000
    cors_origins: str = 'http://localhost:5173,http://127.0.0.1:5173'  #跨域处理

    def validate_required(self) -> None:   # 对必要项 'llm_api_key', 'amap_api_key', 'database_url' 进行缺失检查
        missing = [name for name in ('llm_api_key', 'amap_api_key', 'database_url')
                   if not getattr(self, name).get_secret_value()]
        if missing:
            raise ValueError('请在 backend/.env 配置：' + ', '.join(missing))

    @property  #让一个方法可以像属性一样被访问，不需要加 (), print(settings.allowed_origins)   # ✅ 像属性一样，不用加括号
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(',') if item.strip()]    # cors_origins 这个逗号分隔的字符串，转成 FastAPI CORS 中间件需要的 list[str]


@lru_cache  # 缓存函数的返回值。第一次调用时执行函数体，之后相同参数的调用直接返回缓存结果，不再执行函数体。
def get_settings() -> Settings:
    return Settings()  #  此处返回的Settings就是该文件上方创建的Settings若干参数, 后续每处使用get_settings()方法时都是如此
