import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
FAKE_STORE_BASE_URL = "https://fakestoreapi.com"
MODEL_NAME = "claude-sonnet-4-20250514"
