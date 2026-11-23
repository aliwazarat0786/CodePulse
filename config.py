"""
Configuration module for CodePulse AI.
Loads settings from environment variables with sensible defaults.
"""
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    BASE_DIR = BASE_DIR
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    
    # LLM Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    
    # Analysis & Safety Limits
    ANALYSIS_TIMEOUT = int(os.getenv("ANALYSIS_TIMEOUT", 15))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 1024 * 1024))  # 1MB
    TEMP_DIR = Path(tempfile.gettempdir()) / "codepulse_analysis"
    
    # Database
    ENABLE_PERSISTENCE = os.getenv("ENABLE_PERSISTENCE", "True").lower() in ("true", "1")
    DB_PATH = BASE_DIR / os.getenv("DB_PATH", "codepulse.db")
    
    # Supported Languages
    SUPPORTED_LANGUAGES = ["python", "java", "c", "cpp", "javascript", "sql"]
    
    # Quality Score Calculation Weights
    WEIGHT_CRITICAL = 15.0
    WEIGHT_HIGH = 8.0
    WEIGHT_MEDIUM = 3.0
    WEIGHT_LOW = 1.0
    WEIGHT_SECURITY_PENALTY = 5.0
