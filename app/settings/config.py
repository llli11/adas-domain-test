import os
import typing

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VERSION: str = "0.1.0"
    APP_TITLE: str = "Vue FastAPI Admin"
    PROJECT_NAME: str = "Vue FastAPI Admin"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    DEBUG: bool = True

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root123456"
    MYSQL_DATABASE: str = "mydb_local"
    MYSQL_ROOT_PASSWORD: str = "root123456"

    USE_SERVER: bool = False

    SERVER_HOST: str = "localhost"
    SERVER_PORT: int = 3306
    SERVER_USER: str = "myuser"
    SERVER_PASSWORD: str = "mypassword123456"
    SERVER_DATABASE: str = "mydb_local"

    PLAYW_HOST: str = "playw"
    PLAYW_PORT: int = 7777

    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    model_config = {"env_file": ".env", "extra": "allow"}

    @property
    def db_host(self) -> str:
        return self.MYSQL_HOST

    @property
    def db_port(self) -> int:
        return self.MYSQL_PORT

    @property
    def db_user(self) -> str:
        return self.MYSQL_USER

    @property
    def db_password(self) -> str:
        return self.MYSQL_PASSWORD

    @property
    def db_database(self) -> str:
        return self.MYSQL_DATABASE

    @property
    def TORTOISE_ORM(self) -> dict:
        return {
            "connections": {
                "mysql": {
                    "engine": "tortoise.backends.mysql",
                    "credentials": {
                        "host": self.db_host,
                        "port": self.db_port,
                        "user": self.db_user,
                        "password": self.db_password,
                        "database": self.db_database,
                    },
                },
            },
            "apps": {
                "models": {
                    "models": [
                        "aerich.models",
                        "app.models.admin",
                        "app.models.ecu",
                        "app.models.version_index",
                        "app.models.tool",
                        "app.models.vehicle",
                        "app.models.user_feishu_config",
                        "app.models.expense",
                        "app.models.mapway",
                        "app.models.contractor",
                    ],
                    "default_connection": "mysql",
                },
            },
            "use_tz": False,
            "timezone": "Asia/Shanghai",
        }


settings = Settings()
