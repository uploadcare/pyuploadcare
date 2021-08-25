from pydantic import BaseSettings


class Settings(BaseSettings):
    BASE_URL: str = "https://api.uploadcare.com/"
    PUBLIC_KEY: str
    SECRET_KEY: str

    class Config:
        env_prefix = "UPLOADCARE_"
        case_sensitive = True


settings = Settings()
