"""
Configuration management via environment variables.
API keys and service URLs must be set via environment, never hardcoded.
"""

import os


# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-chat")

# Dify Workflow (optional alternative to direct DeepSeek)
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://xjtuagent.59wanmei.com:5000")
USE_DIFY = os.getenv("USE_DIFY", "false").lower() == "true"

# Default filter keywords (user-editable, served as initial recommendation)
DEFAULT_FILTER_KEYWORDS = [
    "大学", "学院", "高职", "职业技术", "职业学院",
    "师范", "理工", "经贸", "学校", "教育",
]

# Spider defaults
DEFAULT_DELAY_RANGE = (3, 8)
DEFAULT_MAX_PAGES = 100
DEFAULT_TIMEOUT = 20
CACHE_FILE = os.getenv("CACHE_FILE", "data/raw_data_cache.jsonl")

# Analyzer defaults
DEFAULT_MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))
DEFAULT_REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.5"))
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "8000"))


def validate_config():
    """Validate required configuration, raise if missing critical values."""
    if not DEEPSEEK_API_KEY and not DIFY_API_KEY:
        raise ValueError(
            "Either DEEPSEEK_API_KEY or DIFY_API_KEY must be set in environment. "
            "Copy backend/.env.example to backend/.env and fill in your keys."
        )
