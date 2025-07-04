# ---[ Fast Scraper with Parallel Processing ]---
import csv
import os
import re
import time
import base64
import requests
from io import BytesIO
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlencode
import concurrent.futures
import threading
from queue import Queue
import multiprocessing

import base58
import pytesseract
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from eth_utils import is_checksum_address
from solders.pubkey import Pubkey
import chromedriver_autoinstaller
import json
import random
import string
import openai
import anthropic
import io
import socket
import gspread
import shutil
import tempfile

# ---[ UTILITY FUNCTIONS ]---
def get_random_suffix(length=5):
    """Generate a random suffix for unique usernames and names"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def fill_visible_inputs_anywhere(driver, data_dict=None):
    """
    Fill all visible and enabled <input> fields in the DOM, regardless of form context.
    data_dict: Optional dict mapping field types/names to values (e.g., {'email': ..., 'username': ...})
    """
    import time
    random_suffix = get_random_suffix()
    timestamp = int(time.time())
    # Default data if not provided
    default_data = {
        'email': f'user_{timestamp}_{random_suffix}@protonmail.com',
        'username': f'user_{timestamp}_{random_suffix}',
        'name': f'John Doe {random_suffix}',
        'first_name': f'John{random_suffix}',
        'last_name': f'Doe{random_suffix}',
        'password': 'SecurePass123!',
        'phone': '+1-555-123-4567',
        'address': '123 Main Street',
        'city': 'New York',
        'zip': '10001',
    }
    if data_dict:
        default_data.update(data_dict)
    
    inputs = driver.find_elements(By.TAG_NAME, 'input')
    fields_filled = 0
    for inp in inputs:
        try:
            if not inp.is_displayed() or not inp.is_enabled():
                continue
            field_type = inp.get_attribute('type') or 'text'
            field_name = (inp.get_attribute('name') or '').lower()
            field_id = (inp.get_attribute('id') or '').lower()
            field_placeholder = (inp.get_attribute('placeholder') or '').lower()
            field_text = f"{field_name} {field_id} {field_placeholder}".lower()
            value_to_fill = None
            # Priority: email, username, password, name, phone, address, city, zip
            if field_type == 'email' or 'email' in field_text:
                value_to_fill = default_data['email']
            elif field_type == 'password' or 'pass' in field_text:
                value_to_fill = default_data['password']
            elif 'user' in field_text or 'login' in field_text:
                value_to_fill = default_data['username']
            elif 'first' in field_text and 'name' in field_text:
                value_to_fill = default_data['first_name']
            elif 'last' in field_text and 'name' in field_text:
                value_to_fill = default_data['last_name']
            elif 'name' in field_text:
                value_to_fill = default_data['name']
            elif 'phone' in field_text or 'mobile' in field_text:
                value_to_fill = default_data['phone']
            elif 'address' in field_text:
                value_to_fill = default_data['address']
            elif 'city' in field_text:
                value_to_fill = default_data['city']
            elif 'zip' in field_text or 'postal' in field_text:
                value_to_fill = default_data['zip']
            elif field_type == 'text' and not value_to_fill:
                value_to_fill = default_data['username']
            if value_to_fill:
                inp.clear()
                inp.send_keys(value_to_fill)
                print(f"[fill_visible_inputs_anywhere] Filled '{field_name or field_id or field_placeholder or field_type}' with '{value_to_fill}'")
                fields_filled += 1
        except Exception as e:
            print(f"[fill_visible_inputs_anywhere] Could not fill input: {e}")
            continue
    print(f"[fill_visible_inputs_anywhere] Total fields filled: {fields_filled}")
    return fields_filled

def try_click_join_button(driver):
    """Try to find and click a button or link with text 'JOIN' (case-insensitive)"""
    from selenium.webdriver.common.by import By
    import time
    join_selectors = [
        "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'JOIN')]",
        "//a[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'JOIN')]",
        "//div[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'JOIN')]"
    ]
    for selector in join_selectors:
        try:
            elems = driver.find_elements(By.XPATH, selector)
            for elem in elems:
                if elem.is_displayed() and elem.is_enabled():
                    elem.click()
                    print("✅ [JOIN Fallback] Clicked JOIN button/link.")
                    time.sleep(2)
                    return True
        except Exception as e:
            print(f"[JOIN Fallback] JOIN click failed: {e}")
    return False

# === AGENT SYSTEM INTEGRATION ===
import sys
import os

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

# Add the agents directory to the path
agents_path = os.path.join(project_root, 'src', 'agents')
sys.path.insert(0, agents_path)

# Add the analysis directory to the path
analysis_path = os.path.join(project_root, 'src', 'analysis')
sys.path.insert(0, analysis_path)

from integrated_agent_system import integrated_agents

# === ENHANCED ERROR HANDLING AND CONTENT ANALYSIS ===
from enhanced_error_handler import handle_scraping_error, classify_scraping_error, should_retry_scraping
from enhanced_content_signatures import analyze_page_content, extract_addresses_comprehensive

# === SMART TRANSACTION LEARNING SYSTEM ===
from smart_interaction_executor import execute_smart_transaction

# ---[ Load Environment Variables ]---
def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"📄 Loading environment variables from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Environment variables loaded successfully")
    else:
        print("⚠️ No .env file found, using system environment variables")

def fetch_google_sheet_addresses():
    """Fetch all addresses from Google Sheet darknet_automation tab"""
    try:
        gc = gspread.service_account(filename=GOOGLE_SHEET_SERVICE_ACCOUNT)
        sheet = gc.open_by_url(GOOGLE_SHEET_URL).worksheet(GOOGLE_SHEET_NAME)
        
        # Get all values from the sheet
        all_values = sheet.get_all_values()
        if not all_values:
            print("⚠️ No data found in Google Sheet")
            return set()
        
        # Find the address column (assuming it's named 'address' or similar)
        header = all_values[0]
        address_col_index = None
        for i, col_name in enumerate(header):
            if 'address' in col_name.lower():
                address_col_index = i
                break
        
        if address_col_index is None:
            print("⚠️ Address column not found in Google Sheet")
            return set()
        
        # Extract addresses from the column
        addresses = set()
        for row in all_values[1:]:  # Skip header
            if len(row) > address_col_index:
                address = row[address_col_index].strip()
                if address and address.lower() not in ['', 'nan', 'none']:
                    # Normalize address (lowercase, strip whitespace)
                    normalized_address = address.lower().strip()
                    addresses.add(normalized_address)
        
        print(f"✅ Loaded {len(addresses)} addresses from Google Sheet")
        return addresses
        
    except Exception as e:
        print(f"❌ Error fetching Google Sheet addresses: {e}")
        return set()

def fetch_google_sheet_urls():
    """Fetch all URLs from column F 'url' of Google Sheet darknet_automation tab"""
    try:
        gc = gspread.service_account(filename=GOOGLE_SHEET_SERVICE_ACCOUNT)
        sheet = gc.open_by_url(GOOGLE_SHEET_URL).worksheet(GOOGLE_SHEET_NAME)
        
        # Get all values from the sheet
        all_values = sheet.get_all_values()
        if not all_values:
            print("⚠️ No data found in Google Sheet")
            return []
        
        # Find the URL column (column F, index 5, or look for 'url' in header)
        header = all_values[0]
        url_col_index = None
        
        # First try to find column F (index 5)
        if len(header) > 5:
            url_col_index = 5  # Column F
        
        # If column F doesn't exist or we want to be more flexible, look for 'url' in header
        if url_col_index is None:
            for i, col_name in enumerate(header):
                if 'url' in col_name.lower():
                    url_col_index = i
                    break
        
        if url_col_index is None:
            print("⚠️ URL column not found in Google Sheet")
            return []
        
        # Extract URLs from the column
        urls = []
        unique_urls = set()  # Track unique URLs to avoid duplicates
        
        for row in all_values[1:]:  # Skip header
            if len(row) > url_col_index:
                url = row[url_col_index].strip()
                if url and url.lower() not in ['', 'nan', 'none'] and url.startswith('http'):
                    # Avoid duplicates
                    if url not in unique_urls:
                        urls.append(url)
                        unique_urls.add(url)
        
        print(f"✅ Loaded {len(urls)} unique URLs from Google Sheet column F")
        return urls
        
    except Exception as e:
        print(f"❌ Error fetching Google Sheet URLs: {e}")
        return []

def check_and_move_duplicates():
    """Check for duplicates in main CSV and move them to duplicate file"""
    try:
        if not os.path.exists(OUTPUT_CSV):
            print("⚠️ Main CSV file not found, skipping duplicate check")
            return
        
        # Get Google Sheet addresses
        google_addresses = fetch_google_sheet_addresses()
        
        # Read main CSV and find duplicates
        duplicate_rows = []
        non_duplicate_rows = []
        
        with open(OUTPUT_CSV, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            header = next(csv_reader)  # Get header
            
            # Find address column index
            try:
                address_col_index = header.index('address')
            except ValueError:
                print("❌ 'address' column not found in main CSV")
                return
            
            # Process each row
            for row in csv_reader:
                if len(row) > address_col_index:
                    address = row[address_col_index].strip()
                    if address in google_addresses:
                        duplicate_rows.append(row)
                    else:
                        non_duplicate_rows.append(row)
        
        # Move duplicates to duplicate file
        if duplicate_rows:
            # Ensure duplicate file exists with header
            if not os.path.exists(DUPLICATE_DIVERT_CSV):
                with open(DUPLICATE_DIVERT_CSV, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(header)
            
            # Append duplicates to duplicate file
            with open(DUPLICATE_DIVERT_CSV, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                for row in duplicate_rows:
                    writer.writerow(row)
            
            # Rewrite main CSV without duplicates
            with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(header)
                for row in non_duplicate_rows:
                    writer.writerow(row)
            
            print(f"✅ Moved {len(duplicate_rows)} duplicate rows to {DUPLICATE_DIVERT_CSV}")
            print(f"✅ Main CSV now contains {len(non_duplicate_rows)} non-duplicate rows")
        else:
            print("✅ No duplicates found in main CSV")
            
    except Exception as e:
        print(f"❌ Error checking/moving duplicates: {e}")

def is_duplicate_address(address, google_addresses, local_seen_addresses):
    """Check if address is duplicate in either Google Sheet or local processing"""
    # Normalize address for comparison (lowercase, strip whitespace)
    normalized_address = address.lower().strip() if address else ""
    
    # Check against Google Sheet addresses (normalized)
    for google_addr in google_addresses:
        if google_addr and normalized_address == google_addr.lower().strip():
            return True
    
    # Check against local seen addresses (normalized)
    for local_addr in local_seen_addresses:
        if local_addr and normalized_address == local_addr.lower().strip():
            return True
    
    return False

# Load environment variables before importing other modules
load_env_file()

chromedriver_autoinstaller.install()

# ---[ Enhanced AI Configuration ]---
import sys
import os
# Add project root to Python path for config import
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
from config.config import OPENAI_API_KEY, ANTHROPIC_API_KEY

# Enhanced AI models for better intelligence
AI_MODELS = {
    'gpt4': 'gpt-4',
    'gpt4_vision': 'gpt-4o', 
    'gpt35': 'gpt-3.5-turbo',
    'claude': 'claude-3-sonnet-20240229'
}

# ---[ VERBOSE MODE CONFIGURATION ]---
VERBOSE_MODE = False  # Set to True for detailed output, False for clean output

try:
    if OPENAI_API_KEY and ANTHROPIC_API_KEY:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        AI_ENABLED = True
        print("🤖 Enhanced AI agents enabled with API keys")
    else:
        print("⚠️ AI agents disabled: Missing API keys")
        print(f"   OPENAI_API_KEY: {'✅ Set' if OPENAI_API_KEY else '❌ Missing'}")
        print(f"   ANTHROPIC_API_KEY: {'✅ Set' if ANTHROPIC_API_KEY else '❌ Missing'}")
        AI_ENABLED = False
        openai_client = None
        anthropic_client = None
except Exception as e:
    print(f"⚠️ AI agents disabled: {e}")
    AI_ENABLED = False
    openai_client = None
    anthropic_client = None

# ---[ TOR Rotation Functions ]---
def rotate_tor_identity():
    """Rotate TOR identity to get a new exit node"""
    try:
        with socket.create_connection(("127.0.0.1", TOR_CONTROL_PORT), timeout=CONTROL_TIMEOUT) as s:
            s.sendall(f'AUTHENTICATE "{TOR_CONTROL_PASSWORD}"\r\n'.encode())
            if b'250' not in s.recv(1024):
                print("❌ Tor auth failed.")
                return False
            s.sendall(b'SIGNAL NEWNYM\r\n')
            s.recv(1024)
            print("🔄 Tor identity rotated.")
            return True
    except Exception as e:
        print(f"❌ Tor control error: {e}")
        return False

# ---[ Speed Optimized Config ]---
TOR_PROXY = "socks5://127.0.0.1:9050"
TOR_SOCKS_PROXY = "socks5h://127.0.0.1:9050"
TOR_CONTROL_PORT = 9051
TOR_CONTROL_PASSWORD = 'Jasoncomer1$'
CONTROL_TIMEOUT = 40
ROTATE_EVERY_N = 33  # More frequent rotation for better anonymity

# ---[ MULTI-INPUT FILE CONFIGURATION ]---
# Primary input file for new URLs
PRIMARY_INPUT_CSV = "data/raw/human_trafficking_alerts_0702.csv"

# Secondary input source: Google Sheet URLs (column F)
USE_GOOGLE_SHEET_AS_SECONDARY = True

# Legacy secondary input file (kept for fallback)
SECONDARY_INPUT_CSV = "data/raw/crypto_addresses_fast.csv"

# Input rotation settings
ENABLE_INPUT_ROTATION = True
ROTATE_INPUT_EVERY_N_URLS = 500  # Switch input files every 500 URLs
CSAM_ONLY_FROM_SECONDARY = True  # Only process CSAM sites from secondary input

# Current input tracking
current_input_file = PRIMARY_INPUT_CSV
urls_since_input_rotation = 0
input_rotation_lock = threading.Lock()

# Resume configuration - set to start from a specific row (1-based indexing)
# Set START_FROM_ROW = 1 to start from the beginning
# Set START_FROM_ROW = N to start from row N (where N is the row number in the CSV)
START_FROM_ROW = 1  # Currently set to start from row 3233
OUTPUT_CSV = "data/raw/crypto_addresses_fast.csv"
SCREENSHOT_DIR = "data/raw/screenshots_fast"
CAPTCHA_FAILED_CSV = "data/raw/captcha_failed_fast.csv"
UNSOLVED_DIR = "data/raw/unsolved_captchas_fast"
MAX_DEPTH = 4  # Reduced for speed
PAGE_LOAD_TIMEOUT = 45  # Reduced to avoid Chrome internal limits
MAX_WORKERS = 1  # Reduced to prevent DevTools port conflicts on macOS
FAST_MODE = True
HEADLESS_MODE = False  # Changed to False to watch browser
BATCH_SIZE = 20  # Batch CSV writes

# Enhanced safety and reliability settings
MAX_RETRIES = 5  # Increased retries for better success rate
SAVE_INTERVAL = 25  # More frequent saves
BACKUP_INTERVAL = 50  # More frequent backups
MEMORY_LIMIT = 100  # Max URLs in memory before processing

# ---[ GOOGLE SHEET DUPLICATE CHECKING CONFIG ]---
GOOGLE_SHEET_SERVICE_ACCOUNT = '/Users/jasoncomer/Desktop/blockscout_python/ofac-automation-52b699a4735a.json'
GOOGLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/14ApkAb5jHTv-wzP8CFJTax31UXYkFb0ebDDd6Bg1EC8/edit#gid=1998112463'
GOOGLE_SHEET_NAME = 'darknet_automation'
GOOGLE_SHEET_CHECK_INTERVAL = 50  # Check every 50 URLs
DUPLICATE_DIVERT_CSV = 'data/raw/duplicated_address_0702.csv'

# ---[ HUMAN TRAFFICKING DETECTION CONFIGURATION ]---
# Priority thresholds for human trafficking alerts
TRAFFICKING_CRITICAL_THRESHOLD = 15  # Score for CRITICAL priority
TRAFFICKING_HIGH_THRESHOLD = 10      # Score for HIGH priority  
TRAFFICKING_MEDIUM_THRESHOLD = 5     # Score for MEDIUM priority

# Alert file for human trafficking detections
HUMAN_TRAFFICKING_ALERTS_CSV = "data/raw/human_trafficking_alerts_0702.csv"

# Alert file for scam detections
SCAM_ALERTS_CSV = "data/raw/scam_alerts.csv"

# Enhanced detection settings
ENABLE_TRAFFICKING_DETECTION = True
ENABLE_SCAM_DETECTION = True
ENABLE_IMMEDIATE_ALERTS = True
ENABLE_PATTERN_LOGGING = True

# Weight multipliers for different types of indicators
TRAFFICKING_WEIGHTS = {
    "age_specific": 5.0,      # Highest weight for age indicators
    "dehumanizing": 4.0,      # High weight for dehumanizing terms
    "service_terms": 4.0,     # High weight for service indicators
    "operational": 3.5,       # Medium-high weight for operational terms
    "platforms": 3.0,         # Medium weight for platform identifiers
    "payment_security": 2.5   # Medium weight for payment/security terms
}

# ---[ IMMEDIATE PROCESSING CONFIGURATION ]---
# Enable immediate processing for high-priority human trafficking content
ENABLE_IMMEDIATE_PROCESSING = False
IMMEDIATE_PROCESSING_THRESHOLD = 10  # Score threshold for immediate processing

# Retry list configuration - only for failed captcha/login
RETRY_LIST_CSV = "data/raw/retry_failed_captcha_login.csv"
ENABLE_RETRY_LIST = True
RETRY_REASONS = ["captcha_failed", "login_failed", "registration_failed", "form_submission_failed"]

# Enhanced speed optimization settings
SHORT_WAIT = 3.0  # Increased from 2.0 to 3.0 for better title loading
MEDIUM_WAIT = 4.0  # Increased from 3.0 to 4.0 for conservative approach
LONG_WAIT = 10.0   # Increased from 8.0 to 10.0 for extra safety
# Screenshots are ALWAYS taken for every address found

# Thread-safe CSV writing
csv_lock = threading.Lock()
results_queue = Queue()

# Track addresses we have already saved during this run to avoid duplicates across threads
global_seen_lock = threading.Lock()
global_seen_addresses = set()

# Track unique (url, address) pairs to avoid duplicate rows in main CSV
seen_pairs = set()

# Root title tracking - store the first title seen for each onion domain
root_titles_lock = threading.Lock()
root_titles = {}  # {domain: title}

# TOR rotation tracking
tor_rotation_lock = threading.Lock()
urls_since_rotation = 0

# Multi-vendor markets to skip
MULTI_VENDOR_MARKETS = [
    "torbuy", "undermarket", "alphabay", "dream", "empire", "monopoly",
    "versus", "cannazon", "dark0de", "berlusconi", "cryptonia", "nightmare",
    "silkroad", "agora", "evolution", "nucleus", "abraxas", "middleearth",
    "outlaw", "blackbank", "sheep", "hydra", "ramp", "omerta", "valhalla",
    "samsara", "cyberpunk", "apollon", "deepdotweb", "darknetlive"
]

SKIPPED_MARKETS_CSV = "data/raw/skipped_multi_vendor_markets_fast.csv"
DISCOVERED_LINKS_CSV = "data/raw/discovered_links_fast.csv"  # For external .onion link discovery
DEBUG_DIR = "data/raw/debug_html"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(UNSOLVED_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

# Optimized regex patterns
PATTERNS = {
    "BTC": re.compile(r"\b(bc1[a-zA-Z0-9]{25,90}|[13][a-zA-HJ-NP-Z0-9]{25,39})\b"),
    "ETH": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "XMR": re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b"),
    "TRON": re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b"),
    "SOL": re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{44}\b")  # Solana addresses are exactly 44 characters
}

KEYWORDS = ["buy", "checkout", "payment", "wallet", "order", "access", "rent", "trial", "continue", "enter"]

# Category classification keywords
CATEGORY_KEYWORDS = {
    # HUMAN TRAFFICKING - HIGHEST PRIORITY
    "human trafficking": [
        # Age-specific exploitation
        "13yo", "14yo", "15yo", "16yo", "17yo", "preteen", "underage", "barely legal", "lolita",
        "young girl", "teen girl", "little one", "schoolgirl", "child escort",
        
        # Dehumanizing terms
        "fresh girl", "new flower", "clean meat", "unbroken", "no scars", "first time", "tight", "virgin",
        "package ready", "premium stock", "womb ready", "fresh fruit",
        
        # Ethnic targeting
        "asian teen", "russian girl", "latina slave", "african girl", "thai escort", "filipina teen",
        "eastern european girl", "mexican slave", "domestic servant", "obedient slave",
        
        # Service terms
        "rent girl", "order girl", "escort delivery", "overnight stay", "bondage available",
        "no condom", "custom order", "abduction service", "white slave market",
        
        # Operational terms
        "delivery route", "border crossing", "smuggler", "customs bribe", "no passport",
        "encrypted contact", "dark slave market", "onion trafficking",
        
        # Platform identifiers
        "sex.onion", "childmarket.onion", "escort.onion", "lolita.onion", "slavehub", "humanhub",
        
        # Payment/security
        "bitcoin only", "pgp secure", "escort visa", "id fake",
        
        # Additional trafficking indicators
        "traffic", "slave", "prostitution", "escort", "human trafficking", "sex trafficking",
        "forced labor", "domestic servitude", "sexual exploitation", "child exploitation",
        "minor exploitation", "youth exploitation", "teen exploitation", "girl exploitation",
        "boy exploitation", "child prostitution", "teen prostitution", "minor prostitution",
        "forced prostitution", "coerced prostitution", "trafficked person", "trafficked girl",
        "trafficked boy", "trafficked child", "trafficked teen", "trafficked minor",
        "victim of trafficking", "trafficking victim", "exploitation victim", "abuse victim",
        "sexual abuse", "child abuse", "teen abuse", "minor abuse", "youth abuse",
        "commercial sexual exploitation", "csec", "commercial sex", "sex work", "prostitution",
        "escort service", "escort agency", "escort business", "escort company", "escort provider",
        "escort supplier", "escort vendor", "escort seller", "escort trader", "escort dealer",
        "escort broker", "escort agent", "escort manager", "escort operator", "escort owner",
        "escort proprietor", "escort entrepreneur", "escort business owner", "escort service provider",
        "escort service agency", "escort service business", "escort service company", "escort service vendor",
        "escort service seller", "escort service trader", "escort service dealer", "escort service broker",
        "escort service agent", "escort service manager", "escort service operator", "escort service owner",
        "escort service proprietor", "escort service entrepreneur", "escort service business owner"
    ],
    
    # CSAM - SECOND HIGHEST PRIORITY
    "csam": [
        "child", "loli", "boys", "girls", "teen", "young", "minor", "child porn", "childxxx", 
        "preteen", "lolita", "loliporn", "child exploitation", "minor exploitation", "youth exploitation",
        "teen exploitation", "girl exploitation", "boy exploitation", "child prostitution", 
        "teen prostitution", "minor prostitution", "forced prostitution", "coerced prostitution",
        "trafficked person", "trafficked girl", "trafficked boy", "trafficked child", "trafficked teen",
        "trafficked minor", "victim of trafficking", "trafficking victim", "exploitation victim",
        "abuse victim", "sexual abuse", "child abuse", "teen abuse", "minor abuse", "youth abuse",
        "commercial sexual exploitation", "csec", "commercial sex", "sex work", "prostitution",
        "escort service", "escort agency", "escort business", "escort company", "escort provider",
        "escort supplier", "escort vendor", "escort seller", "escort trader", "escort dealer",
        "escort broker", "escort agent", "escort manager", "escort operator", "escort owner",
        "escort proprietor", "escort entrepreneur", "escort business owner", "escort service provider",
        "escort service agency", "escort service business", "escort service company", "escort service vendor",
        "escort service seller", "escort service trader", "escort service dealer", "escort service broker",
        "escort service agent", "escort service manager", "escort service operator", "escort service owner",
        "escort service proprietor", "escort service entrepreneur", "escort service business owner"
    ],
    
    # Additional categories with enhanced detection
    "carding": [
        "card", "cc", "dumps", "cvv", "credit", "debit", "stripe", "paypal", "carding", "carder", "dump", "track",
        "ccpp", "cloned cards", "paypal accounts", "credit card", "debit card", "card shop", "card vendor",
        "card seller", "card market", "card store", "card business", "card service", "card provider",
        "card supplier", "card trader", "card dealer", "card broker", "card agent", "card manager",
        "card operator", "card owner", "card proprietor", "card entrepreneur", "card business owner",
        "cc shop", "cc vendor", "cc seller", "cc market", "cc store", "cc business", "cc service",
        "cc provider", "cc supplier", "cc trader", "cc dealer", "cc broker", "cc agent", "cc manager",
        "cc operator", "cc owner", "cc proprietor", "cc entrepreneur", "cc business owner",
        "credit card shop", "credit card vendor", "credit card seller", "credit card market",
        "debit card shop", "debit card vendor", "debit card seller", "debit card market",
        "paypal account", "paypal accounts", "paypal shop", "paypal vendor", "paypal seller",
        "paypal market", "paypal store", "paypal business", "paypal service", "paypal provider",
        "stripe account", "stripe accounts", "stripe shop", "stripe vendor", "stripe seller",
        "stripe market", "stripe store", "stripe business", "stripe service", "stripe provider"
    ],
    "counterfeit": ["fake", "replica", "counterfeit", "clone", "copy", "imitation", "knockoff", "replicas"],
    "drugs": ["drug", "cocaine", "heroin", "weed", "cannabis", "opioid", "pill", "meth", "amphetamine", "opioids"],
    "weapons": ["gun", "weapon", "rifle", "pistol", "ammo", "explosive", "bomb", "ghost gun", "military grade"],
    "hack": ["hack", "exploit", "vulnerability", "ddos", "malware", "ransomware", "hacking", "cracker"],
    "marketplace": ["market", "shop", "store", "vendor", "seller", "buy", "marketplace"],
    "money laundering": ["mixer", "tumbler", "launder", "clean", "wash", "money laundering"],
    "extortion": ["extort", "blackmail", "sextortion", "threat", "extortion"],
    "bio weapons": ["bio", "biological", "virus", "bacteria", "toxin", "bio weapon"],
    "money services business": ["money transfer", "wire", "remittance", "money service", "msb"],
    "counterfeit documents": ["fake id", "fake passport", "fake license", "document", "id card"],
    "counterfeit money": ["fake money", "counterfeit money", "fake dollar", "fake euro"],
    "darknet forum profile": ["forum", "profile", "user", "member", "darknet forum"],
    "ddos": ["ddos", "distributed denial", "attack", "botnet"],
    "explosives": ["explosive", "bomb", "dynamite", "c4", "rdx", "tnt"],
    "extremist donation": ["extremist", "terror", "donation", "fund", "jihad"],
    "human organ trafficking": ["organ", "kidney", "liver", "organ trafficking"],
    "knockoff vendor": ["knockoff", "replica", "fake", "copy", "imitation"],
    "malware vendor": ["malware", "virus", "trojan", "spyware", "malware vendor"],
    "mercenary": ["mercenary", "hitman", "assassin", "contract killer"],
    "mining botnet": ["mining", "botnet", "crypto mining", "miner"],
    "mixer": ["mixer", "tumbler", "mix", "clean", "wash"],
    "murder for hire": ["murder", "hitman", "assassin", "kill", "murder for hire"],
    "nuclear": ["nuclear", "atomic", "radioactive", "uranium", "plutonium"],
    "ofac sanctioned": ["ofac", "sanctioned", "banned", "blocked"],
    "pirated media": ["pirate", "torrent", "download", "movie", "software", "game"],
    "precursor research chemicals": ["precursor", "chemical", "research chemical", "rc"],
    "privacy": ["privacy", "anonymous", "secure", "private"],
    "raidforums profile": ["raidforums", "forum profile", "user"],
    "ransomware": ["ransomware", "encrypt", "decrypt", "ransom"],
    "scam": [
        "scam", "fake", "fraud", "phishing", "scammer",
        # Bitcoin generators and exploits
        "bitcoin generator", "btc generator", "bitcoin exploit", "btc exploit",
        "bitcoin hack", "btc hack", "bitcoin cracker", "btc cracker",
        "bitcoin multiplier", "btc multiplier", "free bitcoin generator",
        "bitcoin doubler", "btc doubler", "bitcoin mining generator",
        "fake bitcoin generator",
        # Private key scams
        "private key generator", "private key hack", "private key exploit",
        "private key cracker", "private key finder", "private key brute force",
        "private key recovery", "private key extractor", "private key stealer",
        "private key grabber", "private key scanner", "private key database",
        "private key dump", "private key leak", "private key crack",
        "private key brute", "private key force", "private key attack",
        "private key vulnerability", "private key hack tool", "private key cracking",
        "private key breaking", "private key stealing", "private key extraction",
        "private key recovery tool", "private key shop", "private key market",
        # Wallet scams
        "hacked wallets", "walets", "stolen wallets", "wallet market",
        "wallet shop", "bitcoin wallet shop", "buy stolen bitcoin wallets",
        "stolen bitcoin wallets", "wallet database", "wallet dump",
        "wallet leak", "wallet cracker", "wallet hack", "wallet hacker", "wallet hackers", "wallet exploit",
        "wallet generator", "wallet recovery", "wallet stealer",
        "wallet grabber", "wallet scanner", "wallet brute force",
        # Quantum mining scams
        "quantum miner", "quantum mining", "quantum bitcoin miner",
        "quantum crypto miner", "quantum mining software", "quantum mining tool",
        "quantum mining generator", "quantum mining hack", "quantum mining exploit",
        # Other generators
        "free money generator", "money generator", "crypto generator",
        "ethereum generator", "eth generator", "monero generator",
        "xmr generator", "tron generator", "solana generator",
        "sol generator", "altcoin generator", "coin generator",
        # Mining scams
        "cloud mining scam", "fake mining", "mining scam", "mining generator",
        "mining hack", "mining exploit", "mining cracker", "mining stealer",
        # Exchange and trading scams
        "fake exchange", "exchange scam", "trading bot scam", "bot scam",
        "auto trader scam", "trading generator", "profit generator",
        "income generator", "money maker", "get rich quick",
        # Recovery scams
        "recovery service", "recovery tool", "recovery software",
        "lost bitcoin recovery", "stolen crypto recovery", "hacked account recovery",
        # Phishing and fake sites
        "phishing", "fake wallet", "fake exchange", "fake mining",
        "fake generator", "fake hack", "fake exploit", "fake cracker",
        # Scam databases and lists
        "scam list", "scam database", "scam dump", "scam leak",
        
        # Multiplier scams (100x, 1000x, etc.)
        "100x your coins", "1000x your coins", "10x your coins", "50x your coins",
        "200x your coins", "500x your coins", "multiply your coins", "multiply your bitcoin",
        "multiply your crypto", "multiply your money", "multiply your investment",
        "double your coins", "triple your coins", "quadruple your coins",
        "multiply coins", "multiply bitcoin", "multiply crypto", "multiply money",
        "multiply investment", "multiply funds", "multiply balance",
        "your coins in 24 hours", "your bitcoin in 24 hours", "your crypto in 24 hours",
        "coins in 24 hours", "bitcoin in 24 hours", "crypto in 24 hours",
        "officially hidden service", "hidden service anonymous", "anonymous service"
    ],
    "seized funds": ["seized", "confiscated", "frozen", "funds"],
    "sextortion": ["sextortion", "blackmail", "nude", "photo"],
    "spam": ["spam", "bulk", "mass", "email"],
    "spoofing": ["spoof", "fake", "impersonate", "pretend"],
    "state secrets": ["secret", "classified", "government", "intelligence"],
    "terrorism": ["terror", "jihad", "extremist", "terrorism"],
    "victim": ["victim", "target", "person", "individual"],
    "fake identification": ["fake id", "fake passport", "fake license", "identification"],
    
    # More specific, phrase-based keywords to reduce false positives
    "precursor purchaser": ["buy precursor", "purchase precursor", "order precursor chemicals"],
    "precursor receiver": ["receive precursor", "precursor delivery", "precursor shipment"],
    "csam consumer": ["csam viewer", "csam access", "watch child porn", "view child porn", "csam gallery"],
    "csam receiver": ["receive csam", "get csam", "download csam", "csam delivery", "csam download"],
    "darknet sender": ["darknet sender", "darknet shipper", "ship from darknet"],
    "terrorism sender": ["fund terrorism", "send funds to terror", "terrorist financing sender"],
    "terrorism receiver": ["receive funds for terrorism", "terrorist financing receiver"],
    "exotic animal trafficking": ["exotic animal trafficking", "buy exotic animals", "wildlife trafficking"]
}

def log_skipped_market(url, reason="Multi-vendor market"):
    """Log skipped markets"""
    timestamp = datetime.utcnow().isoformat()
    write_to_csv_threadsafe([get_base_domain(url), reason, timestamp], SKIPPED_MARKETS_CSV)

def log_discovered_links(base_url, links, link_type="internal"):
    """Log discovered links to CSV"""
    timestamp = datetime.utcnow().isoformat()
    for link in links:
        write_to_csv_threadsafe([get_base_domain(base_url), link, link_type, timestamp], DISCOVERED_LINKS_CSV)

# Fast address validators
def is_valid_btc_address(addr):
    if addr.startswith("bc1"):
        return 14 <= len(addr) <= 74
    try:
        return base58.b58decode_check(addr)[0] in (0x00, 0x05)
    except:
        return False

def is_valid_eth_address(addr):
    return (addr.startswith("0x") and len(addr) == 42 and
            (addr.islower() or addr.isupper() or is_checksum_address(addr)))

def is_valid_tron_address(addr):
    try:
        return base58.b58decode_check(addr)[0] == 0x41
    except:
        return False

def is_valid_solana_address(addr):
    """Strict Solana address validation"""
    # Solana addresses must be exactly 44 characters
    if len(addr) != 44:
        return False
    
    # Must only contain base58 characters
    valid_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    if not all(c in valid_chars for c in addr):
        return False
    
    # Try to validate with solders library
    try:
        pubkey = Pubkey.from_string(addr)
        return str(pubkey) == addr
    except:
        return False

def is_valid_xmr_address(addr):
    return addr.startswith("4") and len(addr) == 95

def extract_addresses_fast(text):
    """Enhanced address extraction with false positive filtering and dynamic content detection"""
    found = []
    
    # Standard regex extraction
    for chain, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        
        # Filter out common false positives
        filtered_matches = []
        for match in matches:
            # Skip if it's just repeated characters (like "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            if len(set(match)) <= 3:
                continue
                
            # Skip if it contains obvious non-address patterns
            if any(skip in match.lower() for skip in ['example', 'test', 'demo', 'sample', 'placeholder']):
                continue
                
            # Skip if it's too repetitive
            if len(match) > 10 and match.count(match[0]) > len(match) * 0.8:
                continue
                
            filtered_matches.append(match)
        
        # Apply chain-specific validation
        if chain == "BTC":
            filtered_matches = [m for m in filtered_matches if is_valid_btc_address(m)]
        elif chain == "ETH":
            filtered_matches = [m for m in filtered_matches if is_valid_eth_address(m)]
        elif chain == "TRON":
            filtered_matches = [m for m in filtered_matches if is_valid_tron_address(m)]
        elif chain == "SOL":
            filtered_matches = [m for m in filtered_matches if is_valid_solana_address(m)]
        elif chain == "XMR":
            filtered_matches = [m for m in filtered_matches if is_valid_xmr_address(m)]
            
        for match in filtered_matches:
            found.append((chain, match))
    
    # Enhanced extraction: Look for addresses in JavaScript variables
    btc_regex = r"(bc1[a-zA-Z0-9]{25,90}|[13][a-zA-HJ-NP-Z0-9]{25,39})"
    js_patterns = [
        r'["\']' + btc_regex + r'["\']',  # BTC in quotes
        r'["\'](0x[a-fA-F0-9]{40})["\']',  # ETH in quotes
        r'["\'](4[0-9AB][1-9A-HJ-NP-Za-km-z]{93})["\']',  # XMR in quotes
        r'["\'](T[1-9A-HJ-NP-Za-km-z]{33})["\']',  # TRON in quotes
        r'["\']([1-9A-HJ-NP-Za-km-z]{44})["\']',  # SOL in quotes
        r'address["\']?\s*[:=]\s*["\']' + btc_regex + r'["\']',  # BTC with address key
        r'wallet["\']?\s*[:=]\s*["\'](0x[a-fA-F0-9]{40})["\']',  # ETH with wallet key
        r'btc["\']?\s*[:=]\s*["\']' + btc_regex + r'["\']',  # BTC with btc key
        r'eth["\']?\s*[:=]\s*["\'](0x[a-fA-F0-9]{40})["\']',  # ETH with eth key
    ]
    
    for pattern in js_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Determine chain type
            if match.startswith(('1', '3', 'bc1')):
                if is_valid_btc_address(match):
                    found.append(('BTC', match))
            elif match.startswith('0x') and len(match) == 42:
                if is_valid_eth_address(match):
                    found.append(('ETH', match))
            elif match.startswith('4') and len(match) == 95:
                if is_valid_xmr_address(match):
                    found.append(('XMR', match))
            elif match.startswith('T') and len(match) == 34:
                if is_valid_tron_address(match):
                    found.append(('TRON', match))
            elif len(match) == 44:
                if is_valid_solana_address(match):
                    found.append(('SOL', match))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_found = []
    for chain, addr in found:
        if addr not in seen:
            seen.add(addr)
            unique_found.append((chain, addr))
    
    return unique_found

def extract_addresses_enhanced(text, url="", title=""):
    """Enhanced address extraction with multiple methods and context awareness"""
    found = []
    
    if not ENABLE_ENHANCED_ADDRESS_EXTRACTION:
        return extract_addresses_fast(text)
    
    # Method 1: Enhanced regex patterns with multiple variations
    for chain, patterns in ENHANCED_PATTERNS.items():
        for pattern in patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Filter out common false positives
                if is_valid_address_enhanced(chain, match):
                    found.append((chain, match))
    
    # Method 2: HTML attribute extraction
    html_addresses = extract_addresses_from_html_attributes(text)
    found.extend(html_addresses)
    
    # Method 3: JavaScript variable extraction
    js_addresses = extract_addresses_from_javascript(text)
    found.extend(js_addresses)
    
    # Method 4: Meta tag extraction
    meta_addresses = extract_addresses_from_meta_tags(text)
    found.extend(meta_addresses)
    
    # Method 5: Context-aware extraction
    if ENABLE_CONTEXT_AWARE_EXTRACTION:
        context_addresses = extract_addresses_with_context(text, url, title)
        found.extend(context_addresses)
    
    # Method 6: Deep content analysis
    deep_addresses = extract_addresses_deep_analysis(text)
    found.extend(deep_addresses)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_found = []
    for chain, addr in found:
        if addr not in seen:
            seen.add(addr)
            unique_found.append((chain, addr))
    
    return unique_found

def is_valid_address_enhanced(chain, addr):
    """Enhanced address validation with better filtering"""
    # Skip if it's just repeated characters
    if len(set(addr)) <= 3:
        return False
    
    # Skip if it contains obvious non-address patterns
    if any(skip in addr.lower() for skip in ['example', 'test', 'demo', 'sample', 'placeholder']):
        return False
    
    # Skip if it's too repetitive
    if len(addr) > 10 and addr.count(addr[0]) > len(addr) * 0.8:
        return False
    
    # Chain-specific validation
    if chain == "BTC":
        return is_valid_btc_address(addr)
    elif chain == "ETH":
        return is_valid_eth_address(addr)
    elif chain == "TRON":
        return is_valid_tron_address(addr)
    elif chain == "SOL":
        return is_valid_solana_address(addr)
    elif chain == "XMR":
        return is_valid_xmr_address(addr)
    
    return True

def extract_addresses_from_html_attributes(text):
    """Extract addresses from HTML data attributes"""
    addresses = []
    
    # Look for data attributes containing addresses
    data_patterns = [
        r'data-address=["\']([^"\']+)["\']',
        r'data-wallet=["\']([^"\']+)["\']',
        r'data-btc=["\']([^"\']+)["\']',
        r'data-eth=["\']([^"\']+)["\']',
        r'data-xmr=["\']([^"\']+)["\']',
        r'data-tron=["\']([^"\']+)["\']',
        r'data-sol=["\']([^"\']+)["\']',
    ]
    
    for pattern in data_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Determine chain type and validate
            if match.startswith(('1', '3', 'bc1')):
                if is_valid_btc_address(match):
                    addresses.append(('BTC', match))
            elif match.startswith('0x') and len(match) == 42:
                if is_valid_eth_address(match):
                    addresses.append(('ETH', match))
            elif match.startswith('4') and len(match) == 95:
                if is_valid_xmr_address(match):
                    addresses.append(('XMR', match))
            elif match.startswith('T') and len(match) == 34:
                if is_valid_tron_address(match):
                    addresses.append(('TRON', match))
            elif len(match) == 44:
                if is_valid_solana_address(match):
                    addresses.append(('SOL', match))
    
    return addresses

def extract_addresses_from_javascript(text):
    """Extract addresses from JavaScript code"""
    addresses = []
    
    # Look for JavaScript variable assignments
    js_patterns = [
        r'var\s+\w+\s*=\s*["\']([^"\']+)["\']',
        r'let\s+\w+\s*=\s*["\']([^"\']+)["\']',
        r'const\s+\w+\s*=\s*["\']([^"\']+)["\']',
        r'\w+\s*=\s*["\']([^"\']+)["\']',
    ]
    
    for pattern in js_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Determine chain type and validate
            if match.startswith(('1', '3', 'bc1')):
                if is_valid_btc_address(match):
                    addresses.append(('BTC', match))
            elif match.startswith('0x') and len(match) == 42:
                if is_valid_eth_address(match):
                    addresses.append(('ETH', match))
            elif match.startswith('4') and len(match) == 95:
                if is_valid_xmr_address(match):
                    addresses.append(('XMR', match))
            elif match.startswith('T') and len(match) == 34:
                if is_valid_tron_address(match):
                    addresses.append(('TRON', match))
            elif len(match) == 44:
                if is_valid_solana_address(match):
                    addresses.append(('SOL', match))
    
    return addresses

def extract_addresses_from_meta_tags(text):
    """Extract addresses from meta tags"""
    addresses = []
    
    # Look for meta tags containing addresses
    meta_patterns = [
        r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*>',
        r'<meta[^>]*name=["\'](?:wallet|address|btc|eth|xmr|tron|sol)["\'][^>]*content=["\']([^"\']+)["\'][^>]*>',
    ]
    
    for pattern in meta_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Determine chain type and validate
            if match.startswith(('1', '3', 'bc1')):
                if is_valid_btc_address(match):
                    addresses.append(('BTC', match))
            elif match.startswith('0x') and len(match) == 42:
                if is_valid_eth_address(match):
                    addresses.append(('ETH', match))
            elif match.startswith('4') and len(match) == 95:
                if is_valid_xmr_address(match):
                    addresses.append(('XMR', match))
            elif match.startswith('T') and len(match) == 34:
                if is_valid_tron_address(match):
                    addresses.append(('TRON', match))
            elif len(match) == 44:
                if is_valid_solana_address(match):
                    addresses.append(('SOL', match))
    
    return addresses

def extract_addresses_with_context(text, url, title):
    """Extract addresses using context awareness"""
    addresses = []
    
    # Combine all text for context analysis
    context_text = f"{url} {title} {text}".lower()
    
    # Check for payment/wallet context
    has_payment_context = any(keyword in context_text for keyword in CONTEXT_KEYWORDS['payment'])
    has_wallet_context = any(keyword in context_text for keyword in CONTEXT_KEYWORDS['wallet'])
    has_crypto_context = any(keyword in context_text for keyword in CONTEXT_KEYWORDS['crypto'])
    
    # If we have strong context, be more aggressive in extraction
    if has_payment_context or has_wallet_context or has_crypto_context:
        # Use more lenient patterns for high-context pages
        for chain, patterns in ENHANCED_PATTERNS.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                for match in matches:
                    # More lenient validation for high-context pages
                    if is_valid_address_context_aware(chain, match, context_text):
                        addresses.append((chain, match))
    
    return addresses

def is_valid_address_context_aware(chain, addr, context_text):
    """Context-aware address validation"""
    # Basic validation first
    if not is_valid_address_enhanced(chain, addr):
        return False
    
    # Additional context-based validation
    # Skip if address appears in a list of examples
    if 'example' in context_text and addr in context_text:
        return False
    
    # Skip if it's clearly a placeholder
    if any(placeholder in context_text for placeholder in ['placeholder', 'demo', 'test']):
        return False
    
    return True

def extract_addresses_deep_analysis(text):
    """Deep content analysis for hidden addresses"""
    addresses = []
    
    # Look for addresses in comments
    comment_patterns = [
        r'<!--\s*([^>]+)\s*-->',
        r'/\*([^*]+)\*/',
        r'//\s*([^\n]+)',
    ]
    
    for pattern in comment_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Extract addresses from comments
            for chain, patterns in ENHANCED_PATTERNS.items():
                for addr_pattern in patterns:
                    addr_matches = addr_pattern.findall(match)
                    for addr in addr_matches:
                        if is_valid_address_enhanced(chain, addr):
                            addresses.append((chain, addr))
    
    # Look for addresses in script tags
    script_pattern = r'<script[^>]*>(.*?)</script>'
    script_matches = re.findall(script_pattern, text, re.DOTALL | re.IGNORECASE)
    
    for script in script_matches:
        for chain, patterns in ENHANCED_PATTERNS.items():
            for addr_pattern in patterns:
                addr_matches = addr_pattern.findall(script)
                for addr in addr_matches:
                    if is_valid_address_enhanced(chain, addr):
                        addresses.append((chain, addr))
    
    return addresses

def normalize_url(url):
    """Normalize URL for deduplication"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def get_base_domain(url):
    """Extract just the base domain from a URL for display purposes"""
    try:
        parsed = urlparse(url)
        return parsed.hostname or url
    except:
        return url

def get_internal_links_fast(soup, base_url):
    """Enhanced internal link extraction with payment/wallet page prioritization"""
    links = []
    payment_links = []
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        
        # Check if it's an internal link
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.append(full_url)
            
            # Prioritize payment/wallet related links
            href_lower = href.lower()
            if any(keyword in href_lower for keyword in [
                '/buy', '/payment', '/wallet', '/address', '/checkout', 
                '/order', '/purchase', '/pay', '/crypto', '/bitcoin',
                '/btc', '/eth', '/xmr', '/tron', '/sol', '/deposit',
                '/withdraw', '/send', '/receive', '/fund', '/balance'
            ]):
                payment_links.append(full_url)
    
    # Remove duplicates and prioritize payment links
    unique_links = list(set(links))
    unique_payment_links = list(set(payment_links))
    
    # Return payment links first, then other links
    return unique_payment_links + [link for link in unique_links if link not in unique_payment_links]

def sanitize_filename(s):
    """Sanitize a string to be safe for filenames"""
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', s)[:150]

def get_or_set_root_title(url, current_title):
    """Get the root title for a domain, or set it if this is the first visit
    This provides consistent site context instead of random page titles like 'Order #123222'
    """
    try:
        # Extract the onion domain from the URL
        parsed_url = urlparse(url)
        domain = parsed_url.hostname
        
        if not domain or not domain.endswith('.onion'):
            return current_title  # Not an onion URL, use current title
        
        # Use thread-safe access to root_titles
        with root_titles_lock:
            if domain in root_titles:
                # We already have a root title for this domain
                root_title = root_titles[domain]
                if root_title and root_title != "NoTitle":
                    return root_title
                else:
                    # If the stored title is NoTitle but we have a better one now, update it
                    if current_title and current_title != "NoTitle":
                        root_titles[domain] = current_title
                        print(f"🏷️ Updated root title for {domain}: {current_title}")
                        return current_title
                    return root_title
            else:
                # First time visiting this domain, store the title
                if current_title and current_title != "NoTitle":
                    root_titles[domain] = current_title
                    print(f"🏷️ Stored root title for {domain}: {current_title}")
                else:
                    root_titles[domain] = "NoTitle"
                return current_title
    except Exception as e:
        print(f"⚠️ Error in get_or_set_root_title: {e}")
        return current_title

def wait_for_title_to_load(driver, timeout=15):
    """Wait for the page title to change from loading states like 'One moment, please...'"""
    loading_titles = [
        "One moment, please...",
        "Loading...",
        "Please wait...",
        "Loading page...",
        "Page is loading...",
        "Just a moment...",
        "Please wait while we load...",
        "Loading, please wait...",
        "One moment please...",
        "Loading page, please wait...",
        "Please wait while the page loads...",
        "Loading, one moment...",
        "Page loading...",
        "Loading, please wait a moment...",
        "One moment while we load...",
        "Please wait, loading...",
        "Loading, just a moment...",
        "Page is loading, please wait...",
        "Loading, please wait while we prepare...",
        "One moment while we prepare the page..."
    ]
    
    def check_title_loaded(_driver):
        try:
            current_title = _driver.title.strip()
            # Check if title is still a loading state
            for loading_title in loading_titles:
                if loading_title.lower() in current_title.lower():
                    return False
            # Also check if title is empty or very short (likely still loading)
            if not current_title or len(current_title) < 3:
                return False
            return True
        except:
            return False
    
    try:
        WebDriverWait(driver, timeout).until(check_title_loaded)
        return True
    except:
        return False

def wait_for_address_in_dom(driver, timeout=15):
    """Enhanced wait for cryptocurrency addresses to appear in the DOM with dynamic content detection"""
    def check(_driver):
        try:
            # Check current page source
            html = _driver.page_source
            addresses = extract_addresses_fast(html)
            if len(addresses) > 0:
                return True
            
            # Try to trigger dynamic content loading
            try:
                # Scroll to trigger lazy loading
                _driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
                _driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(0.5)
                
                # Try clicking common elements that might reveal addresses
                click_selectors = [
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show')]",
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reveal')]",
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view')]",
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy')]",
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'trial')]",
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'purchase')]",
                    "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'payment')]",
                    "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'wallet')]",
                    "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'address')]",
                    "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy')]",
                    "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'trial')]",
                    "//div[contains(@class, 'payment')]",
                    "//div[contains(@class, 'wallet')]"
                ]
                
                for selector in click_selectors:
                    try:
                        elements = _driver.find_elements(By.XPATH, selector)
                        if elements:
                            elements[0].click()
                            time.sleep(0.5)
                            break
                    except:
                        continue
                
                # Check again after triggering
                html = _driver.page_source
                addresses = extract_addresses_fast(html)
                return len(addresses) > 0
                
            except:
                pass
            
            return False
        except:
            return False
    
    try:
        WebDriverWait(driver, timeout).until(check)
        return True
    except:
        return False

def scroll_entire_page(driver):
    """Scroll the entire page to trigger lazy-loaded content."""
    try:
        # print(f"📜 Scrolling entire page to trigger lazy loading...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1) # Wait for page to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        driver.execute_script("window.scrollTo(0, 0);") # Scroll back to top
        # print(f"✅ Finished scrolling page.")
        return True
    except Exception as e:
        print(f"⚠️ Scrolling failed: {e}")
        return False

def ai_click_interactive_elements(driver):
    """Smart clicking of buttons that likely lead to payment addresses."""
    try:
        print(f"🛒 Smart payment flow navigation activated...")
        clicked_something = False
        
        # First, check if this looks like an e-commerce/payment site
        page_content = driver.page_source.lower()
        
        # E-commerce indicators
        ecommerce_indicators = [
            'price', 'cost', '$', '€', '£', 'bitcoin', 'btc', 'crypto', 'payment',
            'buy', 'purchase', 'order', 'cart', 'checkout', 'wallet', 'address'
        ]
        
        ecommerce_score = sum(1 for indicator in ecommerce_indicators if indicator in page_content)
        
        if ecommerce_score < 3:
            print(f"   -> Low e-commerce score ({ecommerce_score}), skipping button clicks")
            return False
        
        print(f"   -> E-commerce site detected (score: {ecommerce_score}), proceeding with smart navigation")
        
        # Prioritized selectors - safer XPath expressions
        priority_selectors = [
            # Direct payment/purchase actions (highest priority) - safer XPath
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy now')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy now')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'purchase')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'purchase')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'checkout')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'checkout')]",
            
            # Cart actions (medium priority)
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to cart')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to cart')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view cart')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view cart')]",
            
            # Generic buy/order buttons (lower priority)
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'order')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'order')]",
        ]
        
        # Try selectors in priority order
        for i, selector in enumerate(priority_selectors):
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element_text = element.text.strip()[:30]
                        print(f"   -> Clicking priority element: '{element_text}'")
                        
                        # Scroll to element and click
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", element)
                        
                        # Wait for page to load and check if we got to a payment page
                        time.sleep(MEDIUM_WAIT)
                        
                        # Quick check if we're now on a payment page
                        new_content = driver.page_source.lower()
                        payment_indicators = ['payment', 'address', 'wallet', 'bitcoin', 'btc', 'crypto', 'send']
                        payment_score = sum(1 for indicator in payment_indicators if indicator in new_content)
                        
                        if payment_score >= 2:
                            print(f"   -> ✅ Successfully navigated to payment page (score: {payment_score})")
                            return True
                        else:
                            print(f"   -> Page changed but no payment indicators (score: {payment_score})")
                            clicked_something = True
                            # Continue trying other elements
                            
            except Exception as e:
                print(f"   -> Error with selector {i}: {e}")
                continue
        
        # Fallback: try any button with payment-related text
        if not clicked_something:
            print(f"   -> Trying fallback payment buttons...")
            fallback_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'payment')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'payment')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'proceed')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'proceed')]",
            ]
            
            for selector in fallback_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        element = elements[0]
                        if element.is_displayed() and element.is_enabled():
                            element_text = element.text.strip()[:30]
                            print(f"   -> Clicking fallback element: '{element_text}'")
                            driver.execute_script("arguments[0].click();", element)
                            time.sleep(MEDIUM_WAIT)
                            clicked_something = True
                            break
                except Exception:
                    continue
        
        if clicked_something:
            print(f"   -> ✅ Completed smart payment navigation")
        else:
            print(f"   -> ⚠️ No suitable payment buttons found")
            
        return clicked_something
        
    except Exception as e:
        print(f"⚠️ Smart payment navigation failed: {e}")
        return False

def highlight_address_on_screenshot(driver, address, screenshot_path):
    """Highlight the specific address on the screenshot with arrow and box"""
    try:
        # Smart scroll to the address first
        print(f"🎯 Smart scrolling to address: {address[:8]}...{address[-8:]}")
        scroll_success = scroll_to_address(driver, address)
        if scroll_success:
            print(f"✅ Successfully scrolled to address")
        else:
            print(f"⚠️ Could not find address element, taking screenshot anyway")
        
        # Take screenshot after scrolling
        driver.save_screenshot(screenshot_path)
        
        # Try to find the address element on the page
        address_selectors = [
            f"//*[contains(text(), '{address}')]",
            f"//*[contains(., '{address}')]",
            f"//input[@value='{address}']",
            f"//textarea[contains(text(), '{address}')]",
            f"//code[contains(text(), '{address}')]",
            f"//pre[contains(text(), '{address}')]"
        ]
        
        address_element = None
        for selector in address_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    address_element = elements[0]
                    break
            except:
                continue
        
        if address_element:
            # Get element location and size
            location = address_element.location
            size = address_element.size
            
            # Load the screenshot
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)
            
            # Calculate coordinates
            x = location['x']
            y = location['y']
            width = size['width']
            height = size['height']
            
            # Draw red rectangle around address
            draw.rectangle([x, y, x + width, y + height], outline='red', width=3)
            
            # Draw arrow pointing to address
            arrow_x = x + width + 20
            arrow_y = y + height // 2
            
            # Arrow head
            draw.polygon([
                (arrow_x, arrow_y),
                (arrow_x - 10, arrow_y - 5),
                (arrow_x - 10, arrow_y + 5)
            ], fill='red')
            
            # Arrow line
            draw.line([(arrow_x - 10, arrow_y), (arrow_x - 30, arrow_y)], fill='red', width=3)
            
            # Add text label
            try:
                # Try to use a system font
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
            
            label_text = f"Address: {address[:8]}...{address[-8:]}"
            draw.text((arrow_x - 30, arrow_y - 25), label_text, fill='red', font=font)
            
            # Save highlighted screenshot
            img.save(screenshot_path)
            return True
            
        else:
            # If we can't find the element, add a text overlay to the screenshot
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Add text overlay
            text = f"Address found: {address[:10]}...{address[-10:]}"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Position text at top of image
            x = (img.width - text_width) // 2
            y = 20
            
            # Draw background rectangle
            draw.rectangle([x-10, y-5, x+text_width+10, y+text_height+5], fill='red')
            draw.text((x, y), text, fill='white', font=font)
            
            img.save(screenshot_path)
            return True
            
    except Exception as e:
        print(f"⚠️ Highlighting failed: {e}")
        # If highlighting fails, just save the regular screenshot
        try:
            driver.save_screenshot(screenshot_path)
            return True
        except:
            return False

def process_url_fast(url, worker_id):
    """Fast single URL processor with AI login/registration/captcha"""
    global urls_since_rotation
    driver = None
    results = [] # Initialize results list at the top level of the function
    
    # === ML LEARNING SYSTEM INTEGRATION ===
    ml_extractor = None
    try:
        from ml_learning_system import get_ml_extractor
        ml_extractor = get_ml_extractor()
    except Exception as e:
        print(f"⚠️ [{worker_id}] ML system initialization failed: {e}")
    
    try:
        print(f"🔍 [{worker_id}] Processing: {get_base_domain(url)}")
        
        # === AGENT SYSTEM INTEGRATION ===
        strategy = 1  # Default strategy
        try:
            # Get best strategy for this URL
            strategy = integrated_agents.get_best_strategy(url)
            print(f"🤖 [{worker_id}] Selected strategy: {strategy}")
            
            # Note: record_processing_start method doesn't exist, so we skip it
        except Exception as e:
            print(f"⚠️ [{worker_id}] Agent system error: {e}")
            # Continue processing even if agent system fails
        
        # Check if we need to rotate TOR identity
        with tor_rotation_lock:
            urls_since_rotation += 1
            if urls_since_rotation >= ROTATE_EVERY_N:
                print(f"🔄 [{worker_id}] Rotating TOR identity after {urls_since_rotation} URLs")
                if rotate_tor_identity():
                    urls_since_rotation = 0
                    time.sleep(2)  # Wait for new circuit to establish
                else:
                    print(f"⚠️ [{worker_id}] TOR rotation failed, continuing with current identity")
        
        if is_multi_vendor_market(url):
            print(f"⏭️ [{worker_id}] Skipping multi-vendor market: {get_base_domain(url)}")
            log_skipped_market(url, "Multi-vendor market")
            # Record failure in agent system
            try:
                integrated_agents.record_failure(url, "multi_vendor_market", strategy, worker_id, "multi_vendor_market")
            except:
                pass
            return []
        
        try:
            driver = create_driver(worker_id)
            print(f"🌐 [{worker_id}] Loading page: {get_base_domain(url)}")
            driver.get(url)
            time.sleep(SHORT_WAIT)
        except Exception as e:
            print(f"❌ [{worker_id}] Failed to create driver or load page: {e}")
            # Record failure in agent system
            try:
                integrated_agents.record_failure(url, "driver_creation_failed", strategy, worker_id, "driver_creation")
            except:
                pass
            return []

        # Detect Chrome error page (e.g., ERR_SOCKS_CONNECTION_FAILED) and abort early
        error_markers = [
            "ERR_SOCKS_CONNECTION_FAILED",
            "ERR_TUNNEL_CONNECTION_FAILED",
            "ERR_CONNECTION_TIMED_OUT",
            "This site can't be reached",
            "This site can't be reached.",
            "This site can't be reached",
        ]
        if any(marker.lower() in driver.page_source.lower() for marker in error_markers):
            print(f"⚠️ [{worker_id}] Chrome error page detected for {get_base_domain(url)} – skipping further processing.")
            driver.quit()
            return []

        # Wait for the page title to load properly (not loading states like "One moment, please...")
        print(f"⏳ [{worker_id}] Waiting for page title to load...")
        if wait_for_title_to_load(driver, timeout=15):
            print(f"✅ [{worker_id}] Page title loaded successfully")
        else:
            print(f"⚠️ [{worker_id}] Page title may still be loading, continuing anyway")

        # Get page content after title has loaded
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        current_page_title = soup.title.string.strip() if soup.title else "NoTitle"
        
        # Use root title for consistent site context instead of random page titles
        title = get_or_set_root_title(url, current_page_title)
        
        categories = classify_site(url, title, html)
        
        # Record site features in ML system
        if ml_extractor:
            try:
                # Create SiteFeatures object
                from ml_learning_system import SiteFeatures
                site_features = SiteFeatures(
                    has_cart=len(soup.find_all('button', string=lambda x: x and 'cart' in x.lower())) > 0,
                    has_registration=len(soup.find_all('a', string=lambda x: x and 'register' in x.lower())) > 0,
                    has_login=len(soup.find_all('a', string=lambda x: x and 'login' in x.lower())) > 0,
                    has_search=len(soup.find_all('input', {'type': 'search'})) > 0,
                    has_categories=len(soup.find_all('a', string=lambda x: x and 'category' in x.lower())) > 0,
                    page_type="market" if any(cat in categories for cat in ['marketplace', 'carding']) else "unknown",
                    has_payment_forms=len(soup.find_all('form', string=lambda x: x and 'payment' in x.lower())) > 0,
                    has_bitcoin_mentions='bitcoin' in html.lower(),
                    has_crypto_mentions=any(crypto in html.lower() for crypto in ['crypto', 'bitcoin', 'ethereum', 'monero']),
                    has_wallet_mentions='wallet' in html.lower(),
                    text_length=len(soup.get_text()),
                    link_count=len(soup.find_all('a')),
                    form_count=len(soup.find_all('form')),
                    button_count=len(soup.find_all('button')),
                    input_count=len(soup.find_all('input'))
                )
                # Store site features for later use
                ml_extractor._current_site_features = site_features
                print(f"🤖 [{worker_id}] ML: Recorded site features")
            except Exception as e:
                print(f"⚠️ [{worker_id}] ML site features recording failed: {e}")
        
        # Run specialized human trafficking detection
        trafficking_alert = detect_human_trafficking_priority(url, title, html)
        
        # Run specialized scam detection
        scam_alert = detect_scam_priority(url, title, html)
        
        print(f"📄 [{worker_id}] Page title: {title}")
        # print(f"🏷️ [{worker_id}] Categories: {', '.join(categories)}")
        
        # Enhanced logging for human trafficking detection
        if trafficking_alert["requires_immediate_attention"]:
            # print(f"🚨 [{worker_id}] HUMAN TRAFFICKING DETECTED - {trafficking_alert['priority']} PRIORITY")
            # print(f"   Score: {trafficking_alert['score']}")
            # print(f"   Patterns: {', '.join(trafficking_alert['patterns'])}")
            pass
        elif trafficking_alert["score"] > 0:
            # print(f"⚠️ [{worker_id}] Potential human trafficking indicators detected (Score: {trafficking_alert['score']})")
            pass
        
        # Enhanced logging for scam detection
        if scam_alert["requires_immediate_attention"]:
            # print(f"🚨 [{worker_id}] SCAM DETECTED - {scam_alert['priority']} PRIORITY")
            # print(f"   Score: {scam_alert['score']}")
            # print(f"   Patterns: {', '.join(scam_alert['patterns'])}")
            pass
        elif scam_alert["score"] > 0:
            # print(f"⚠️ [{worker_id}] Potential scam indicators detected (Score: {scam_alert['score']})")
            pass
        
        # Check if immediate processing is needed
        if (ENABLE_IMMEDIATE_PROCESSING and 
            (trafficking_alert["score"] >= IMMEDIATE_PROCESSING_THRESHOLD and
             trafficking_alert["requires_immediate_attention"]) or
            (scam_alert["score"] >= 10 and scam_alert["requires_immediate_attention"]) or
            "scam" in categories):
            
            # Determine priority level
            if "scam" in categories or scam_alert["requires_immediate_attention"]:
                priority = "SCAM_HIGH"
                # print(f"🚨 [{worker_id}] SCAM DETECTED - Triggering immediate processing")
            else:
                priority = trafficking_alert["priority"]
                # print(f"🚨 [{worker_id}] TRIGGERING IMMEDIATE PROCESSING - Score: {trafficking_alert['score']:.1f}")
            
            # Close current driver and start immediate processing
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            # Process immediately with dedicated driver
            immediate_results = process_url_immediately(url, worker_id, priority)
            
            # Record results in agent system
            try:
                if immediate_results:
                    integrated_agents.record_success(url, "immediate_processing", worker_id, "immediate_processing", immediate_results)
                else:
                    integrated_agents.record_failure(url, "no_addresses", "immediate_processing", worker_id, "immediate_processing")
            except:
                pass
            
            # Return immediate results instead of continuing with normal processing
            if immediate_results:
                # print(f"🎉 [{worker_id}] Immediate processing successful - found {len(immediate_results)} addresses")
                return immediate_results
            else:
                # print(f"⚠️ [{worker_id}] Immediate processing completed but no addresses found")
                return []
        
        # Continue with normal processing for non-immediate cases
        # print(f"📋 [{worker_id}] Continuing with normal processing flow...")

        # === STRATEGY IMPLEMENTATION WITH AI FALLBACK ===
        print(f"🎯 [{worker_id}] Implementing strategy {strategy} with AI fallback")
        
        # Strategy-specific configuration - AI DISABLED by default, enabled as fallback
        if strategy == 1:  # Basic Strategy - Traditional methods only
            print(f"⚡ [{worker_id}] Basic Strategy: Traditional methods, AI fallback disabled")
            ENABLE_AI_FALLBACK = False  # No AI at all for basic strategy
            MAX_LINKS_TO_TRY = 2
            ENABLE_DEEP_CRAWLING = False
            USE_ENHANCED_EXTRACTION = False
            
        elif strategy == 2:  # AI Enhanced Strategy - AI as fallback
            print(f"🤖 [{worker_id}] AI Enhanced Strategy: Traditional first, AI fallback enabled")
            ENABLE_AI_FALLBACK = True  # AI only as fallback
            MAX_LINKS_TO_TRY = 5
            ENABLE_DEEP_CRAWLING = True
            USE_ENHANCED_EXTRACTION = True
            
        elif strategy == 3:  # Visual Captcha Focus - AI fallback for captchas only
            print(f"🔍 [{worker_id}] Visual Captcha Strategy: Traditional first, AI captcha fallback")
            ENABLE_AI_FALLBACK = True  # AI only for captcha fallback
            MAX_LINKS_TO_TRY = 3
            ENABLE_DEEP_CRAWLING = False
            USE_ENHANCED_EXTRACTION = False
                
        elif strategy == 4:  # JavaScript Interactive Strategy - AI fallback for interactions
            print(f"⚙️ [{worker_id}] JavaScript Interactive Strategy: Traditional first, AI interaction fallback")
            ENABLE_AI_FALLBACK = True  # AI only for interaction fallback
            MAX_LINKS_TO_TRY = 4
            ENABLE_DEEP_CRAWLING = True
            USE_ENHANCED_EXTRACTION = True
            
        elif strategy == 5:  # Custom Site Strategy - AI fallback enabled
            print(f"🕵️ [{worker_id}] Custom Site Strategy: Traditional first, AI fallback enabled")
            ENABLE_AI_FALLBACK = True  # AI as fallback when traditional methods fail
            MAX_LINKS_TO_TRY = 8  # More thorough link exploration
            ENABLE_DEEP_CRAWLING = True
            USE_ENHANCED_EXTRACTION = True
            # Use longer waits for more careful analysis
            time.sleep(LONG_WAIT)  # Extra wait for stealth
            
        else:  # Default fallback
            print(f"❓ [{worker_id}] Unknown strategy {strategy}, using default with AI fallback")
            ENABLE_AI_FALLBACK = True
            MAX_LINKS_TO_TRY = 3
            ENABLE_DEEP_CRAWLING = False
            USE_ENHANCED_EXTRACTION = False

        # --- PHASE 1: TRADITIONAL METHODS FIRST ---
        print(f"🔍 [{worker_id}] Phase 1: Traditional address extraction...")
        
        # Step 1: Always scroll the page first to reveal all content
        scroll_entire_page(driver)
        
        # Step 2: Traditional address extraction
        extraction_start_time = time.time()
        if USE_ENHANCED_EXTRACTION:
            addresses = extract_addresses_enhanced(driver.page_source, url, title)
            extraction_method = "enhanced"
            print(f"🔍 [{worker_id}] Enhanced extraction found {len(addresses)} addresses")
        else:
            addresses = extract_addresses_fast(driver.page_source)
            extraction_method = "fast"
            print(f"⚡ [{worker_id}] Fast extraction found {len(addresses)} addresses")
        
        # Record extraction attempt in ML system
        if ml_extractor:
            try:
                extraction_time = time.time() - extraction_start_time
                success = len(addresses) > 0
                ml_extractor.record_extraction_attempt(
                    strategy=strategy,
                    success=success,
                    time_taken=extraction_time
                )
                print(f"🤖 [{worker_id}] ML: Recorded extraction attempt (success={success}, time={extraction_time:.2f}s)")
            except Exception as e:
                print(f"⚠️ [{worker_id}] ML recording failed: {e}")
        
        # Step 3: Wait for dynamic content if no addresses found
        if len(addresses) == 0:
            print(f"⏳ [{worker_id}] No addresses found initially, waiting for dynamic content...")
            if wait_for_address_in_dom(driver, timeout=15):
                print(f"✅ [{worker_id}] Addresses appeared after waiting!")
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                addresses = extract_addresses_enhanced(html, url, title)
                print(f"🔍 [{worker_id}] Found {len(addresses)} addresses after waiting")
        
        # Step 4: CRITICAL - Check for registration/signup requirements FIRST
        registration_credentials = None
        if len(addresses) == 0:
            print(f"👤 [{worker_id}] No addresses found, checking if registration is required...")
            
            # Check for signup/login requirements
            page_text = driver.page_source.lower()
            signup_indicators = ['sign up', 'signup', 'register', 'create account', 'join now', 'login required']
            
            if any(indicator in page_text for indicator in signup_indicators):
                print(f"📝 [{worker_id}] Registration/signup detected, attempting registration...")
                registration_result = ai_handle_registration_enhanced(driver, driver.current_url, categories)
                if registration_result and isinstance(registration_result, dict):
                    registration_credentials = registration_result
                    print(f"✅ [{worker_id}] Registration completed with credentials stored")
                    time.sleep(3)
                    scroll_entire_page(driver)
                    time.sleep(1)
                    addresses = extract_addresses_enhanced(driver.page_source, url, title)
                    if addresses:
                        print(f"🎯 [{worker_id}] Registration revealed {len(addresses)} addresses!")
                    else:
                        print(f"🛒 [{worker_id}] No addresses after registration, checking if login is needed...")
                        
                        # Check if we need to login after registration
                        current_page_text = driver.page_source.lower()
                        login_indicators = ['login', 'log in', 'sign in', 'signin']
                        
                        if any(indicator in current_page_text for indicator in login_indicators):
                            print(f"🔑 [{worker_id}] Login required after registration, attempting login...")
                            if ai_handle_login_with_credentials(driver, driver.current_url, registration_credentials):
                                print(f"✅ [{worker_id}] Login successful, checking for addresses...")
                                time.sleep(3)
                                scroll_entire_page(driver)
                                time.sleep(1)
                                addresses = extract_addresses_enhanced(driver.page_source, url, title)
                                if addresses:
                                    print(f"🎯 [{worker_id}] Login revealed {len(addresses)} addresses!")
                                else:
                                    print(f"🛒 [{worker_id}] No addresses after login, proceeding to purchase flow...")
                            else:
                                print(f"❌ [{worker_id}] Login failed after registration")
                        else:
                            print(f"🛒 [{worker_id}] No login required, proceeding to purchase flow...")
                elif registration_result:
                    print(f"✅ [{worker_id}] Registration completed (legacy response)")
                    time.sleep(3)
                    scroll_entire_page(driver)
                    time.sleep(1)
                    addresses = extract_addresses_enhanced(driver.page_source, url, title)
                    if addresses:
                        print(f"🎯 [{worker_id}] Registration revealed {len(addresses)} addresses!")
                    else:
                        print(f"🛒 [{worker_id}] No addresses after registration, proceeding to purchase flow...")
                else:
                    print(f"❌ [{worker_id}] Registration failed")
        
        # Step 5: Check for add to cart buttons (after potential registration)
        add_to_cart_attempted = False
        if len(addresses) == 0:
            print(f"🛒 [{worker_id}] No addresses found, checking for add to cart on current page...")
            if enhanced_add_to_cart(driver):
                add_to_cart_attempted = True
                print(f"✅ [{worker_id}] Add to cart clicked successfully!")
                print(f"⏳ [{worker_id}] Waiting for page update after add to cart...")
                time.sleep(3)  # Longer wait for cart update
                scroll_entire_page(driver)
                time.sleep(1)
                
                # Re-extract after add to cart
                print(f"🔍 [{worker_id}] Checking for addresses after add to cart...")
                addresses = extract_addresses_enhanced(driver.page_source, url, title)
                if addresses:
                    print(f"🎯 [{worker_id}] Add to cart revealed {len(addresses)} addresses!")
                else:
                    # Try to proceed to checkout after adding to cart
                    print(f"🛒 [{worker_id}] No addresses after add to cart, trying to proceed to checkout...")
                    print(f"📄 [{worker_id}] Current page title: {driver.title}")
                    print(f"🌐 [{worker_id}] Current URL: {driver.current_url}")
                    
                    if enhanced_checkout_click(driver):
                        print(f"✅ [{worker_id}] Checkout button clicked successfully!")
                        print(f"⏳ [{worker_id}] Waiting for checkout page to load...")
                        time.sleep(4)  # Longer wait for checkout page
                        scroll_entire_page(driver)
                        time.sleep(1)
                        
                        print(f"🔍 [{worker_id}] Checking for addresses on checkout page...")
                        print(f"📄 [{worker_id}] New page title: {driver.title}")
                        print(f"🌐 [{worker_id}] New URL: {driver.current_url}")
                        
                        addresses = extract_addresses_enhanced(driver.page_source, url, title)
                        if addresses:
                            print(f"🎯 [{worker_id}] Checkout page revealed {len(addresses)} addresses!")
                        else:
                            print(f"❌ [{worker_id}] No addresses found yet, checkout page may need form filling...")
                            
                            # Try to handle the checkout form to reveal payment addresses
                            print(f"💳 [{worker_id}] Attempting to fill checkout form to reveal payment info...")
                            if ai_handle_checkout_form(driver, driver.current_url, categories):
                                print(f"✅ [{worker_id}] Checkout form handled, checking for addresses again...")
                                time.sleep(3)  # Wait for payment info to appear
                                scroll_entire_page(driver)
                                time.sleep(1)
                                
                                addresses = extract_addresses_enhanced(driver.page_source, url, title)
                                if addresses:
                                    print(f"🎯 [{worker_id}] Form filling revealed {len(addresses)} addresses!")
                                else:
                                    print(f"🔄 [{worker_id}] Still no addresses, trying payment method selection...")
                                    # Try to select crypto payment method
                                    if handle_crypto_payment_selection(driver):
                                        print(f"✅ [{worker_id}] Crypto payment selected, checking again...")
                                        time.sleep(3)
                                        scroll_entire_page(driver)
                                        time.sleep(1)
                                        addresses = extract_addresses_enhanced(driver.page_source, url, title)
                                        if addresses:
                                            print(f"🎯 [{worker_id}] Crypto selection revealed {len(addresses)} addresses!")
                                        else:
                                            print(f"❌ [{worker_id}] Still no addresses after all checkout attempts")
                                    else:
                                        print(f"❌ [{worker_id}] Could not select crypto payment method")
                            else:
                                print(f"❌ [{worker_id}] Could not handle checkout form")
                    else:
                        print(f"❌ [{worker_id}] Could not find or click checkout button after add to cart")
            else:
                print(f"❌ [{worker_id}] Could not find or click add to cart button")
        
        # Step 5: Try internal links only if add to cart didn't work
        if len(addresses) == 0:
            print(f"🔍 [{worker_id}] No addresses found, checking internal links...")
            internal_links = get_internal_links_fast(soup, url)
            
            # Categorize links by priority
            payment_links = [link for link in internal_links if any(keyword in link.lower() for keyword in 
                ['/buy', '/payment', '/wallet', '/address', '/checkout', '/order', '/purchase', '/pay', '/crypto', '/bitcoin'])]
            
            for i, link_url in enumerate(payment_links[:MAX_LINKS_TO_TRY]):
                print(f"🔍 [{worker_id}] Trying payment link {i+1}: {link_url}")
                try:
                    driver.get(link_url)
                    time.sleep(SHORT_WAIT)
                    
                    # Abort this link if we hit a Chrome error page
                    if is_chrome_error_page(driver.page_source):
                        print(f"⚠️ [{worker_id}] Chrome error page for {link_url} – skipping link.")
                        continue
                    
                    # CRITICAL: Check for add to cart on each link page too (but only if not already attempted)
                    link_addresses = extract_addresses_fast(driver.page_source)
                    if len(link_addresses) == 0 and not add_to_cart_attempted:
                        print(f"🛒 [{worker_id}] No addresses on link page, trying add to cart...")
                        if enhanced_add_to_cart(driver):
                            add_to_cart_attempted = True  # Mark as attempted to prevent duplicates
                            print(f"✅ [{worker_id}] Add to cart clicked on link page, waiting...")
                            time.sleep(MEDIUM_WAIT)
                            scroll_entire_page(driver)
                            time.sleep(SHORT_WAIT)
                            link_addresses = extract_addresses_fast(driver.page_source)
                    elif add_to_cart_attempted:
                        print(f"⏭️ [{worker_id}] Skipping add to cart on link page (already attempted earlier)")
                    
                    if wait_for_address_in_dom(driver, timeout=10):
                        print(f"✅ [{worker_id}] Addresses found on {link_url}")
                        addresses = extract_addresses_fast(driver.page_source)
                        if addresses:
                            break
                except Exception as e:
                    err_msg = str(e)
                    if "ERR_SOCKS_CONNECTION_FAILED" in err_msg or "net::ERR" in err_msg:
                        print(f"⚠️ [{worker_id}] SOCKS connection failed for {link_url} (likely offline or Tor issue)")
                    else:
                        print(f"⚠️ [{worker_id}] Error trying link {link_url}: {err_msg}")
                    continue
        
        # --- PHASE 2: AI FALLBACK (ONLY IF TRADITIONAL METHODS FAILED) ---
        ai_used = False
        if len(addresses) == 0 and ENABLE_AI_FALLBACK:
            print(f"🤖 [{worker_id}] Phase 2: AI fallback activated (traditional methods found 0 addresses)")
            
            # AI Interaction Logic - only as fallback
            ai_handled = False
            
            # Try smart iterative e-commerce flow first
            print(f"🔄 [{worker_id}] Starting smart iterative e-commerce flow...")
            iterative_addresses = smart_iterative_ecommerce_flow(driver, url, title, categories, max_iterations=3, worker_id=worker_id)
            if iterative_addresses:
                addresses.extend(iterative_addresses)
                ai_handled = True
                ai_used = True
                print(f"✅ [{worker_id}] Smart iterative flow found {len(iterative_addresses)} addresses!")
            else:
                # Fallback to simple AI interactive elements
                if ai_click_interactive_elements(driver):
                    ai_handled = True
                    ai_used = True
                    print(f"⏳ [{worker_id}] AI clicked interactive elements, waiting for page...")
                    time.sleep(LONG_WAIT)
                    scroll_entire_page(driver)
                    
                    # Re-extract after AI interaction
                    addresses = extract_addresses_enhanced(driver.page_source, url, title)
                    if addresses:
                        print(f"✅ [{worker_id}] AI interaction found {len(addresses)} addresses!")
            
            # Try AI form handling if still no addresses
            if not addresses and not ai_handled:
                print(f"🤖 [{worker_id}] Trying AI form handling...")
                if ai_solve_captcha_enhanced(driver): 
                    ai_handled = True
                    ai_used = True
                elif ai_solve_visual_captcha(driver): 
                    ai_handled = True
                    ai_used = True
                elif ai_handle_login_enhanced(driver, driver.current_url, categories): 
                    ai_handled = True
                    ai_used = True
                elif ai_handle_registration_enhanced(driver, driver.current_url, categories): 
                    ai_handled = True
                    ai_used = True
                elif ai_handle_checkout_form(driver, driver.current_url, categories): 
                    ai_handled = True
                    ai_used = True
                
                if ai_handled:
                    print(f"🤖 [{worker_id}] AI form handling completed, waiting for page...")
                    time.sleep(LONG_WAIT)
                    addresses = extract_addresses_enhanced(driver.page_source, url, title)
                    if addresses:
                        print(f"✅ [{worker_id}] AI form handling found {len(addresses)} addresses!")
            
            # Try smart multi-step transaction as final AI fallback
            if not addresses:
                print(f"🧠 [{worker_id}] Trying smart transaction flow as final fallback...")
                try:
                    smart_result = execute_smart_transaction(driver, driver.page_source, url, title)
                    if smart_result['success'] and smart_result.get('addresses_found'):
                        addresses.extend(smart_result['addresses_found'])
                        ai_used = True
                        print(f"🎯 [{worker_id}] Smart transaction found {len(smart_result['addresses_found'])} addresses!")
                    elif smart_result.get('steps_completed', 0) > 0:
                        print(f"🔄 [{worker_id}] Smart transaction completed {smart_result['steps_completed']} steps")
                        ai_used = True
                        # Re-extract after smart transaction
                        addresses = extract_addresses_enhanced(driver.page_source, url, title)
                except Exception as e:
                    print(f"⚠️ [{worker_id}] Smart transaction error: {e}")
            
            # Report AI usage
            if ai_used and addresses:
                print(f"💰 [{worker_id}] AI fallback successful - traditional: 0, AI: {len(addresses)} addresses")
            elif ai_used:
                print(f"❌ [{worker_id}] AI fallback used but found 0 addresses")
            else:
                print(f"❌ [{worker_id}] Both traditional and AI methods failed to find addresses")
        
        elif len(addresses) > 0:
            print(f"✅ [{worker_id}] Traditional methods successful - found {len(addresses)} addresses (AI fallback not needed)")
        else:
            print(f"❌ [{worker_id}] Traditional methods failed, AI fallback disabled for this strategy")
        
        # Check for and handle multi-coin selection pages
        page_text_lower = driver.page_source.lower()
        coin_selection_keywords = ['select your coin', 'select a coin', 'choose payment method', 'payment method']
        if any(keyword in page_text_lower for keyword in coin_selection_keywords):
            # Only use AI coin selection as fallback when traditional methods found 0 addresses
            if len(addresses) == 0 and ENABLE_AI_FALLBACK and check_api_quota():
                print(f"💰 [{worker_id}] Coin selection page detected, trying AI handling as fallback...")
                try:
                    coin_results = ai_handle_coin_selection_page(driver, url, categories)
                    if coin_results:
                        addresses.extend([(r['chain'], r['address']) for r in coin_results])
                        results.extend(coin_results)
                        ai_used = True
                        print(f"✅ [{worker_id}] AI coin selection found {len(coin_results)} addresses!")
                except Exception as e:
                    print(f"⚠️ [{worker_id}] AI coin selection failed: {e}")
            else:
                print(f"💰 [{worker_id}] Coin selection page detected, but skipping AI handling (addresses already found or AI disabled)")
        
        # Wait for JavaScript to load and execute
        # print(f"⏳ [{worker_id}] Waiting for JavaScript content to load...")
        try:
            # Wait for page to be fully loaded
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            # Additional wait for dynamic content
            time.sleep(MEDIUM_WAIT)
            # Scroll to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SHORT_WAIT)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(SHORT_WAIT)
        except Exception as e:
            print(f"⚠️ [{worker_id}] JavaScript wait failed: {e}")
        
        # Address extraction now handled in Phase 1 above
        # Debug HTML saving for AI interactions that failed to find addresses
        if ai_used and len(addresses) == 0:
            print(f"🐛 [{worker_id}] AI interaction was performed, but no address found. Saving page source for debugging...")
            try:
                debug_filename = f"{sanitize_filename(url)}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.html"
                debug_path = os.path.join(DEBUG_DIR, debug_filename)
                with open(debug_path, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print(f"💾 [{worker_id}] Debug HTML saved to: {debug_path}")
            except Exception as e:
                print(f"❌ [{worker_id}] Could not save debug HTML: {e}")

        # Use root title for consistency (should already be set from earlier)
        display_title = get_or_set_root_title(url, soup.title.string.strip() if soup.title else "NoTitle")
        should_skip, skip_reason = should_skip_page(url, display_title, html)
        if should_skip:
            print(f"⏭️ [{worker_id}] Skipping page: {skip_reason}")
            log_skipped_market(url, skip_reason)
            return []

        if addresses:
            print(f"✅ [{worker_id}] Found {len(addresses)} addresses on page!")
            existing_addrs = {res['address'] for res in results}
            new_addresses = [(chain, addr) for chain, addr in addresses if addr not in existing_addrs]
            print(f"🔍 [{worker_id}] Debug: {len(addresses)} total addresses, {len(new_addresses)} new addresses")
            print(f"🔍 [{worker_id}] Debug: existing_addrs count: {len(existing_addrs)}")
            if new_addresses:
                print(f"✅ [{worker_id}] Found {len(new_addresses)} new addresses on {get_base_domain(url)}")
                hostname = urlparse(url).hostname or ''
                if hostname.endswith('.onion'):
                    suffix = hostname[:-6][-6:]
                else:
                    suffix = hostname[-6:]
                # Use root title for consistent file naming
                display_title = get_or_set_root_title(url, title)
                title_prefix = sanitize_filename(display_title[:10])
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                for i, (chain, addr) in enumerate(new_addresses):
                    print(f"🔍 [{worker_id}] Processing address {i+1}/{len(new_addresses)}: {chain} - {addr[:8]}...{addr[-8:]}")
                    description = get_description_for_address(soup, addr)
                    if "Description not found" in description:
                        print(f"🤖 [{worker_id}] Rule-based description failed ('{description}'). Using content-based fallback...")
                        description = generate_content_based_description(categories)
                    screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                    print(f"📸 [{worker_id}] Taking screenshot for {chain} address: {addr[:4]}...{addr[-4:]}")
                    try:
                        success = highlight_address_on_screenshot(driver, addr, screenshot_path)
                        if success:
                            print(f"✅ [{worker_id}] Highlighted screenshot saved: {screenshot_name}")
                        else:
                            print(f"❌ [{worker_id}] Screenshot failed")
                            screenshot_path = "screenshot_failed.png"
                    except Exception as e:
                        print(f"❌ [{worker_id}] Screenshot failed: {e}")
                        screenshot_path = "screenshot_failed.png"
                    # Use standard categories since scam sites are now properly skipped
                    categories_out = list(categories) if isinstance(categories, list) else []
                    result_row = {
                        'url': get_base_domain(url),
                        'title': display_title,
                        'description': description,
                        'chain': chain,
                        'address': addr,
                        'timestamp': datetime.utcnow().isoformat(),
                        'screenshot': screenshot_path,
                        'categories': json.dumps(categories_out),
                        'scam': False
                    }
                    results.append(result_row)
                    print(f"🏦 [{worker_id}] Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                    # Track address for duplicate detection (but don't write to CSV here)
                    with global_seen_lock:
                        if addr in global_seen_addresses:
                            print(f"⏭️ [{worker_id}] Duplicate {chain} address detected (same run)")
                        else:
                            global_seen_addresses.add(addr)
                            print(f"✅ [{worker_id}] New {chain} address tracked for CSV writing")
            else:
                print(f"⚠️ [{worker_id}] All {len(addresses)} addresses were duplicates, skipping processing")



        # Extract and immediately visit external .onion links
        external_links = get_external_onion_links(soup, url)
        if external_links:
            print(f"🌐 [{worker_id}] Found {len(external_links)} external .onion links (visiting immediately):")
            for link in external_links[:3]:  # Show first 3
                print(f"   🔗 {link}")
            if len(external_links) > 3:
                print(f"   ... and {len(external_links) - 3} more")
            
            # Visit external links immediately (strategy-dependent limit)
            external_limit = 3 if ENABLE_DEEP_CRAWLING else 1
            for i, external_url in enumerate(external_links[:external_limit]):
                print(f"🌐 [{worker_id}] Navigating to external site {i+1}/{external_limit}: {external_url}")
                try:
                    # Create a new driver for external site
                    external_driver = create_driver(f"{worker_id}_external_{i}")
                    external_driver.get(external_url)
                    time.sleep(SHORT_WAIT)
                    
                    # Wait for dynamic content
                    if wait_for_address_in_dom(external_driver, timeout=10):
                        print(f"✅ [{worker_id}] Addresses appeared on external site {external_url}")
                    
                    external_html = external_driver.page_source
                    external_soup = BeautifulSoup(external_html, 'html.parser')
                    external_addresses = extract_addresses_fast(external_html)
                    print(f"🔍 [{worker_id}] External site scan found {len(external_addresses)} addresses")
                    
                    if external_addresses:
                        print(f"✅ [{worker_id}] Found {len(external_addresses)} addresses on external site {external_url}!")
                        hostname = urlparse(external_url).hostname or ''
                        if hostname.endswith('.onion'):
                           suffix = hostname[:-6][-6:]
                        else:
                           suffix = hostname[-6:]
                        external_current_title = external_driver.title.strip() if external_driver.title else "NoTitle"
                        # Use root title for external site for consistency
                        external_title = get_or_set_root_title(external_url, external_current_title)
                        # Re-classify the new page for more accurate context
                        external_categories = classify_site(external_url, external_title, external_html)
                        title_prefix = sanitize_filename(external_title[:10])
                        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                        for j, (chain, addr) in enumerate(external_addresses):
                            print(f"🔍 [{worker_id}] Processing external address {j+1}/{len(external_addresses)}: {chain} - {addr[:8]}...{addr[-8:]}")
                            description = get_description_for_address(external_soup, addr)
                            if "Description not found" in description:
                                print(f"🤖 [{worker_id}] Rule-based description for external site failed ('{description}'). Using content-based fallback...")
                                description = generate_content_based_description(external_categories)
                            screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_external{i}_{j}.png"
                            screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                            
                            # ALWAYS take screenshot for every address
                            print(f"📸 [{worker_id}] Taking screenshot for {chain} address from external site {external_url}: {addr[:4]}...{addr[-4:]}")
                            try:
                                success = highlight_address_on_screenshot(external_driver, addr, screenshot_path)
                                if success:
                                    print(f"✅ [{worker_id}] Highlighted screenshot saved: {screenshot_name}")
                                else:
                                    print(f"❌ [{worker_id}] Screenshot failed")
                                    screenshot_path = "screenshot_failed.png"
                            except Exception as e:
                                print(f"❌ [{worker_id}] Screenshot failed: {e}")
                                screenshot_path = "screenshot_failed.png"
                            
                            results.append({
                                'url': get_base_domain(external_url),
                                'title': external_title,
                                'description': description,
                                'chain': chain,
                                'address': addr,
                                'timestamp': datetime.utcnow().isoformat(),
                                'screenshot': screenshot_path,
                                'categories': json.dumps(external_categories)
                            })
                            print(f"🏦 [{worker_id}] Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                        
                        # If we found addresses, we can stop trying more external links
                        break
                        
                except Exception as e:
                    error_str = str(e).lower()
                    print(f"⚠️ [{worker_id}] Error visiting external site {external_url}: {e}")
                    
                    # Only log external links if we encounter captcha/login issues without finding addresses
                    if ("captcha" in error_str or "verification" in error_str or 
                        "login" in error_str or "authentication" in error_str or 
                        "signin" in error_str) and len(results) == 0:
                        print(f"📝 [{worker_id}] Logging external link {external_url} due to captcha/login failure")
                        log_discovered_links(url, [external_url], "external_captcha_login")
                    continue
                finally:
                    if 'external_driver' in locals():
                        try:
                            external_driver.quit()
                        except:
                            pass
        
        # Quick internal link extraction for deeper crawling
        # This logic is now only triggered if the results list is still empty after all prior checks
        if len(results) == 0:
            print(f"🔍 [{worker_id}] No addresses found, checking for payment/wallet links...")
            internal_links = get_internal_links_fast(soup, url)
            
            # Categorize links by priority
            payment_links = [link for link in internal_links if any(keyword in link.lower() for keyword in 
                ['/buy', '/payment', '/wallet', '/address', '/checkout', '/order', '/purchase', '/pay', '/crypto', '/bitcoin'])]
            crypto_links = [link for link in internal_links if any(keyword in link.lower() for keyword in 
                ['/btc', '/eth', '/xmr', '/tron', '/sol', '/deposit', '/withdraw', '/send', '/receive'])]
            other_links = [link for link in internal_links if link not in payment_links and link not in crypto_links]
            
            print(f"🔗 [{worker_id}] Found {len(internal_links)} internal links:")
            print(f"   💳 Payment links: {len(payment_links)}")
            print(f"   🪙 Crypto links: {len(crypto_links)}")
            print(f"   🔗 Other links: {len(other_links)}")
            
            # Log all discovered links
            if internal_links:
                print(f"📝 [{worker_id}] Found {len(internal_links)} internal links (visiting immediately)")
            
            # Try payment links first (highest priority)
            # Use strategy-dependent link limits
            other_limit = MAX_LINKS_TO_TRY - len(payment_links) - len(crypto_links)
            links_to_try = payment_links + crypto_links + other_links[:max(1, other_limit)]
            
            for i, link_url in enumerate(links_to_try[:MAX_LINKS_TO_TRY]):
                print(f"🔍 [{worker_id}] Trying link {i+1}/{MAX_LINKS_TO_TRY}: {link_url}")
                print(f"🌐 [{worker_id}] Navigating to found page: {link_url}")
                try:
                    driver.get(link_url)
                    time.sleep(SHORT_WAIT)
                    
                    # Wait for dynamic content
                    if wait_for_address_in_dom(driver, timeout=10):
                        print(f"✅ [{worker_id}] Addresses appeared on {link_url}")
                    
                    link_html = driver.page_source
                    link_soup = BeautifulSoup(link_html, 'html.parser')
                    link_addresses = extract_addresses_fast(link_html)
                    print(f"🔍 [{worker_id}] Link scan found {len(link_addresses)} addresses")
                    
                    if link_addresses:
                        print(f"✅ [{worker_id}] Found {len(link_addresses)} addresses on {link_url}!")
                        hostname = urlparse(link_url).hostname or ''
                        if hostname.endswith('.onion'):
                           suffix = hostname[:-6][-6:]
                        else:
                           suffix = hostname[-6:]
                        link_current_title = driver.title.strip() if driver.title else "NoTitle"
                        # Use root title for internal link for consistency
                        link_title = get_or_set_root_title(link_url, link_current_title)
                        # Re-classify the new page for more accurate context
                        link_categories = classify_site(link_url, link_title, link_html)
                        title_prefix = sanitize_filename(link_title[:10])
                        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                        for j, (chain, addr) in enumerate(link_addresses):
                            print(f"🔍 [{worker_id}] Processing internal link address {j+1}/{len(link_addresses)}: {chain} - {addr[:8]}...{addr[-8:]}")
                            description = get_description_for_address(link_soup, addr)
                            if "Description not found" in description:
                                print(f"🤖 [{worker_id}] Rule-based description for link failed ('{description}'). Using content-based fallback...")
                                description = generate_content_based_description(link_categories)
                            screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_link{i}_{j}.png"
                            screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                            
                            # ALWAYS take screenshot for every address
                            print(f"📸 [{worker_id}] Taking screenshot for {chain} address from {link_url}: {addr[:4]}...{addr[-4:]}")
                            try:
                                success = highlight_address_on_screenshot(driver, addr, screenshot_path)
                                if success:
                                    print(f"✅ [{worker_id}] Highlighted screenshot saved: {screenshot_name}")
                                else:
                                    print(f"❌ [{worker_id}] Screenshot failed")
                                    screenshot_path = "screenshot_failed.png"
                            except Exception as e:
                                print(f"❌ [{worker_id}] Screenshot failed: {e}")
                                screenshot_path = "screenshot_failed.png"
                            
                            results.append({
                                'url': get_base_domain(link_url),
                                'title': link_title,
                                'description': description,
                                'chain': chain,
                                'address': addr,
                                'timestamp': datetime.utcnow().isoformat(),
                                'screenshot': screenshot_path,
                                'categories': json.dumps(link_categories)
                            })
                            print(f"🏦 [{worker_id}] Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                        
                        # If we found addresses, we can stop trying more links
                        break
                        
                except Exception as e:
                    err_msg = str(e)
                    if "ERR_SOCKS_CONNECTION_FAILED" in err_msg or "net::ERR" in err_msg:
                        print(f"⚠️ [{worker_id}] SOCKS connection failed for {link_url} (likely offline or Tor issue)")
                    else:
                        print(f"⚠️ [{worker_id}] Error trying link {link_url}: {err_msg}")
                    continue
                    
            if not results:
                print(f"❌ [{worker_id}] No addresses found on any payment/wallet links")
        else:
            # Even if we found addresses, still log the links we discovered
            internal_links = get_internal_links_fast(soup, url)
            if internal_links:
                print(f"📝 [{worker_id}] Found {len(internal_links)} internal links (visiting immediately)")
                # log_discovered_links(url, internal_links, "internal")  # No longer needed - links visited immediately
                # print(f"📝 [{worker_id}] Logged {len(internal_links)} internal links to CSV")  # No longer needed
        # Record final site results in ML system
        if ml_extractor and hasattr(ml_extractor, '_current_site_features'):
            try:
                from ml_learning_system import ExtractionAttempt
                total_addresses = len(results)
                success = total_addresses > 0
                
                # Create extraction attempt record
                extraction_attempt = ExtractionAttempt(
                    strategy=strategy,
                    success=success,
                    time_taken=time.time() - extraction_start_time if 'extraction_start_time' in locals() else 0.0,
                    addresses_found=total_addresses
                )
                
                # Get final addresses
                final_addresses = [result['address'] for result in results] if results else []
                
                # Record site result with correct parameters
                ml_extractor.record_site_result(
                    url=url,
                    features=ml_extractor._current_site_features,
                    attempts=[extraction_attempt],
                    final_addresses=final_addresses,
                    total_time=time.time() - extraction_start_time if 'extraction_start_time' in locals() else 0.0,
                    success=success
                )
                print(f"🤖 [{worker_id}] ML: Recorded site result (success={success}, addresses={total_addresses})")
            except Exception as e:
                print(f"⚠️ [{worker_id}] ML site result recording failed: {e}")
        
        if len(results) == 0:
            print(f"❌ [{worker_id}] No addresses found on {get_base_domain(url)}")
            # Record failure in agent system
            try:
                integrated_agents.record_failure(url, "no_addresses", strategy, worker_id, "address_extraction")
            except:
                pass
        else:
            print(f"🎉 [{worker_id}] Successfully processed {len(results)} addresses from {get_base_domain(url)}")
            print(f"📊 [{worker_id}] Final results summary:")
            for i, result in enumerate(results):
                print(f"   {i+1}. {result['chain']} - {result['address'][:8]}...{result['address'][-8:]} → 📸 {result['screenshot']}")
            # Record success in agent system
            try:
                integrated_agents.record_success(url, strategy, worker_id, "address_extraction", results)
            except:
                pass
        return results
    except Exception as e:
        print(f"❌ [{worker_id}] Error processing {get_base_domain(url)}: {e}")
        
        # Record failure in agent system
        try:
            integrated_agents.record_failure(url, "processing_error", strategy, worker_id, "address_extraction")
        except:
            pass
        
        # Determine if this is a retryable error
        error_str = str(e).lower()
        retry_reason = None
        
        if "captcha" in error_str or "verification" in error_str:
            retry_reason = "captcha_failed"
        elif "login" in error_str or "authentication" in error_str or "signin" in error_str:
            retry_reason = "login_failed"
        elif "registration" in error_str or "signup" in error_str:
            retry_reason = "registration_failed"
        elif "form" in error_str or "submit" in error_str:
            retry_reason = "form_submission_failed"
        
        # Add to retry list only for specific failure types
        if retry_reason:
            add_to_retry_list(url, retry_reason, str(e))
        
        # Try to rotate TOR identity on connection errors
        if "connection" in error_str or "timeout" in error_str:
            print(f"🔄 [{worker_id}] Connection error detected, attempting TOR rotation")
            if rotate_tor_identity():
                print(f"✅ [{worker_id}] TOR rotated after connection error")
                time.sleep(3)  # Wait for new circuit
            else:
                print(f"⚠️ [{worker_id}] TOR rotation failed after connection error")
            time.sleep(5)  # Wait longer for new circuit to establish
        return []
    finally:
        if driver:
            try:
                print(f"🔒 [{worker_id}] Closing browser for {get_base_domain(url)}")
                driver.quit()
            except:
                pass

# ---[ AI Helper Functions ]---
def ai_generate_fake_user():
    """Generate fake user data using OpenAI/Anthropic"""
    try:
        prompt = (
            "Generate a realistic fake user profile for a dark web market. "
            "Return as JSON with fields: username, password, email, btc_address, pin, invite_code, pgp_key, telegram, age, country. "
            "Username: 8-12 lowercase letters/numbers. Password: 10-16 chars, strong. Email: realistic, not real domain. "
            "BTC address: valid format but fake. PIN: 4-6 digits. Invite code: 8-12 chars. PGP key: fake but realistic format. "
            "Telegram: @username format. Age: 18-45. Country: common country name."
        )
        if AI_ENABLED:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            import json as _json
            data = _json.loads(response.choices[0].message.content)
            return data
    except Exception as e:
        # Fallback with comprehensive fake data
        import random, string
        random_suffix = get_random_suffix()
        username = f'user_{int(time.time())}_{random_suffix}'
        password = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%^&*', k=14))
        email = f'{username}@protonmail.com'
        btc_address = '1' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=33))
        pin = ''.join(random.choices(string.digits, k=4))
        invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        pgp_key = '-----BEGIN PGP PUBLIC KEY BLOCK-----\n' + ''.join(random.choices(string.ascii_letters + string.digits, k=100)) + '\n-----END PGP PUBLIC KEY BLOCK-----'
        telegram = '@' + username
        age = str(random.randint(18, 45))
        country = random.choice(['USA', 'UK', 'Germany', 'Canada', 'Australia', 'Netherlands'])
        
        return {
            'username': username, 
            'password': password, 
            'email': email,
            'btc_address': btc_address,
            'pin': pin,
            'invite_code': invite_code,
            'pgp_key': pgp_key,
            'telegram': telegram,
            'age': age,
            'country': country
        }

def ai_solve_captcha(image):
    """Solve captcha using OCR and fallback to AI if needed"""
    try:
        # OCR first
        text = pytesseract.image_to_string(image)
        text = text.strip()
        if text and len(text) >= 4:
            return text
        # Fallback to AI
        if AI_ENABLED:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()
            prompt = (
                "This is a captcha image from a dark web site. "
                "Please read the text and return only the captcha code."
            )
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
                    ]}
                ],
                max_tokens=10
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        return ""

def ai_handle_login_enhanced(driver, url, categories=None):
    """Smart login handling with basic methods first, AI as fallback"""
    try:
        print(f"🔐 Smart login handling activated...")
        
        # Step 1: Try basic form detection and filling (no API calls)
        print("   -> Trying basic form detection and filling...")
        forms = driver.find_elements(By.TAG_NAME, 'form')
        for form in forms:
            form_html = form.get_attribute('outerHTML').lower()
            if any(keyword in form_html for keyword in ['login', 'signin', 'access', 'enter', 'continue']):
                if attempt_form_fill(driver, form, url, "login"):
                    print("   -> ✅ Basic login form fill successful")
                    return True
        
        # Step 2: Try basic input field filling (no API calls)
        print("   -> Trying basic input field filling...")
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        if attempt_input_fill(driver, inputs, url, "login"):
            print("   -> ✅ Basic input field fill successful")
            return True
        
        # Step 3: Try basic button clicking (no API calls)
        print("   -> Trying basic button clicking...")
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        if attempt_button_clicks(driver, buttons, url):
            print("   -> ✅ Basic button click successful")
            return True
        
        # Step 4: Try basic link clicking (no API calls)
        print("   -> Trying basic link clicking...")
        links = driver.find_elements(By.TAG_NAME, 'a')
        if attempt_link_clicks(driver, links, url):
            print("   -> ✅ Basic link click successful")
            return True
        
        # Step 5: Try AI methods (API calls)
        if check_api_quota():
            print("   -> All basic methods failed, trying AI methods...")
            # AI methods would go here if we had them enabled
            pass
        else:
            print("   -> API quota limit reached, skipping AI methods")
        
        print("   -> ❌ All login methods failed")
        return False
        
    except Exception as e:
        print(f"⚠️ Smart login handling failed: {e}")
        return False

def ai_handle_registration_enhanced(driver, url, categories=None):
    """Smart registration handling with enhanced signup detection and workflow"""
    try:
        print(f"📝 Enhanced registration handling activated...")
        
        # Step 1: Look for and click signup/register buttons first
        print("   -> Step 1: Looking for signup/register buttons...")
        signup_buttons = []
        
        # Find signup buttons by text
        signup_texts = ['sign up', 'signup', 'register', 'join', 'create account', 'join now']
        for text in signup_texts:
            buttons = driver.find_elements(By.XPATH, f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]" )
            buttons.extend(driver.find_elements(By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]" ))
            buttons.extend(driver.find_elements(By.XPATH, f"//input[@type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]" ))
            signup_buttons.extend(buttons)
        
        # Try clicking signup buttons
        for btn in signup_buttons:
            if btn.is_displayed() and btn.is_enabled():
                try:
                    print(f"   -> Clicking signup button: {btn.text[:30]}")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)  # Wait for signup form to appear
                    break
                except Exception as e:
                    print(f"   -> Signup button click failed: {e}")
                    continue
        
        # Step 2: Enhanced form detection and filling after clicking signup
        print("   -> Step 2: Enhanced registration form detection...")
        time.sleep(1)  # Wait for form to load
        
        forms = driver.find_elements(By.TAG_NAME, 'form')
        registration_forms = []
        
        # Prioritize forms that look like registration
        for form in forms:
            form_html = form.get_attribute('outerHTML').lower()
            form_action = form.get_attribute('action') or ""
            
            # Check if form looks like registration
            if any(keyword in form_html for keyword in ['register', 'signup', 'join', 'registration', 'create']):
                registration_forms.append(form)
            elif any(keyword in form_action.lower() for keyword in ['register', 'signup', 'join']):
                registration_forms.append(form)
        
        # Try registration forms first, then all forms
        forms_to_try = registration_forms if registration_forms else forms
        
        for form in forms_to_try:
            print(f"   -> Trying registration form...")
            result = enhanced_registration_form_fill(driver, form, url)
            if result:
                print("   -> ✅ Enhanced registration form fill successful")
                time.sleep(3)  # Wait for registration to complete
                return result
        
        # Step 3: Try input field filling if no forms worked
        print("   -> Step 3: Direct input field filling...")
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        visible_inputs = [inp for inp in inputs if inp.is_displayed() and inp.is_enabled()]
        
        if len(visible_inputs) >= 2:  # Need at least email/username and password
            if enhanced_registration_input_fill(driver, visible_inputs, url):
                print("   -> ✅ Enhanced input field fill successful")
                return True
        
        # Step 4: Try modal/popup registration forms
        print("   -> Step 4: Looking for modal/popup registration forms...")
        modal_selectors = ['.modal', '.popup', '.overlay', '.dialog', '[role="dialog"]']
        for selector in modal_selectors:
            try:
                modals = driver.find_elements(By.CSS_SELECTOR, selector)
                for modal in modals:
                    if modal.is_displayed():
                        modal_text = modal.text.lower()
                        if any(keyword in modal_text for keyword in ['register', 'signup', 'join', 'create account']):
                            print(f"   -> Found registration modal, attempting to fill...")
                            modal_forms = modal.find_elements(By.TAG_NAME, 'form')
                            if modal_forms:
                                if enhanced_registration_form_fill(driver, modal_forms[0], url):
                                    print("   -> ✅ Modal registration successful")
                                    return True
            except:
                continue
        
        print("   -> ❌ All registration methods failed")
        return False
        
    except Exception as e:
        print(f"⚠️ Enhanced registration handling failed: {e}")
        return False


def ai_handle_login_with_credentials(driver, url, credentials):
    """Handle login using stored credentials"""
    try:
        if not credentials:
            return False
        
        print(f"🔑 Attempting login with credentials...")
        
        # Find login fields
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        filled = 0
        
        for inp in inputs:
            if not inp.is_displayed():
                continue
            
            input_type = inp.get_attribute('type').lower()
            input_name = inp.get_attribute('name').lower() if inp.get_attribute('name') else ''
            
            try:
                # Email/username field
                if input_type in ['email', 'text'] and any(k in input_name for k in ['email', 'user', 'login']):
                    value = credentials.get('email') or credentials.get('username')
                    if value:
                        inp.clear()
                        inp.send_keys(value)
                        filled += 1
                
                # Password field
                elif input_type == 'password':
                    if credentials.get('password'):
                        inp.clear()
                        inp.send_keys(credentials['password'])
                        filled += 1
            except:
                continue
        
        if filled >= 2:
            # Find and click login button
            buttons = driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')] | //input[@type='submit']")
            for btn in buttons:
                if btn.is_displayed():
                    try:
                        btn.click()
                        time.sleep(3)
                        return True
                    except:
                        continue
        
        return False
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def enhanced_registration_form_fill(driver, form, url):
    """Enhanced form filling specifically for registration forms"""
    try:
        print("      -> Enhanced registration form filling...")
        
        # Generate registration data
        import time
        timestamp = int(time.time())
        random_suffix = get_random_suffix()
        registration_data = {
            'username': f'user_{timestamp}_{random_suffix}',
            'email': f'user_{timestamp}_{random_suffix}@protonmail.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'first_name': f'John{random_suffix}',
            'last_name': f'Doe{random_suffix}',
            'age': '25',
            'agree': True,
            'terms': True,
            'newsletter': False
        }
        
        # Get all inputs in the form
        inputs = form.find_elements(By.TAG_NAME, 'input')
        selects = form.find_elements(By.TAG_NAME, 'select')
        textareas = form.find_elements(By.TAG_NAME, 'textarea')
        
        fields_filled = 0
        
        # Fill input fields
        for inp in inputs:
            try:
                field_type = inp.get_attribute('type') or 'text'
                field_name = (inp.get_attribute('name') or '').lower()
                field_id = (inp.get_attribute('id') or '').lower()
                field_placeholder = (inp.get_attribute('placeholder') or '').lower()
                
                field_identifier = f"{field_name} {field_id} {field_placeholder}"
                
                if field_type == 'email' or 'email' in field_identifier:
                    inp.clear()
                    inp.send_keys(registration_data['email'])
                    fields_filled += 1
                elif field_type == 'password':
                    if 'confirm' in field_identifier or 'repeat' in field_identifier:
                        inp.clear()
                        inp.send_keys(registration_data['confirm_password'])
                    else:
                        inp.clear()
                        inp.send_keys(registration_data['password'])
                    fields_filled += 1
                elif 'username' in field_identifier or 'user' in field_identifier:
                    inp.clear()
                    inp.send_keys(registration_data['username'])
                    fields_filled += 1
                elif 'first' in field_identifier and 'name' in field_identifier:
                    inp.clear()
                    inp.send_keys(registration_data['first_name'])
                    fields_filled += 1
                elif 'last' in field_identifier and 'name' in field_identifier:
                    inp.clear()
                    inp.send_keys(registration_data['last_name'])
                    fields_filled += 1
                elif 'age' in field_identifier:
                    inp.clear()
                    inp.send_keys(registration_data['age'])
                    fields_filled += 1
                elif 'captcha' in field_identifier or 'result' in field_identifier:
                    # Handle math captcha - look for captcha text on the page
                    try:
                        captcha_elements = form.find_elements(By.XPATH, ".//*[contains(text(), '+') or contains(text(), '-') or contains(text(), '*') or contains(text(), '=')]")
                        for captcha_elem in captcha_elements:
                            captcha_text = captcha_elem.text.strip()
                            if any(op in captcha_text for op in ['+', '-', '*', '=']):
                                captcha_result = solve_math_captcha(captcha_text)
                                if captcha_result is not None:
                                    inp.clear()
                                    inp.send_keys(str(captcha_result))
                                    fields_filled += 1
                                    print(f"      -> Solved math captcha: {captcha_text} = {captcha_result}")
                                    break
                    except:
                        pass
                elif field_type == 'checkbox':
                    if 'agree' in field_identifier or 'terms' in field_identifier or 'accept' in field_identifier:
                        if not inp.is_selected():
                            inp.click()
                            fields_filled += 1
                    elif 'newsletter' in field_identifier or 'marketing' in field_identifier:
                        # Skip newsletter checkboxes
                        pass
                elif field_type == 'text' and not any(skip in field_identifier for skip in ['search', 'query']):
                    # Fill any remaining text fields with username
                    inp.clear()
                    inp.send_keys(registration_data['username'])
                    fields_filled += 1
                    
            except Exception as e:
                print(f"      -> Could not fill field {field_name}: {e}")
                continue
        
        # Handle select fields
        for select in selects:
            try:
                select_name = (select.get_attribute('name') or '').lower()
                if 'country' in select_name:
                    from selenium.webdriver.support.ui import Select
                    select_obj = Select(select)
                    options = select_obj.options
                    for option in options:
                        if 'united states' in option.text.lower() or option.get_attribute('value') == 'US':
                            select_obj.select_by_visible_text(option.text)
                            fields_filled += 1
                            break
            except:
                continue
        
        print(f"      -> Filled {fields_filled} registration fields")
        
        if fields_filled > 0:
            # Try to submit the form
            submit_buttons = form.find_elements(By.XPATH, ".//button[@type='submit'] | .//input[@type='submit']")
            if not submit_buttons:
                submit_buttons = form.find_elements(By.XPATH, ".//button | .//input[@type='submit']")
            
            for btn in submit_buttons:
                btn_text = (btn.text or btn.get_attribute('value') or '').lower()
                if any(keyword in btn_text for keyword in ['submit', 'register', 'signup', 'join', 'create']):
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"      -> Clicked submit button: {btn_text[:20]}")
                        time.sleep(3)  # Wait for registration to process
                        return registration_data  # Return credentials for later login
                    except:
                        continue
            
            # If no submit button found, try form.submit()
            try:
                form.submit()
                print(f"      -> Submitted form directly")
                time.sleep(3)
                return registration_data  # Return credentials for later login
            except:
                pass
        
        return fields_filled > 0
        
    except Exception as e:
        print(f"      -> Enhanced form fill failed: {e}")
        return False

def enhanced_registration_input_fill(driver, inputs, url):
    """Enhanced input filling for registration when no form is detected"""
    try:
        print("      -> Enhanced registration input filling...")
        
        # Generate registration data
        import time
        timestamp = int(time.time())
        random_suffix = get_random_suffix()
        registration_data = {
            'username': f'user_{timestamp}_{random_suffix}',
            'email': f'user_{timestamp}_{random_suffix}@protonmail.com',
            'password': 'SecurePass123!',
        }
        
        # Categorize inputs
        email_inputs = []
        password_inputs = []
        text_inputs = []
        
        for inp in inputs:
            field_type = inp.get_attribute('type') or 'text'
            field_name = (inp.get_attribute('name') or '').lower()
            field_id = (inp.get_attribute('id') or '').lower()
            field_placeholder = (inp.get_attribute('placeholder') or '').lower()
            
            field_identifier = f"{field_name} {field_id} {field_placeholder}"
            
            if field_type == 'email' or 'email' in field_identifier:
                email_inputs.append(inp)
            elif field_type == 'password':
                password_inputs.append(inp)
            elif field_type == 'text':
                text_inputs.append(inp)
        
        fields_filled = 0
        
        # Fill email field
        if email_inputs:
            email_inputs[0].clear()
            email_inputs[0].send_keys(registration_data['email'])
            fields_filled += 1
        
        # Fill password fields
        for pwd_inp in password_inputs:
            pwd_inp.clear()
            pwd_inp.send_keys(registration_data['password'])
            fields_filled += 1
        
        # Fill first text input with username if no email field
        if not email_inputs and text_inputs:
            text_inputs[0].clear()
            text_inputs[0].send_keys(registration_data['username'])
            fields_filled += 1
        
        if fields_filled >= 2:
            # Try to submit by pressing Enter on last field
            from selenium.webdriver.common.keys import Keys
            if password_inputs:
                password_inputs[-1].send_keys(Keys.RETURN)
            elif text_inputs:
                text_inputs[-1].send_keys(Keys.RETURN)
            
            time.sleep(3)  # Wait for registration
            return True
        
        return False
        
    except Exception as e:
        print(f"      -> Enhanced input fill failed: {e}")
        return False

def ai_handle_checkout_form(driver, url, categories=None):
    """Enhanced checkout handling with comprehensive form filling and crypto selection"""
    try:
        print(f"💳 Enhanced checkout handling activated...")
        
        # Step 0: Wait for page to load and scroll to reveal all content
        time.sleep(2)
        scroll_entire_page(driver)
        time.sleep(1)
        
        # Step 1: Look for and handle crypto/payment method selection first
        print("   -> Step 1: Looking for crypto payment selection...")
        if handle_crypto_payment_selection(driver):
            print("   -> ✅ Crypto payment method selected")
            time.sleep(2)  # Wait for payment form to appear
        
        # Step 2: Enhanced form detection and filling
        print("   -> Step 2: Enhanced form detection and filling...")
        forms = driver.find_elements(By.TAG_NAME, 'form')
        
        # Prioritize checkout/billing forms
        checkout_forms = []
        for form in forms:
            form_html = form.get_attribute('outerHTML').lower()
            if any(keyword in form_html for keyword in ['checkout', 'billing', 'order', 'payment', 'address']):
                checkout_forms.append(form)
        
        # Try checkout forms first, then all forms
        forms_to_try = checkout_forms if checkout_forms else forms
        
        for form in forms_to_try:
            if enhanced_form_fill(driver, form, url, "checkout"):
                print("   -> ✅ Enhanced checkout form fill successful")
                
                # Step 3: After filling form, look for submit/place order button
                print("   -> Step 3: Looking for place order button...")
                if click_place_order_button(driver):
                    print("   -> ✅ Place order button clicked")
                    return True
        
        # Step 4: If no forms worked, try direct input filling
        print("   -> Step 4: Direct input field filling...")
        if enhanced_input_fill(driver, url):
            print("   -> ✅ Direct input fill successful")
            
            # Try to submit after filling
            if click_place_order_button(driver):
                print("   -> ✅ Place order button clicked after input fill")
                return True
        
        # Step 5: Last resort - try any prominent buttons
        print("   -> Step 5: Trying prominent buttons...")
        if click_checkout_buttons(driver):
            print("   -> ✅ Checkout button clicked")
            return True
        
        print("   -> ❌ All checkout methods failed")
        return False
        
    except Exception as e:
        print(f"⚠️ Enhanced checkout handling failed: {e}")
        return False

def handle_crypto_payment_selection(driver):
    """Enhanced crypto payment selection with comprehensive detection"""
    try:
        print("        🔍 Looking for crypto payment selection...")
        
        # Wait for payment options to load
        time.sleep(2)
        scroll_entire_page(driver)
        time.sleep(1)
        
        # Strategy 1: Look for crypto payment method sections/containers
        crypto_containers = [
            ".payment-method", ".payment-option", ".payment-methods", 
            ".checkout-payment", ".payment-section", "#payment-methods",
            ".woocommerce-checkout-payment", ".payment_methods"
        ]
        
        for container_selector in crypto_containers:
            try:
                containers = driver.find_elements(By.CSS_SELECTOR, container_selector)
                for container in containers:
                    if container.is_displayed():
                        container_text = container.text.lower()
                        if any(crypto in container_text for crypto in ["bitcoin", "btc", "crypto", "cryptocurrency", "digital currency"]):
                            print(f"        🎯 Found crypto payment container: {container_selector}")
                            # Look for clickable elements within this container
                            clickables = container.find_elements(By.XPATH, ".//input | .//button | .//a | .//label")
                            for clickable in clickables:
                                if clickable.is_displayed() and clickable.is_enabled():
                                    try:
                                        driver.execute_script("arguments[0].click();", clickable)
                                        print(f"        ✅ Clicked crypto payment in container: {clickable.text[:30]}")
                                        return True
                                    except:
                                        continue
            except:
                continue
        
        # Strategy 2: Look for Bitcoin/crypto radio buttons or checkboxes with enhanced detection
        crypto_input_selectors = [
            "//input[@type='radio'][contains(@name, 'payment') or contains(@name, 'method') or contains(@name, 'gateway')]",
            "//input[@type='checkbox'][contains(@name, 'payment') or contains(@name, 'method') or contains(@name, 'gateway')]",
            "//input[@type='radio'][contains(@value, 'bitcoin') or contains(@value, 'btc') or contains(@value, 'crypto')]",
            "//input[@type='radio'][contains(@id, 'bitcoin') or contains(@id, 'btc') or contains(@id, 'crypto')]"
        ]
        
        for selector in crypto_input_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if not elem.is_displayed() or not elem.is_enabled():
                        continue
                        
                    # Check if this element or its label mentions crypto
                    elem_text = ""
                    elem_value = elem.get_attribute('value') or ""
                    elem_id = elem.get_attribute('id') or ""
                    
                    # Get associated label text
                    try:
                        if elem_id:
                            label = driver.find_element(By.XPATH, f"//label[@for='{elem_id}']")
                            elem_text += " " + label.text.lower()
                    except:
                        pass
                    
                    # Check parent and sibling text
                    try:
                        parent = elem.find_element(By.XPATH, "..")
                        elem_text += " " + parent.text.lower()
                    except:
                        pass
                    
                    # Combine all text sources
                    all_text = f"{elem_text} {elem_value} {elem_id}".lower()
                    
                    if any(crypto in all_text for crypto in ["bitcoin", "btc", "crypto", "cryptocurrency", "digital currency"]):
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", elem)
                            print(f"        ✅ Selected crypto payment input: {all_text[:50]}")
                            
                            # Wait for crypto payment form to appear
                            time.sleep(2)
                            return True
                        except:
                            continue
            except:
                continue
        
        # Strategy 3: Look for Bitcoin/crypto buttons or links with enhanced patterns
        crypto_button_selectors = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bitcoin')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'btc')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'crypto')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bitcoin')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'btc')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'crypto')]",
            # Additional patterns
            "//button[contains(@class, 'bitcoin') or contains(@class, 'btc') or contains(@class, 'crypto')]",
            "//a[contains(@class, 'bitcoin') or contains(@class, 'btc') or contains(@class, 'crypto')]",
            "//div[contains(@class, 'payment') and contains(text(), 'Bitcoin')]//input",
            "//div[contains(@class, 'payment') and contains(text(), 'BTC')]//input"
        ]
        
        for selector in crypto_button_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", elem)
                            print(f"        ✅ Clicked crypto payment button: {elem.text[:30]}")
                            time.sleep(2)
                            return True
                        except:
                            continue
            except:
                continue
        
        # Strategy 4: Look for dropdown with crypto options (enhanced)
        try:
            selects = driver.find_elements(By.TAG_NAME, "select")
            for select in selects:
                select_name = select.get_attribute('name') or ""
                select_id = select.get_attribute('id') or ""
                
                # Check if this looks like a payment method selector
                if any(term in f"{select_name} {select_id}".lower() for term in ["payment", "method", "gateway", "currency"]):
                    options = select.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        option_text = option.text.lower()
                        option_value = option.get_attribute('value') or ""
                        
                        if any(crypto in f"{option_text} {option_value}".lower() for crypto in ["bitcoin", "btc", "crypto", "cryptocurrency"]):
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select)
                                time.sleep(0.5)
                                option.click()
                                print(f"        ✅ Selected crypto from dropdown: {option.text[:30]}")
                                time.sleep(2)
                                return True
                            except:
                                continue
        except:
            pass
        
        # Strategy 5: Look for payment gateway images/icons (many sites use Bitcoin logos)
        try:
            crypto_images = driver.find_elements(By.XPATH, "//img[contains(@src, 'bitcoin') or contains(@src, 'btc') or contains(@alt, 'bitcoin') or contains(@alt, 'btc')]")
            for img in crypto_images:
                if img.is_displayed():
                    # Try to find a clickable parent element
                    try:
                        clickable_parent = img.find_element(By.XPATH, "./ancestor::*[self::a or self::button or self::label or self::div[@onclick]]")
                        if clickable_parent.is_enabled():
                            driver.execute_script("arguments[0].click();", clickable_parent)
                            print(f"        ✅ Clicked crypto payment via image parent")
                            time.sleep(2)
                            return True
                    except:
                        # Try clicking the image itself
                        try:
                            driver.execute_script("arguments[0].click();", img)
                            print(f"        ✅ Clicked crypto payment image")
                            time.sleep(2)
                            return True
                        except:
                            continue
        except:
            pass
        
        print("        ❌ No crypto payment options found")
        return False
        
    except Exception as e:
        print(f"        ❌ Crypto payment selection failed: {e}")
        return False

def handle_platform_specific_country_selection(driver, field, platform_detected, field_id):
    """Handle country selection based on detected e-commerce platform with enhanced error handling"""
    try:
        print(f"        🛒 Using {platform_detected} specific country selection...")
        
        # Common imports
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.common.action_chains import ActionChains
        
        # Ensure field is visible and interactable
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
            time.sleep(0.3)
        except:
            pass
        
        if platform_detected == 'Shopify':
            # Shopify often uses searchable dropdowns - multiple approaches
            strategies = [
                # Strategy 1: Direct typing
                lambda: shopify_direct_typing(driver, field),
                # Strategy 2: Click and type
                lambda: shopify_click_type(driver, field),
                # Strategy 3: ActionChains approach
                lambda: shopify_action_chains(driver, field)
            ]
            
            for i, strategy in enumerate(strategies):
                try:
                    print(f"        🔍 Shopify strategy {i+1}/3...")
                    if strategy():
                        return True
                except Exception as e:
                    print(f"        ⚠️ Shopify strategy {i+1} failed: {e}")
                    continue
            return False
            
        elif platform_detected == 'WooCommerce':
            # WooCommerce often uses Select2 widgets
            return handle_woocommerce_select2(driver, field, field_id)
            
        elif platform_detected == 'Magento':
            # Magento typically uses standard selects with country codes
            return handle_magento_country(driver, field)
            
        elif platform_detected in ['BigCommerce', 'PrestaShop', 'OpenCart', 'PayPal']:
            # These typically use standard selects
            return handle_standard_select_country(driver, field)
            
        elif platform_detected == 'Stripe':
            # Stripe Elements often use custom inputs with autocomplete
            return handle_stripe_country(driver, field)
            
        elif platform_detected == 'Bootstrap/Foundation':
            # Try multiple approaches for Bootstrap forms
            return handle_bootstrap_country(driver, field)
            
        else:
            # Generic handling for unknown platforms - comprehensive approach
            return handle_generic_country_selection(driver, field)
            
    except Exception as e:
        print(f"        ❌ Platform-specific handling failed: {e}")
        return False

def shopify_direct_typing(driver, field):
    """Direct typing approach for Shopify"""
    field.click()
    time.sleep(0.5)
    field.clear()
    field.send_keys("United States")
    time.sleep(0.8)
    from selenium.webdriver.common.keys import Keys
    field.send_keys(Keys.ENTER)
    time.sleep(0.5)
    current_value = field.get_attribute('value') or ''
    return 'united states' in current_value.lower() or 'us' in current_value.lower()

def shopify_click_type(driver, field):
    """Click and type approach for Shopify"""
    driver.execute_script("arguments[0].click();", field)
    time.sleep(0.3)
    driver.execute_script("arguments[0].focus();", field)
    time.sleep(0.3)
    field.clear()
    time.sleep(0.2)
    field.send_keys("United States")
    time.sleep(1.0)
    from selenium.webdriver.common.keys import Keys
    field.send_keys(Keys.ENTER)
    time.sleep(0.8)
    current_value = field.get_attribute('value') or ''
    return 'united states' in current_value.lower() or 'us' in current_value.lower()

def shopify_action_chains(driver, field):
    """ActionChains approach for Shopify"""
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    
    actions = ActionChains(driver)
    actions.move_to_element(field).click().perform()
    time.sleep(0.5)
    actions.send_keys(Keys.CONTROL + "a").perform()  # Select all
    time.sleep(0.2)
    actions.send_keys("United States").perform()
    time.sleep(1.0)
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(0.8)
    current_value = field.get_attribute('value') or ''
    return 'united states' in current_value.lower() or 'us' in current_value.lower()

def handle_woocommerce_select2(driver, field, field_id):
    """Handle WooCommerce Select2 widgets"""
    try:
        print(f"        🛒 Handling WooCommerce Select2 widget...")
        
        # Find the Select2 container
        select2_container = driver.find_element(By.CSS_SELECTOR, f"#{field_id} + .select2-container")
        select2_selection = select2_container.find_element(By.CSS_SELECTOR, ".select2-selection")
        
        # Click the Select2 widget to open dropdown
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select2_selection)
        time.sleep(0.3)
        select2_selection.click()
        time.sleep(0.8)
        
        # Type in the search box that appears
        search_box = driver.find_element(By.CSS_SELECTOR, ".select2-search__field")
        search_box.send_keys("United States")
        time.sleep(1.0)
        
        from selenium.webdriver.common.keys import Keys
        search_box.send_keys(Keys.ENTER)
        time.sleep(0.8)
        
        # Verify selection
        selected_text = select2_selection.find_element(By.CSS_SELECTOR, ".select2-selection__rendered").text
        return 'united states' in selected_text.lower()
        
    except Exception as e:
        print(f"        ⚠️ Select2 approach failed: {e}")
        # Fallback to standard select approach
        return handle_standard_select_country(driver, field)

def handle_magento_country(driver, field):
    """Handle Magento country selection"""
    try:
        from selenium.webdriver.support.ui import Select
        select = Select(field)
        
        # Try by value first (Magento often uses country codes)
        for value in ['US', 'USA', 'United States', 'united_states']:
            try:
                select.select_by_value(value)
                return True
            except:
                continue
        
        # Try by visible text
        options = select.options
        for option in options:
            option_text = option.text.lower()
            if any(text in option_text for text in ['united states', 'usa', 'america']):
                select.select_by_visible_text(option.text)
                return True
        
        return False
    except Exception as e:
        print(f"        ⚠️ Magento selection failed: {e}")
        return False

def handle_standard_select_country(driver, field):
    """Handle standard HTML select elements"""
    try:
        from selenium.webdriver.support.ui import Select
        select = Select(field)
        options = select.options
        
        # Try to find US option by text
        for option in options:
            option_text = option.text.lower()
            if any(text in option_text for text in ['united states', 'usa', 'america']):
                select.select_by_visible_text(option.text)
                return True
        
        # Try by value
        for value in ['US', 'USA', 'United States']:
            try:
                select.select_by_value(value)
                return True
            except:
                continue
        
        return False
    except Exception as e:
        print(f"        ⚠️ Standard select failed: {e}")
        return False

def handle_stripe_country(driver, field):
    """Handle Stripe Elements country selection"""
    strategies = [
        # Strategy 1: Tab completion
        lambda: stripe_tab_approach(driver, field),
        # Strategy 2: Arrow key navigation
        lambda: stripe_arrow_approach(driver, field),
        # Strategy 3: Direct entry
        lambda: stripe_direct_approach(driver, field)
    ]
    
    for i, strategy in enumerate(strategies):
        try:
            print(f"        🔍 Stripe strategy {i+1}/3...")
            if strategy():
                return True
        except Exception as e:
            print(f"        ⚠️ Stripe strategy {i+1} failed: {e}")
            continue
    return False

def stripe_tab_approach(driver, field):
    """Stripe Tab completion approach"""
    field.click()
    time.sleep(0.3)
    field.clear()
    field.send_keys("United States")
    time.sleep(0.8)
    from selenium.webdriver.common.keys import Keys
    field.send_keys(Keys.TAB)
    time.sleep(0.5)
    current_value = field.get_attribute('value') or ''
    return 'united states' in current_value.lower() or 'us' in current_value.lower()

def stripe_arrow_approach(driver, field):
    """Stripe Arrow key navigation"""
    from selenium.webdriver.common.keys import Keys
    field.click()
    time.sleep(0.3)
    field.clear()
    field.send_keys("United States")
    time.sleep(0.8)
    field.send_keys(Keys.ARROW_DOWN)
    time.sleep(0.3)
    field.send_keys(Keys.ENTER)
    time.sleep(0.5)
    current_value = field.get_attribute('value') or ''
    return 'united states' in current_value.lower() or 'us' in current_value.lower()

def stripe_direct_approach(driver, field):
    """Stripe Direct entry approach"""
    field.click()
    time.sleep(0.3)
    field.clear()
    field.send_keys("United States")
    time.sleep(0.8)
    from selenium.webdriver.common.keys import Keys
    field.send_keys(Keys.ENTER)
    time.sleep(0.5)
    current_value = field.get_attribute('value') or ''
    return 'united states' in current_value.lower() or 'us' in current_value.lower()

def handle_bootstrap_country(driver, field):
    """Handle Bootstrap/Foundation forms"""
    # Try typing approach first (many Bootstrap forms use searchable selects)
    try:
        field.click()
        time.sleep(0.3)
        field.clear()
        field.send_keys("United States")
        time.sleep(0.8)
        from selenium.webdriver.common.keys import Keys
        field.send_keys(Keys.ENTER)
        time.sleep(0.5)
        current_value = field.get_attribute('value') or ''
        if 'united states' in current_value.lower() or 'us' in current_value.lower():
            return True
    except:
        pass
    
    # Fallback to standard select
    return handle_standard_select_country(driver, field)

def handle_generic_country_selection(driver, field):
    """Comprehensive generic country selection with multiple fallbacks"""
    strategies = [
        # Strategy 1: Enhanced typing with multiple confirmations
        lambda: generic_enhanced_typing(driver, field),
        # Strategy 2: Standard select approach
        lambda: handle_standard_select_country(driver, field),
        # Strategy 3: JavaScript injection
        lambda: generic_javascript_injection(driver, field),
        # Strategy 4: ActionChains approach
        lambda: generic_action_chains(driver, field)
    ]
    
    for i, strategy in enumerate(strategies):
        try:
            print(f"        🔍 Generic strategy {i+1}/4...")
            if strategy():
                return True
        except Exception as e:
            print(f"        ⚠️ Generic strategy {i+1} failed: {e}")
            continue
    return False

def generic_enhanced_typing(driver, field):
    """Enhanced typing with multiple confirmation methods"""
    from selenium.webdriver.common.keys import Keys
    
    # Ensure field is focused
    driver.execute_script("arguments[0].focus();", field)
    time.sleep(0.3)
    field.click()
    time.sleep(0.3)
    
    # Clear and type
    field.clear()
    time.sleep(0.2)
    field.send_keys("United States")
    time.sleep(1.0)
    
    # Try multiple confirmation methods
    confirmation_methods = [Keys.ENTER, Keys.TAB, Keys.ARROW_DOWN + Keys.ENTER]
    
    for method in confirmation_methods:
        try:
            if isinstance(method, str):
                field.send_keys(method)
            else:
                field.send_keys(method)
            time.sleep(0.8)
            
            current_value = field.get_attribute('value') or ''
            if 'united states' in current_value.lower() or 'us' in current_value.lower():
                return True
        except:
            continue
    
    return False

def generic_javascript_injection(driver, field):
    """JavaScript injection approach"""
    try:
        # Try setting value directly
        driver.execute_script("arguments[0].value = 'United States';", field)
        time.sleep(0.3)
        
        # Trigger change event
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", field)
        time.sleep(0.3)
        
        current_value = field.get_attribute('value') or ''
        return 'united states' in current_value.lower() or 'us' in current_value.lower()
    except:
        return False

def generic_action_chains(driver, field):
    """ActionChains approach for generic fields"""
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    
    try:
        actions = ActionChains(driver)
        actions.move_to_element(field).click().perform()
        time.sleep(0.5)
        actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()  # Select all
        time.sleep(0.2)
        actions.send_keys("United States").perform()
        time.sleep(1.0)
        actions.send_keys(Keys.ENTER).perform()
        time.sleep(0.8)
        
        current_value = field.get_attribute('value') or ''
        return 'united states' in current_value.lower() or 'us' in current_value.lower()
    except:
        return False

def enhanced_form_fill(driver, form, url, form_type):
    """Enhanced form filling with better field detection"""
    try:
        print("        Enhanced form filling...")
        
        # Enhanced fake data for checkout
        random_suffix = get_random_suffix()
        checkout_data = {
            'email': f'john.doe{random_suffix}@protonmail.com',
            'firstname': f'John{random_suffix}',
            'lastname': f'Doe{random_suffix}',
            'fullname': f'John Doe {random_suffix}',
            'company': 'Tech Corp',
            'address1': '123 Main Street',
            'address2': 'Apt 4B',
            'street': '123 Main Street',
            'city': 'New York',
            'state': 'NY',
            'zip': '10001',
            'postal': '10001',
            'country': 'US',
            'phone': '+1-555-123-4567',
            'mobile': '+1-555-123-4567'
        }
        
        # Get all form fields
        inputs = form.find_elements(By.TAG_NAME, 'input')
        textareas = form.find_elements(By.TAG_NAME, 'textarea')
        selects = form.find_elements(By.TAG_NAME, 'select')
        all_fields = inputs + textareas + selects
        
        fields_filled = 0
        country_fields = []  # Store country fields for last
        
        # PHASE 1: Fill all non-country fields first
        print("        📝 Phase 1: Filling all non-country fields...")
        
        for field in all_fields:
            try:
                if not field.is_displayed() or not field.is_enabled():
                    continue
                    
                field_type = field.get_attribute('type') or ''
                field_name = field.get_attribute('name') or ''
                field_id = field.get_attribute('id') or ''
                field_placeholder = field.get_attribute('placeholder') or ''
                
                # Get label text if available
                label_text = ""
                try:
                    if field_id:
                        label = driver.find_element(By.XPATH, f"//label[@for='{field_id}']")
                        label_text = label.text.lower()
                except:
                    pass
                
                # Combine all identifiers including label text
                field_text = f"{field_name} {field_id} {field_placeholder} {label_text}".lower()
                
                # Debug logging for all fields
                if field.tag_name == 'select':
                    print(f"        🔍 Found dropdown - Name: '{field_name}', ID: '{field_id}', Placeholder: '{field_placeholder}', Label: '{label_text}'")
                    # Also log first few options to see what's in the dropdown
                    try:
                        options = field.find_elements(By.TAG_NAME, 'option')
                        option_texts = [opt.text for opt in options[:5]]
                        print(f"        📋 First 5 options: {option_texts}")
                    except:
                        pass
                
                value_to_fill = None
                
                # Enhanced field matching for all form fields
                if field_type == 'password' or any(word in field_text for word in ['password', 'pass', 'pwd']):
                    value_to_fill = 'SecurePass123!'
                elif any(word in field_text for word in ['email', 'mail']):
                    value_to_fill = checkout_data['email']
                elif any(word in field_text for word in ['first', 'fname']) or 'first name as in id' in field_text:
                    value_to_fill = checkout_data['firstname']
                elif any(word in field_text for word in ['last', 'lname', 'surname']) or 'last name as in id' in field_text:
                    value_to_fill = checkout_data['lastname']
                elif any(word in field_text for word in ['full', 'name']) and 'first' not in field_text and 'last' not in field_text:
                    value_to_fill = checkout_data['fullname']
                elif any(word in field_text for word in ['company', 'business', 'organization']):
                    value_to_fill = checkout_data['company']
                elif any(word in field_text for word in ['address1', 'address_1', 'street1', 'street_1']):
                    value_to_fill = checkout_data['address1']
                elif any(word in field_text for word in ['address2', 'address_2', 'street2', 'street_2']):
                    value_to_fill = checkout_data['address2']
                elif any(word in field_text for word in ['street', 'address']) and '2' not in field_text:
                    value_to_fill = checkout_data['street']
                elif any(word in field_text for word in ['city', 'town']) or 'town / city' in field_text:
                    value_to_fill = checkout_data['city']
                elif any(word in field_text for word in ['state', 'province', 'region']):
                    value_to_fill = checkout_data['state']
                elif any(word in field_text for word in ['zip', 'postal', 'postcode']) or 'postcode / zip' in field_text:
                    value_to_fill = checkout_data['zip']
                elif any(word in field_text for word in ['country']):
                    # SKIP country fields for now - handle them last
                    country_fields.append(field)
                    print(f"        🌍 Found country field, saving for last: {field_name or field_id}")
                    continue
                elif any(word in field_text for word in ['phone', 'telephone', 'mobile']):
                    value_to_fill = checkout_data['phone']
                elif any(word in field_text for word in ['username', 'user', 'account']):
                    value_to_fill = 'johndoe123'
                elif any(word in field_text for word in ['note', 'notes', 'comment', 'additional', 'order notes']):
                    value_to_fill = 'Standard delivery please'
                # Catch-all for any remaining required text fields
                elif field_type in ['text', 'email', 'tel'] and not value_to_fill:
                    # Try to guess based on field position or common patterns
                    if 'required' in field.get_attribute('class') or '' or field.get_attribute('required'):
                        if not value_to_fill:
                            value_to_fill = 'DefaultValue'
                
                # Handle select fields with safer approach
                if field.tag_name == 'select' and not value_to_fill:
                    try:
                        # Wait for dropdown to be ready
                        time.sleep(0.5)
                        
                        # Check if dropdown is interactable
                        if not field.is_displayed() or not field.is_enabled():
                            continue
                            
                        # Use Selenium Select class for safer dropdown handling
                        from selenium.webdriver.support.ui import Select
                        select = Select(field)
                        options = select.options
                        
                        # Enhanced country/region detection with more patterns
                        is_country_field = (
                            any(word in field_text for word in ['country', 'region', 'billing']) or
                            'select a country' in field_text or
                            'choose country' in field_text or
                            'billing country' in field_text or
                            'country / region' in field_text or
                            'select a country / region' in field_text or
                            'country/region' in field_text or
                            # Check for common field names/IDs
                            any(word in field_name for word in ['country', 'region', 'billing_country']) or
                            any(word in field_id for word in ['country', 'region', 'billing_country']) or
                            # Check placeholder text specifically
                            'select a country / region...' in field_placeholder.lower() or
                            # WooCommerce specific patterns
                            field_name == 'billing_country' or field_id == 'billing_country'
                        )
                        
                        # Comprehensive e-commerce platform detection
                        try:
                            field_classes = field.get_attribute('class') or ''
                            page_html = driver.page_source.lower()
                            
                            platform_detected = 'unknown'
                            is_select2_field = False
                            
                            # 1. WooCommerce (WordPress)
                            if ('woocommerce' in page_html or 'select2-hidden-accessible' in field_classes or
                                field_name == 'billing_country' or field_id == 'billing_country'):
                                platform_detected = 'WooCommerce'
                                is_select2_field = True
                            
                            # 2. Shopify
                            elif ('shopify' in page_html or 'checkout.shopify.com' in driver.current_url or
                                  'shopify-checkout' in field_classes or 'field__input' in field_classes):
                                platform_detected = 'Shopify'
                            
                            # 3. Magento
                            elif ('magento' in page_html or 'mage-' in field_classes or
                                  'checkout-billing-address' in field_classes):
                                platform_detected = 'Magento'
                            
                            # 4. BigCommerce
                            elif ('bigcommerce' in page_html or 'bc-' in field_classes):
                                platform_detected = 'BigCommerce'
                            
                            # 5. Stripe Checkout
                            elif ('stripe' in page_html or 'stripe-checkout' in field_classes):
                                platform_detected = 'Stripe'
                            
                            # 6. PayPal Checkout
                            elif ('paypal' in page_html or 'paypal-checkout' in field_classes):
                                platform_detected = 'PayPal'
                            
                            # 7. PrestaShop
                            elif ('prestashop' in page_html or 'ps-' in field_classes):
                                platform_detected = 'PrestaShop'
                            
                            # 8. OpenCart
                            elif ('opencart' in page_html or 'oc-' in field_classes):
                                platform_detected = 'OpenCart'
                            
                            # 9. Bootstrap/Foundation
                            elif ('form-control' in field_classes or 'form-select' in field_classes):
                                platform_detected = 'Bootstrap/Foundation'
                            
                            if platform_detected != 'unknown':
                                print(f"        🛒 Detected {platform_detected} checkout system")
                        except:
                            pass
                        
                        # Additional fallback: check if this looks like a country dropdown by examining options
                        if not is_country_field and len(options) > 5:
                            try:
                                # Sample first few options to see if they look like countries
                                sample_text = ' '.join([opt.text.lower() for opt in options[:8]])
                                country_keywords = ['united states', 'canada', 'australia', 'germany', 'france', 'united kingdom', 'ukraine', 'uruguay']
                                if sum(1 for keyword in country_keywords if keyword in sample_text) >= 2:
                                    is_country_field = True
                                    print(f"        🔍 Detected country field by analyzing dropdown options")
                            except:
                                pass
                        
                        if is_country_field or is_select2_field:
                            # SKIP country fields for now - handle them last
                            country_fields.append((field, platform_detected, field_id, is_select2_field))
                            print(f"        🌍 Found country dropdown, saving for last: {field_name or field_id} (Platform: {platform_detected})")
                            continue
                        
                        elif 'state' in field_text or 'province' in field_text:
                            print(f"        🔍 Processing state dropdown...")
                            # Look for NY option using Select class
                            for option in options:
                                option_text = option.text.lower()
                                option_value = option.get_attribute('value') or ''
                                if 'new york' in option_text or option_value in ['NY', 'New York']:
                                    try:
                                        select.select_by_visible_text(option.text)
                                        fields_filled += 1
                                        print(f"        ✅ Selected state: {option.text}")
                                        time.sleep(1)
                                        break
                                    except:
                                        try:
                                            select.select_by_value(option_value)
                                            fields_filled += 1
                                            print(f"        ✅ Selected state by value: {option_value}")
                                            time.sleep(1)
                                            break
                                        except:
                                            continue
                        
                        else:
                            # For other dropdowns, first check if it might be a country field we missed
                            might_be_country = False
                            if len(options) > 5:
                                try:
                                    # Check if dropdown contains many country-like options
                                    all_option_text = ' '.join([opt.text.lower() for opt in options])
                                    country_count = sum(1 for country in ['united states', 'canada', 'australia', 'germany', 'france', 'united kingdom', 'ukraine', 'uruguay', 'united arab emirates'] if country in all_option_text)
                                    if country_count >= 3:
                                        might_be_country = True
                                        print(f"        🔍 Dropdown appears to be country field (found {country_count} countries)")
                                except:
                                    pass
                            
                            if might_be_country:
                                # Try the same country selection logic
                                found_country = False
                                
                                # Try typing first with robust clicking
                                try:
                                    print(f"        🔍 Clicking potential country field to enable typing...")
                                    
                                    # Scroll and focus the field properly
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
                                    time.sleep(0.2)
                                    
                                    # Multiple click attempts
                                    field.click()
                                    time.sleep(0.2)
                                    driver.execute_script("arguments[0].click();", field)
                                    time.sleep(0.2)
                                    driver.execute_script("arguments[0].focus();", field)
                                    time.sleep(0.3)
                                    
                                    # Clear and type
                                    field.clear()
                                    time.sleep(0.1)
                                    print(f"        ⌨️ Typing into potential country field...")
                                    field.send_keys("United States")
                                    time.sleep(0.8)
                                    
                                    from selenium.webdriver.common.keys import Keys
                                    field.send_keys(Keys.ENTER)
                                    time.sleep(0.5)
                                    
                                    current_value = field.get_attribute('value') or ''
                                    if 'united states' in current_value.lower() or 'us' in current_value.lower():
                                        fields_filled += 1
                                        found_country = True
                                        print(f"        ✅ Typed into potential country field: {current_value}")
                                except:
                                    pass
                                
                                # Fall back to dropdown selection
                                if not found_country:
                                    for option in options:
                                        option_text = option.text.lower()
                                        if 'united states' in option_text or option_text == 'us':
                                            try:
                                                select.select_by_visible_text(option.text)
                                                fields_filled += 1
                                                found_country = True
                                                print(f"        ✅ Selected from potential country dropdown: {option.text}")
                                                break
                                            except:
                                                continue
                            else:
                                # For non-country dropdowns, be very conservative
                                try:
                                    if len(options) > 1 and options[1].get_attribute('value'):
                                        select.select_by_index(1)  # Select second option (first is usually empty)
                                        fields_filled += 1
                                        print(f"        ✅ Selected dropdown option: {options[1].text}")
                                        time.sleep(0.5)
                                except Exception as e:
                                    print(f"        ⚠️ Skipping dropdown to avoid page issues: {e}")
                                
                    except Exception as e:
                        print(f"        ❌ Dropdown handling failed, continuing with other fields: {e}")
                        # Don't let dropdown failures break the entire form filling
                
                # BRUTE FORCE: Try to fill ANY dropdown that might be a country field
                elif field.tag_name == 'select' and not value_to_fill:
                    try:
                        print(f"        🚨 BRUTE FORCE: Trying to fill dropdown as country field...")
                        options = field.find_elements(By.TAG_NAME, 'option')
                        
                        # Check if any option looks like "United States"
                        us_option = None
                        for option in options:
                            option_text = option.text.lower()
                            if any(pattern in option_text for pattern in ['united states', 'usa', 'us (', 'us)', 'america']):
                                us_option = option
                                break
                        
                        if us_option:
                            print(f"        🎯 Found US option in dropdown: '{us_option.text}'")
                            
                            # Try multiple selection methods
                            methods_tried = []
                            
                            # Method 1: Direct click
                            try:
                                driver.execute_script("arguments[0].scrollIntoView();", us_option)
                                time.sleep(0.3)
                                us_option.click()
                                fields_filled += 1
                                methods_tried.append("direct_click")
                                print(f"        ✅ BRUTE FORCE: Selected US via direct click")
                            except Exception as e1:
                                methods_tried.append(f"direct_click_failed: {e1}")
                                
                                # Method 2: JavaScript click
                                try:
                                    driver.execute_script("arguments[0].click();", us_option)
                                    fields_filled += 1
                                    methods_tried.append("js_click")
                                    print(f"        ✅ BRUTE FORCE: Selected US via JavaScript click")
                                except Exception as e2:
                                    methods_tried.append(f"js_click_failed: {e2}")
                                    
                                    # Method 3: Select class
                                    try:
                                        from selenium.webdriver.support.ui import Select
                                        select = Select(field)
                                        select.select_by_visible_text(us_option.text)
                                        fields_filled += 1
                                        methods_tried.append("select_by_text")
                                        print(f"        ✅ BRUTE FORCE: Selected US via Select class")
                                    except Exception as e3:
                                        methods_tried.append(f"select_by_text_failed: {e3}")
                                        
                                        # Method 4: Try typing approach on the dropdown
                                        try:
                                            field.click()
                                            time.sleep(0.3)
                                            field.send_keys("United States")
                                            time.sleep(0.5)
                                            from selenium.webdriver.common.keys import Keys
                                            field.send_keys(Keys.ENTER)
                                            time.sleep(0.5)
                                            fields_filled += 1
                                            methods_tried.append("typing")
                                            print(f"        ✅ BRUTE FORCE: Selected US via typing")
                                        except Exception as e4:
                                            methods_tried.append(f"typing_failed: {e4}")
                            
                            print(f"        📊 BRUTE FORCE methods tried: {methods_tried}")
                        else:
                            print(f"        ❌ BRUTE FORCE: No US option found in dropdown")
                            
                    except Exception as e:
                        print(f"        ❌ BRUTE FORCE approach failed: {e}")
                
                # Fill text inputs
                elif value_to_fill and field.tag_name in ['input', 'textarea']:
                    try:
                        field.clear()
                        field.send_keys(value_to_fill)
                        fields_filled += 1
                    except:
                        try:
                            driver.execute_script("arguments[0].value = arguments[1];", field, value_to_fill)
                            fields_filled += 1
                        except:
                            pass
                            
            except:
                continue
        
        # PHASE 2: Now handle country fields with dedicated time and attention
        print(f"        🌍 Phase 2: Handling {len(country_fields)} country fields as final step...")
        
        if country_fields:
            # Wait a bit for the form to settle
            time.sleep(2)
            scroll_entire_page(driver)
            time.sleep(1)
            
            for country_data in country_fields:
                try:
                    if isinstance(country_data, tuple):
                        # This is a select field with platform info
                        field, platform_detected, field_id, is_select2_field = country_data
                        print(f"        🌍 Processing country dropdown: {field.get_attribute('name') or field_id} (Platform: {platform_detected})")
                        
                        if handle_country_field_final(driver, field, platform_detected, field_id, is_select2_field):
                            fields_filled += 1
                            print(f"        ✅ Country dropdown filled successfully!")
                        else:
                            print(f"        ❌ Country dropdown failed")
                    else:
                        # This is a regular input field
                        field = country_data
                        print(f"        🌍 Processing country input: {field.get_attribute('name') or field.get_attribute('id')}")
                        
                        if handle_country_input_final(driver, field):
                            fields_filled += 1
                            print(f"        ✅ Country input filled successfully!")
                        else:
                            print(f"        ❌ Country input failed")
                            
                except Exception as e:
                    print(f"        ❌ Error processing country field: {e}")
                    continue
        
        print(f"        ✅ Filled {fields_filled} fields in form (including {len([f for f in country_fields if f])} country fields)")
        return fields_filled > 0
        
    except Exception as e:
        print(f"        ❌ Enhanced form fill failed: {e}")
        return False

def handle_country_field_final(driver, field, platform_detected, field_id, is_select2_field):
    """Dedicated final country field handling with maximum time and attention"""
    try:
        print(f"        🎯 FINAL COUNTRY ATTEMPT: Taking extra time for {platform_detected} field...")
        
        # Extra scrolling and focusing
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
        time.sleep(1)
        
        # Try platform-specific handling first
        if platform_detected != 'unknown' and not is_select2_field:
            print(f"        🛒 Trying platform-specific approach for {platform_detected}...")
            if handle_platform_specific_country_selection(driver, field, platform_detected, field_id):
                return True
        
        # Special Select2 handling
        if is_select2_field:
            print(f"        🛒 Trying Select2 approach with extra time...")
            try:
                # Strategy 1: Find the Select2 container by field ID
                select2_container = None
                select2_selection = None
                
                try:
                    select2_container = driver.find_element(By.CSS_SELECTOR, f"#{field_id} + .select2-container")
                    select2_selection = select2_container.find_element(By.CSS_SELECTOR, ".select2-selection")
                    print(f"        ✅ Found Select2 container by field ID")
                except:
                    # Strategy 2: Find any Select2 container near country fields
                    try:
                        select2_containers = driver.find_elements(By.CSS_SELECTOR, ".select2-container")
                        for container in select2_containers:
                            # Check if this container is for a country field
                            try:
                                selection = container.find_element(By.CSS_SELECTOR, ".select2-selection")
                                selection_text = selection.text.lower()
                                if any(country_hint in selection_text for country_hint in ['country', 'select country', 'united states', 'choose']):
                                    select2_container = container
                                    select2_selection = selection
                                    print(f"        ✅ Found Select2 container by country text: {selection_text}")
                                    break
                            except:
                                continue
                    except:
                        pass
                
                if not select2_container or not select2_selection:
                    print(f"        ❌ Could not find Select2 container")
                    return False
                
                # Scroll to the element first
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select2_selection)
                time.sleep(1)
                
                # Click to open the dropdown
                print(f"        🔍 Clicking Select2 container to open dropdown...")
                print(f"        📋 Current selection text: '{select2_selection.text}'")
                
                # Try multiple click methods
                try:
                    select2_selection.click()
                    print(f"        ✅ Clicked with .click()")
                except:
                    try:
                        driver.execute_script("arguments[0].click();", select2_selection)
                        print(f"        ✅ Clicked with JavaScript")
                    except:
                        # Try clicking the arrow/trigger
                        try:
                            arrow = select2_container.find_element(By.CSS_SELECTOR, ".select2-selection__arrow")
                            arrow.click()
                            print(f"        ✅ Clicked Select2 arrow")
                        except:
                            print(f"        ❌ All click methods failed")
                            return False
                
                # Wait for dropdown to open
                time.sleep(2)
                
                # Verify dropdown is open by looking for search field
                try:
                    search_field = driver.find_element(By.CSS_SELECTOR, ".select2-search__field")
                    if search_field.is_displayed():
                        print(f"        ✅ Dropdown opened successfully - search field is visible")
                    else:
                        print(f"        ⚠️ Search field found but not visible")
                        # Try clicking again
                        select2_selection.click()
                        time.sleep(1)
                except:
                    print(f"        ❌ Dropdown may not have opened - search field not found")
                    # Try clicking again
                    try:
                        select2_selection.click()
                        time.sleep(2)
                    except:
                        pass
                
                # Find the search field
                search_box = driver.find_element(By.CSS_SELECTOR, ".select2-search__field")
                print(f"        ⌨️ Typing 'United States' in search field...")
                search_box.clear()
                time.sleep(0.5)
                search_box.send_keys("United States")
                time.sleep(3)  # Extra time for filtering and results to appear
                
                # Strategy 1: Try to click the US result directly
                try:
                    print(f"        🎯 Looking for US result in dropdown...")
                    
                    # Look for the results container using aria-owns attribute
                    aria_owns = search_box.get_attribute('aria-owns')
                    print(f"        📋 Results container ID: {aria_owns}")
                    
                    if aria_owns:
                        # Try to find results by the specific container ID
                        results_container = driver.find_element(By.ID, aria_owns)
                        us_options = results_container.find_elements(By.XPATH, ".//li[contains(text(), 'United States') or contains(text(), 'USA') or contains(@id, 'US')]")
                        
                        if us_options:
                            print(f"        ✅ Found {len(us_options)} US option(s), clicking first one...")
                            driver.execute_script("arguments[0].click();", us_options[0])
                            time.sleep(2)
                            
                            # Verify selection
                            selected_text = select2_selection.find_element(By.CSS_SELECTOR, ".select2-selection__rendered").text
                            if 'united states' in selected_text.lower():
                                print(f"        ✅ Select2 direct click successful: {selected_text}")
                                return True
                        else:
                            print(f"        ⚠️ No US options found in results container")
                    
                except Exception as result_error:
                    print(f"        ⚠️ Direct result click failed: {result_error}")
                
                # Strategy 2: Try generic result selectors
                try:
                    print(f"        🔍 Trying generic Select2 result selectors...")
                    generic_selectors = [
                        "//li[contains(@class, 'select2-results__option') and contains(text(), 'United States')]",
                        "//li[contains(@class, 'select2-results__option') and contains(text(), 'USA')]", 
                        "//li[contains(@class, 'select2-results__option') and contains(@id, 'US')]",
                        ".select2-results__option:contains('United States')",
                        ".select2-results__option:contains('USA')"
                    ]
                    
                    for selector in generic_selectors:
                        try:
                            if selector.startswith("//"):
                                elements = driver.find_elements(By.XPATH, selector)
                            else:
                                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            
                            if elements:
                                print(f"        ✅ Found option with selector: {selector}")
                                driver.execute_script("arguments[0].click();", elements[0])
                                time.sleep(2)
                                
                                selected_text = select2_selection.find_element(By.CSS_SELECTOR, ".select2-selection__rendered").text
                                if 'united states' in selected_text.lower():
                                    print(f"        ✅ Select2 generic click successful: {selected_text}")
                                    return True
                        except:
                            continue
                            
                except Exception as generic_error:
                    print(f"        ⚠️ Generic selectors failed: {generic_error}")
                
                # Strategy 3: Try Enter key as fallback
                try:
                    print(f"        ⌨️ Trying Enter key as fallback...")
                    from selenium.webdriver.common.keys import Keys
                    search_box.send_keys(Keys.ENTER)
                    time.sleep(2)  # Extra time for filtering and results to appear
                    
                    selected_text = select2_selection.find_element(By.CSS_SELECTOR, ".select2-selection__rendered").text
                    if 'united states' in selected_text.lower():
                        print(f"        ✅ Select2 Enter key successful: {selected_text}")
                        return True
                        
                except Exception as enter_error:
                    print(f"        ⚠️ Enter key failed: {enter_error}")
                
                # Strategy 4: Try Arrow Down + Enter
                try:
                    print(f"        🔽 Trying Arrow Down + Enter...")
                    search_box.send_keys(Keys.ARROW_DOWN)
                    time.sleep(1)
                    search_box.send_keys(Keys.ENTER)
                    time.sleep(2)
                    
                    selected_text = select2_selection.find_element(By.CSS_SELECTOR, ".select2-selection__rendered").text
                    if 'united states' in selected_text.lower():
                        print(f"        ✅ Select2 Arrow+Enter successful: {selected_text}")
                        return True
                        
                except Exception as arrow_error:
                    print(f"        ⚠️ Arrow+Enter failed: {arrow_error}")
                
                print(f"        ❌ All Select2 strategies failed")
                return False
                
            except Exception as e:
                print(f"        ⚠️ Select2 approach failed: {e}")
        
        # Enhanced typing approach with maximum time
        print(f"        ⌨️ Trying enhanced typing approach with maximum time...")
        try:
            # Multiple focus attempts
            driver.execute_script("arguments[0].focus();", field)
            time.sleep(0.5)
            field.click()
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", field)
            time.sleep(1)
            
            # Clear thoroughly
            field.clear()
            time.sleep(0.5)
            driver.execute_script("arguments[0].value = '';", field)
            time.sleep(0.5)
            
            # Type slowly
            field.send_keys("United States")
            time.sleep(2)  # Extra time for autocomplete
            
            from selenium.webdriver.common.keys import Keys
            
            # Try Enter first
            field.send_keys(Keys.ENTER)
            time.sleep(2)  # Extra time for filtering and results to appear
            
            # Check if it worked
            current_value = field.get_attribute('value') or ''
            if 'united states' in current_value.lower() or 'us' in current_value.lower():
                return True
            
            # Try Tab if Enter didn't work
            print(f"        🔄 Enter didn't work, trying Tab...")
            field.clear()
            time.sleep(0.5)
            field.send_keys("United States")
            time.sleep(2)
            field.send_keys(Keys.TAB)
            time.sleep(2)
            
            current_value = field.get_attribute('value') or ''
            if 'united states' in current_value.lower() or 'us' in current_value.lower():
                return True
                
        except Exception as e:
            print(f"        ⚠️ Enhanced typing failed: {e}")
        
        # Fallback to dropdown selection
        print(f"        📋 Trying dropdown selection as final fallback...")
        try:
            from selenium.webdriver.support.ui import Select
            select = Select(field)
            options = select.options
            
            for option in options:
                option_text = option.text.lower()
                option_value = option.get_attribute('value') or ''
                if any(country in option_text for country in ['united states', 'usa', 'us']) or option_value in ['US', 'USA', 'united_states']:
                    try:
                        select.select_by_visible_text(option.text)
                        time.sleep(1)
                        return True
                    except:
                        try:
                            select.select_by_value(option_value)
                            time.sleep(1)
                            return True
                        except:
                            continue
        except:
            pass
        
        return False
        
    except Exception as e:
        print(f"        ❌ Final country field handling failed: {e}")
        return False

def handle_country_input_final(driver, field):
    """Dedicated final country input handling with maximum time and attention"""
    try:
        print(f"        🎯 FINAL COUNTRY INPUT: Taking extra time...")
        
        # Extra scrolling and focusing
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
        time.sleep(1)
        
        # Multiple focus attempts
        driver.execute_script("arguments[0].focus();", field)
        time.sleep(0.5)
        field.click()
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", field)
        time.sleep(1)
        
        # Clear thoroughly
        field.clear()
        time.sleep(0.5)
        driver.execute_script("arguments[0].value = '';", field)
        time.sleep(0.5)
        
        # Type slowly and deliberately
        field.send_keys("United States")
        time.sleep(2)  # Extra time
        
        from selenium.webdriver.common.keys import Keys
        
        # Try Enter
        field.send_keys(Keys.ENTER)
        time.sleep(2)
        
        # Check if it worked
        current_value = field.get_attribute('value') or ''
        if 'united states' in current_value.lower() or 'us' in current_value.lower():
            return True
        
        # Try Tab
        print(f"        🔄 Enter didn't work, trying Tab...")
        field.clear()
        time.sleep(0.5)
        field.send_keys("United States")
        time.sleep(2)
        field.send_keys(Keys.TAB)
        time.sleep(2)
        
        current_value = field.get_attribute('value') or ''
        return 'united states' in current_value.lower() or 'us' in current_value.lower()
        
    except Exception as e:
        print(f"        ❌ Final country input handling failed: {e}")
        return False

def enhanced_input_fill(driver, url):
    """Enhanced input filling for checkout pages"""
    try:
        print("        Enhanced input filling...")
        
        # Get all visible inputs
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        visible_inputs = [inp for inp in inputs if inp.is_displayed() and inp.is_enabled()]
        
        if len(visible_inputs) < 2:
            return False
        
        checkout_data = {
            'email': 'john.doe@protonmail.com',
            'name': 'John Doe',
            'address': '123 Main Street',
            'city': 'New York',
            'zip': '10001',
            'phone': '+1-555-123-4567'
        }
        
        fields_filled = 0
        
        for inp in visible_inputs:
            try:
                field_type = inp.get_attribute('type') or 'text'
                field_name = inp.get_attribute('name') or ''
                field_placeholder = inp.get_attribute('placeholder') or ''
                
                field_text = f"{field_name} {field_placeholder}".lower()
                
                if field_type == 'email' or 'email' in field_text:
                    inp.clear()
                    inp.send_keys(checkout_data['email'])
                    fields_filled += 1
                elif 'name' in field_text:
                    inp.clear()
                    inp.send_keys(checkout_data['name'])
                    fields_filled += 1
                elif 'address' in field_text:
                    inp.clear()
                    inp.send_keys(checkout_data['address'])
                    fields_filled += 1
                elif 'city' in field_text:
                    inp.clear()
                    inp.send_keys(checkout_data['city'])
                    fields_filled += 1
                elif 'zip' in field_text or 'postal' in field_text:
                    inp.clear()
                    inp.send_keys(checkout_data['zip'])
                    fields_filled += 1
                elif 'phone' in field_text:
                    inp.clear()
                    inp.send_keys(checkout_data['phone'])
                    fields_filled += 1
            except:
                continue
        
        print(f"        ✅ Filled {fields_filled} input fields")
        return fields_filled > 0
        
    except Exception as e:
        print(f"        ❌ Enhanced input fill failed: {e}")
        return False

def click_place_order_button(driver):
    """Look for and click place order/submit buttons"""
    try:
        print("        Looking for place order button...")
        
        order_texts = [
            "place order", "submit order", "complete order", "confirm order",
            "place your order", "submit", "confirm", "complete purchase",
            "finish", "pay now", "order now"
        ]
        
        for text in order_texts:
            selectors = [
                f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
                f"//input[@type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
                f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            driver.execute_script("arguments[0].click();", elem)
                            print(f"        ✅ Clicked place order button: {elem.text[:30]}")
                            return True
                except:
                    continue
        
        # Fallback: look for any submit button
        try:
            submit_buttons = driver.find_elements(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
            for btn in submit_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"        ✅ Clicked submit button: {btn.get_attribute('value') or btn.text}")
                    return True
        except:
            pass
        
        return False
        
    except Exception as e:
        print(f"        ❌ Place order button click failed: {e}")
        return False

def click_checkout_buttons(driver):
    """Last resort: click any checkout-related buttons"""
    try:
        print("        Looking for any checkout buttons...")
        
        buttons = driver.find_elements(By.TAG_NAME, "button")
        buttons.extend(driver.find_elements(By.XPATH, "//input[@type='submit']"))
        
        for btn in buttons:
            if not btn.is_displayed() or not btn.is_enabled():
                continue
                
            btn_text = btn.text.lower() if btn.text else ""
            btn_value = btn.get_attribute('value') or ""
            btn_value = btn_value.lower()
            
            if any(word in btn_text or word in btn_value for word in [
                "submit", "continue", "next", "proceed", "confirm", "order", "checkout"
            ]):
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"        ✅ Clicked checkout button: {btn.text[:30] or btn_value[:30]}")
                    return True
                except:
                    continue
        
        return False
        
    except Exception as e:
        print(f"        ❌ Checkout button click failed: {e}")
        return False

def attempt_form_fill(driver, form, url, form_type):
    """Attempt to fill any form with fake data, covering all common fields"""
    try:
        # Expanded fake user data
        random_suffix = get_random_suffix()
        creds = {
            'username': f'user_{int(time.time())}_{random_suffix}',
            'email': f'user_{int(time.time())}_{random_suffix}@example.com',
            'password': 'password123',
            'btc_address': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
            'pin': '1234',
            'invite_code': 'INVITE123',
            'pgp_key': '-----BEGIN PGP PUBLIC KEY BLOCK-----',
            'telegram': '@user123',
            'age': '25',
            'country': 'US',
            'firstname': f'John{random_suffix}',
            'lastname': f'Doe{random_suffix}',
            'fullname': f'John Doe {random_suffix}',
            'address1': '123 Main St',
            'address2': 'Apt 4B',
            'street': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'province': 'NY',
            'region': 'NY',
            'zip': '10001',
            'postal': '10001',
            'phone': '+1-555-123-4567',
            'telephone': '+1-555-123-4567',
            'mobile': '+1-555-123-4567',
            'card': '4111111111111111',
            'cvv': '123',
            'exp': '12/29',
            'iban': 'DE89370400440532013000',
            'swift': 'DEUTDEFF',
            'ssn': '12-3456789',
            'taxid': '12-3456789',
            'company': 'Acme Corp',
            'website': 'https://example.com',
            'url': 'https://example.com',
            'note': 'N/A',
        }
        # Get all input fields
        inputs = form.find_elements(By.TAG_NAME, 'input')
        textareas = form.find_elements(By.TAG_NAME, 'textarea')
        selects = form.find_elements(By.TAG_NAME, 'select')
        all_fields = inputs + textareas + selects
        fields_filled = 0
        unfilled_fields = []
        for field in all_fields:
            name = field.get_attribute('name') or ''
            id_attr = field.get_attribute('id') or ''
            placeholder = field.get_attribute('placeholder') or ''
            typ = field.get_attribute('type') or ''
            label = ''
            try:
                label_elem = form.find_element(By.XPATH, f".//label[@for='{id_attr}']")
                label = label_elem.text.lower()
            except:
                pass
            # Combine all attributes for matching
            field_text = f"{name} {id_attr} {placeholder} {typ} {label}".lower()
            value_to_fill = None
            # Robust matching for all common fields
            if any(word in field_text for word in ['user', 'login', 'name']) and typ != 'password':
                value_to_fill = creds['username']
            elif any(word in field_text for word in ['first']):
                value_to_fill = creds['firstname']
            elif any(word in field_text for word in ['last', 'surname']):
                value_to_fill = creds['lastname']
            elif any(word in field_text for word in ['full name']):
                value_to_fill = creds['fullname']
            elif any(word in field_text for word in ['email', 'mail']):
                value_to_fill = creds['email']
            elif any(word in field_text for word in ['pass', 'pwd']):
                value_to_fill = creds['password']
            elif any(word in field_text for word in ['btc', 'bitcoin', 'wallet', 'address']) and not any(word in field_text for word in ['street', 'city', 'state', 'zip', 'postal']):
                value_to_fill = creds['btc_address']
            elif any(word in field_text for word in ['pin', 'security']):
                value_to_fill = creds['pin']
            elif any(word in field_text for word in ['invite', 'referral']):
                value_to_fill = creds['invite_code']
            elif any(word in field_text for word in ['pgp', 'key', 'public']):
                value_to_fill = creds['pgp_key']
            elif any(word in field_text for word in ['telegram', 'signal', 'wickr']):
                value_to_fill = creds['telegram']
            elif any(word in field_text for word in ['age', 'birth', 'year']):
                value_to_fill = creds['age']
            elif any(word in field_text for word in ['country']):
                value_to_fill = creds['country']
            elif any(word in field_text for word in ['address1', 'address 1', 'street1', 'street 1']):
                value_to_fill = creds['address1']
            elif any(word in field_text for word in ['address2', 'address 2', 'street2', 'street 2']):
                value_to_fill = creds['address2']
            elif any(word in field_text for word in ['street']):
                value_to_fill = creds['street']
            elif any(word in field_text for word in ['city', 'town']):
                value_to_fill = creds['city']
            elif any(word in field_text for word in ['state', 'province', 'region']):
                value_to_fill = creds['state']
            elif any(word in field_text for word in ['zip', 'postal', 'postcode']):
                value_to_fill = creds['zip']
            elif any(word in field_text for word in ['phone', 'telephone', 'mobile', 'cell']):
                value_to_fill = creds['phone']
            elif any(word in field_text for word in ['card', 'ccnum', 'credit']):
                value_to_fill = creds['card']
            elif any(word in field_text for word in ['cvv', 'cvc']):
                value_to_fill = creds['cvv']
            elif any(word in field_text for word in ['exp', 'expiry', 'expiration']):
                value_to_fill = creds['exp']
            elif any(word in field_text for word in ['iban']):
                value_to_fill = creds['iban']
            elif any(word in field_text for word in ['swift', 'bic']):
                value_to_fill = creds['swift']
            elif any(word in field_text for word in ['ssn', 'social']):
                value_to_fill = creds['ssn']
            elif any(word in field_text for word in ['tax', 'vat']):
                value_to_fill = creds['taxid']
            elif any(word in field_text for word in ['company', 'business']):
                value_to_fill = creds['company']
            elif any(word in field_text for word in ['website', 'url']):
                value_to_fill = creds['website']
            elif any(word in field_text for word in ['note', 'comment', 'message']):
                value_to_fill = creds['note']
            # For selects, try to pick the first non-empty option
            elif field.tag_name == 'select':
                try:
                    options = field.find_elements(By.TAG_NAME, 'option')
                    for option in options:
                        if option.get_attribute('value') and option.get_attribute('value').strip():
                            option.click()
                            fields_filled += 1
                            value_to_fill = option.get_attribute('value')
                            break
                except Exception as e:
                    print(f"      -> ❌ Could not select option for '{name}': {e}")
            # For high-priority sites, fill ANY text field
            elif typ == 'text' and not any(word in field_text for word in ['search', 'query']):
                value_to_fill = creds['username']
            if value_to_fill:
                try:
                    if not field.is_displayed() or not field.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
                        time.sleep(0.1)
                    field.clear()
                    field.send_keys(value_to_fill)
                    fields_filled += 1
                except Exception:
                    try:
                        print(f"      -> Field not interactable, trying JS fallback.")
                        driver.execute_script("arguments[0].value = arguments[1];", field, value_to_fill)
                        fields_filled += 1
                    except Exception as e_js:
                        print(f"      -> ❌ Could not fill field '{name}'. JS Reason: {e_js}")
                        unfilled_fields.append(name or id_attr or placeholder or typ)
            else:
                unfilled_fields.append(name or id_attr or placeholder or typ)
        # Submit form if we filled any fields
        if fields_filled > 0:
            try:
                form.submit()
            except:
                submit_buttons = form.find_elements(By.XPATH, ".//button[@type='submit'] | .//input[@type='submit']")
                if submit_buttons:
                    submit_buttons[0].click()
            time.sleep(MEDIUM_WAIT)
            # Log the attempt
            if form_type == "login":
                write_to_csv_threadsafe([url, creds['username'], creds['password'], fields_filled, datetime.utcnow().isoformat()], 'data/raw/login_attempts.csv')
            elif form_type == "registration":
                write_to_csv_threadsafe([url, creds['username'], creds['password'], creds['email'], fields_filled, datetime.utcnow().isoformat()], 'data/raw/registration_attempts.csv')
            elif form_type == "checkout":
                write_to_csv_threadsafe([url, creds['email'], creds.get('btc_address', 'N/A'), fields_filled, datetime.utcnow().isoformat()], 'data/raw/checkout_attempts.csv')
            if unfilled_fields:
                print(f"⚠️ Unfilled fields: {unfilled_fields}")
            print(f"✅ Filled {form_type} form with {fields_filled} fields")
            return True
        if unfilled_fields:
            print(f"⚠️ Unfilled fields: {unfilled_fields}")
        return False
    except Exception as e:
        print(f"⚠️ Form fill attempt failed: {e}")
        return False

def attempt_input_fill(driver, inputs, url, form_type):
    """Attempt to fill any input fields that look like forms"""
    try:
        # Try basic fake user generation first (no API calls)
        random_suffix = get_random_suffix()
        basic_creds = {
            'username': f'user_{int(time.time())}_{random_suffix}',
            'email': f'user_{int(time.time())}_{random_suffix}@example.com',
            'password': 'password123',
            'btc_address': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
            'pin': '1234',
            'invite_code': 'INVITE123',
            'pgp_key': '-----BEGIN PGP PUBLIC KEY BLOCK-----',
            'telegram': '@user123',
            'age': '25',
            'country': 'US'
        }
        
        # Use basic credentials instead of AI-generated ones
        creds = basic_creds
        
        # Look for input fields that might be login/registration
        login_inputs = []
        for inp in inputs:
            name = inp.get_attribute('name') or ''
            id_attr = inp.get_attribute('id') or ''
            placeholder = inp.get_attribute('placeholder') or ''
            typ = inp.get_attribute('type') or ''
            
            field_text = f"{name} {id_attr} {placeholder} {typ}".lower()
            
            # Check if this looks like a login field
            if any(word in field_text for word in ['user', 'login', 'name', 'email', 'pass', 'pwd']):
                login_inputs.append(inp)
        
        if len(login_inputs) >= 2:  # Need at least username and password
            fields_filled = 0
            for inp in login_inputs:
                name = inp.get_attribute('name') or ''
                typ = inp.get_attribute('type') or ''
                
                if 'pass' in name.lower() or typ == 'password':
                    inp.clear()
                    inp.send_keys(creds['password'])
                    fields_filled += 1
                elif 'user' in name.lower() or 'email' in name.lower() or typ == 'text':
                    inp.clear()
                    inp.send_keys(creds['username'])
                    fields_filled += 1
            
            if fields_filled >= 2:
                # Try to submit by pressing Enter
                login_inputs[-1].send_keys(Keys.RETURN)
                time.sleep(MEDIUM_WAIT)
                
                # Log the attempt
                if form_type == "login":
                    write_to_csv_threadsafe([url, creds['username'], creds['password'], fields_filled, datetime.utcnow().isoformat()], 'data/raw/login_attempts.csv')
                else:
                    write_to_csv_threadsafe([url, creds['username'], creds['password'], creds['email'], fields_filled, datetime.utcnow().isoformat()], 'data/raw/registration_attempts.csv')
                
                print(f"✅ Filled {form_type} inputs with {fields_filled} fields")
                return True
        
        return False
    except Exception as e:
        print(f"⚠️ Input fill attempt failed: {e}")
        return False

def attempt_button_clicks(driver, buttons, url):
    """Attempt to click buttons that might trigger forms"""
    try:
        # Look for buttons that might trigger login/registration
        for button in buttons:
            text = button.text.lower()
            onclick = button.get_attribute('onclick') or ''
            
            if any(word in text for word in ['login', 'signin', 'access', 'enter', 'continue', 'register', 'signup', 'join', 'registration']):
                try:
                    button.click()
                    time.sleep(SHORT_WAIT)
                    print(f"✅ Clicked button: {text}")
                    return True
                except:
                    continue
        
        return False
    except Exception as e:
        print(f"⚠️ Button click attempt failed: {e}")
        return False

def attempt_link_clicks(driver, links, url):
    """Attempt to click links that might lead to login"""
    try:
        # Look for links that might lead to login
        for link in links:
            href = link.get_attribute('href')
            if href and '/login' in href.lower():
                try:
                    link.click()
                    time.sleep(SHORT_WAIT)
                    print(f"✅ Clicked link: {href}")
                    return True
                except:
                    continue
        
        return False
    except Exception as e:
        print(f"⚠️ Link click attempt failed: {e}")
        return False

def attempt_js_form_detection(driver, url):
    """Attempt to detect login form using JavaScript"""
    try:
        # Use JavaScript to detect login form
        script = """
        var forms = document.getElementsByTagName('form');
        for (var i = 0; i < forms.length; i++) {
            var form = forms[i];
            var form_html = form.outerHTML.toLowerCase();
            if (form_html.includes('login') || form_html.includes('signin') || form_html.includes('access') || form_html.includes('enter') || form_html.includes('continue')) {
                return true;
            }
        }
        return false;
        """
        result = driver.execute_script(script)
        return result
    except Exception as e:
        print(f"⚠️ JavaScript form detection failed: {e}")
        return False

def scroll_to_address(driver, address):
    """Smartly scroll to where the address is located on the page"""
    try:
        # Try multiple selectors to find the address
        selectors = [
            f"//*[contains(text(), '{address}')]",
            f"//input[@value='{address}']",
            f"//textarea[contains(text(), '{address}')]",
            f"//code[contains(text(), '{address}')]",
            f"//pre[contains(text(), '{address}')]",
            f"//span[contains(text(), '{address}')]",
            f"//div[contains(text(), '{address}')]",
            f"//p[contains(text(), '{address}')]"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    element = elements[0]
                    # Scroll element into view with some padding
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
                    time.sleep(0.5)  # Let scroll complete
                    return True
            except:
                continue
        
        # If we can't find the exact element, try to find any element containing part of the address
        address_parts = [address[:10], address[-10:], address[10:20]]
        for part in address_parts:
            try:
                elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{part}')]")
                if elements:
                    element = elements[0]
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
                    time.sleep(0.5)
                    return True
            except:
                continue
        
        return False
    except Exception as e:
        print(f"⚠️ Smart scrolling failed: {e}")
        return False

def classify_site(url, title, html_content):
    """Enhanced site classification with priority focus on human trafficking detection"""
    try:
        # Combine all text for analysis
        text_to_analyze = f"{url} {title} {html_content}".lower()
        
        # CRITICAL: Check for CSAM first - CSAM should NEVER be overridden by any other category
        csam_keywords = ["child", "loli", "loliporn", "lolita", "boys", "girls", "teen", "young", "minor", "child porn", "childxxx", "preteen"]
        csam_detected = any(keyword in text_to_analyze for keyword in csam_keywords)
        
        if csam_detected:
            print(f"🚨 CSAM content detected - this takes absolute priority over all other classifications")
            # Continue with normal scoring to get additional categories, but CSAM will be prioritized
        
        # Enhanced scoring system with priority weights
        scores = {}
        priority_multipliers = {
            "human trafficking": 3.0,  # Highest priority
            "csam": 2.5,              # Second highest priority
            "human organ trafficking": 2.0,
            "extortion": 1.5,
            "sextortion": 1.5,
            "carding": 1.2,
            "weapons": 1.2,
            "drugs": 1.0,
            "terrorism": 1.5,
            "murder for hire": 1.5,
            "mercenary": 1.2,
            "bio weapons": 1.5,
            "nuclear": 1.5,
            "state secrets": 1.5,
            "extremist donation": 1.5
        }
        
        # Calculate weighted scores
        for category, keywords in CATEGORY_KEYWORDS.items():
            base_score = 0
            
            # Enhanced pattern matching
            for keyword in keywords:
                # Exact word match (highest weight)
                if f" {keyword} " in f" {text_to_analyze} ":
                    base_score += 3
                # Partial word match
                elif keyword in text_to_analyze:
                    base_score += 1
                # Phrase match (for multi-word keywords)
                elif " " in keyword and keyword in text_to_analyze:
                    base_score += 2
            
            # Apply priority multiplier
            multiplier = priority_multipliers.get(category, 1.0)
            scores[category] = base_score * multiplier
        
        # Special detection for human trafficking patterns
        trafficking_indicators = [
            # Age patterns
            r'\b(1[3-7]yo)\b', r'\b(preteen|underage|barely legal)\b',
            # Service patterns
            r'\b(rent|order)\s+(girl|boy|child|teen)\b', r'\b(escort\s+delivery)\b',
            r'\b(overnight\s+stay)\b', r'\b(custom\s+order)\b',
            # Platform patterns
            r'\.onion', r'\b(slavehub|humanhub)\b',
            # Operational patterns
            r'\b(delivery\s+route)\b', r'\b(border\s+crossing)\b',
            r'\b(customs\s+bribe)\b', r'\b(no\s+passport)\b'
        ]
        
        trafficking_score = 0
        for pattern in trafficking_indicators:
            matches = re.findall(pattern, text_to_analyze, re.IGNORECASE)
            trafficking_score += len(matches) * 2
        
        if trafficking_score > 0:
            scores["human trafficking"] = scores.get("human trafficking", 0) + trafficking_score
        
        # CRITICAL: CSAM should NEVER be overridden by other categories
        # Removed dangerous carding override that was incorrectly suppressing CSAM classification
        
        # PRIORITY OVERRIDE: If scam score is significant, it can override human trafficking but NEVER CSAM
        if scores.get("scam", 0) >= 3:
            print(f"🔍 Scam score ({scores.get('scam', 0)}) is significant, overriding human trafficking classification (CSAM protected)")
            scores["human trafficking"] = 0
            # CRITICAL: CSAM should NEVER be overridden - removed scores["csam"] = 0
        
        # CRITICAL: If CSAM was detected, ensure it's always first in the results
        if csam_detected and scores.get("csam", 0) > 0:
            # Sort other categories by score but always put CSAM first
            other_categories = sorted([(cat, score) for cat, score in scores.items() if cat != "csam" and score >= 2], 
                                    key=lambda x: x[1], reverse=True)
            top_categories = ["csam"]
            for cat, score in other_categories[:2]:  # Add up to 2 more categories
                top_categories.append(cat)
            print(f"🚨 CSAM prioritized in classification: {top_categories}")
            return top_categories
        
        # Normal sorting for non-CSAM content
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_categories:
            # Return categories with scores above threshold, prioritizing human trafficking
            top_categories = []
            for cat, score in sorted_categories:
                if score >= 2:  # Lowered threshold for better detection
                    top_categories.append(cat)
                    # Limit to top 3 categories to avoid noise
                    if len(top_categories) >= 3:
                        break
            
            if top_categories:
                return top_categories
        
        # Enhanced fallback detection with carding and scam priority
        words = set(re.findall(r'\w+', text_to_analyze))
        if any(word in text_to_analyze for word in ["ccpp", "cc shop", "card shop", "paypal account", "cloned cards"]):
            return ["carding"]
        # Explicit fallback: if 'wallet' and any of 'hack', 'hacker', 'hackers' are present as whole words, classify as scam
        if "wallet" in words and words.intersection({"hack", "hacker", "hackers"}):
            print("[DEBUG] Fallback scam logic triggered for wallet + hack/hacker/hackers.")
            return ["scam"]
        # Explicit fallback: if scammy mining/generator/quantum terms are present, classify as scam (and mining botnet if present)
        mining_scam_terms = ["quantum miner", "quantum mining", "bitcoin generator", "btc generator", "mining generator", "mining scam", "mining hack", "mining exploit", "mining cracker", "mining stealer", "cloud mining scam", "fake mining", "bitcoin mining generator"]
        if any(term in text_to_analyze for term in mining_scam_terms):
            if any(word in text_to_analyze for word in ["mining", "miner", "botnet"]):
                return ["scam", "mining botnet"]
            else:
                return ["scam"]
        elif any(word in text_to_analyze for word in ["wallet", "hack", "hacker", "hackers", "bitcoin generator", "btc generator", "private key generator", "stolen wallet"]):
            return ["scam"]
        elif any(word in text_to_analyze for word in ["market", "shop", "store", "vendor", "seller"]):
            return ["marketplace"]
        elif any(word in text_to_analyze for word in ["forum", "board", "community"]):
            return ["darknet forum profile"]
        elif any(word in text_to_analyze for word in ["card", "cc", "dumps"]):
            return ["carding"]
        elif any(word in text_to_analyze for word in ["child", "loli", "teen", "young"]):
            return ["csam"]
        elif any(word in text_to_analyze for word in ["traffic", "slave", "escort", "prostitution"]):
            return ["human trafficking"]
        else:
            return ["darknet"]  # Default fallback
    except Exception as e:
        print(f"⚠️ Enhanced category classification failed: {e}")
        return ["darknet"]

def ai_handle_captcha(driver):
    """Detect and solve captchas using AI"""
    try:
        # Look for images with 'captcha' in alt or src
        images = driver.find_elements(By.TAG_NAME, 'img')
        for img in images:
            src = img.get_attribute('src') or ''
            alt = img.get_attribute('alt') or ''
            if 'captcha' in src.lower() or 'captcha' in alt.lower():
                try:
                    # Take screenshot of captcha
                    img.screenshot(f"captcha_{int(time.time())}.png")
                    
                    # Get image data
                    img_data = img.screenshot_as_png
                    img_pil = Image.open(BytesIO(img_data))
                    
                    # Try to solve with AI
                    solution = ai_solve_captcha(img_pil)
                    if solution:
                        # Look for input field near the captcha
                        captcha_inputs = driver.find_elements(By.XPATH, 
                            "//input[contains(@name, 'captcha') or contains(@id, 'captcha') or contains(@placeholder, 'captcha')]")
                        
                        if captcha_inputs:
                            captcha_inputs[0].clear()
                            captcha_inputs[0].send_keys(solution)
                            
                            # Try to submit
                            try:
                                captcha_inputs[0].send_keys(Keys.RETURN)
                            except:
                                # Look for submit button
                                submit_buttons = driver.find_elements(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
                                if submit_buttons:
                                    submit_buttons[0].click()
                            
                            time.sleep(MEDIUM_WAIT)
                            return True
                except Exception as e:
                    print(f"⚠️ Captcha solving failed: {e}")
                    # Log failed captcha
                    write_to_csv_threadsafe([driver.current_url, str(e), datetime.utcnow().isoformat()], CAPTCHA_FAILED_CSV)
        
        return False
    except Exception as e:
        print(f"⚠️ Captcha detection failed: {e}")
        return False

def ai_handle_coin_selection_page(driver, url, categories):
    """
    Handles pages where the user must select a coin to reveal a payment address.
    It now constructs the URL directly with GET parameters for maximum reliability.
    """
    try:
        print("🪙 Coin selection page detected. Initiating direct URL construction protocol...")
        results = []

        # 1. Scrape the initial page to get the form action and coin values
        initial_page_html = driver.page_source
        soup = BeautifulSoup(initial_page_html, 'html.parser')
        
        # Find the form's action URL
        form = soup.find('form')
        if not form or not form.get('action'):
            print("   -> Could not find a form with an 'action' attribute. Aborting.")
            return []
        action_url = urljoin(url, form.get('action'))

        # Find all coin inputs to iterate through
        coin_inputs = soup.find_all('input', {'type': ['radio', 'checkbox']})
        coin_values = [ci.get('value') for ci in coin_inputs if ci.get('value')]
        if not coin_values:
            print("   -> Could not find any radio/checkbox inputs with 'value' attributes. Aborting.")
            return []

        print(f"   -> Found {len(coin_values)} coin options: {', '.join(coin_values)}")
        existing_addrs_in_results = set(r['address'] for r in results)

        # 2. Loop through each coin, construct the URL, and navigate
        for i, coin in enumerate(coin_values):
            try:
                print(f"   -> [{i+1}/{len(coin_values)}] Processing '{coin}'...")
                
                # Generate fresh credentials for each attempt
                creds = ai_generate_fake_user()
                
                # These parameters are based on the example URL you found.
                params = {
                    'username': creds['username'],
                    'password': creds['password'],
                    'months': '1',
                    'usd': '42',
                    'payCrypto': coin,
                    'button': 'button'
                }

                # Construct the full URL with encoded parameters
                final_url = f"{action_url}?{urlencode(params)}"
                
                print(f"      -> Navigating directly to: {final_url[:100]}...")
                driver.get(final_url)
                time.sleep(MEDIUM_WAIT) # Wait for page to process and render

                # 3. Scrape the resulting page for addresses
                address_page_html = driver.page_source
                addresses = extract_addresses_fast(address_page_html)

                if addresses:
                    print(f"         -> Found {len(addresses)} addresses on the '{coin}' payment page.")
                    for chain, addr in addresses:
                        if addr not in existing_addrs_in_results:
                            print(f"            -> New address found: {chain} - {addr[:10]}...")
                            screenshot_path = "direct_nav_submission.png"
                            try:
                                hostname = urlparse(url).hostname or ''
                                suffix = hostname[:-6][-6:] if hostname.endswith('.onion') else hostname[-6:]
                                title_prefix = sanitize_filename(driver.title[:10])
                                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                                screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_coin_{chain}.png"
                                screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                highlight_address_on_screenshot(driver, addr, screenshot_path)
                            except Exception as e:
                                print(f"            -> Screenshot failed: {e}")

                            results.append({
                                'url': driver.current_url,
                                'title': driver.title,
                                'chain': chain,
                                'address': addr,
                                'timestamp': datetime.utcnow().isoformat(),
                                'screenshot': screenshot_path,
                                'categories': json.dumps(categories)
                            })
                            existing_addrs_in_results.add(addr)
                else:
                    print("         -> No addresses found on the resulting page.")
            except Exception as e:
                print(f"      -> ❌ Error processing coin '{coin}': {e}")
                continue

        return results
    except Exception as e:
        print(f"❌ Error during direct URL construction: {e}")
        return []

def ai_solve_visual_captcha(driver):
    """
    Solves visual captchas like "Press the red circle" or simple instructions like "Click the checkout button".
    This is a sophisticated function that uses a multi-pronged approach.
    """
    try:
        print("🕵️  Visual captcha detected. Attempting to solve...")

        # 1. Find the instruction text (e.g., "Press the red circle")
        instruction_text = ""
        possible_instructions = driver.find_elements(By.XPATH, "//*[contains(text(), 'Press the') or contains(text(), 'Click the')]")
        if not possible_instructions:
            # Fallback for dynamic text in spans or divs
            possible_instructions = driver.find_elements(By.XPATH, "//p | //h1 | //h2 | //h3 | //div | //span")

        for elem in possible_instructions:
            if 'Press the' in elem.text or 'Click the' in elem.text:
                instruction_text = elem.text.strip()
                print(f"   -> Instruction found: '{instruction_text}'")
                break
        
        if not instruction_text:
            # print("   -> ❌ Could not find instruction text. Aborting visual captcha solver.") # Reduced noise
            return False

        # 2. Parse the instruction - check for simple button command first
        simple_button_match = re.search(r'(?:Press|Click) the (\w+) button', instruction_text, re.IGNORECASE)
        if simple_button_match:
            button_text = simple_button_match.group(1).lower().strip()
            print(f"   -> Simple instruction detected: Click the '{button_text}' button.")
            
            button_selectors = [
                f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
                f"//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
                f"//input[@type='submit' or @type='button'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]"
            ]
            
            for selector in button_selectors:
                try:
                    element = driver.find_element(By.XPATH, selector)
                    if element and element.is_displayed() and element.is_enabled():
                        print(f"   -> ✅ Found button with text '{button_text}'. Clicking it now.")
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(MEDIUM_WAIT)
                        return True
                except:
                    continue
            
            print(f"   -> ❌ Could not find a clickable button with text '{button_text}'.")
            return False

        # 3. Parse for complex visual captcha (color + shape)
        color_shape_match = re.search(r'(?:Press|Click) the (\w+) (\w+)', instruction_text, re.IGNORECASE)
        if not color_shape_match:
            # print(f"   -> ❌ Could not parse instruction: '{instruction_text}'. Aborting visual captcha solver.") # Reduced noise
            return False
        
        target_color_name = color_shape_match.group(1).lower()
        target_shape = color_shape_match.group(2).lower()
        print(f"   -> Target identified: Color='{target_color_name}', Shape='{target_shape}'")

        # 4. Define a color map (name to RGB)
        color_map = {
            'red': (255, 0, 0), 'green': (0, 255, 0), 'blue': (0, 0, 255),
            'yellow': (255, 255, 0), 'pink': (255, 192, 203), 'magenta': (255, 0, 255),
            'cyan': (0, 255, 255), 'orange': (255, 165, 0), 'purple': (128, 0, 128),
            'black': (0, 0, 0), 'white': (255, 255, 255), 'gray': (128, 128, 128)
        }
        
        if target_color_name not in color_map:
            print(f"   -> ❌ Unknown target color: '{target_color_name}'. Aborting.")
            return False
        target_rgb = color_map[target_color_name]

        # 5. Find all potential clickable elements (circles, squares, etc.)
        # This is a generic approach; might need tuning for specific sites.
        # We'll assume they are divs for now, as in the example.
        candidate_elements = driver.find_elements(By.XPATH, "//div[@onclick or contains(@style, 'background-color')] | //span[@onclick or contains(@style, 'background-color')] | //button")

        if not candidate_elements:
            print("   -> ❌ Could not find any candidate clickable elements. Aborting.")
            return False
        
        print(f"   -> Found {len(candidate_elements)} candidate elements to analyze.")

        # 6. Helper function to calculate color difference
        def get_color_distance(rgb1, rgb2):
            return sum([(c1 - c2) ** 2 for c1, c2 in zip(rgb1, rgb2)]) ** 0.5

        # 7. Iterate through elements, find the best color match
        best_match_element = None
        smallest_distance = float('inf')

        for i, elem in enumerate(candidate_elements):
            try:
                # Method A: Get color from CSS (most reliable)
                elem_color_str = elem.value_of_css_property('background-color')
                
                # Parse RGBA string like 'rgba(255, 0, 0, 1)'
                rgb_match = re.search(r'rgba?\((\d+), (\d+), (\d+)', elem_color_str)
                if rgb_match:
                    elem_rgb = tuple(map(int, rgb_match.groups()))
                    distance = get_color_distance(target_rgb, elem_rgb)
                    print(f"      -> Element {i}: Found color {elem_rgb} via CSS. Distance to '{target_color_name}' is {distance:.2f}")

                    if distance < smallest_distance:
                        smallest_distance = distance
                        best_match_element = elem
            except Exception:
                # Method B: Image analysis (fallback)
                try:
                    print(f"      -> Element {i}: CSS color failed. Trying image analysis fallback.")
                    img_data = elem.screenshot_as_png
                    img = Image.open(io.BytesIO(img_data)).convert('RGB')
                    # Downscale to 1x1 to get average color
                    dominant_color = img.resize((1, 1), Image.Resampling.LANCZOS).getpixel((0, 0))
                    distance = get_color_distance(target_rgb, dominant_color)
                    print(f"      -> Element {i}: Found color {dominant_color} via Image. Distance to '{target_color_name}' is {distance:.2f}")

                    if distance < smallest_distance:
                        smallest_distance = distance
                        best_match_element = elem
                except Exception as e:
                    print(f"      -> Element {i}: Image analysis also failed: {e}")
                    continue

        # 8. Click the best match if it's good enough
        # The threshold of 100 is arbitrary; a perfect match is 0.
        if best_match_element and smallest_distance < 100:
            print(f"   -> ✅ Best match found with distance {smallest_distance:.2f}. Clicking it now.")
            try:
                # Use JavaScript click for reliability
                driver.execute_script("arguments[0].click();", best_match_element)
                time.sleep(MEDIUM_WAIT)
                print("   -> ✅ Successfully clicked the correct element.")
                return True
            except Exception as e:
                print(f"   -> ❌ Clicking the element failed: {e}")
                return False
        else:
            print("   -> ❌ Could not find a suitable element to click.")
            return False

    except Exception as e:
        print(f"⚠️  Visual captcha solver failed with an error: {e}")
        return False

def get_description_for_address(soup, address, max_len=500):
    """
    Finds a description associated with a cryptocurrency address on the page.
    It looks for the address in the text and then walks up the DOM to find a parent
    element that contains a reasonably sized text block.
    """
    try:
        # Find the element containing the address text
        element = soup.find(string=re.compile(re.escape(address), re.IGNORECASE))
        if not element:
            return "Description not found (element missing)"

        # Walk up the DOM tree to find a suitable parent container
        current = element.parent
        for _ in range(7):  # Go up a maximum of 7 levels
            if not current:
                break
            
            # Get the text, stripping extra whitespace
            text = current.get_text(separator=' ', strip=True)
            
            # A good description is longer than just the address but not excessively long
            if len(address) + 15 < len(text) < max_len:
                # Clean up the text
                cleaned_text = re.sub(r'\\s+', ' ', text).strip()
                return cleaned_text
            
            current = current.parent

        # Fallback if no ideal container is found, return the immediate parent's text
        fallback_text = element.parent.get_text(separator=' ', strip=True)
        fallback_text = re.sub(r'\\s+', ' ', fallback_text).strip()
        if len(fallback_text) > max_len:
            return fallback_text[:max_len] + "..."
        return fallback_text if fallback_text else "Description not found (empty parent)"

    except Exception as e:
        return f"Description not found (error: {e})"

def generate_content_based_description(categories, max_len=100):
    """
    Generates a fallback description based on the site's classified categories.
    """
    if not categories:
        return "Content-based description unavailable (no categories)."

    # Create a more readable string from the category list
    if len(categories) == 1:
        desc = f"A site related to {categories[0]}."
    elif len(categories) == 2:
        desc = f"A site related to {categories[0]} and {categories[1]}."
    else:
        # Join all but the last with commas, and add "and" before the last one
        most_categories = ", ".join(categories[:-1])
        desc = f"A site related to {most_categories}, and {categories[-1]}."

    # Prefix to know its origin
    final_desc = f"Content-based: {desc}"

    if len(final_desc) > max_len:
        return final_desc[:max_len] + "..."
    return final_desc

def ai_get_description(driver, address=None, max_len=500):
    """
    Uses AI to generate a description of the product/service on the current page.
    This is used as a fallback when rule-based description fails.
    """
    if not AI_ENABLED:
        return "AI-based description disabled."
    
    # Check API quota before making calls
    if API_QUOTA_MANAGEMENT and not check_api_quota():
        return "Description generation skipped due to API quota limits."
    
    try:
        # Get the page HTML content
        html_content = driver.page_source

        # Extract visible text from HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get and clean text content
        text_content = soup.get_text(separator=' ', strip=True)
        # Truncate to 1500 characters for safety
        content_preview = text_content[:1500]
        if len(text_content) > 1500:
            print(f"⚠️ Content truncated from {len(text_content)} to 1500 characters for AI description")

        prompt = (
            "Analyze the following webpage text content and identify the main product or service being offered for sale. "
            "Provide a concise, one-sentence description focusing only on what is being sold. "
            "If there are multiple items, describe the general category of items. "
            f"Content: {content_preview}"
        )

        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        increment_api_call_counter()
        response = client.chat.completions.create(
            model=AI_MODELS['gpt4'],  # Use text model, or 'gpt-4o' if available
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100  # A short description
        )

        description = response.choices[0].message.content.strip()

        # Clean up and truncate
        import re
        cleaned_description = re.sub(r'\s+', ' ', description).strip()
        if len(cleaned_description) > max_len:
            return cleaned_description[:max_len] + "..."
        # Prefix to know it's AI-generated
        return f"AI: {cleaned_description}"

    except Exception as e:
        error_str = str(e)
        if "quota" in error_str.lower() or "insufficient_quota" in error_str.lower():
            handle_api_quota_error("ai_get_description")
            return "Description generation failed due to API quota limits."
        else:
            print(f"⚠️ AI description failed: {e}")
            return "AI description generation failed."

def detect_human_trafficking_priority(url, title, html_content):
    """Specialized function to detect high-priority human trafficking indicators"""
    if not ENABLE_TRAFFICKING_DETECTION:
        return {
            "priority": "DISABLED",
            "score": 0,
            "patterns": [],
            "requires_immediate_attention": False
        }
    
    try:
        text_to_analyze = f"{url} {title} {html_content}".lower()
        
        # Critical indicators that require immediate attention
        critical_indicators = {
            "age_specific": [
                r'\b(1[3-7]yo)\b', r'\b(preteen|underage|barely legal)\b', r'\b(young girl|teen girl|little one|schoolgirl)\b'
            ],
            "dehumanizing": [
                r'\b(fresh girl|new flower|clean meat|unbroken|no scars)\b',
                r'\b(first time|tight|virgin|package ready|premium stock)\b',
                r'\b(womb ready|fresh fruit)\b'
            ],
            "service_terms": [
                r'\b(rent girl|order girl|escort delivery|overnight stay)\b',
                r'\b(bondage available|no condom|custom order)\b',
                r'\b(abduction service|white slave market)\b'
            ],
            "operational": [
                r'\b(delivery route|border crossing|smuggler|customs bribe)\b',
                r'\b(no passport|encrypted contact|dark slave market)\b',
                r'\b(onion trafficking)\b'
            ],
            "platforms": [
                r'sex\.onion', r'childmarket\.onion', r'escort\.onion',
                r'lolita\.onion', r'slavehub', r'humanhub'
            ],
            "payment_security": [
                r'\b(bitcoin only|pgp secure|escort visa|id fake)\b'
            ]
        }
        
        # Calculate weighted critical score
        critical_score = 0
        detected_patterns = []
        category_scores = {}
        
        for category, patterns in critical_indicators.items():
            category_score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_to_analyze, re.IGNORECASE)
                if matches:
                    weight = TRAFFICKING_WEIGHTS.get(category, 1.0)
                    category_score += len(matches) * weight
                    detected_patterns.extend(matches)
            
            category_scores[category] = category_score
            critical_score += category_score
        
        # Determine priority level using configurable thresholds
        if critical_score >= TRAFFICKING_CRITICAL_THRESHOLD:
            priority = "CRITICAL"
        elif critical_score >= TRAFFICKING_HIGH_THRESHOLD:
            priority = "HIGH"
        elif critical_score >= TRAFFICKING_MEDIUM_THRESHOLD:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        # Log high-priority detections
        if critical_score >= TRAFFICKING_MEDIUM_THRESHOLD and ENABLE_PATTERN_LOGGING:
            timestamp = datetime.utcnow().isoformat()
            alert_data = [
                url, title[:100], priority, str(critical_score),
                "|".join(set(detected_patterns)), 
                "|".join([f"{k}:{v:.1f}" for k, v in category_scores.items() if v > 0]),
                timestamp
            ]
            write_to_csv_threadsafe(alert_data, HUMAN_TRAFFICKING_ALERTS_CSV)
            
            # Print immediate alert for critical cases
            if priority in ["CRITICAL", "HIGH"] and ENABLE_IMMEDIATE_ALERTS:
                # print(f"🚨 HUMAN TRAFFICKING ALERT - {priority} PRIORITY")
                # print(f"   URL: {url}")
                # print(f"   Score: {critical_score:.1f}")
                # print(f"   Patterns: {', '.join(set(detected_patterns))}")
                # print(f"   Category Scores: {', '.join([f'{k}:{v:.1f}' for k, v in category_scores.items() if v > 0])}")
                # print(f"🏷️ [{worker_id}] Categories: {', '.join(categories)}")
                # print(f"🚨 [{worker_id}] Trafficking Score: {trafficking_alert['score']:.1f} ({trafficking_alert['priority']})")
                print(f"🚨 HUMAN TRAFFICKING ALERT - {priority} PRIORITY")
                print(f"   URL: {url}")
                print(f"   Score: {critical_score:.1f}")
                print(f"   Patterns: {', '.join(set(detected_patterns))}")
                print(f"   Category Scores: {', '.join([f'{k}:{v:.1f}' for k, v in category_scores.items() if v > 0])}")
                print(f"   Timestamp: {timestamp}")
                print("-" * 60)
        
        return {
            "priority": priority,
            "score": critical_score,
            "patterns": list(set(detected_patterns)),
            "category_scores": category_scores,
            "requires_immediate_attention": priority in ["CRITICAL", "HIGH"]
        }
        
    except Exception as e:
        print(f"⚠️ Human trafficking detection failed: {e}")
        return {
            "priority": "ERROR",
            "score": 0,
            "patterns": [],
            "category_scores": {},
            "requires_immediate_attention": False
        }

def add_to_retry_list(url, reason, details=""):
    """Add URL to retry list only for specific failure reasons"""
    if not ENABLE_RETRY_LIST:
        return
    
    if reason in RETRY_REASONS:
        retry_data = [url, reason, details, datetime.utcnow().isoformat()]
        write_to_csv_threadsafe(retry_data, RETRY_LIST_CSV)
        print(f"📝 Added to retry list: {get_base_domain(url)} (Reason: {reason})")
    else:
        print(f"⏭️ Not adding to retry list: {url} (Reason: {reason} - not retryable)")

def process_url_immediately(url, worker_id, priority="HIGH"):
    """Immediately process a high-priority URL for human trafficking detection"""
    print(f"🚨 [{worker_id}] IMMEDIATE PROCESSING - {priority} PRIORITY URL: {get_base_domain(url)}")
    
    # Initialize variables to ensure they are available in the 'finally' block
    driver = None
    addresses = []
    categories = []
    title = ""

    try:
        # Create a dedicated driver for immediate processing
        driver = create_driver(f"{worker_id}_immediate")
        
        # Set shorter timeouts for immediate processing
        driver.set_page_load_timeout(30)  # Faster timeout for immediate processing
        driver.set_script_timeout(20)  # Add script timeout for immediate processing
        
        print(f"🌐 [{worker_id}] Loading page immediately: {get_base_domain(url)}")
        driver.get(url)
        time.sleep(SHORT_WAIT)
        
        # Abort early if Chrome shows its network error page (site unreachable via Tor)
        _err_ps = driver.page_source.lower()
        if any(ind in _err_ps for ind in [
            "err_socks_connection_failed", "err_tunnel_connection_failed",
            "err_connection_timed_out", "this site can't be reached"]):
            print(f"⚠️ [{worker_id}] Chrome error page detected for {get_base_domain(url)} – skipping immediate processing.")
            driver.quit()
            return []
        
        # Wait for the page title to load properly
        print(f"⏳ [{worker_id}] Waiting for page title to load (immediate processing)...")
        if wait_for_title_to_load(driver, timeout=10):  # Shorter timeout for immediate processing
            print(f"✅ [{worker_id}] Page title loaded successfully")
        else:
            print(f"⚠️ [{worker_id}] Page title may still be loading, continuing anyway")
        
        # Get page content after title has loaded
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        current_page_title = soup.title.string.strip() if soup.title else "NoTitle"
        
        # Use root title for consistent site context
        title = get_or_set_root_title(url, current_page_title)
        
        # Run human trafficking detection
        trafficking_alert = detect_human_trafficking_priority(url, title, html)
        categories = classify_site(url, title, html)
        
        print(f"📄 [{worker_id}] Immediate scan - Title: {title}")
        # print(f"🏷️ [{worker_id}] Categories: {', '.join(categories)}")
        print(f"🚨 [{worker_id}] Trafficking Score: {trafficking_alert['score']:.1f} ({trafficking_alert['priority']})")
        
        # Extract addresses immediately
        addresses = extract_addresses_fast(html)
        results = []
        
        if addresses:
            print(f"✅ [{worker_id}] Found {len(addresses)} addresses on immediate scan!")
            for chain, addr in addresses:
                description = get_description_for_address(soup, addr)
                if "Description not found" in description:
                    description = ai_get_description(driver, addr)
                    if "failed" in description.lower():
                        description = generate_content_based_description(categories)
                
                # Take individual address screenshot
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                addr_screenshot_name = f"IMMEDIATE_{priority}_{chain}_{addr[:8]}_{timestamp}.png"
                addr_screenshot_path = os.path.join(SCREENSHOT_DIR, addr_screenshot_name)
                
                try:
                    success = highlight_address_on_screenshot(driver, addr, addr_screenshot_path)
                    if success:
                        print(f"✅ [{worker_id}] Address screenshot: {addr_screenshot_name}")
                    else:
                        addr_screenshot_path = "screenshot_failed.png"
                except Exception as e:
                    print(f"❌ [{worker_id}] Address screenshot failed: {e}")
                    addr_screenshot_path = "screenshot_failed.png"
                
                results.append({
                    'url': get_base_domain(url),
                    'title': title,
                    'description': description,
                    'chain': chain,
                    'address': addr,
                    'timestamp': datetime.utcnow().isoformat(),
                    'screenshot': addr_screenshot_path,
                    'categories': json.dumps(categories),
                    'processing_type': 'immediate',
                    'trafficking_score': trafficking_alert['score'],
                    'trafficking_priority': trafficking_alert['priority']
                })
                print(f"🏦 [{worker_id}] IMMEDIATE {chain} address: {addr[:4]}...{addr[-4:]}")
        
        # Log immediate processing results
        immediate_data = [
            get_base_domain(url), title, priority, str(trafficking_alert['score']),
            trafficking_alert['priority'], "|".join(trafficking_alert['patterns']),
            len(addresses), "address_screenshots_only", datetime.utcnow().isoformat()
        ]
        write_to_csv_threadsafe(immediate_data, "data/raw/immediate_processing_log.csv")
        
        print(f"🎉 [{worker_id}] Immediate processing completed for {get_base_domain(url)}")
        return results
        
    except Exception as e:
        print(f"❌ [{worker_id}] Immediate processing failed for {get_base_domain(url)}: {e}")
        # Add to retry list if it's a captcha/login failure
        if any(reason in str(e).lower() for reason in RETRY_REASONS):
            retry_data = [url, "immediate_processing_failed", str(e), datetime.utcnow().isoformat()]
            write_to_csv_threadsafe(retry_data, RETRY_LIST_CSV)
            print(f"📝 [{worker_id}] Added to retry list: {url}")
        return []
    finally:
        # Attempt to navigate via navbar buy button/form before extraction (only if driver still active)
        try:
            if driver and try_navbar_buy_button(driver):
                print(f"🛒 [{worker_id}] Navbar buy attempt succeeded in immediate processing, waiting for page...")
                time.sleep(MEDIUM_WAIT)
                scroll_entire_page(driver)
                time.sleep(SHORT_WAIT)
                html = driver.page_source  # Refresh page source after navigation
                soup = BeautifulSoup(html, 'html.parser')
                # Use root title for consistency
                current_title = soup.title.string.strip() if soup.title else title
                title = get_or_set_root_title(url, current_title)
        except Exception as nav_exc:
            print(f"⚠️ [{worker_id}] Navbar buy attempt in immediate processing failed: {nav_exc}")

        # After navbar, try smart iterative flow quickly
        if driver and not addresses:
            iterative_addresses = smart_iterative_ecommerce_flow(driver, url, title, categories, max_iterations=2, worker_id=worker_id)
            if iterative_addresses:
                addresses = iterative_addresses
                print(f"✅ [{worker_id}] Iterative flow in immediate processing found {len(addresses)} addresses!")

        # Quit the driver as the final cleanup step
        if driver:
            try:
                driver.quit()
            except:
                pass

def process_retry_list():
    """Process URLs that failed due to captcha/login issues"""
    if not os.path.exists(RETRY_LIST_CSV):
        print("📝 No retry list found.")
        return
    
    print("🔄 Processing retry list...")
    
    # Read retry URLs
    retry_urls = []
    try:
        with open(RETRY_LIST_CSV, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if row and row[0].startswith('http'):
                    retry_urls.append(row[0])
    except Exception as e:
        print(f"❌ Error reading retry list: {e}")
        return
    
    if not retry_urls:
        print("📝 Retry list is empty.")
        return
    
    print(f"🔄 Found {len(retry_urls)} URLs in retry list")
    
    # Process retry URLs with higher priority
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(process_url_fast, url, f"RETRY_{i % MAX_WORKERS}"): url 
                        for i, url in enumerate(retry_urls)}
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results = future.result()
                if results:
                    print(f"✅ Retry successful for {url}")
                else:
                    print(f"❌ Retry failed for {url}")
            except Exception as e:
                print(f"❌ Retry error for {url}: {e}")
    
    print("🔄 Retry list processing completed.")

def main():
    """Main parallel processing function"""
    global urls_since_rotation
    
    try:
        # Initialize agent system
        if not initialize_agent_system():
            print("⚠️ Continuing without agent system")
        
        # Start agent status monitoring thread
        def print_agent_status():
            while True:
                time.sleep(60)
                try:
                    status = integrated_agents.get_system_status()
                    print(f"\n🤖 Agent Status: {status['live_stats']['total_processed']} processed, "
                          f"{status['live_stats']['successes']} successes, "
                          f"{status['live_stats']['failures']} failures")
                except:
                    pass
        
        status_thread = threading.Thread(target=print_agent_status)
        status_thread.daemon = True
        status_thread.start()
        
        print("🚀 Starting Fast Parallel Scraper...")
        if START_FROM_ROW > 1:
            print(f"🔄 RESUMING from row {START_FROM_ROW}")
        print(f"📁 Primary input: {PRIMARY_INPUT_CSV}")
        if USE_GOOGLE_SHEET_AS_SECONDARY:
            print(f"📁 Secondary input: Google Sheet URLs (column F)")
        else:
            print(f"📁 Secondary input: {SECONDARY_INPUT_CSV}")
        print(f"🔄 Input rotation: Every {ROTATE_INPUT_EVERY_N_URLS} URLs")
        print(f"📁 Output: {OUTPUT_CSV}")
        print(f"📸 Screenshots: {SCREENSHOT_DIR}")
        print(f"🔧 Workers: {MAX_WORKERS}")
        print(f"⚡ Fast Mode: {FAST_MODE}")
        print(f"👻 Headless: {HEADLESS_MODE}")
        print(f"⏱️  Timeouts: {PAGE_LOAD_TIMEOUT}s page load, {SHORT_WAIT}s short wait")
        print(f"🔄 TOR Rotation: Every {ROTATE_EVERY_N} URLs")
        print("=" * 60)
        
        # Create output CSV with headers if it doesn't exist
        if not os.path.exists(OUTPUT_CSV):
            with open(OUTPUT_CSV, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['url', 'title', 'chain', 'address', 'timestamp', 'screenshot', 'categories', 'description', 'scam'])
            print(f"📁 Created new output file: {OUTPUT_CSV}")
        
        # Create human trafficking alerts CSV with headers if it doesn't exist
        if not os.path.exists(HUMAN_TRAFFICKING_ALERTS_CSV):
            with open(HUMAN_TRAFFICKING_ALERTS_CSV, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['url', 'title', 'priority', 'score', 'detected_patterns', 'category_scores', 'timestamp'])
            print(f"🚨 Created human trafficking alerts file: {HUMAN_TRAFFICKING_ALERTS_CSV}")
        
        # Create scam alerts CSV with headers if it doesn't exist
        if not os.path.exists(SCAM_ALERTS_CSV):
            with open(SCAM_ALERTS_CSV, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['url', 'title', 'priority', 'score', 'detected_patterns', 'category_scores', 'timestamp'])
            print(f"🚨 Created scam alerts file: {SCAM_ALERTS_CSV}")
        
        # Create immediate processing log CSV with headers if it doesn't exist
        if not os.path.exists("data/raw/immediate_processing_log.csv"):
            with open("data/raw/immediate_processing_log.csv", 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['url', 'title', 'priority', 'score', 'trafficking_priority', 'patterns', 'addresses_found', 'screenshot_type', 'timestamp'])
            print(f"⚡ Created immediate processing log file: data/raw/immediate_processing_log.csv")
        
        # Create retry list CSV with headers if it doesn't exist
        if not os.path.exists(RETRY_LIST_CSV):
            with open(RETRY_LIST_CSV, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['url', 'reason', 'details', 'timestamp'])
            print(f"🔄 Created retry list file: {RETRY_LIST_CSV}")
        
        # Create duplicate divert CSV with headers if it doesn't exist
        if not os.path.exists(DUPLICATE_DIVERT_CSV):
            with open(DUPLICATE_DIVERT_CSV, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['url', 'title', 'chain', 'address', 'timestamp', 'screenshot', 'categories', 'description', 'scam'])
            print(f"🔄 Created duplicate divert file: {DUPLICATE_DIVERT_CSV}")
        
        # Initialize TOR rotation counter
        urls_since_rotation = 0
        
        # Initialize Google Sheet duplicate checking
        print("🔍 Initializing Google Sheet duplicate checking...")
        google_addresses = fetch_google_sheet_addresses()
        print(f"📊 Loaded {len(google_addresses)} addresses from Google Sheet")
        
        # Initialize seen_addresses set before URL loading
        seen_addresses = set()
        
        # Load existing addresses from CSV to prevent duplicates across runs
        if os.path.exists(OUTPUT_CSV):
            try:
                with open(OUTPUT_CSV, 'r') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    for row in reader:
                        if len(row) >= 4:  # Ensure we have enough columns
                            url_existing = row[0]
                            addr_existing = row[3]
                            # Store original address in seen_pairs, normalized address in seen_addresses for comparison
                            if addr_existing:
                                normalized_addr = addr_existing.lower().strip()
                                seen_addresses.add(normalized_addr)  # For duplicate checking
                                seen_pairs.add((url_existing, addr_existing))  # Original format
                print(f"📋 Loaded {len(seen_addresses)} existing addresses from {OUTPUT_CSV}")
            except Exception as e:
                print(f"⚠️ Could not load existing addresses: {e}")
        
        # Perform initial duplicate check and move any existing duplicates
        print("🔍 Performing initial duplicate check...")
        check_and_move_duplicates()
        
        # Read URLs from current input file with unique address tracking
        current_file = get_next_input_file()
        csam_only = ((current_file == SECONDARY_INPUT_CSV or current_file == "GOOGLE_SHEET") and CSAM_ONLY_FROM_SECONDARY)
        urls = load_urls_from_input_file(current_file, csam_only, seen_addresses, START_FROM_ROW)
        
        if not urls:
            print(f"❌ No unique URLs found in {current_file}")
            return
        
        print(f"📊 Found {len(urls)} URLs to process")
        print(f"🔄 Starting parallel processing with {MAX_WORKERS} workers...")
        print("=" * 60)
        
        # Process URLs in parallel
        all_results = []
        
        
        
        processed_count = 0
        success_count = 0
        error_count = 0
        start_time = datetime.utcnow()
        
        # Add delay between worker starts to prevent Chrome conflicts
        print(f"🔧 Starting {MAX_WORKERS} workers with staggered initialization...")
        time.sleep(2)  # Small delay before starting workers
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all URLs with retry logic
            if ENABLE_RETRY_LOGIC:
                future_to_url = {executor.submit(process_url_with_retry, url, i % MAX_WORKERS): url 
                                for i, url in enumerate(urls)}
            else:
                future_to_url = {executor.submit(process_url_fast, url, i % MAX_WORKERS): url 
                                for i, url in enumerate(urls)}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                processed_count += 1
                
                # Progress update every 10 URLs
                if processed_count % 10 == 0:
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    rate = processed_count / elapsed if elapsed > 0 else 0
                    eta = (len(urls) - processed_count) / rate if rate > 0 else 0
                    print(f"📈 Progress: {processed_count}/{len(urls)} URLs ({processed_count/len(urls)*100:.1f}%)")
                    print(f"⏱️  Rate: {rate:.1f} URLs/sec, ETA: {eta/60:.1f} minutes")
                    print(f"✅ Success: {success_count}, ❌ Errors: {error_count}")
                    print(f"🏦 Addresses found: {len(all_results)}")
                    
                    # ML Learning Stats Update
                    try:
                        from ml_learning_system import get_ml_extractor
                        ml = get_ml_extractor()
                        stats = ml.get_learning_stats()
                        print(f"🤖 ML Stats: {stats['total_sites_processed']} sites, "
                              f"{stats['overall_success_rate']:.1%} success rate, "
                              f"{stats['total_extraction_attempts']} attempts")
                        if stats['recent_performance']:
                            print(f"📊 Recent: {stats['recent_performance']['success_rate']:.1%} success rate "
                                  f"({stats['recent_performance']['attempts_count']} attempts)")
                    except Exception as e:
                        print(f"⚠️ ML stats error: {e}")
                    
                    print("-" * 40)
                
                # Periodic Google Sheet duplicate check
                if processed_count % GOOGLE_SHEET_CHECK_INTERVAL == 0:
                    print(f"🔍 Periodic duplicate check at {processed_count} URLs...")
                    # Reload Google Sheet addresses
                    google_addresses = fetch_google_sheet_addresses()
                    # Check and move duplicates
                    check_and_move_duplicates()
                
                try:
                    results = future.result()
                    if results:
                        success_count += 1
                        for result in results:
                            url_r = result['url']
                            addr = result['address']
                            pair = (url_r, addr)

                            # Ensure we handle each (url, address) pair only once
                            if pair in seen_pairs:
                                # Exact duplicate row already exists; skip silently
                                continue

                            # Normalize address for comparison only (don't change original)
                            normalized_addr = addr.lower().strip() if addr else ""
                            
                            # Check if address is duplicate in Google Sheet or local processing
                            if is_duplicate_address(normalized_addr, google_addresses, seen_addresses):
                                # Duplicate found - write to duplicate file with full data (original format)
                                write_to_csv_threadsafe([
                                    get_base_domain(url_r), result['title'], result['chain'], addr, result['timestamp'], result['screenshot'], result['categories'], result['description'], result['scam']
                                ], DUPLICATE_DIVERT_CSV)
                                print(f"⏭️ [{processed_count}] Duplicate address diverted to {DUPLICATE_DIVERT_CSV}")
                            else:
                                # Completely new address – write to main CSV (original format)
                                seen_addresses.add(normalized_addr)  # Store normalized for comparison
                                write_to_csv_threadsafe([
                                    get_base_domain(url_r), result['title'], result['chain'], addr, result['timestamp'], result['screenshot'], result['categories'], result['description'], result['scam']
                                ], OUTPUT_CSV)
                                print(f"💾 [{processed_count}] Saved new {result['chain']} address to CSV (scam={result['scam']})")

                            seen_pairs.add(pair)
                    else:
                        success_count += 1  # Still counts as successful processing
                            
                except Exception as e:
                    error_count += 1
                    print(f"❌ [{processed_count}] Error processing {get_base_domain(url)}: {e}")
        
        # Final statistics
        total_time = (datetime.utcnow() - start_time).total_seconds()
        print("=" * 60)
        print("🎉 SCRAPING COMPLETED!")
        print(f"📊 Final Statistics:")
        print(f"   • Total URLs processed: {processed_count}")
        print(f"   • Successful: {success_count}")
        print(f"   • Errors: {error_count}")
        print(f"   • Unique addresses found: {len(all_results)}")
        print(f"   • Total time: {total_time/60:.1f} minutes")
        print(f"   • Average rate: {processed_count/total_time:.1f} URLs/sec")
        print(f"📁 Results saved to: {OUTPUT_CSV}")
        print(f"📁 Primary input: {PRIMARY_INPUT_CSV}")
        if USE_GOOGLE_SHEET_AS_SECONDARY:
            print(f"📁 Secondary input: Google Sheet URLs (column F)")
        else:
            print(f"📁 Secondary input: {SECONDARY_INPUT_CSV}")
        print(f"🔄 Input rotation: {'ENABLED' if ENABLE_INPUT_ROTATION else 'DISABLED'}")
        print(f"📸 Screenshots saved to: {SCREENSHOT_DIR}")
        print("=" * 60)

        # Process retry list
        process_retry_list()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"⚠️ Main function error: {e}")
    finally:
        cleanup_agent_system()

def create_driver(worker_id=None):
    """Create an optimized Chrome driver with unique user data directory and DevTools port"""
    import tempfile
    import os
    import random
    import time
    
    chrome_options = Options()
    
    # macOS-specific fixes
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-gpu-sandbox")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-field-trial-config")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--safebrowsing-disable-auto-update")
    chrome_options.add_argument("--disable-component-extensions-with-background-pages")
    chrome_options.add_argument("--disable-background-mode")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-site-isolation-trials")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--max_old_space_size=4096")
    
    # Performance optimizations
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-css")
    chrome_options.add_argument("--disable-animations")
    
    # TOR proxy
    chrome_options.add_argument(f"--proxy-server={TOR_PROXY}")
    
    # Headless mode
    if HEADLESS_MODE:
        chrome_options.add_argument("--headless=new")
    
    # Fix DevTools port conflict by using unique ports
    devtools_port = random.randint(9222, 9999)
    chrome_options.add_argument(f"--remote-debugging-port={devtools_port}")
    
    # Add unique user data directory for each worker to prevent conflicts
    if worker_id is not None:
        # Create a unique temporary directory for this worker
        temp_dir = tempfile.mkdtemp(prefix=f"chrome_worker_{worker_id}_")
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
    else:
        # For cases where worker_id is not provided, use a random directory
        temp_dir = tempfile.mkdtemp(prefix="chrome_worker_")
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
    
    # Enable JavaScript for dynamic address loading
    # chrome_options.add_argument("--disable-javascript")  # Commented out to enable JS
    
    # Try multiple times with different configurations
    for attempt in range(3):
        try:
            print(f"🔧 Creating Chrome driver (attempt {attempt + 1}/3)...")
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            driver.set_script_timeout(30)  # Add script timeout to prevent renderer timeouts
            print(f"✅ Chrome driver created successfully for worker {worker_id}")
            return driver
        except Exception as e:
            print(f"⚠️ Chrome driver creation failed (attempt {attempt + 1}/3): {e}")
            if attempt < 2:  # Don't sleep on last attempt
                time.sleep(2)  # Wait before retry
                # Add more aggressive options for retry
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu-sandbox")
                chrome_options.add_argument("--disable-software-rasterizer")
                chrome_options.add_argument("--disable-background-timer-throttling")
                chrome_options.add_argument("--disable-backgrounding-occluded-windows")
                chrome_options.add_argument("--disable-renderer-backgrounding")
    
    # If all attempts failed, try with minimal options
    print("🔄 Trying with minimal Chrome options...")
    minimal_options = Options()
    minimal_options.add_argument("--no-sandbox")
    minimal_options.add_argument("--disable-dev-shm-usage")
    minimal_options.add_argument("--disable-gpu")
    minimal_options.add_argument(f"--proxy-server={TOR_PROXY}")
    if HEADLESS_MODE:
        minimal_options.add_argument("--headless=new")
    
    try:
        driver = webdriver.Chrome(options=minimal_options)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.set_script_timeout(30)
        print(f"✅ Chrome driver created with minimal options for worker {worker_id}")
        return driver
    except Exception as e:
        print(f"❌ Chrome driver creation failed with minimal options: {e}")
        raise

def get_next_input_file():
    """Get the next input file to process, rotating between primary and secondary"""
    global current_input_file, urls_since_input_rotation
    
    with input_rotation_lock:
        urls_since_input_rotation += 1
        
        # Check if we should rotate input files
        if (ENABLE_INPUT_ROTATION and 
            urls_since_input_rotation >= ROTATE_INPUT_EVERY_N_URLS):
            
            if current_input_file == PRIMARY_INPUT_CSV:
                if USE_GOOGLE_SHEET_AS_SECONDARY:
                    current_input_file = "GOOGLE_SHEET"
                    print(f"🔄 Rotating to Google Sheet URLs (column F)")
                else:
                    current_input_file = SECONDARY_INPUT_CSV
                    print(f"🔄 Rotating to secondary input: {SECONDARY_INPUT_CSV}")
            else:
                current_input_file = PRIMARY_INPUT_CSV
                print(f"🔄 Rotating to primary input: {PRIMARY_INPUT_CSV}")
            
            urls_since_input_rotation = 0
        
        return current_input_file

def load_urls_from_input_file(input_file, csam_only=False, seen_addresses=None, start_row=1):
    """Load URLs from input file or Google Sheet with optional CSAM filtering and unique address tracking"""
    urls = []
    unique_urls = set()  # Track unique URLs to avoid duplicates
    
    try:
        # Handle Google Sheet URLs
        if input_file == "GOOGLE_SHEET":
            urls = fetch_google_sheet_urls()
            print(f"📁 Loaded {len(urls)} unique URLs from Google Sheet column F")
            if csam_only:
                print(f"🔍 Note: CSAM filtering not available for Google Sheet URLs")
            if seen_addresses:
                print(f"🚫 Note: Address-based filtering not available for Google Sheet URLs")
            return urls
        
        # Handle file-based inputs
        with open(input_file, 'r') as f:
            reader = csv.reader(f)
            
            # Handle different CSV formats
            if input_file == SECONDARY_INPUT_CSV:
                # Secondary file has headers: url, title, chain, address, timestamp, screenshot, categories, description
                next(reader)  # Skip header
                row_number = 1  # Start counting after header
                for row in reader:
                    row_number += 1
                    # Skip rows before the start_row
                    if row_number < start_row:
                        continue
                    if len(row) >= 8:  # Ensure we have enough columns
                        url = row[0]
                        address = row[3]  # Address column
                        categories_str = row[6]  # categories column
                        
                        # Skip if we've already seen this address (avoid re-scraping)
                        if seen_addresses and address in seen_addresses:
                            continue
                        
                        # Skip if we've already added this URL (avoid duplicates within file)
                        if url in unique_urls:
                            continue
                        
                        # Check if CSAM filtering is enabled
                        if csam_only:
                            # Parse categories JSON and check for CSAM
                            try:
                                import json
                                categories = json.loads(categories_str)
                                if isinstance(categories, list) and "csam" in categories:
                                    if url.startswith('http'):
                                        urls.append(url)
                                        unique_urls.add(url)
                            except:
                                # If JSON parsing fails, check if "csam" is in the string
                                if "csam" in categories_str.lower() and url.startswith('http'):
                                    urls.append(url)
                                    unique_urls.add(url)
                        else:
                            # No filtering, add all URLs
                            if url.startswith('http'):
                                urls.append(url)
                                unique_urls.add(url)
            else:
                # Primary file format (just URLs)
                row_number = 0  # Start counting from 0 for primary file (no header)
                for row in reader:
                    row_number += 1
                    # Skip rows before the start_row
                    if row_number < start_row:
                        continue
                    if row and row[0].startswith('http'):
                        url = row[0]
                        if url not in unique_urls:  # Avoid duplicates
                            urls.append(url)
                            unique_urls.add(url)
        
        print(f"📁 Loaded {len(urls)} unique URLs from {input_file}")
        if start_row > 1:
            print(f"🔄 Started from row {start_row}")
        if csam_only:
            print(f"🔍 Filtered for CSAM sites only")
        if seen_addresses:
            print(f"🚫 Skipped URLs with already-seen addresses")
        
        return urls
        
    except Exception as e:
        print(f"❌ Error reading input file {input_file}: {e}")
        return []

def clean_title_for_csv(title, max_length=100):
    """
    Clean a title by keeping everything up to the first comma or pipe character to prevent CSV parsing issues.
    
    Args:
        title (str): The original title
        max_length (int): Maximum length for the title
    
    Returns:
        str: Cleaned title
    """
    if not title:
        return title
    
    # Remove quotes if present
    title = title.strip('"')
    
    # Find the first occurrence of problematic characters
    comma_pos = title.find(',')
    pipe_pos = title.find('|')
    
    # Find the earliest problematic character
    cut_positions = [pos for pos in [comma_pos, pipe_pos] if pos != -1]
    
    if cut_positions:
        # Keep everything up to (but not including) the earliest problematic character
        cut_pos = min(cut_positions)
        title = title[:cut_pos].strip()
    
    # Also limit overall length
    if len(title) > max_length:
        title = title[:max_length].strip()
        # Try to cut at a word boundary
        last_space = title.rfind(' ')
        if last_space > max_length * 0.8:  # If we can cut at a space and keep most of the title
            title = title[:last_space].strip()
    
    return title

def sanitize_csv_field(field, max_length=1000, field_type="general"):
    """
    Sanitize a field for CSV writing by handling quotes, newlines, and other problematic characters.
    
    Args:
        field: The field value to sanitize
        max_length: Maximum length for the field
        field_type: Type of field for special handling ("description", "title", "general")
    
    Returns:
        str: Sanitized field value
    """
    if field is None:
        return ""
    
    # Convert to string
    field_str = str(field)
    
    # Special handling for description field
    if field_type == "description":
        # Remove JavaScript code and problematic content
        if 'function setCookie' in field_str or 'jQuery.ajax' in field_str:
            # Extract only the meaningful part before JavaScript
            parts = field_str.split('function setCookie')
            if parts[0].strip():
                field_str = parts[0].strip()
            else:
                field_str = 'Content-based description'
        
        # Remove other JavaScript patterns
        js_patterns = [
            'setInterval(function()',
            'jQuery.ajax({',
            'document.cookie',
            'setCookie(',
            'var expires',
            'date.setTime(',
            'toUTCString()'
        ]
        
        for pattern in js_patterns:
            if pattern in field_str:
                parts = field_str.split(pattern)
                if parts[0].strip():
                    field_str = parts[0].strip()
                else:
                    field_str = 'Content-based description'
                break
    
    # Remove or replace problematic characters
    # Replace newlines with spaces
    field_str = field_str.replace('\n', ' ').replace('\r', ' ')
    
    # Replace tabs with spaces
    field_str = field_str.replace('\t', ' ')
    
    # Remove null bytes
    field_str = field_str.replace('\x00', '')
    
    # Handle quotes - escape them properly for CSV
    # If the field contains quotes, we need to escape them by doubling them
    if '"' in field_str:
        field_str = field_str.replace('"', '""')
    
    # Limit length to prevent extremely long fields
    if len(field_str) > max_length:
        field_str = field_str[:max_length].strip()
        # Try to cut at a word boundary
        last_space = field_str.rfind(' ')
        if last_space > max_length * 0.8:
            field_str = field_str[:last_space].strip()
    
    # Remove any remaining control characters except basic whitespace
    import re
    field_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', field_str)
    
    return field_str.strip()

def write_to_csv_threadsafe(row, file):
    """Thread-safe CSV writing with comprehensive data sanitization"""
    with csv_lock:
        # Create a copy of the row to avoid modifying the original
        sanitized_row = []
        
        for i, field in enumerate(row):
            if file == OUTPUT_CSV and i == 1:  # Title column (index 1)
                # Apply special title cleaning for titles
                cleaned_title = clean_title_for_csv(field)
                sanitized_row.append(sanitize_csv_field(cleaned_title, max_length=100, field_type="title"))
            elif file == OUTPUT_CSV and i == 7:  # Description column (index 7)
                # Apply special description sanitization to remove JavaScript code
                sanitized_row.append(sanitize_csv_field(field, max_length=500, field_type="description"))
            else:
                # Apply general sanitization for all other fields
                sanitized_row.append(sanitize_csv_field(field, max_length=1000, field_type="general"))
        
        with open(file, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(sanitized_row)

def is_multi_vendor_market(url):
    """Check if URL is a known multi-vendor market"""
    url_lower = url.lower()
    return any(market in url_lower for market in MULTI_VENDOR_MARKETS)

def should_skip_page(url, title, html):
    """Check if page should be skipped based on content"""
    url_lower = url.lower()
    title_lower = title.lower() if title else ""
    html_lower = html.lower()
    
    # Comprehensive scam detection patterns - SKIP THESE ENTIRELY
    skip_scam_keywords = [
        # Bitcoin generators and exploits - SKIP
        "bitcoin generator", "btc generator", "bitcoin exploit", "btc exploit",
        "bitcoin hack", "btc hack", "bitcoin cracker", "btc cracker",
        "bitcoin multiplier", "btc multiplier", "free bitcoin generator",
        "bitcoin doubler", "btc doubler", "bitcoin mining generator",
        "fake bitcoin generator",
        
        # Private key scams and exploits - SKIP
        "private key generator", "private key hack", "private key exploit",
        "private key cracker", "private key finder", "private key brute force",
        "private key recovery", "private key extractor", "private key stealer",
        "private key grabber", "private key scanner", "private key database",
        "private key dump", "private key leak", "private key crack",
        "private key brute", "private key force", "private key attack",
        "private key vulnerability", "private key hack tool", "private key cracking",
        "private key breaking", "private key stealing", "private key extraction",
        "private key recovery tool", "private key shop", "private key market",
        
        # Wallet scams - SKIP
        "hacked wallets", "stolen wallets", "wallet market",
        "wallet shop", "bitcoin wallet shop", "buy stolen bitcoin wallets",
        "buy stolen cryptocurrency wallets", "buy stolen crypto wallets",
        "buy stolen cryptocurrency wallet", "buy stolen crypto wallet", "buy stolen bitcoin wallet",
        "stolen bitcoin wallets", "stolen cryptocurrency wallets", "stolen crypto wallets",
        "stolen bitcoin wallet", "stolen cryptocurrency wallet", "stolen crypto wallet",
        "wallet database", "wallet dump",
        "wallet leak", "wallet cracker", "wallet hack", "wallet hacker", "wallet hackers" 
        "wallet exploit", "wallet generator", "wallet recovery", "wallet stealer",
        "wallet grabber", "wallet scanner", "wallet brute force",
        
        # Quantum mining scams - SKIP
        "quantum miner", "quantum mining", "quantum bitcoin miner",
        "quantum crypto miner", "quantum mining software", "quantum mining tool",
        "quantum mining generator", "quantum mining hack", "quantum mining exploit",
        
        # Other obvious scams - SKIP
        "free money generator", "money generator", "crypto generator",
        "ethereum generator", "eth generator", "monero generator",
        "xmr generator", "tron generator", "solana generator",
        "sol generator", "altcoin generator", "coin generator",
        
        # Mining scams - SKIP
        "cloud mining scam", "fake mining", "mining scam", "mining generator",
        "mining hack", "mining exploit", "mining cracker", "mining stealer",
        
        # Exchange and trading scams - SKIP
        "fake exchange", "exchange scam", "trading bot scam", "bot scam",
        "auto trader scam", "trading generator", "profit generator",
        "income generator", "money maker", "get rich quick",
        
        # Recovery scams - SKIP
        "recovery service", "recovery tool", "recovery software",
        "lost bitcoin recovery", "stolen crypto recovery", "hacked account recovery",
        
        # Phishing and fake sites - SKIP
        "phishing", "fake wallet", "fake exchange", "fake mining",
        "fake generator", "fake hack", "fake exploit", "fake cracker",
        
        # Multiplier scams (100x, 1000x, etc.)
        "100x your coins", "1000x your coins", "10x your coins", "50x your coins",
        "200x your coins", "500x your coins", "multiply your coins", "multiply your bitcoin",
        "multiply your crypto", "multiply your money", "multiply your investment",
        "double your coins", "triple your coins", "quadruple your coins",
        "multiply coins", "multiply bitcoin", "multiply crypto", "multiply money",
        "multiply investment", "multiply funds", "multiply balance",
        "your coins in 24 hours", "your bitcoin in 24 hours", "your crypto in 24 hours",
        "coins in 24 hours", "bitcoin in 24 hours", "crypto in 24 hours",
        "officially hidden service", "hidden service anonymous", "anonymous service"
    ]
    
    # Check for scam patterns
    for keyword in skip_scam_keywords:
        if (keyword in url_lower or 
            keyword in title_lower or 
            keyword in html_lower):
            return True, f"Obvious scam - skipping: '{keyword}'"
    
    # Less obvious scam patterns - FLAG BUT DON'T SKIP
    flag_scam_keywords = [
        "scam list", "scam database", "scam dump", "scam leak",
        "walets", "wallet", "hack", "hacker", "hackers"  # These might be legitimate in some contexts
    ]
    
    # Check for less obvious scam patterns - FLAG BUT PROCESS
    for keyword in flag_scam_keywords:
        if (keyword in url_lower or 
            keyword in title_lower or 
            keyword in html_lower):
            return False, f"Potential scam: '{keyword}'"  # Don't skip, just flag
    
    return False, ""

def detect_scam_priority(url, title, html_content):
    """Specialized function to detect high-priority scam indicators"""
    if not ENABLE_SCAM_DETECTION:
        return {
            "priority": "DISABLED",
            "score": 0,
            "patterns": [],
            "requires_immediate_attention": False
        }
    
    try:
        text_to_analyze = f"{url} {title} {html_content}".lower()
        
        # Scam indicators with different categories and weights
        scam_indicators = {
            "generator_scams": [
                r'\b(bitcoin|btc|ethereum|eth|monero|xmr|tron|solana|sol)\s+generator\b',
                r'\b(free\s+money|crypto|coin|altcoin)\s+generator\b',
                r'\b(money|profit|income)\s+generator\b'
            ],
            "wallet_scams": [
                r'\b(hacked|stolen)\s+wallet\b', r'\bwalets?\b', r'\bwallet\s+(market|shop|database|dump|leak)\b',
                r'\b(buy|purchase)\s+stolen\s+(bitcoin|cryptocurrency|crypto)\s+wallets?\b', 
                r'\bstolen\s+(bitcoin|cryptocurrency|crypto)\s+wallets?\b',
                r'\bwallet\s+(cracker|hack|exploit|generator)\b'
            ],
            "private_key_scams": [
                r'\bprivate\s+key\s+(generator|hack|exploit|cracker|finder|recovery|extractor)\b',
                r'\bprivate\s+key\s+(stealer|grabber|scanner|database|dump|leak)\b',
                r'\bprivate\s+key\s+(shop|market|brute\s+force|attack|vulnerability)\b'
            ],
            "quantum_mining_scams": [
                r'\bquantum\s+(miner|mining|bitcoin\s+miner|crypto\s+miner)\b',
                r'\bquantum\s+mining\s+(software|tool|generator|hack|exploit)\b'
            ],
            "mining_scams": [
                r'\b(cloud\s+mining|fake\s+mining|mining)\s+scam\b',
                r'\bmining\s+(generator|hack|exploit|cracker|stealer)\b'
            ],
            "exchange_trading_scams": [
                r'\b(fake\s+exchange|exchange\s+scam|trading\s+bot\s+scam)\b',
                r'\b(bot\s+scam|auto\s+trader\s+scam|trading\s+generator)\b',
                r'\b(profit|income|money\s+maker|get\s+rich\s+quick)\s+generator\b'
            ],
            "recovery_scams": [
                r'\b(recovery\s+service|recovery\s+tool|recovery\s+software)\b',
                r'\b(lost|stolen|hacked)\s+(bitcoin|crypto|account)\s+recovery\b'
            ],
            "phishing_fake": [
                r'\bphishing\b', r'\bfake\s+(wallet|exchange|mining|generator|hack|exploit|cracker)\b'
            ],
            "multiplier_scams": [
                r'\b\d+x\s+your\s+(coins|bitcoin|crypto|money|investment)\b',
                r'\bmultiply\s+your\s+(coins|bitcoin|crypto|money|investment|funds|balance)\b',
                r'\b(double|triple|quadruple)\s+your\s+(coins|bitcoin|crypto|money)\b',
                r'\byour\s+(coins|bitcoin|crypto)\s+in\s+24\s+hours\b',
                r'\b(coins|bitcoin|crypto)\s+in\s+24\s+hours\b',
                r'\bofficially\s+hidden\s+service\b',
                r'\bhidden\s+service\s+anonymous\b',
                r'\banonymous\s+service\b'
            ]
        }
        
        # Calculate weighted scam score
        scam_score = 0
        detected_patterns = []
        category_scores = {}
        
        for category, patterns in scam_indicators.items():
            category_score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_to_analyze, re.IGNORECASE)
                if matches:
                    # Flatten tuples to strings if necessary
                    for m in matches:
                        if isinstance(m, tuple):
                            detected_patterns.append(' '.join([str(x) for x in m if x]))
                        else:
                            detected_patterns.append(str(m))
                    weight = 3.0 if category in ["generator_scams", "wallet_scams", "multiplier_scams"] else 2.5
                    category_score += len(matches) * weight
            
            category_scores[category] = category_score
            scam_score += category_score
        
        # Determine priority level
        if scam_score >= 15:
            priority = "CRITICAL"
        elif scam_score >= 10:
            priority = "HIGH"
        elif scam_score >= 5:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        # Log scam detections
        if scam_score >= 5 and ENABLE_PATTERN_LOGGING:
            timestamp = datetime.utcnow().isoformat()
            alert_data = [
                url, title[:100], priority, str(scam_score),
                "|".join(set(detected_patterns)), 
                "|".join([f"{k}:{v:.1f}" for k, v in category_scores.items() if v > 0]),
                timestamp
            ]
            write_to_csv_threadsafe(alert_data, SCAM_ALERTS_CSV)
            
            # Print immediate alert for critical cases
            if priority in ["CRITICAL", "HIGH"] and ENABLE_IMMEDIATE_ALERTS:
                print(f"🚨 SCAM ALERT - {priority} PRIORITY")
                print(f"   URL: {url}")
                print(f"   Score: {scam_score:.1f}")
                print(f"   Patterns: {', '.join(set(detected_patterns))}")
                print(f"   Category Scores: {', '.join([f'{k}:{v:.1f}' for k, v in category_scores.items() if v > 0])}")
                print(f"   Timestamp: {timestamp}")
                print("-" * 60)
        
        return {
            "priority": priority,
            "score": scam_score,
            "patterns": list(set(detected_patterns)),
            "category_scores": category_scores,
            "requires_immediate_attention": priority in ["CRITICAL", "HIGH"]
        }
        
    except Exception as e:
        print(f"⚠️ Scam detection failed: {e}")
        return {
            "priority": "ERROR",
            "score": 0,
            "patterns": [],
            "category_scores": {},
            "requires_immediate_attention": False
        }

def get_external_onion_links(soup, base_url):
    """Extract external .onion links for discovery"""
    external_links = []
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        
        # Check if it's an external .onion link
        parsed = urlparse(full_url)
        if (parsed.netloc != urlparse(base_url).netloc and 
            parsed.netloc.endswith('.onion') and
            parsed.scheme in ['http', 'https']):
            external_links.append(full_url)
    
    # Remove duplicates
    return list(set(external_links))

# === AGENT SYSTEM INITIALIZATION ===
def initialize_agent_system():
    try:
        integrated_agents.start_system()
        print("🤖 Agent system integrated into scraper")
        return True
    except Exception as e:
        print(f"⚠️ Agent system initialization failed: {e}")
        return False

def cleanup_agent_system():
    try:
        integrated_agents.stop_system()
        print("🛑 Agent system cleaned up")
    except Exception as e:
        print(f"⚠️ Agent system cleanup failed: {e}")

def ai_solve_captcha_enhanced(driver):
    """Enhanced AI captcha solving with smart fallback system"""
    if not ENABLE_AI_CAPTCHA_SOLVING or EMERGENCY_MODE:
        print("⚠️ AI captcha solving disabled, using basic fallback")
        return attempt_captcha_bypass(driver)
    
    try:
        print("🤖 Smart captcha solving activated...")
        
        # Step 1: Try basic captcha bypass methods first (no API calls)
        print("   -> Trying basic captcha bypass methods...")
        if attempt_captcha_bypass(driver):
            print("   -> ✅ Basic captcha bypass successful")
            return True
        
        # Step 2: Try OCR-based captcha solving (no API calls)
        print("   -> Trying OCR-based captcha solving...")
        if ai_solve_visual_captcha(driver):
            print("   -> ✅ OCR captcha solving successful")
            return True
        
        # Step 3: Try text-based captcha solving (no API calls)
        print("   -> Trying text-based captcha solving...")
        if ai_solve_text_captcha(driver):
            print("   -> ✅ Text captcha solving successful")
            return True
        
        # Step 4: Try interactive captcha solving (no API calls)
        print("   -> Trying interactive captcha solving...")
        if ai_solve_interactive_captcha(driver):
            print("   -> ✅ Interactive captcha solving successful")
            return True
        
        # Step 5: Try AI methods (API calls)
        if check_api_quota():
            print("   -> All basic methods failed, trying AI methods...")
            
            # Method 1: Traditional image captcha detection with AI
            if ai_solve_image_captcha(driver):
                return True
            
            # Method 2: AI-powered captcha bypass
            if ai_bypass_captcha_ai(driver):
                return True
        else:
            print("   -> API quota limit reached, skipping AI methods")
        
        # Final fallback to basic captcha handling
        print("🔄 All methods failed, trying basic captcha handling")
        return ai_handle_captcha(driver)
        
    except Exception as e:
        print(f"⚠️ Enhanced captcha solving failed: {e}")
        # Always try basic fallback
        return ai_handle_captcha(driver)

def ai_solve_image_captcha(driver):
    """Solve traditional image-based captchas using AI vision"""
    try:
        # Look for captcha images
        captcha_selectors = [
            "img[src*='captcha']",
            "img[alt*='captcha']",
            "img[class*='captcha']",
            "img[id*='captcha']",
            ".captcha img",
            "#captcha img"
        ]
        
        for selector in captcha_selectors:
            try:
                captcha_img = driver.find_element(By.CSS_SELECTOR, selector)
                if captcha_img.is_displayed():
                    print("   -> Found image captcha, solving with AI vision...")
                    
                    # Take screenshot of captcha
                    img_data = captcha_img.screenshot_as_png
                    img_pil = Image.open(BytesIO(img_data))
                    
                    # Solve with AI
                    solution = ai_solve_captcha_with_vision(img_pil)
                    if solution:
                        # Find input field
                        captcha_inputs = driver.find_elements(By.XPATH, 
                            "//input[contains(@name, 'captcha') or contains(@id, 'captcha') or contains(@placeholder, 'captcha')]")
                        
                        if captcha_inputs:
                            captcha_inputs[0].clear()
                            captcha_inputs[0].send_keys(solution)
                            
                            # Submit
                            try:
                                captcha_inputs[0].send_keys(Keys.RETURN)
                            except:
                                submit_buttons = driver.find_elements(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
                                if submit_buttons:
                                    submit_buttons[0].click()
                            
                            time.sleep(MEDIUM_WAIT)
                            print("   -> ✅ Image captcha solved successfully")
                            return True
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"⚠️ Image captcha solving failed: {e}")
        return False

def ai_solve_captcha_with_vision(image):
    """Solve captcha using AI vision models with quota management"""
    try:
        if not AI_ENABLED:
            return ""
        
        # Check API quota before making calls
        if API_QUOTA_MANAGEMENT and not check_api_quota():
            print("   -> Using OCR fallback due to API quota limits")
            return pytesseract.image_to_string(image).strip()
        
        # Convert image to base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Try multiple AI models
        models_to_try = ['gpt4_vision', 'gpt4', 'claude']
        
        for model_name in models_to_try:
            try:
                if model_name == 'gpt4_vision':
                    # Check quota before API call
                    if API_QUOTA_MANAGEMENT and not check_api_quota():
                        break
                    
                    prompt = (
                        "This is a captcha image from a dark web site. "
                        "Please read the text and return only the captcha code. "
                        "Ignore any background noise or distortion."
                    )
                    
                    increment_api_call_counter()
                    response = openai_client.chat.completions.create(
                        model=AI_MODELS[model_name],
                        messages=[
                            {"role": "user", "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
                            ]}
                        ],
                        max_tokens=10
                    )
                else:
                    # For text-only models, use OCR first
                    text = pytesseract.image_to_string(image)
                    if text and len(text.strip()) >= 3:
                        return text.strip()
                    continue
                
                solution = response.choices[0].message.content.strip()
                if solution and len(solution) >= 3:
                    return solution
                    
            except Exception as e:
                error_str = str(e)
                if "quota" in error_str.lower() or "insufficient_quota" in error_str.lower():
                    handle_api_quota_error("ai_solve_captcha_with_vision")
                    # Fall back to OCR
                    if USE_OCR_FALLBACK:
                        print("   -> Falling back to OCR due to API quota error")
                        return pytesseract.image_to_string(image).strip()
                    break
                else:
                    print(f"   -> Model {model_name} failed: {e}")
                    continue
        
        # Final fallback to OCR if all AI methods fail
        if USE_OCR_FALLBACK:
            print("   -> Using OCR as final fallback")
            return pytesseract.image_to_string(image).strip()
        
        return ""
        
    except Exception as e:
        print(f"⚠️ AI vision captcha solving failed: {e}")
        if USE_OCR_FALLBACK:
            try:
                return pytesseract.image_to_string(image).strip()
            except:
                pass
        return ""

def ai_solve_text_captcha(driver):
    """Solve text-based captchas (math problems, word problems, etc.)"""
    try:
        # Look for text-based captcha elements
        text_selectors = [
            "//div[contains(text(), 'captcha')]",
            "//span[contains(text(), 'captcha')]",
            "//p[contains(text(), 'captcha')]",
            "//div[contains(@class, 'captcha')]",
            "//span[contains(@class, 'captcha')]"
        ]
        
        for selector in text_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.lower()
                    
                    # Check for math problems
                    if any(op in text for op in ['+', '-', '*', '/', '=']):
                        solution = solve_math_captcha(text)
                        if solution:
                            # Find input field and submit
                            inputs = driver.find_elements(By.TAG_NAME, "input")
                            for inp in inputs:
                                if inp.is_displayed() and inp.get_attribute('type') == 'text':
                                    inp.clear()
                                    inp.send_keys(str(solution))
                                    inp.send_keys(Keys.RETURN)
                                    time.sleep(MEDIUM_WAIT)
                                    print("   -> ✅ Math captcha solved")
                                    return True
                    
                    # Check for word problems
                    elif any(word in text for word in ['color', 'animal', 'fruit', 'vehicle']):
                        solution = solve_word_captcha(text)
                        if solution:
                            # Find input field and submit
                            inputs = driver.find_elements(By.TAG_NAME, "input")
                            for inp in inputs:
                                if inp.is_displayed() and inp.get_attribute('type') == 'text':
                                    inp.clear()
                                    inp.send_keys(solution)
                                    inp.send_keys(Keys.RETURN)
                                    time.sleep(MEDIUM_WAIT)
                                    print("   -> ✅ Word captcha solved")
                                    return True
                                    
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"⚠️ Text captcha solving failed: {e}")
        return False

def solve_math_captcha(text):
    """Solve simple math captchas"""
    try:
        # Extract numbers and operators
        import re
        numbers = re.findall(r'\d+', text)
        operators = re.findall(r'[+\-*/]', text)
        
        if len(numbers) >= 2 and operators:
            a, b = int(numbers[0]), int(numbers[1])
            op = operators[0]
            
            if op == '+':
                return a + b
            elif op == '-':
                return a - b
            elif op == '*':
                return a * b
            elif op == '/':
                return a // b if b != 0 else 0
        
        return None
        
    except:
        return None

def solve_word_captcha(text):
    """Solve word-based captchas using AI with quota management"""
    try:
        if not AI_ENABLED:
            return ""
        
        # Check API quota before making calls
        if API_QUOTA_MANAGEMENT and not check_api_quota():
            print("   -> Skipping AI word captcha solving due to quota limits")
            return ""
        
        prompt = f"Solve this captcha question: {text}. Return only the answer."
        
        increment_api_call_counter()
        response = openai_client.chat.completions.create(
            model=AI_MODELS['gpt35'],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        error_str = str(e)
        if "quota" in error_str.lower() or "insufficient_quota" in error_str.lower():
            handle_api_quota_error("solve_word_captcha")
        return ""

def ai_solve_interactive_captcha(driver):
    """Solve interactive captchas (click, drag, etc.)"""
    try:
        # Look for interactive elements
        interactive_selectors = [
            "//div[contains(@class, 'captcha')]//div",
            "//div[contains(@class, 'captcha')]//span",
            "//div[contains(@class, 'captcha')]//button",
            "//canvas[contains(@class, 'captcha')]"
        ]
        
        for selector in interactive_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    # Try clicking elements
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            driver.execute_script("arguments[0].click();", element)
                            time.sleep(SHORT_WAIT)
                            
                            # Check if captcha was solved
                            if not driver.find_elements(By.XPATH, "//*[contains(text(), 'captcha')]"):
                                print("   -> ✅ Interactive captcha solved")
                                return True
                                
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"⚠️ Interactive captcha solving failed: {e}")
        return False

def ai_bypass_captcha_ai(driver):
    """Use AI to bypass captcha entirely with quota management"""
    try:
        if not AI_ENABLED:
            return False
        
        # Check API quota before making calls
        if API_QUOTA_MANAGEMENT and not check_api_quota():
            print("   -> Skipping AI captcha bypass due to quota limits, trying basic bypass")
            if ENABLE_BASIC_CAPTCHA_BYPASS:
                return attempt_captcha_bypass(driver)
            return False
        
        # Get page content
        html = driver.page_source
        
        prompt = f"""
        Analyze this webpage HTML and determine if there's a way to bypass the captcha:
        {html[:2000]}
        
        Look for:
        1. Hidden form fields that can be filled
        2. Alternative submission methods
        3. JavaScript that can be executed
        4. API endpoints that can be called directly
        
        Return only 'BYPASS' if you find a bypass method, or 'NO_BYPASS' if not.
        """
        
        increment_api_call_counter()
        response = openai_client.chat.completions.create(
            model=AI_MODELS['gpt4'],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        
        if result == 'BYPASS':
            print("   -> 🤖 AI detected bypass method, attempting...")
            # Try to execute bypass
            return attempt_captcha_bypass(driver)
        
        return False
        
    except Exception as e:
        error_str = str(e)
        if "quota" in error_str.lower() or "insufficient_quota" in error_str.lower():
            handle_api_quota_error("ai_bypass_captcha_ai")
            # Try basic bypass without AI
            if ENABLE_BASIC_CAPTCHA_BYPASS:
                print("   -> Trying basic captcha bypass due to quota error")
                return attempt_captcha_bypass(driver)
        else:
            print(f"⚠️ AI captcha bypass failed: {e}")
        return False

def attempt_captcha_bypass(driver):
    """Attempt to bypass captcha using various methods"""
    try:
        # Method 1: Try to submit form without captcha
        forms = driver.find_elements(By.TAG_NAME, "form")
        for form in forms:
            try:
                form.submit()
                time.sleep(MEDIUM_WAIT)
                if not driver.find_elements(By.XPATH, "//*[contains(text(), 'captcha')]"):
                    print("   -> ✅ Captcha bypassed via form submission")
                    return True
            except:
                continue
        
        # Method 2: Try JavaScript submission
        try:
            driver.execute_script("document.querySelector('form').submit();")
            time.sleep(MEDIUM_WAIT)
            if not driver.find_elements(By.XPATH, "//*[contains(text(), 'captcha')]"):
                print("   -> ✅ Captcha bypassed via JavaScript")
                return True
        except:
            pass
        
        # Method 3: Try to remove captcha requirement
        try:
            driver.execute_script("""
                var captchaElements = document.querySelectorAll('[class*="captcha"], [id*="captcha"]');
                for (var i = 0; i < captchaElements.length; i++) {
                    captchaElements[i].style.display = 'none';
                }
            """)
            time.sleep(SHORT_WAIT)
            print("   -> ✅ Captcha elements hidden")
            return True
        except:
            pass
        
        return False
        
    except Exception as e:
        print(f"⚠️ Captcha bypass attempt failed: {e}")
        return False

def process_url_with_retry(url, worker_id, max_attempts=None):
    """Enhanced URL processing with intelligent retry logic and error handling"""
    if max_attempts is None:
        max_attempts = MAX_RETRY_ATTEMPTS
    
    last_error_type = None
    
    for attempt in range(max_attempts):
        try:
            print(f"🔄 [{worker_id}] Attempt {attempt + 1}/{max_attempts} for {url}")
            
            # Process URL
            results = process_url_fast(url, worker_id)
            
            if results:
                print(f"✅ [{worker_id}] Success on attempt {attempt + 1}")
                return results
            else:
                # Classify the "no results" as an error for intelligent handling
                error_type = "no_addresses"
                recovery_info = handle_scraping_error(error_type, url, "No addresses found", attempt + 1)
                
                if not recovery_info['retry_recommended']:
                    print(f"🚫 [{worker_id}] No retry recommended for {error_type}")
                    break
                
                print(f"🔧 [{worker_id}] Recovery action: {recovery_info['recovery_action']}")
                print(f"⏳ [{worker_id}] Waiting {recovery_info['delay']:.1f}s before retry...")
                time.sleep(recovery_info['delay'])
                
                # Apply recovery actions
                if recovery_info['tor_rotation']:
                    print(f"🔄 [{worker_id}] Rotating TOR identity as part of recovery")
                    if rotate_tor_identity():
                        time.sleep(3)  # Wait for new circuit
                
                last_error_type = error_type
                
        except Exception as e:
            err_msg = str(e)
            if "ERR_SOCKS_CONNECTION_FAILED" in err_msg or ("net::ERR" in err_msg and "SOCKS" in err_msg):
                print(f"⚠️ [{worker_id}] Tor connection failed for {url} – skipping (site offline or circuit issue)")
            else:
                print(f"❌ [{worker_id}] Error processing {get_base_domain(url)}: {err_msg}")
            continue
    
    # Record final failure with context
    if last_error_type:
        print(f"❌ [{worker_id}] All {max_attempts} attempts failed for {url} (last error: {last_error_type})")
        integrated_agents.record_failure(url, last_error_type, "enhanced_retry", worker_id, "retry_exhausted")
    else:
        print(f"❌ [{worker_id}] All {max_attempts} attempts failed for {url}")
    
    return []

# ---[ PHASE 3 ENHANCEMENTS ]---
# Enhanced address extraction with multiple methods
ENABLE_ENHANCED_ADDRESS_EXTRACTION = True  # Re-enabled as fallback option for complex cases
ENABLE_AI_CAPTCHA_SOLVING = True  # Enhanced with better quota management
ENABLE_RETRY_LOGIC = True
ENABLE_CONTEXT_AWARE_EXTRACTION = True

# Enhanced retry configuration with exponential backoff
MAX_RETRY_ATTEMPTS = 5  # Increased from 3 for better success rate
RETRY_DELAY_BASE = 3.0  # Increased from 2.0 for more conservative approach
RETRY_DELAY_MULTIPLIER = 2.0  # Increased from 1.5 for better backoff
RETRYABLE_ERRORS = [
    'captcha', 'timeout', 'connection', 'blocked', 'suspicious', 
    'rate_limit', 'temporary', 'maintenance', 'overloaded',
    'no_addresses', 'processing_error', 'failed', 'error',
    'denied', 'forbidden', 'unavailable', 'busy'
]

# Enhanced address extraction patterns
ENHANCED_PATTERNS = {
    "BTC": [
        re.compile(r"\b(bc1[a-zA-Z0-9]{25,90}|[13][a-zA-HJ-NP-Z0-9]{25,39})\b"),
        re.compile(r'["\'](bc1[a-zA-Z0-9]{25,90}|[13][a-zA-HJ-NP-Z0-9]{25,39})["\']'),
        re.compile(r'address["\']?\s*[:=]\s*["\'](bc1[a-zA-Z0-9]{25,90}|[13][a-zA-HJ-NP-Z0-9]{25,39})["\']'),
        re.compile(r'btc["\']?\s*[:=]\s*["\'](bc1[a-zA-Z0-9]{25,90}|[13][a-zA-HJ-NP-Z0-9]{25,39})["\']'),
        re.compile(r'bitcoin["\']?\s*[:=]\s*["\'](bc1[a-zA-Z0-9]{25,90}|[13][a-zA-HJ-NP-Z0-9]{25,39})["\']'),
    ],
    "ETH": [
        re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
        re.compile(r'["\'](0x[a-fA-F0-9]{40})["\']'),
        re.compile(r'address["\']?\s*[:=]\s*["\'](0x[a-fA-F0-9]{40})["\']'),
        re.compile(r'eth["\']?\s*[:=]\s*["\'](0x[a-fA-F0-9]{40})["\']'),
        re.compile(r'ethereum["\']?\s*[:=]\s*["\'](0x[a-fA-F0-9]{40})["\']'),
    ],
    "XMR": [
        re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b"),
        re.compile(r'["\'](4[0-9AB][1-9A-HJ-NP-Za-km-z]{93})["\']'),
        re.compile(r'address["\']?\s*[:=]\s*["\'](4[0-9AB][1-9A-HJ-NP-Za-km-z]{93})["\']'),
        re.compile(r'xmr["\']?\s*[:=]\s*["\'](4[0-9AB][1-9A-HJ-NP-Za-km-z]{93})["\']'),
        re.compile(r'monero["\']?\s*[:=]\s*["\'](4[0-9AB][1-9A-HJ-NP-Za-km-z]{93})["\']'),
    ],
    "TRON": [
        re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b"),
        re.compile(r'["\'](T[1-9A-HJ-NP-Za-km-z]{33})["\']'),
        re.compile(r'address["\']?\s*[:=]\s*["\'](T[1-9A-HJ-NP-Za-km-z]{33})["\']'),
        re.compile(r'tron["\']?\s*[:=]\s*["\'](T[1-9A-HJ-NP-Za-km-z]{33})["\']'),
    ],
    "SOL": [
        re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{44}\b"),
        re.compile(r'["\']([1-9A-HJ-NP-Za-km-z]{44})["\']'),
        re.compile(r'address["\']?\s*[:=]\s*["\']([1-9A-HJ-NP-Za-km-z]{44})["\']'),
        re.compile(r'sol["\']?\s*[:=]\s*["\']([1-9A-HJ-NP-Za-km-z]{44})["\']'),
        re.compile(r'solana["\']?\s*[:=]\s*["\']([1-9A-HJ-NP-Za-km-z]{44})["\']'),
    ]
}

# Context-aware extraction keywords
CONTEXT_KEYWORDS = {
    'payment': ['pay', 'payment', 'checkout', 'order', 'purchase', 'buy', 'deposit', 'send'],
    'wallet': ['wallet', 'address', 'receive', 'fund', 'balance', 'account'],
    'crypto': ['bitcoin', 'btc', 'ethereum', 'eth', 'monero', 'xmr', 'tron', 'solana', 'sol'],
    'transaction': ['tx', 'transaction', 'transfer', 'withdraw', 'exchange']
}

# ---[ API QUOTA MANAGEMENT ]---
API_QUOTA_MANAGEMENT = True
FALLBACK_ON_API_ERROR = True
API_CALL_LIMIT_PER_HOUR = 15  # Increased from 5 for better AI captcha solving
API_CALLS_MADE = 0
LAST_API_RESET = time.time()

# Enhanced fallback options when API quota is exceeded
DISABLE_AI_ON_QUOTA_ERROR = False  # Keep AI enabled but use fallbacks
USE_OCR_FALLBACK = True
ENABLE_BASIC_CAPTCHA_BYPASS = True
ENABLE_ADVANCED_CAPTCHA_BYPASS = True  # New enhanced bypass methods

# Emergency mode - disable all AI features to avoid quota errors
EMERGENCY_MODE = False  # Set to True to disable all AI features immediately

def check_api_quota():
    """Check if we can make API calls without exceeding quota"""
    global API_CALLS_MADE, LAST_API_RESET
    
    current_time = time.time()
    # Reset counter every hour
    if current_time - LAST_API_RESET > 3600:
        API_CALLS_MADE = 0
        LAST_API_RESET = current_time
    
    # Check if we're approaching quota limit
    if API_CALLS_MADE >= API_CALL_LIMIT_PER_HOUR:
        print(f"⚠️ API quota limit reached ({API_CALLS_MADE}/{API_CALL_LIMIT_PER_HOUR}), using fallback methods")
        return False
    
    return True

def increment_api_call_counter():
    """Increment API call counter"""
    global API_CALLS_MADE
    API_CALLS_MADE += 1

def handle_api_quota_error(function_name="Unknown"):
    """Handle API quota errors gracefully"""
    print(f"🚨 API Quota Error in {function_name}")
    print("💡 Recommendations:")
    print("   1. Check your OpenAI billing at: https://platform.openai.com/account/billing")
    print("   2. Add credits to your OpenAI account")
    print("   3. Consider upgrading your OpenAI plan")
    print("   4. The scraper will continue with fallback methods")
    
    if DISABLE_AI_ON_QUOTA_ERROR:
        print("🔄 Disabling AI features temporarily to avoid further quota errors")
        return False
    
    return True

def smart_iterative_ecommerce_flow(driver, url, title, categories, max_iterations=5, worker_id=None):
    """
    Smart iterative e-commerce flow handler that tries multiple approaches
    to navigate complex purchase flows until addresses are found.
    """
    try:
        print(f"🔄 Smart iterative e-commerce flow activated (max {max_iterations} iterations)")
        
        addresses_found = []
        iteration = 0
        attempted_actions = set()  # Track what we've tried
        
        # Define all possible actions in priority order
        action_strategies = [
            # Direct extraction attempts
            {"name": "direct_extraction", "priority": 1},
            {"name": "scroll_and_wait", "priority": 1},
            {"name": "coin_selection", "priority": 2},
            
            # Simple purchase flows
            {"name": "click_buy_now", "priority": 2},
            {"name": "add_to_cart", "priority": 3},
            {"name": "checkout_button", "priority": 3},
            {"name": "purchase_button", "priority": 3},
            
            # Form interactions
            {"name": "fill_contact_form", "priority": 4},
            {"name": "fill_shipping_form", "priority": 4},
            {"name": "fill_payment_form", "priority": 4},
            
            # Authentication flows
            {"name": "register_account", "priority": 5},
            {"name": "login_account", "priority": 5},
            {"name": "guest_checkout", "priority": 4},
            
            # Verification flows
            {"name": "solve_captcha", "priority": 6},
            {"name": "verify_age", "priority": 5},
            {"name": "accept_terms", "priority": 4},
            
            # Advanced interactions
            {"name": "select_product_options", "priority": 6},
            {"name": "select_quantity", "priority": 6},
            {"name": "select_shipping", "priority": 6},
            {"name": "trial_signup", "priority": 7},
            
            # Navigation flows
            {"name": "browse_products", "priority": 7},
            {"name": "access_premium", "priority": 7},
            {"name": "continue_shopping", "priority": 8},
        ]
        
        # Sort by priority
        action_strategies.sort(key=lambda x: x["priority"])
        
        while iteration < max_iterations and not addresses_found:
            iteration += 1
            print(f"🔄 Iteration {iteration}/{max_iterations}")

            # Try navbar buy button first
            if try_navbar_buy_button(driver):
                print(f"   ✅ Navbar 'Buy' button clicked, waiting for page update...")
                time.sleep(2)
                scroll_entire_page(driver)
                time.sleep(1)
                
                # Check for and handle email modals that might appear after clicking buy
                print(f"   🔍 Checking for email modals after buy button click...")
                modal_context = {
                    "trigger_action": "navbar_buy_click",
                    "page_state": "post_buy_click",
                    "expected_behavior": "email_collection_for_purchase"
                }
                modal_handled = try_handle_generic_email_modal_with_retries(driver, worker_id, modal_context)
                if modal_handled:
                    print(f"   ✅ Email modal handled successfully after buy click")
                    time.sleep(2)  # Wait for modal submission to process
                
                addresses_found = extract_addresses_enhanced(driver.page_source, url, title)
                if addresses_found:
                    print(f"✅ Found {len(addresses_found)} addresses after navbar buy click")
                    break

            # Check for addresses first
            addresses_found = extract_addresses_enhanced(driver.page_source, url, title)
            if addresses_found:
                print(f"✅ Found {len(addresses_found)} addresses on iteration {iteration}")
                break
            
            # Analyze current page state
            page_state = analyze_page_state(driver)
            print(f"   Page state: {page_state['type']} (score: {page_state['confidence']})")
            
            # Select best action based on page state and what we haven't tried
            best_action = select_best_action(page_state, action_strategies, attempted_actions)
            
            if not best_action:
                print(f"   No more actions to try, ending iteration")
                break
            
            print(f"   Executing action: {best_action}")
            attempted_actions.add(best_action)
            
            # Execute the selected action
            action_success = execute_ecommerce_action(driver, best_action, page_state)
            
            if action_success:
                print(f"   ✅ Action '{best_action}' completed successfully")
                
                # Check for and handle email modals that might appear after any action
                print(f"   🔍 Checking for email modals after '{best_action}' action...")
                modal_context = {
                    "trigger_action": best_action,
                    "page_state": f"post_{best_action}",
                    "expected_behavior": "email_collection_or_verification"
                }
                modal_handled = try_handle_generic_email_modal_with_retries(driver, worker_id, modal_context)
                if modal_handled:
                    print(f"   ✅ Email modal handled successfully after '{best_action}' action")
                    time.sleep(2)  # Wait for modal submission to process
                
                # Special handling: if we successfully added to cart, try to proceed to checkout
                if best_action == "add_to_cart":
                    print("   🛒 Item added to cart, attempting to proceed to checkout...")
                    time.sleep(MEDIUM_WAIT)  # Wait for cart update
                    
                    # Try to click checkout button
                    checkout_success = enhanced_checkout_click(driver)
                    if checkout_success:
                        print("   ✅ Proceeded to checkout page")
                        time.sleep(MEDIUM_WAIT)
                        
                        # Check for modals again after checkout click
                        print(f"   🔍 Checking for email modals after checkout click...")
                        checkout_modal_context = {
                            "trigger_action": "checkout_click",
                            "page_state": "checkout_page",
                            "expected_behavior": "email_collection_for_checkout"
                        }
                        checkout_modal_handled = try_handle_generic_email_modal_with_retries(driver, worker_id, checkout_modal_context)
                        if checkout_modal_handled:
                            print(f"   ✅ Email modal handled successfully after checkout click")
                            time.sleep(2)
                        
                        # Now try to complete the checkout process
                        checkout_completed = ai_handle_checkout_form(driver, url, categories)
                        if checkout_completed:
                            print("   💳 Checkout completed successfully")
                        else:
                            print("   ⚠️ Checkout form handling failed")
                    else:
                        print("   ⚠️ Could not find checkout button after adding to cart")
                
                # Wait for page to update after action
                time.sleep(SHORT_WAIT)
                
                # Scroll and wait for dynamic content
                scroll_entire_page(driver)
                time.sleep(SHORT_WAIT)
                
            else:
                print(f"   ❌ Action '{best_action}' failed")
        
        # Final address extraction attempt
        if not addresses_found:
            addresses_found = extract_addresses_enhanced(driver.page_source, url, title)
        
        print(f"🎯 Iterative flow completed: {len(addresses_found)} addresses found after {iteration} iterations")
        return addresses_found
        
    except Exception as e:
        print(f"⚠️ Smart iterative flow failed: {e}")
        return []

def analyze_page_state(driver):
    """Analyze current page to determine what type of page we're on and what actions are possible"""
    try:
        page_content = driver.page_source.lower()
        
        # Define page type indicators
        page_indicators = {
            "product_page": ["add to cart", "buy now", "purchase", "price", "product"],
            "cart_page": ["cart", "checkout", "proceed", "total", "quantity"],
            "checkout_page": ["checkout", "billing", "shipping", "payment", "order"],
            "login_page": ["login", "sign in", "username", "password", "authenticate"],
            "register_page": ["register", "sign up", "create account", "join", "new user"],
            "payment_page": ["payment", "address", "wallet", "bitcoin", "crypto", "send"],
            "verification_page": ["captcha", "verify", "confirm", "validation", "check"],
            "form_page": ["form", "submit", "required", "field", "input"],
            "coin_selection": ["select coin", "payment method", "cryptocurrency", "choose"],
            "trial_page": ["trial", "free", "demo", "test", "preview"],
            "premium_page": ["premium", "vip", "exclusive", "member", "subscription"],
            "terms_page": ["terms", "agreement", "accept", "policy", "conditions"]
        }
        
        # Calculate scores for each page type
        page_scores = {}
        for page_type, indicators in page_indicators.items():
            score = sum(1 for indicator in indicators if indicator in page_content)
            page_scores[page_type] = score
        
        # Find the page type with highest score
        best_match = max(page_scores.items(), key=lambda x: x[1])
        page_type, confidence = best_match
        
        # Get available actions on current page
        available_actions = detect_available_actions(driver, page_content)
        
        return {
            "type": page_type,
            "confidence": confidence,
            "available_actions": available_actions,
            "content_length": len(page_content),
            "has_forms": "form" in page_content,
            "has_buttons": "button" in page_content,
            "has_links": "<a " in page_content
        }
        
    except Exception as e:
        print(f"⚠️ Page state analysis failed: {e}")
        return {"type": "unknown", "confidence": 0, "available_actions": []}

def detect_available_actions(driver, page_content):
    """Detect what actions are possible on the current page"""
    available_actions = []
    
    try:
        # Check for specific elements
        action_checks = {
            "click_buy_now": ["buy now", "buy instantly"],
            "add_to_cart": ["add to cart", "add to basket"],
            "checkout_button": ["checkout", "proceed to checkout"],
            "purchase_button": ["purchase", "buy", "order now"],
            "register_account": ["register", "sign up", "create account"],
            "login_account": ["login", "sign in", "log in"],
            "fill_contact_form": ["contact", "name", "email"],
            "fill_shipping_form": ["shipping", "address", "delivery"],
            "fill_payment_form": ["payment", "credit card", "billing"],
            "solve_captcha": ["captcha", "verification", "prove you're human"],
            "coin_selection": ["select coin", "payment method", "cryptocurrency"],
            "accept_terms": ["accept", "agree", "terms", "conditions"],
            "select_quantity": ["quantity", "qty", "amount"],
            "guest_checkout": ["guest", "continue without", "skip registration"],
            "trial_signup": ["free trial", "start trial", "try free"]
        }
        
        for action, keywords in action_checks.items():
            if any(keyword in page_content for keyword in keywords):
                available_actions.append(action)
        
        # Check for actual elements
        element_checks = {
            "click_buy_now": "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy now')]",
            "add_to_cart": "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to cart')]",
            "checkout_button": "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'checkout')]",
            "register_account": "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'register')]",
            "login_account": "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]"
        }
        
        for action, xpath in element_checks.items():
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if any(elem.is_displayed() and elem.is_enabled() for elem in elements):
                    if action not in available_actions:
                        available_actions.append(action)
            except:
                continue
        
        return available_actions
        
    except Exception as e:
        print(f"⚠️ Action detection failed: {e}")
        return []

def select_best_action(page_state, action_strategies, attempted_actions):
    """Select the best action to try next based on page state and what we haven't tried"""
    
    # Filter to actions we haven't tried yet
    available_strategies = [
        action for action in action_strategies 
        if action["name"] not in attempted_actions
    ]
    
    if not available_strategies:
        return None
    
    # Filter to actions that are relevant for current page state
    relevant_actions = []
    
    page_type = page_state["type"]
    available_actions = page_state["available_actions"]
    
    # Page-specific action preferences
    page_preferences = {
        "product_page": ["add_to_cart", "click_buy_now", "purchase_button", "select_quantity"],
        "cart_page": ["checkout_button", "continue_shopping", "select_shipping"],
        "checkout_page": ["fill_shipping_form", "fill_payment_form", "guest_checkout"],
        "login_page": ["login_account", "register_account", "guest_checkout"],
        "register_page": ["register_account", "fill_contact_form"],
        "payment_page": ["coin_selection", "fill_payment_form"],
        "verification_page": ["solve_captcha", "verify_age", "accept_terms"],
        "form_page": ["fill_contact_form", "fill_shipping_form", "fill_payment_form"],
        "coin_selection": ["coin_selection"],
        "trial_page": ["trial_signup", "register_account"],
        "terms_page": ["accept_terms"]
    }
    
    # Get preferred actions for current page type
    preferred_actions = page_preferences.get(page_type, [])
    
    # Score actions based on relevance
    for strategy in available_strategies:
        action_name = strategy["name"]
        score = strategy["priority"]
        
        # Boost score if action is preferred for this page type
        if action_name in preferred_actions:
            score -= 2  # Lower number = higher priority
        
        # Boost score if action is detected as available
        if action_name in available_actions:
            score -= 1
        
        relevant_actions.append({
            "name": action_name,
            "score": score
        })
    
    # Sort by score (lower is better)
    relevant_actions.sort(key=lambda x: x["score"])
    
    # Return the best action
    if relevant_actions:
        return relevant_actions[0]["name"]
    
    return None

def execute_ecommerce_action(driver, action, page_state):
    """Execute a specific e-commerce action"""
    try:
        print(f"      Executing: {action}")
        
        if action == "direct_extraction":
            # Just extract addresses without doing anything
            return True
            
        elif action == "scroll_and_wait":
            scroll_entire_page(driver)
            time.sleep(MEDIUM_WAIT)
            return True
            
        elif action == "coin_selection":
            return handle_coin_selection_action(driver)
            
        elif action == "click_buy_now":
            return click_elements_by_text(driver, ["buy now", "buy instantly"])
            
        elif action == "add_to_cart":
            return enhanced_add_to_cart(driver)
            
        elif action == "checkout_button":
            return enhanced_checkout_click(driver)
            
        elif action == "purchase_button":
            return click_elements_by_text(driver, ["purchase", "buy", "order now"])
            
        elif action == "register_account":
            return ai_handle_registration_enhanced(driver, driver.current_url, page_state)
            
        elif action == "login_account":
            return ai_handle_login_enhanced(driver, driver.current_url, page_state)
            
        elif action == "fill_contact_form":
            return fill_form_by_type(driver, "contact")
            
        elif action == "fill_shipping_form":
            return fill_form_by_type(driver, "shipping")
            
        elif action == "fill_payment_form":
            return fill_form_by_type(driver, "payment")
            
        elif action == "solve_captcha":
            return ai_solve_captcha_enhanced(driver)
            
        elif action == "verify_age":
            return handle_age_verification(driver)
            
        elif action == "accept_terms":
            return click_elements_by_text(driver, ["accept", "agree", "i agree"])
            
        elif action == "select_product_options":
            return select_product_options(driver)
            
        elif action == "select_quantity":
            return select_quantity(driver)
            
        elif action == "select_shipping":
            return select_shipping_option(driver)
            
        elif action == "guest_checkout":
            return click_elements_by_text(driver, ["guest checkout", "continue as guest", "skip registration"])
            
        elif action == "trial_signup":
            return click_elements_by_text(driver, ["free trial", "start trial", "try free"])
            
        elif action == "browse_products":
            return browse_products(driver)
            
        elif action == "access_premium":
            return click_elements_by_text(driver, ["premium", "vip", "upgrade"])
            
        elif action == "continue_shopping":
            return click_elements_by_text(driver, ["continue shopping", "keep shopping"])
            
        else:
            print(f"      Unknown action: {action}")
            return False
            
    except Exception as e:
        print(f"      Action execution failed: {e}")
        return False

def enhanced_add_to_cart(driver):
    """Enhanced add to cart with multiple detection strategies"""
    try:
        print("        Trying enhanced add to cart...")
        
        # Strategy 1: Look for buttons/links with "add to cart" text (multiple approaches)
        cart_texts = ["add to cart", "add to basket", "add item", "add product", "add", "cart"]
        
        for text in cart_texts:
            # Try simple text contains first
            try:
                buttons = driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                buttons.extend(driver.find_elements(By.XPATH, f"//a[contains(text(), '{text}')]"))
                buttons.extend(driver.find_elements(By.XPATH, f"//input[@type='submit'][contains(@value, '{text}')]"))
                
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(0.3)
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"        ✅ Clicked add to cart button: {btn.text[:30]}")
                            return True
                        except:
                            continue
            except:
                pass
        
        # Strategy 2: Look for buttons with cart-related IDs/classes
        cart_selectors = [
            "//button[contains(@id, 'cart') or contains(@class, 'cart')]",
            "//button[contains(@id, 'add') or contains(@class, 'add')]",
            "//a[contains(@id, 'cart') or contains(@class, 'cart')]",
            "//input[@type='submit'][contains(@id, 'cart') or contains(@class, 'cart')]"
        ]
        
        for selector in cart_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        # Check if text suggests it's an add to cart button
                        elem_text = elem.text.lower() if elem.text else ""
                        if any(word in elem_text for word in ["add", "cart", "basket", "buy"]):
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                time.sleep(0.3)
                                driver.execute_script("arguments[0].click();", elem)
                                print(f"        ✅ Clicked cart element by ID/class: {elem.text[:30]}")
                                return True
                            except:
                                continue
            except:
                continue
        
        # Strategy 3: Look for forms that might be add to cart forms
        try:
            forms = driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                form_html = form.get_attribute('outerHTML').lower()
                if any(word in form_html for word in ["cart", "add", "basket", "buy"]):
                    # Try to submit this form
                    submit_buttons = form.find_elements(By.XPATH, ".//button | .//input[@type='submit']")
                    for btn in submit_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            try:
                                driver.execute_script("arguments[0].click();", btn)
                                print(f"        ✅ Submitted add to cart form")
                                return True
                            except:
                                continue
        except:
            pass
        
        # Strategy 4: Fallback - click any prominent button that might be add to cart
        try:
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            all_buttons.extend(driver.find_elements(By.XPATH, "//input[@type='submit']"))
            
            # Filter to buttons that are likely add to cart
            cart_candidates = []
            for btn in all_buttons:
                if not btn.is_displayed() or not btn.is_enabled():
                    continue
                    
                btn_text = btn.text.lower() if btn.text else ""
                btn_value = btn.get_attribute('value') or ""
                btn_value = btn_value.lower()
                
                # Score this button based on how likely it is to be add to cart
                score = 0
                if "add" in btn_text or "add" in btn_value:
                    score += 3
                if "cart" in btn_text or "cart" in btn_value:
                    score += 3
                if "basket" in btn_text or "basket" in btn_value:
                    score += 2
                if "buy" in btn_text or "buy" in btn_value:
                    score += 2
                if "purchase" in btn_text or "purchase" in btn_value:
                    score += 1
                
                if score > 0:
                    cart_candidates.append((btn, score))
            
            # Sort by score and try the best candidates
            cart_candidates.sort(key=lambda x: x[1], reverse=True)
            for btn, score in cart_candidates[:3]:  # Try top 3
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(0.3)
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"        ✅ Clicked likely cart button (score {score}): {btn.text[:30]}")
                    return True
                except:
                    continue
        except:
            pass
        
        print("        ❌ Could not find any add to cart buttons")
        return False
        
    except Exception as e:
        print(f"        ❌ Enhanced add to cart failed: {e}")
        return False

def enhanced_checkout_click(driver):
    """Enhanced checkout button detection and clicking with better timing and detection"""
    try:
        print("        Trying enhanced checkout click...")
        
        # Wait for page to update after add to cart
        time.sleep(1.0)
        
        # Scroll to reveal any checkout buttons that might be hidden
        scroll_entire_page(driver)
        time.sleep(0.5)
        
        # Strategy 1: Look for checkout buttons with comprehensive text matches
        checkout_texts = [
            # Primary checkout terms
            "proceed to checkout", "go to checkout", "continue to checkout", "checkout now",
            "checkout", "view cart", "view basket", "cart", "basket",
            # Secondary terms
            "proceed", "continue", "next step", "next", "order now", "place order",
            # WooCommerce specific
            "view cart", "proceed to checkout", "checkout",
            # Shopify specific  
            "checkout", "continue to checkout", "proceed to checkout",
            # Other platforms
            "continue shopping", "go to cart", "shopping cart"
        ]
        
        # Strategy 0: Look for cart notification popups/messages with checkout buttons
        try:
            print("        🔍 Looking for cart notification popups...")
            # Common cart notification selectors
            notification_selectors = [
                ".cart-notification", ".cart-popup", ".cart-modal", ".cart-drawer",
                ".added-to-cart", ".cart-success", ".mini-cart", ".cart-overlay",
                "#cart-notification", "#cart-popup", "#cart-modal", "#cart-drawer"
            ]
            
            for selector in notification_selectors:
                try:
                    notifications = driver.find_elements(By.CSS_SELECTOR, selector)
                    for notification in notifications:
                        if notification.is_displayed():
                            print(f"        🎯 Found cart notification: {selector}")
                            # Look for checkout buttons within the notification
                            checkout_links = notification.find_elements(By.XPATH, ".//a | .//button")
                            for link in checkout_links:
                                if link.is_displayed() and link.is_enabled():
                                    link_text = link.text.lower()
                                    if any(term in link_text for term in ["checkout", "cart", "proceed", "view", "continue"]):
                                        driver.execute_script("arguments[0].click();", link)
                                        print(f"        ✅ Clicked notification checkout button: {link.text[:30]}")
                                        return True
                except:
                    continue
        except:
            pass
        
        for text in checkout_texts:
            try:
                # Try case-insensitive text matching with improved selectors
                selectors = [
                    # Primary selectors with translate for case insensitivity
                    f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
                    f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
                    f"//input[@type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
                    # Exact text matches (case sensitive fallback)
                    f"//button[contains(text(), '{text}')]",
                    f"//a[contains(text(), '{text}')]",
                    f"//input[@value='{text}']",
                    # Case variations
                    f"//button[contains(text(), '{text.title()}')]",
                    f"//a[contains(text(), '{text.title()}')]",
                    f"//button[contains(text(), '{text.upper()}')]",
                    f"//a[contains(text(), '{text.upper()}')]"
                ]
                
                for selector in selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        for elem in elements:
                            if elem.is_displayed() and elem.is_enabled():
                                # Extra check to make sure it's really a checkout button
                                elem_text = elem.text.lower()
                                elem_href = elem.get_attribute('href') or ""
                                elem_onclick = elem.get_attribute('onclick') or ""
                                
                                # Skip if it looks like a "continue shopping" button instead of checkout
                                if "continue shopping" in elem_text and "checkout" not in elem_text:
                                    continue
                                
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                time.sleep(0.5)
                                driver.execute_script("arguments[0].click();", elem)
                                print(f"        ✅ Clicked checkout button: {elem.text[:30]}")
                                return True
                    except:
                        continue
            except:
                continue
        
        # Strategy 1.5: Look for floating cart icons or cart counters (often appear after add to cart)
        try:
            print("        🔍 Looking for cart icons and counters...")
            cart_icon_selectors = [
                # Cart icons with counters
                ".cart-icon", ".shopping-cart", ".cart-link", ".cart-counter",
                ".header-cart", ".mini-cart-link", ".cart-toggle", ".cart-widget",
                "#cart-icon", "#shopping-cart", "#cart-link", "#cart-counter",
                # Common cart icon patterns
                "a[href*='cart']", "a[href*='basket']", "a[href*='checkout']",
                ".fa-shopping-cart", ".fa-shopping-bag", ".icon-cart", ".icon-basket"
            ]
            
            for selector in cart_icon_selectors:
                try:
                    cart_icons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for icon in cart_icons:
                        if icon.is_displayed() and icon.is_enabled():
                            # Check if it has a counter (indicating items were added)
                            icon_html = icon.get_attribute('outerHTML').lower()
                            icon_text = icon.text
                            
                            # Look for cart count indicators
                            if any(indicator in icon_html for indicator in ['count', 'quantity', 'items', 'badge']) or \
                               any(char.isdigit() for char in icon_text):
                                print(f"        🎯 Found cart icon with counter: {icon.text}")
                                driver.execute_script("arguments[0].click();", icon)
                                print(f"        ✅ Clicked cart icon: {icon.text[:30]}")
                                return True
                except:
                    continue
        except:
            pass
        
        # Strategy 2: Look for buttons with checkout-related IDs/classes
        checkout_selectors = [
            "//button[contains(@id, 'checkout') or contains(@class, 'checkout')]",
            "//a[contains(@id, 'checkout') or contains(@class, 'checkout')]",
            "//button[contains(@id, 'proceed') or contains(@class, 'proceed')]",
            "//a[contains(@id, 'proceed') or contains(@class, 'proceed')]",
            "//input[@type='submit'][contains(@id, 'checkout') or contains(@class, 'checkout')]",
            # Additional cart-related selectors
            "//a[contains(@id, 'cart') or contains(@class, 'cart')]",
            "//button[contains(@id, 'cart') or contains(@class, 'cart')]",
            "//a[contains(@href, 'cart') or contains(@href, 'checkout')]"
        ]
        
        for selector in checkout_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", elem)
                        print(f"        ✅ Clicked checkout element by ID/class: {elem.text[:30]}")
                        return True
            except:
                continue
        
        # Strategy 3: Look for forms that might be checkout forms
        try:
            forms = driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                form_html = form.get_attribute('outerHTML').lower()
                if any(word in form_html for word in ["checkout", "proceed", "order", "payment"]):
                    submit_buttons = form.find_elements(By.XPATH, ".//button | .//input[@type='submit']")
                    for btn in submit_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            try:
                                driver.execute_script("arguments[0].click();", btn)
                                print(f"        ✅ Submitted checkout form")
                                return True
                            except:
                                continue
        except:
            pass
        
        # Strategy 4: Smart scoring of all buttons for checkout likelihood
        try:
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            all_buttons.extend(driver.find_elements(By.XPATH, "//input[@type='submit']"))
            all_buttons.extend(driver.find_elements(By.TAG_NAME, "a"))
            
            checkout_candidates = []
            for btn in all_buttons:
                if not btn.is_displayed() or not btn.is_enabled():
                    continue
                    
                btn_text = btn.text.lower() if btn.text else ""
                btn_value = btn.get_attribute('value') or ""
                btn_value = btn_value.lower()
                btn_id = btn.get_attribute('id') or ""
                btn_id = btn_id.lower()
                btn_class = btn.get_attribute('class') or ""
                btn_class = btn_class.lower()
                
                # Score this button based on checkout likelihood
                score = 0
                
                # High value keywords
                if any(word in btn_text for word in ["proceed to checkout", "go to checkout"]):
                    score += 10
                elif "checkout" in btn_text or "checkout" in btn_value:
                    score += 8
                elif "proceed" in btn_text or "proceed" in btn_value:
                    score += 6
                elif "continue" in btn_text or "continue" in btn_value:
                    score += 4
                elif "next" in btn_text or "next" in btn_value:
                    score += 3
                elif "order" in btn_text or "order" in btn_value:
                    score += 5
                
                # ID/Class bonuses
                if "checkout" in btn_id or "checkout" in btn_class:
                    score += 5
                if "proceed" in btn_id or "proceed" in btn_class:
                    score += 4
                
                if score > 0:
                    checkout_candidates.append((btn, score))
            
            # Sort by score and try the best candidates
            checkout_candidates.sort(key=lambda x: x[1], reverse=True)
            for btn, score in checkout_candidates[:3]:  # Try top 3
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"        ✅ Clicked likely checkout button (score {score}): {btn.text[:30]}")
                    return True
                except:
                    continue
        except:
            pass
        
        print("        ❌ Could not find any checkout buttons")
        return False
        
    except Exception as e:
        print(f"        ❌ Enhanced checkout click failed: {e}")
        return False

def click_elements_by_text(driver, text_options):
    """Click elements that contain any of the specified text options"""
    try:
        for text in text_options:
            # Use safer XPath expressions that don't rely on translate()
            selectors = [
                # Button with case-insensitive text matching
                f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
                f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
                f"//input[@type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
                f"//input[@type='button'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
                # Fallback: exact text match (case sensitive)
                f"//button[contains(text(), '{text}')]",
                f"//a[contains(text(), '{text}')]",
                f"//input[@value='{text}']"
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", element)
                            print(f"        Clicked: {element.text[:30]}")
                            return True
                except Exception as e:
                    # If XPath fails, try CSS selectors as fallback
                    try:
                        # Try CSS selector approach
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        for button in buttons:
                            if text.lower() in button.text.lower():
                                if button.is_displayed() and button.is_enabled():
                                    button.click()
                                    print(f"        Clicked (CSS): {button.text[:30]}")
                                    return True
                    except:
                        pass
                    continue
        
        return False
    except Exception as e:
        print(f"      Click by text failed: {e}")
        return False

def handle_coin_selection_action(driver):
    """Handle coin selection pages"""
    try:
        # Look for coin selection dropdowns or buttons with safer XPath
        coin_selectors = [
            "//select[contains(@name, 'coin') or contains(@name, 'currency') or contains(@name, 'payment')]",
            # Safer approach: use text() instead of . and add fallbacks
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bitcoin')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'btc')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bitcoin')]",
            # Fallback selectors without translate()
            "//button[contains(text(), 'Bitcoin') or contains(text(), 'BTC') or contains(text(), 'bitcoin') or contains(text(), 'btc')]",
            "//a[contains(text(), 'Bitcoin') or contains(text(), 'BTC') or contains(text(), 'bitcoin') or contains(text(), 'btc')]"
        ]
        
        for selector in coin_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    element = elements[0]
                    if element.tag_name == "select":
                        # Handle dropdown
                        options = element.find_elements(By.TAG_NAME, "option")
                        for option in options:
                            if any(coin in option.text.lower() for coin in ['bitcoin', 'btc', 'crypto']):
                                option.click()
                                return True
                    else:
                        # Handle button/link
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            return True
            except Exception as e:
                # If XPath fails, try CSS approach
                try:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        if any(coin in button.text.lower() for coin in ['bitcoin', 'btc', 'crypto']):
                            if button.is_displayed() and button.is_enabled():
                                button.click()
                                return True
                except:
                    pass
                continue
        
        return False
    except Exception as e:
        print(f"      Coin selection failed: {e}")
        return False

def fill_form_by_type(driver, form_type):
    """Fill forms based on type (contact, shipping, payment)"""
    try:
        forms = driver.find_elements(By.TAG_NAME, "form")
        for form in forms:
            form_html = form.get_attribute('outerHTML').lower()
            if form_type in form_html or any(keyword in form_html for keyword in [form_type, 'checkout', 'order']):
                return attempt_form_fill(driver, form, driver.current_url, form_type)
        
        # Try filling any visible form
        if forms:
            return attempt_form_fill(driver, forms[0], driver.current_url, form_type)
        
        return False
    except Exception as e:
        print(f"      Form fill failed: {e}")
        return False

def handle_age_verification(driver):
    """Handle age verification"""
    try:
        # Look for age verification elements
        age_selectors = [
            "//select[contains(@name, 'age') or contains(@name, 'birth')]",
            "//input[contains(@name, 'age') or contains(@name, 'birth')]",
            # Fixed XPath - safer approach
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'yes') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm')]",
            # Fallback selectors without translate()
            "//button[contains(text(), 'Yes') or contains(text(), 'yes') or contains(text(), 'Confirm') or contains(text(), 'confirm')]"
        ]
        
        for selector in age_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    element = elements[0]
                    if element.tag_name == "select":
                        # Select an adult age
                        options = element.find_elements(By.TAG_NAME, "option")
                        for option in options:
                            if any(age in option.text for age in ['25', '30', '21', '18']):
                                option.click()
                                return True
                    elif element.tag_name == "input":
                        # Enter adult age
                        element.clear()
                        element.send_keys("25")
                        return True
                    else:
                        # Click confirmation button
                        element.click()
                        return True
            except:
                continue
        
        return False
    except Exception as e:
        print(f"      Age verification failed: {e}")
        return False

def select_product_options(driver):
    """Select product options like size, color, etc."""
    try:
        # Look for product option selects
        option_selectors = [
            "//select[contains(@name, 'size') or contains(@name, 'color') or contains(@name, 'option')]",
            "//input[@type='radio'][contains(@name, 'option') or contains(@name, 'variant')]"
        ]
        
        for selector in option_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    element = elements[0]
                    if element.tag_name == "select":
                        options = element.find_elements(By.TAG_NAME, "option")
                        if len(options) > 1:
                            options[1].click()  # Select first non-default option
                            return True
                    else:
                        element.click()
                        return True
            except:
                continue
        
        return False
    except Exception as e:
        print(f"      Product option selection failed: {e}")
        return False

def select_quantity(driver):
    """Select or increase quantity"""
    try:
        # Look for quantity inputs
        qty_selectors = [
            "//input[contains(@name, 'quantity') or contains(@name, 'qty')]",
            "//select[contains(@name, 'quantity') or contains(@name, 'qty')]"
        ]
        
        for selector in qty_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    element = elements[0]
                    if element.tag_name == "input":
                        element.clear()
                        element.send_keys("1")
                        return True
                    elif element.tag_name == "select":
                        options = element.find_elements(By.TAG_NAME, "option")
                        if len(options) > 1:
                            options[1].click()
                            return True
            except:
                continue
        
        return False
    except Exception as e:
        print(f"      Quantity selection failed: {e}")
        return False

def select_shipping_option(driver):
    """Select shipping option"""
    try:
        # Look for shipping options
        shipping_selectors = [
            "//input[@type='radio'][contains(@name, 'shipping')]",
            "//select[contains(@name, 'shipping')]"
        ]
        
        for selector in shipping_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    elements[0].click()
                    return True
            except:
                continue
        
        return False
    except Exception as e:
        print(f"      Shipping selection failed: {e}")
        return False

def browse_products(driver):
    """Browse to product pages"""
    try:
        # Look for product links
        product_selectors = [
            "//a[contains(@href, 'product') or contains(@href, 'item')]",
            "//a[contains(@class, 'product')]",
            "//div[contains(@class, 'product')]//a"
        ]
        
        for selector in product_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    element = elements[0]
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        return True
            except:
                continue
        
        return False
    except Exception as e:
        print(f"      Product browsing failed: {e}")
        return False

def try_navbar_buy_button(driver):
    """Try to find and click a 'Buy' button/link in the navigation bar or submit a buy form. Tries all strategies additively."""
    # 1. Original nav bar selectors
    nav_selectors = [
        "//nav//a[contains(translate(text(), 'BUY', 'buy'), 'buy')]",
        "//header//a[contains(translate(text(), 'BUY', 'buy'), 'buy')]",
        "//a[contains(@href, 'buy')]",
        "//button[contains(translate(text(), 'BUY', 'buy'), 'buy')]"
    ]
    for selector in nav_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for el in elements:
                if el.is_displayed():
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                    except:
                        pass
                    try:
                        el.click()
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", el)
                        except Exception as ee:
                            print(f"⚠️ JS click failed on nav selector element: {ee}")
                            continue
                    print(f"🛒 Clicked nav selector: {selector}")
                    time.sleep(1.5)
                    return True
        except Exception as e:
            print(f"⚠️ Navbar buy button click failed (selector {selector}): {e}")
    # 2. Buttons with id/class containing 'buy'
    try:
        btns = driver.find_elements(By.XPATH, "//button[contains(@id, 'buy') or contains(@class, 'buy')]")
        for btn in btns:
            if btn.is_displayed():
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                except:
                    pass
                try:
                    btn.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                    except:
                        continue
                print("🛒 Clicked button with id/class containing 'buy'")
                time.sleep(1.5)
                return True
    except Exception as e:
        print(f"⚠️ Buy button by id/class failed: {e}")
    # 3. Buttons with descendant span/div containing 'Buy'
    try:
        btns = driver.find_elements(By.XPATH, "//button[.//span[contains(translate(text(), 'BUY', 'buy'), 'buy')] or .//div[contains(translate(text(), 'BUY', 'buy'), 'buy')]]")
        for btn in btns:
            if btn.is_displayed():
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                except:
                    pass
                try:
                    btn.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                    except:
                        continue
                print("🛒 Clicked button with descendant span/div containing 'Buy'")
                time.sleep(1.5)
                return True
    except Exception as e:
        print(f"⚠️ Buy button with descendant span/div failed: {e}")
    # 4. Submit forms with action containing 'buy'
    try:
        forms = driver.find_elements(By.XPATH, "//form[contains(@action, 'buy')]")
        for form in forms:
            try:
                # Try clicking any visible button inside the form first
                buttons = form.find_elements(By.XPATH, ".//button | .//input[@type='submit']")
                clicked = False
                for btn in buttons:
                    if btn.is_displayed():
                        try:
                            btn.click()
                            clicked = True
                        except Exception:
                            try:
                                driver.execute_script("arguments[0].click();", btn)
                                clicked = True
                            except:
                                pass
                        if clicked:
                            print("🛒 Submitted form button inside action 'buy'")
                            time.sleep(1.5)
                            return True
                # If no clickable button, submit the form via JS
                driver.execute_script("arguments[0].submit();", form)
                print("🛒 Submitted form with JS submit (action contains 'buy')")
                time.sleep(1.5)
                return True
            except Exception as fe:
                print(f"⚠️ Form submit attempt failed: {fe}")
    except Exception as e:
        print(f"⚠️ Buy form submit failed: {e}")
    # 5. Try clicking any visible button with text containing 'buy' (case-insensitive, anywhere in button)
    try:
        btns = driver.find_elements(By.XPATH, "//button[contains(translate(., 'BUY', 'buy'), 'buy')]")
        for btn in btns:
            if btn.is_displayed():
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                except:
                    pass
                try:
                    btn.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                    except:
                        continue
                print("🛒 Clicked button with text containing 'buy'")
                time.sleep(1.5)
                return True
    except Exception as e:
        print(f"⚠️ Buy button by text failed: {e}")
    # 6. Try clicking any input[type=submit] with value containing 'buy'
    try:
        inputs = driver.find_elements(By.XPATH, "//input[@type='submit' and contains(translate(@value, 'BUY', 'buy'), 'buy')]")
        for inp in inputs:
            if inp.is_displayed():
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", inp)
                except:
                    pass
                try:
                    inp.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", inp)
                    except:
                        continue
                print("🛒 Clicked input[type=submit] with value containing 'buy'")
                time.sleep(1.5)
                return True
    except Exception as e:
        print(f"⚠️ Buy input[type=submit] failed: {e}")
    # 7. As last resort, click all visible buttons on page sequentially (up to 10)
    try:
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for idx, btn in enumerate(buttons[:10]):
            if btn.is_displayed():
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                except:
                    pass
                try:
                    btn.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                    except:
                        continue
                print(f"🛒 Fallback clicked button #{idx+1} on page")
                time.sleep(1.5)
                # After each click, check if address appears quickly
                page_html = driver.page_source
                if any(word in page_html.lower() for word in ['bitcoin', 'btc', 'address', 'wallet']):
                    return True
    except Exception as e:
        print(f"⚠️ Fallback button clicks failed: {e}")
    return False

def handle_generic_email_modal(driver, context):
    """
    Handle generic email modal by looking for email inputs and submit buttons.
    Returns True if modal was handled, False otherwise.
    """
    try:
        print(f"🔍 [Modal Handler] Starting modal detection for context: {context}")
        
        # Look for common modal selectors
        modal_selectors = [
            '#blockoPayModal',  # Specific to this site
            '.modal', '.popup', '.overlay', '.dialog', '[role="dialog"]',
            '.lightbox', '.modal-dialog', '.modal-content'
        ]
        
        for selector in modal_selectors:
            try:
                print(f"🔍 [Modal Handler] Checking selector: {selector}")
                modals = driver.find_elements(By.CSS_SELECTOR, selector)
                for modal in modals:
                    if modal.is_displayed():
                        print(f"🎯 [Modal Handler] Found visible modal with selector: {selector}")
                        # Look for email input in the modal
                        email_inputs = modal.find_elements(By.XPATH, 
                            ".//input[@type='email'] | .//input[contains(@placeholder, 'email')] | .//input[contains(@placeholder, 'mail')]")
                        
                        if email_inputs:
                            email_input = email_inputs[0]
                            print(f"📝 [Modal Handler] Found email input in modal")
                            
                            # Generate email
                            timestamp = int(time.time())
                            random_suffix = get_random_suffix()
                            email = f'user_{timestamp}_{random_suffix}@protonmail.com'
                            print(f"📧 [Modal Handler] Generated email: {email}")
                            
                            # Fill email with slow typing
                            print(f"⏳ [Modal Handler] Clearing email field...")
                            email_input.clear()
                            time.sleep(1)  # Wait 1 second after clearing
                            
                            print(f"⌨️ [Modal Handler] Typing email character by character...")
                            for i, char in enumerate(email):
                                email_input.send_keys(char)
                                print(f"   Typed character {i+1}/{len(email)}: '{char}'")
                                time.sleep(0.3)  # 300ms delay between characters
                            
                            print(f"✅ [Modal Handler] Email field filled successfully")
                            time.sleep(2)  # Wait 2 seconds to see the filled email
                            
                            # Verify the email was entered correctly
                            entered_value = email_input.get_attribute('value')
                            print(f"🔍 [Modal Handler] Email field contains: '{entered_value}'")
                            
                            # Look for submit button
                            submit_buttons = modal.find_elements(By.XPATH,
                                ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')] | " +
                                ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')] | " +
                                ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')] | " +
                                ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')] | " +
                                ".//input[@type='submit'] | .//button[@type='submit']")
                            
                            if submit_buttons:
                                submit_button = submit_buttons[0]
                                print(f"🔘 [Modal Handler] Found submit button: {submit_button.text[:30]}")
                                print(f"⏰ [Modal Handler] Waiting 5 seconds before clicking submit button...")
                                time.sleep(5)  # Wait 5 seconds before clicking
                                
                                print(f"🖱️ [Modal Handler] Clicking submit button now...")
                                submit_button.click()
                                print(f"✅ [Modal Handler] Submit button clicked successfully")
                                time.sleep(3)  # Wait for modal to close
                                return True
                            else:
                                # Try pressing Enter on the email input
                                print(f"⌨️ [Modal Handler] No submit button found, pressing Enter key...")
                                time.sleep(2)  # Wait 2 seconds before pressing Enter
                                email_input.send_keys(Keys.RETURN)
                                print(f"✅ [Modal Handler] Pressed Enter key on email input")
                                time.sleep(3)  # Wait for response
                                return True
            except Exception as e:
                print(f"⚠️ [Modal Handler] Error with selector {selector}: {e}")
                continue
        
        # If no modal found, look for email inputs anywhere on the page
        print(f"🔍 [Modal Handler] No modal found, checking for email inputs anywhere on page...")
        email_inputs = driver.find_elements(By.XPATH, 
            "//input[@type='email'] | //input[contains(@placeholder, 'email')] | //input[contains(@placeholder, 'mail')]")
        
        if email_inputs:
            email_input = email_inputs[0]
            if email_input.is_displayed():
                print(f"📝 [Modal Handler] Found standalone email input")
                
                # Generate email
                timestamp = int(time.time())
                random_suffix = get_random_suffix()
                email = f'user_{timestamp}_{random_suffix}@protonmail.com'
                print(f"📧 [Modal Handler] Generated email: {email}")
                
                # Fill email with slow typing
                print(f"⏳ [Modal Handler] Clearing email field...")
                email_input.clear()
                time.sleep(1)  # Wait 1 second after clearing
                
                print(f"⌨️ [Modal Handler] Typing email character by character...")
                for i, char in enumerate(email):
                    email_input.send_keys(char)
                    print(f"   Typed character {i+1}/{len(email)}: '{char}'")
                    time.sleep(0.3)  # 300ms delay between characters
                
                print(f"✅ [Modal Handler] Email field filled successfully")
                time.sleep(2)  # Wait 2 seconds to see the filled email
                
                # Verify the email was entered correctly
                entered_value = email_input.get_attribute('value')
                print(f"🔍 [Modal Handler] Email field contains: '{entered_value}'")
                
                # Look for nearby submit button
                try:
                    parent_form = email_input.find_element(By.XPATH, "./ancestor::form")
                    if parent_form:
                        submit_buttons = parent_form.find_elements(By.XPATH,
                            ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')] | " +
                            ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')] | " +
                            ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')] | " +
                            ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')] | " +
                            ".//input[@type='submit'] | .//button[@type='submit']")
                        
                        if submit_buttons:
                            submit_button = submit_buttons[0]
                            print(f"🔘 [Modal Handler] Found submit button in form: {submit_button.text[:30]}")
                            print(f"⏰ [Modal Handler] Waiting 5 seconds before clicking submit button...")
                            time.sleep(5)  # Wait 5 seconds before clicking
                            
                            print(f"🖱️ [Modal Handler] Clicking submit button now...")
                            submit_button.click()
                            print(f"✅ [Modal Handler] Submit button clicked successfully")
                            time.sleep(3)  # Wait for response
                            return True
                except:
                    pass
                
                # Try pressing Enter
                print(f"⌨️ [Modal Handler] No submit button found, pressing Enter key...")
                time.sleep(2)  # Wait 2 seconds before pressing Enter
                email_input.send_keys(Keys.RETURN)
                print(f"✅ [Modal Handler] Pressed Enter key on email input")
                time.sleep(3)  # Wait for response
                return True
        
        print(f"❌ [Modal Handler] No email inputs found anywhere on page")
        return False
        
    except Exception as e:
        print(f"❌ [Modal Handler] Error: {e}")
        return False

def try_handle_generic_email_modal_with_retries(driver, worker_id, context):
    """
    Try to handle generic email modal up to 3 times with 2s wait between attempts. Logs each attempt.
    Fallback: fill all visible inputs and try to click a submit/payment button.
    """
    print(f"🔄 [Modal Retry Handler] Starting modal detection with retries for context: {context}")
    
    for attempt in range(1, 4):
        print(f"🛠️ [Modal Retry Handler] Attempt {attempt}/3: Checking for generic email modal after {context}...")
        time.sleep(2)
        try:
            if handle_generic_email_modal(driver, context):
                print(f"✅ [Modal Retry Handler] Generic email modal handled after {context} (attempt {attempt}).")
                return True
            else:
                print(f"🛠️ [Modal Retry Handler] No generic email modal found after {context} (attempt {attempt}).")
        except Exception as e:
            print(f"⚠️ [Modal Retry Handler] Error in generic email modal handler after {context} (attempt {attempt}): {e}")
    
    # Fallback: fill all visible inputs and try to click a submit/payment button
    print(f"🔄 [Modal Retry Handler] No modal/email handled after retries for {context}. Trying fallback approach...")
    print(f"🔄 [Modal Retry Handler] Attempting to fill all visible inputs...")
    fields_filled = fill_visible_inputs_anywhere(driver)
    if fields_filled > 0:
        print(f"✅ [Modal Retry Handler] Filled {fields_filled} visible input fields. Attempting to click a submit/payment button...")
        buttons = driver.find_elements(By.XPATH, "//button | //input[@type='submit'] | //input[@type='button']")
        for btn in buttons:
            try:
                if btn.is_displayed() and btn.is_enabled():
                    btn_text = (btn.text or btn.get_attribute('value') or '').lower()
                    if any(word in btn_text for word in ['pay', 'submit', 'buy', 'send', 'continue', 'ok', 'download']):
                        print(f"🔘 [Modal Retry Handler] Found suitable button: {btn_text}")
                        print(f"⏰ [Modal Retry Handler] Waiting 3 seconds before clicking fallback button...")
                        time.sleep(3)  # Wait 3 seconds before clicking
                        
                        print(f"🖱️ [Modal Retry Handler] Clicking fallback button now...")
                        btn.click()
                        print(f"✅ [Modal Retry Handler] Fallback button clicked successfully: {btn_text}")
                        time.sleep(2)  # Wait for response
                        return True
            except Exception as e:
                print(f"⚠️ [Modal Retry Handler] Could not click button: {e}")
                continue
        print(f"❌ [Modal Retry Handler] No suitable button found to click after filling inputs.")
    else:
        print(f"❌ [Modal Retry Handler] No visible input fields were filled.")
    
    # NEW: Try clicking JOIN button as a last fallback
    print(f"🔄 [Modal Retry Handler] Attempting to click JOIN button as last fallback...")
    if try_click_join_button(driver):
        print(f"✅ [Modal Retry Handler] JOIN button clicked as fallback.")
        return True
    else:
        print(f"❌ [Modal Retry Handler] JOIN button not found or not clickable.")

    print(f"❌ [Modal Retry Handler] All modal handling attempts failed for context: {context}")
    return False

# Utility to detect Chrome's built-in network error pages so we can abort early.
def is_chrome_error_page(html: str) -> bool:
    html = html.lower()
    return any(tok in html for tok in (
        "err_socks_connection_failed",
        "err_tunnel_connection_failed",
        "err_connection_timed_out",
        "err_no_supported_proxies",
        "this site can't be reached",  # curly apostrophe
        "this site can't be reached",  # straight apostrophe
    ))

if __name__ == "__main__":
    main()            