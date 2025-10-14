import os
import re
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import URL

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # путь до корня проекта
CONFIG_PATH = BASE_DIR / "config.yaml"

load_dotenv()


def resolve_env_vars(obj):
    if isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(i) for i in obj]
    elif isinstance(obj, str):
        return re.sub(r"\$\{(\w+)\}", lambda m: os.getenv(m.group(1), m.group(0)), obj)
    else:
        return obj


def load_yaml_config(path: str = CONFIG_PATH):
    with open(path, "r") as f:
        raw = yaml.safe_load(f)
    return resolve_env_vars(raw)


class DatabaseConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    name: str
    driver: str
    database_system: str

    @property
    def url(self):
        return URL.create(
            drivername=f"{self.database_system}+{self.driver}",
            username=self.user,
            database=self.name,
            password=self.password,
            port=self.port,
            host=self.host,
        ).render_as_string(hide_password=False)


class Security(BaseModel):
    access_token_expire_minute: int
    secret_key: str
    algorithm: str


class Config(BaseModel):
    database: DatabaseConfig
    security: Security


def load_config() -> Config:
    data = load_yaml_config()
    return Config(**data)


config = load_config()
