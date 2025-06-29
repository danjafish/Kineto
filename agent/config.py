import os
from dotenv import load_dotenv

load_dotenv()  # optional: read from .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME       = "gpt-4o"
MAX_TOKENS       = int(os.getenv("MAX_TOKENS", "4096"))
TEMPERATURE      = float(os.getenv("TEMPERATURE", "0.2"))
