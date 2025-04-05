import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SECRET_KEY = os.getenv("SESSION_SECRET", "dev-default-key")
    DEBUG = os.getenv("DEBUG", "1") == "1"

settings = Settings()
