# app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Literal


class Settings(BaseSettings):
    # 애플리케이션 메타
    app_name: str = "WASD FastAPI WMS"
    app_env: Literal["local", "dev", "prod", "test"] = "local"
    debug: bool = True
    api_prefix: str = "/api"

    # 데이터베이스 기본 설정
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "fastwms"
    db_echo: bool = False                 # SQLAlchemy 쿼리 로깅 여부
    db_pool_size: int = 10                # 기본 커넥션 풀 크기
    db_pool_recycle: int = 1800           # 초 단위. 0은 재활용 안 함

    # 구성: .env 자동 로드
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,             # 환경변수 대소문자 무시
        extra="ignore",                   # 정의되지 않은 값은 무시
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        """
        MySQL/MariaDB용 DSN 문자열 생성함.
        드라이버는 PyMySQL 사용함.
        예: mysql+pymysql://user:password@host:port/dbname?charset=utf8mb4
        """
        password_escaped = self.db_password.replace("@", "%40")
        return (
            f"mysql+pymysql://{self.db_user}:{password_escaped}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )

    @field_validator("db_pool_size")
    @classmethod
    def _valid_pool_size(cls, v: int) -> int:
        # 최소 1 보장함
        return max(1, v)

    @field_validator("db_pool_recycle")
    @classmethod
    def _valid_pool_recycle(cls, v: int) -> int:
        # 음수 방지함
        return max(0, v)


@lru_cache
def get_settings() -> Settings:
    """
    Settings 싱글톤 반환함.
    lru_cache로 재계산 방지함.
    """
    return Settings()
