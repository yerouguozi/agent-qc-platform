from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Agent QC Platform"
    database_url: str = "sqlite:///./qc.db"
    deepseek_api_key: str = ""
    model_name: str = "deepseek-v4-flash"
    judge_max_retries: int = 2
    judge_timeout: float = 60.0
    sut_chat_url: str = ""
    sut_auth_token: str = ""
    sut_dataset_id: str = ""
    trace_result_max_chars: int = 2000

    class Config:
        env_file = ".env"


settings = Settings()