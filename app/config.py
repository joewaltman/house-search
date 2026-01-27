import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List
from app.models.config_model import AppConfig


class Settings(BaseSettings):
    """Environment variables configuration"""

    # API Keys
    rentcast_api_key: str = ""
    rapidapi_key: str = ""
    homesage_api_key: str = ""

    # Email
    resend_api_key: str = ""
    notification_email: str = ""
    from_email: str = "notifications@house-search.com"

    # Service config
    check_times: str = "08:00,18:00"
    timezone: str = "America/Los_Angeles"
    log_level: str = "INFO"

    # API Quotas
    rentcast_monthly_limit: int = 50
    rapidapi_monthly_limit: int = 100
    homesage_monthly_limit: int = 500

    class Config:
        env_file = ".env"
        case_sensitive = False


def load_yaml_config(config_path: str = "config.yaml") -> AppConfig:
    """Load YAML configuration file"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    return AppConfig(**data)


def get_all_zipcodes(config: AppConfig) -> List[str]:
    """Get combined list of all zipcodes"""
    return config.zipcodes.priority + config.zipcodes.additional


# Global settings instances
settings = Settings()
app_config = load_yaml_config()
