"""配置管理模块 - 简化版"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field


class AppConfig(BaseSettings):
    """应用配置"""
    debug: bool = Field(default=True)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # 场景配置文件路径
    scenes_file: str = Field(default="scenes.yaml")

    # 默认环境
    default_env: str = Field(default="test")

    class Config:
        env_prefix = "APP_"


def load_config() -> AppConfig:
    """加载配置"""
    return AppConfig()


# 全局配置实例
config = load_config()
