from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    apliqa_edition: str = "community"
    database_url: str
    llm_provider: str = "mistral"
    mistral_api_key: str = ""
    auth_provider: str = "none"

    @property
    def is_community(self) -> bool:
        return self.apliqa_edition == "community"


settings = Settings()
