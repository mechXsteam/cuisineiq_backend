from pydantic_settings import BaseSettings


class Settings(BaseSettings):
        DATABASE_URL: str
        S3_BUCKET: str
        AWS_ACCESS_KEY_ID: str
        AWS_SECRET_ACCESS_KEY: str
        SECRET_KEY: str

        class Config:
                env_file = ".env"


settings = Settings()
