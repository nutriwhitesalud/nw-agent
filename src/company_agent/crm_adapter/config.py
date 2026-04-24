from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CrmSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "crm-adapter"
    internal_api_key: str = Field(alias="INTERNAL_API_KEY")
    crm_provider: str = Field(default="mock", alias="CRM_PROVIDER")
    crm_base_url: str | None = Field(default=None, alias="CRM_BASE_URL")
    crm_api_key: str | None = Field(default=None, alias="CRM_API_KEY")
