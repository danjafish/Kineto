import os
from dotenv import load_dotenv

load_dotenv()  # optional: read from .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME       = os.getenv("OPENAI_MODEL", "gpt-4")
MAX_TOKENS       = int(os.getenv("MAX_TOKENS", "2048"))
TEMPERATURE      = float(os.getenv("TEMPERATURE", "0.2"))
