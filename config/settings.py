"""
Centralized settings configuration for the onion scraper system.
This file provides a clean interface for all configuration settings.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Load environment variables
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

# Import existing config
from .config import *

# Directory paths
DATA_DIR = BASE_DIR / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
ARCHIVES_DIR = DATA_DIR / 'archives'

LOGS_DIR = BASE_DIR / 'logs'
DEBUG_LOGS_DIR = LOGS_DIR / 'debug'
ERROR_LOGS_DIR = LOGS_DIR / 'errors'
PROGRESS_LOGS_DIR = LOGS_DIR / 'progress'

BACKUPS_DIR = BASE_DIR / 'backups'
DAILY_BACKUPS_DIR = BACKUPS_DIR / 'daily'
WEEKLY_BACKUPS_DIR = BACKUPS_DIR / 'weekly'

# Ensure directories exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, ARCHIVES_DIR, 
                 DEBUG_LOGS_DIR, ERROR_LOGS_DIR, PROGRESS_LOGS_DIR,
                 DAILY_BACKUPS_DIR, WEEKLY_BACKUPS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Tor configuration
TOR_SOCKS_PROXY = os.getenv('TOR_SOCKS_PROXY', 'socks5h://127.0.0.1:9050')
TOR_CONTROL_PORT = int(os.getenv('TOR_CONTROL_PORT', '9051'))
TOR_CONTROL_PASSWORD = os.getenv('TOR_CONTROL_PASSWORD', 'Jasoncomer1$')

# API configuration
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = int(os.getenv('API_PORT', '8000'))
API_DEBUG = os.getenv('API_DEBUG', 'False').lower() == 'true'

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/processed/scraper.db')

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Scraping configuration
MAX_WORKERS = int(os.getenv('MAX_WORKERS', '15'))
SLEEP_BETWEEN_REQUESTS = (
    int(os.getenv('MIN_SLEEP', '2')),
    int(os.getenv('MAX_SLEEP', '8'))
)
ROTATE_EVERY_N = int(os.getenv('ROTATE_EVERY_N', '25'))
MAX_DEPTH = int(os.getenv('MAX_DEPTH', '4'))

# File paths
OUTPUT_FILE = RAW_DATA_DIR / f"discovered_onions_{os.getenv('DATE_SUFFIX', 'latest')}.csv"
ADDRESSES_FILE = RAW_DATA_DIR / f"crypto_addresses_{os.getenv('DATE_SUFFIX', 'latest')}.csv"
PROGRESS_FILE = PROCESSED_DATA_DIR / "crawler_progress.json"
RESTART_FILE = PROCESSED_DATA_DIR / "crawler_restart.json"

# Google Drive configuration
GOOGLE_DRIVE_CREDENTIALS_FILE = BASE_DIR / 'google_sheets_service_account.json'
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

# Screenshot configuration
SCREENSHOTS_DIR = RAW_DATA_DIR / 'screenshots_fast'
DEBUG_HTML_DIR = RAW_DATA_DIR / 'debug_html'
UNSOLVED_CAPTCHAS_DIR = RAW_DATA_DIR / 'unsolved_captchas_fast'

# Agent configuration
AGENT_TIMEOUT = int(os.getenv('AGENT_TIMEOUT', '30'))
AGENT_MAX_RETRIES = int(os.getenv('AGENT_MAX_RETRIES', '3'))
AGENT_LEARNING_RATE = float(os.getenv('AGENT_LEARNING_RATE', '0.1'))

# Content analysis configuration
CSAM_DETECTION_ENABLED = os.getenv('CSAM_DETECTION_ENABLED', 'True').lower() == 'true'
TRAFFICKING_DETECTION_ENABLED = os.getenv('TRAFFICKING_DETECTION_ENABLED', 'True').lower() == 'true'
SCAM_DETECTION_ENABLED = os.getenv('SCAM_DETECTION_ENABLED', 'True').lower() == 'true'

# Export configuration
EXPORT_FORMATS = ['csv', 'json', 'xlsx']
DEFAULT_EXPORT_FORMAT = os.getenv('DEFAULT_EXPORT_FORMAT', 'csv')

# Security configuration
ENCRYPTION_ENABLED = os.getenv('ENCRYPTION_ENABLED', 'False').lower() == 'true'
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# Performance configuration
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour
MAX_MEMORY_USAGE = int(os.getenv('MAX_MEMORY_USAGE', '1024'))  # MB

# Development configuration
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
TESTING_MODE = os.getenv('TESTING_MODE', 'False').lower() == 'true' 