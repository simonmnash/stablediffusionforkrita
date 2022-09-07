from pydantic import BaseSettings


class Settings(BaseSettings):
    api_key: str
    huggingface_token: str
    class Config:
        env_file = ".env"
