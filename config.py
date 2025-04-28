# config.py
import os

# Default paths
DEFAULT_CSV_PATH = os.getenv("CSV_PATH", "data.csv")
DEFAULT_VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "data/vector_db")

# LLM settings
DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")