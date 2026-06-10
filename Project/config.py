"""
Configuration module for Security Advisory Digest system.
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT}/data/advisories.db")
DB_PATH = PROJECT_ROOT / "data" / "advisories.db"

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

# RSS feeds configuration
RSS_FEEDS = [
    "https://github.blog/security/feed/",
    "https://www.cisa.gov/cybersecurity-advisories/all.xml",
]

# Inventory configuration
INVENTORY_FILE = PROJECT_ROOT / "data" / "inventory.csv"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# FastAPI configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_TITLE = "Security Advisory Digest"
API_VERSION = "1.0.0"

# Request timeout
REQUEST_TIMEOUT = 30

# Batch processing
BATCH_SIZE = 10
