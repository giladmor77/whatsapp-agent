import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

GREEN_API_URL = _require("GREEN_API_URL")
GREEN_API_INSTANCE = _require("GREEN_API_INSTANCE")
GREEN_API_TOKEN = _require("GREEN_API_TOKEN")

LLM_PROVIDER = _require("LLM_PROVIDER")
LLM_MODEL = _require("LLM_MODEL")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/conversations.db")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "20"))

_spec_path = Path(__file__).parent / "spec.json"
with open(_spec_path, encoding="utf-8") as _f:
    SPEC = json.load(_f)

AUTHORIZED_PHONES: set[str] = {
    c["phone_e164"] for c in SPEC["audience"].get("authorized_contacts", [])
}
BOT_NAME: str = SPEC["identity"]["name"]
ANSWER_GROUPS: bool = SPEC["audience"].get("answer_groups", False)
