import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # 環境変数ロード
    BASE_DIR_PATH: str = str(Path(__file__).parent.parent.parent.absolute())
    RESOURCE_GROUP: str = os.getenv("RESOURCE_GROUP")
    WANDB_APIKEY: str = os.getenv("WANDB_APIKEY")

    # BASE_CONFIG: dict = yaml.safe_load(
    #    open(str(Path(BASE_DIR_PATH) / "main.yaml"), "r", encoding="utf-8_sig")
    # )
    # RESOURCE_GROUP: str = BASE_CONFIG.get("resource_group", "a-batch")
    # WANDB_APIKEY: str = BASE_CONFIG.get("wandb_apikey")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
