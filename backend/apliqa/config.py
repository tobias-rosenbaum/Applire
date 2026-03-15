from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    apliqa_edition: str = "community"
    database_url: str
    llm_provider: str = "mistral"
    mistral_api_key: str = ""
    mistral_model: str = "mistral-small-latest"
    openai_api_key: str = ""
    openai_base_url: str = ""          # empty = use OpenAI default; set to point at LM Studio etc.
    openai_model: str = "gpt-4o"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"
    auth_provider: str = "none"
    mcp_transport: str = "stdio"
    apliqa_base_url: str = "http://localhost:8001"
    upload_dir: str = "./data/uploads"
    storage_backend: str = "local"
    ocr_backend: str = "mistral_vision"

    @property
    def is_community(self) -> bool:
        return self.apliqa_edition == "community"


settings = Settings()
