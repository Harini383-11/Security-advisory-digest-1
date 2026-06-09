"""
Configuration settings for Security Advisory Digest.
Loads from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "data" / "advisory.db"))
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", str(PROJECT_ROOT / "data" / "chroma_db"))

# API Configuration
CISA_KEV_API_URL = os.getenv(
    "CISA_KEV_API_URL",
    "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
)
NVD_API_KEY = os.getenv("NVD_API_KEY", "")
NVD_API_BASE_URL = os.getenv(
    "NVD_API_BASE_URL",
    "https://services.nvd.nist.gov/rest/json/cves/2.0"
)

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# ChromaDB Configuration
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "security_advisories")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(PROJECT_ROOT / "logs" / "advisory_digest.log"))

# Streamlit Configuration
STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
STREAMLIT_THEME_PRIMARY_COLOR = os.getenv("STREAMLIT_THEME_PRIMARY_COLOR", "#FF6B6B")

# Create necessary directories
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
Path(VECTOR_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
