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
import openai
import anthropic
import io
import socket

chromedriver_autoinstaller.install()

# ---[ Enhanced AI Configuration ]---
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Enhanced AI models for better intelligence
AI_MODELS = {
    'gpt4': 'gpt-4',
    'gpt4_vision': 'gpt-4-vision-preview', 
    'gpt35': 'gpt-3.5-turbo',
    'claude': 'claude-3-sonnet-20240229'
}

try:
    openai.api_key = OPENAI_API_KEY
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    AI_ENABLED = True
    print("🤖 Enhanced AI agents enabled")
except Exception as e:
    print(f"⚠️ AI agents disabled: {e}")
    AI_ENABLED = False

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
ROTATE_EVERY_N = 20  # More frequent rotation for better anonymity
INPUT_CSV = "discovered_onions_20250618.csv"
OUTPUT_CSV = "crypto_addresses_fast.csv"
SCREENSHOT_DIR = "screenshots_fast"
CAPTCHA_FAILED_CSV = "captcha_failed_fast.csv"
UNSOLVED_DIR = "unsolved_captchas_fast"
MAX_DEPTH = 2  # Reduced for speed
PAGE_LOAD_TIMEOUT = 60  # Increased for complex sites
MAX_WORKERS = 4  # Parallel browsers
FAST_MODE = True
HEADLESS_MODE = True  # Changed to False to watch browser
BATCH_SIZE = 10  # Batch CSV writes

# Enhanced safety and reliability settings
MAX_RETRIES = 3  # Increased retries for better success rate
SAVE_INTERVAL = 25  # More frequent saves
BACKUP_INTERVAL = 50  # More frequent backups
MEMORY_LIMIT = 1000  # Max URLs in memory before processing

# Enhanced speed optimization settings
SHORT_WAIT = 1.0  # Increased for better reliability
MEDIUM_WAIT = 2.0
LONG_WAIT = 5.0
# Screenshots are ALWAYS taken for every address found

# Thread-safe CSV writing
csv_lock = threading.Lock()
results_queue = Queue()

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

SKIPPED_MARKETS_CSV = "skipped_multi_vendor_markets_fast.csv"
DISCOVERED_LINKS_CSV = "discovered_links_fast.csv"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(UNSOLVED_DIR, exist_ok=True)

# Optimized regex patterns
PATTERNS = {
    "BTC": re.compile(r"\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b"),
    "ETH": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "XMR": re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b"),
    "TRON": re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b"),
    "SOL": re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{44}\b")  # Solana addresses are exactly 44 characters
}

KEYWORDS = ["buy", "checkout", "payment", "wallet", "order", "access", "rent", "trial", "continue", "enter"]

# Category classification keywords
CATEGORY_KEYWORDS = {
    "csam": ["child", "loli", "boys", "girls", "teen", "young", "minor", "cp", "child porn", "childxxx", "preteen", "lolita", "loliporn"],
    "carding": ["card", "cc", "dumps", "cvv", "credit", "debit", "stripe", "paypal", "carding", "carder", "dump", "track"],
    "counterfeit": ["fake", "replica", "counterfeit", "clone", "copy", "imitation", "knockoff", "replicas"],
    "drugs": ["drug", "cocaine", "heroin", "weed", "cannabis", "opioid", "pill", "meth", "amphetamine", "opioids"],
    "weapons": ["gun", "weapon", "rifle", "pistol", "ammo", "explosive", "bomb", "ghost gun", "military grade"],
    "hack": ["hack", "exploit", "vulnerability", "ddos", "malware", "ransomware", "hacking", "cracker"],
    "marketplace": ["market", "shop", "store", "vendor", "seller", "buy", "marketplace"],
    "money laundering": ["mixer", "tumbler", "launder", "clean", "wash", "money laundering"],
    "extortion": ["extort", "blackmail", "sextortion", "threat", "extortion"],
    "human trafficking": ["traffic", "slave", "prostitution", "escort", "human trafficking"],
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
    "scam": ["scam", "fake", "fraud", "phishing", "scammer"],
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

def create_driver():
    """Create an optimized Chrome driver"""
    chrome_options = Options()
    if HEADLESS_MODE:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--proxy-server={TOR_PROXY}")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-css")
    chrome_options.add_argument("--disable-animations")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-site-isolation-trials")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-field-trial-config")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--max_old_space_size=4096")
    # Enable JavaScript for dynamic address loading
    # chrome_options.add_argument("--disable-javascript")  # Commented out to enable JS
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver

def write_to_csv_threadsafe(row, file):
    """Thread-safe CSV writing"""
    with csv_lock:
        with open(file, 'a', newline='') as f:
            csv.writer(f).writerow(row)

def is_multi_vendor_market(url):
    """Check if URL is a known multi-vendor market"""
    url_lower = url.lower()
    return any(market in url_lower for market in MULTI_VENDOR_MARKETS)

def should_skip_page(url, title, html):
    """Check if page should be skipped based on content"""
    url_lower = url.lower()
    title_lower = title.lower() if title else ""
    html_lower = html.lower()
    
    # Skip bitcoin generators and exploits
    skip_keywords = [
        "bitcoin generator",
        "btc generator", 
        "bitcoin exploit",
        "btc exploit",
        "bitcoin hack",
        "btc hack",
        "bitcoin cracker",
        "btc cracker",
        "bitcoin multiplier",
        "btc multiplier",
        "free bitcoin generator",
        "bitcoin doubler",
        "btc doubler",
        "bitcoin mining generator",
        "fake bitcoin generator",
        # Private key scams and exploits
        "private key generator",
        "private key hack",
        "private key exploit",
        "private key cracker",
        "private key finder",
        "private key brute force",
        "private key recovery",
        "private key extractor",
        "private key stealer",
        "private key grabber",
        "private key scanner",
        "private key database",
        "private key dump",
        "private key leak",
        "private key crack",
        "private key brute",
        "private key force",
        "private key attack",
        "private key vulnerability",
        "private key exploit",
        "private key hack tool",
        "private key cracking",
        "private key breaking",
        "private key stealing",
        "private key extraction",
        "private key recovery tool",
        # New skip keywords
        "private key shop",
        "scam list",
        "buy stolen bitcoin wallets",
        "bitcoin wallet market",
        "stolen bitcoin wallets",
        "wallet market",
        "private key market",
        "stolen wallets",
        "wallet shop",
        "bitcoin wallet shop"
    ]
    
    for keyword in skip_keywords:
        if (keyword in url_lower or 
            keyword in title_lower or 
            keyword in html_lower):
            return True, f"Contains '{keyword}'"
    
    return False, ""

def log_skipped_market(url, reason="Multi-vendor market"):
    """Log skipped markets"""
    timestamp = datetime.utcnow().isoformat()
    write_to_csv_threadsafe([url, reason, timestamp], SKIPPED_MARKETS_CSV)

def log_discovered_links(base_url, links, link_type="internal"):
    """Log discovered links to CSV"""
    timestamp = datetime.utcnow().isoformat()
    for link in links:
        write_to_csv_threadsafe([base_url, link, link_type, timestamp], DISCOVERED_LINKS_CSV)

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
    js_patterns = [
        r'["\']([13][a-zA-HJ-NP-Z0-9]{25,39})["\']',  # BTC in quotes
        r'["\'](0x[a-fA-F0-9]{40})["\']',  # ETH in quotes
        r'["\'](4[0-9AB][1-9A-HJ-NP-Za-km-z]{93})["\']',  # XMR in quotes
        r'["\'](T[1-9A-HJ-NP-Za-km-z]{33})["\']',  # TRON in quotes
        r'["\']([1-9A-HJ-NP-Za-km-z]{44})["\']',  # SOL in quotes
        r'address["\']?\s*[:=]\s*["\']([13][a-zA-HJ-NP-Z0-9]{25,39})["\']',  # BTC with address key
        r'wallet["\']?\s*[:=]\s*["\'](0x[a-fA-F0-9]{40})["\']',  # ETH with wallet key
        r'btc["\']?\s*[:=]\s*["\']([13][a-zA-HJ-NP-Z0-9]{25,39})["\']',  # BTC with btc key
        r'eth["\']?\s*[:=]\s*["\'](0x[a-fA-F0-9]{40})["\']',  # ETH with eth key
    ]
    
    for pattern in js_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Determine chain type
            if match.startswith(('1', '3')) and len(match) >= 26:
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

def normalize_url(url):
    """Normalize URL for deduplication"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

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
    """Sanitize filename"""
    return re.sub(r'[^\w\-_.]', '_', s)

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
        print(f"📜 Scrolling entire page to trigger lazy loading...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1) # Wait for page to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        driver.execute_script("window.scrollTo(0, 0);") # Scroll back to top
        print(f"✅ Finished scrolling page.")
        return True
    except Exception as e:
        print(f"⚠️ Scrolling failed: {e}")
        return False

def ai_click_interactive_elements(driver):
    """Proactively click buttons and links that might reveal addresses."""
    try:
        print(f"🖱️ Proactively clicking interactive elements...")
        clicked_something = False
        selectors = [
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'trial')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'payment')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'purchase')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign up')]",
            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy')]",
            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'trial')]",
            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'payment')]",
            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'purchase')]",
            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign up')]"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        print(f"   -> Clicking element with text '{element.text[:30]}'")
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(MEDIUM_WAIT)
                        clicked_something = True
                        # After clicking, the DOM might change, so we should probably stop and let the main loop re-evaluate
                        return True 
            except Exception:
                continue
                
        if clicked_something:
            print(f"✅ Clicked interactive elements.")
        else:
            print(f"🤷 No obvious interactive elements to click.")
            
        return clicked_something
    except Exception as e:
        print(f"⚠️ Clicking interactive elements failed: {e}")
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
    try:
        print(f"🔍 [{worker_id}] Processing: {url}")
        
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
            print(f"⏭️ [{worker_id}] Skipping multi-vendor market: {url}")
            log_skipped_market(url, "Multi-vendor market")
            return []
        
        driver = create_driver()
        print(f"🌐 [{worker_id}] Loading page: {url}")
        driver.get(url)
        time.sleep(SHORT_WAIT)

        # Get initial page content and classify it first, so AI functions can use it
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string.strip() if soup.title else "NoTitle"
        categories = classify_site(url, title, html)
        print(f"📄 [{worker_id}] Page title: {title}")
        print(f"🏷️ [{worker_id}] Categories: {', '.join(categories)}")

        # --- AI login/registration/captcha handling ---
        ai_handled = False
        if ai_handle_captcha(driver):
            print(f"🤖 [{worker_id}] Captcha detected and solved!")
            ai_handled = True
        if ai_solve_visual_captcha(driver):
            print(f"🤖 [{worker_id}] Visual captcha detected and solved!")
            ai_handled = True
        if ai_handle_login_enhanced(driver, url, categories):
            print(f"🤖 [{worker_id}] Login form detected and submitted!")
            ai_handled = True
        if ai_handle_registration_enhanced(driver, url, categories):
            print(f"🤖 [{worker_id}] Registration form detected and submitted!")
            ai_handled = True
        if ai_handled:
            time.sleep(SHORT_WAIT)
            driver.get(url)  # Reload page after AI interaction
            time.sleep(SHORT_WAIT)
            print(f"🔄 [{worker_id}] Reloaded page after AI interaction")

        # Proactively scroll and click to reveal dynamic content
        scroll_entire_page(driver)
        if ai_click_interactive_elements(driver):
            # If we clicked something, the page may have changed. Wait a bit.
            print(f"⏳ [{worker_id}] Page may have changed after click, waiting...")
            time.sleep(LONG_WAIT)
        
        # Check for and handle multi-coin selection pages
        page_text_lower = driver.page_source.lower()
        coin_selection_keywords = ['select your coin', 'select a coin', 'choose payment method', 'payment method']
        if any(keyword in page_text_lower for keyword in coin_selection_keywords):
            coin_results = ai_handle_coin_selection_page(driver, url, categories)
            if coin_results:
                results.extend(coin_results)
                # We have found addresses, but let's continue the normal flow just in case there are more.
        
        # Wait for JavaScript to load and execute
        print(f"⏳ [{worker_id}] Waiting for JavaScript content to load...")
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
        
        # We already have html, soup, title, and categories from above
        addresses = extract_addresses_fast(driver.page_source)
        
        print(f"🔍 [{worker_id}] Initial scan found {len(addresses)} addresses")
        # If no addresses found initially, wait for them to load
        if len(addresses) == 0:
            print(f"⏳ [{worker_id}] No addresses found initially, waiting for dynamic content...")
            if wait_for_address_in_dom(driver, timeout=15):
                print(f"✅ [{worker_id}] Addresses appeared after waiting!")
                html = driver.page_source
                addresses = extract_addresses_fast(html)
                print(f"🔍 [{worker_id}] Found {len(addresses)} addresses after waiting")
            else:
                print(f"❌ [{worker_id}] No addresses appeared after waiting")
        # Check if page should be skipped
        should_skip, skip_reason = should_skip_page(url, title, html)
        if should_skip:
            print(f"⏭️ [{worker_id}] Skipping page: {skip_reason}")
            log_skipped_market(url, skip_reason)
            return []
        
        if addresses:
            # Add any newly found addresses to the results list
            existing_addrs = {res['address'] for res in results}
            new_addresses = [(chain, addr) for chain, addr in addresses if addr not in existing_addrs]

            if new_addresses:
                print(f"✅ [{worker_id}] Found {len(new_addresses)} new addresses on {url}")
                hostname = urlparse(url).hostname or ''
                if hostname.endswith('.onion'):
                    suffix = hostname[:-6][-6:]
                else:
                    suffix = hostname[-6:]
                title_prefix = sanitize_filename(title[:10])
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                for i, (chain, addr) in enumerate(new_addresses):
                    screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                    # ALWAYS take screenshot for every address
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
                    results.append({
                        'url': url,
                        'title': title,
                        'chain': chain,
                        'address': addr,
                        'timestamp': datetime.utcnow().isoformat(),
                        'screenshot': screenshot_path,
                        'categories': json.dumps(categories)
                    })
                    print(f"🏦 [{worker_id}] Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
        
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
                log_discovered_links(url, internal_links, "internal")
                print(f"📝 [{worker_id}] Logged {len(internal_links)} internal links to CSV")
            
            # Try payment links first (highest priority)
            links_to_try = payment_links + crypto_links + other_links[:3]  # Limit other links to avoid too much crawling
            
            for i, link_url in enumerate(links_to_try[:5]):  # Try up to 5 links
                print(f"🔍 [{worker_id}] Trying link {i+1}/5: {link_url}")
                try:
                    driver.get(link_url)
                    time.sleep(SHORT_WAIT)
                    
                    # Wait for dynamic content
                    if wait_for_address_in_dom(driver, timeout=10):
                        print(f"✅ [{worker_id}] Addresses appeared on {link_url}")
                    
                    link_html = driver.page_source
                    link_addresses = extract_addresses_fast(link_html)
                    print(f"🔍 [{worker_id}] Link scan found {len(link_addresses)} addresses")
                    
                    if link_addresses:
                        print(f"✅ [{worker_id}] Found {len(link_addresses)} addresses on {link_url}!")
                        hostname = urlparse(link_url).hostname or ''
                        if hostname.endswith('.onion'):
                           suffix = hostname[:-6][-6:]
                        else:
                           suffix = hostname[-6:]
                        title_prefix = sanitize_filename(title[:10])
                        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                        for j, (chain, addr) in enumerate(link_addresses):
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
                                'url': link_url,
                                'title': title,
                                'chain': chain,
                                'address': addr,
                                'timestamp': datetime.utcnow().isoformat(),
                                'screenshot': screenshot_path,
                                'categories': json.dumps(categories)
                            })
                            print(f"🏦 [{worker_id}] Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                        
                        # If we found addresses, we can stop trying more links
                        break
                        
                except Exception as e:
                    print(f"⚠️ [{worker_id}] Error trying link {link_url}: {e}")
                    continue
                    
            if not results:
                print(f"❌ [{worker_id}] No addresses found on any payment/wallet links")
        else:
            # Even if we found addresses, still log the links we discovered
            internal_links = get_internal_links_fast(soup, url)
            if internal_links:
                log_discovered_links(url, internal_links, "internal")
                print(f"📝 [{worker_id}] Logged {len(internal_links)} internal links to CSV")
        if len(results) == 0:
            print(f"❌ [{worker_id}] No addresses found on {url}")
        else:
            print(f"🎉 [{worker_id}] Successfully processed {len(results)} addresses from {url}")
        return results
    except Exception as e:
        print(f"❌ [{worker_id}] Error processing {url}: {e}")
        # Try to rotate TOR identity on connection errors
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            print(f"🔄 [{worker_id}] Connection error detected, attempting TOR rotation")
            if rotate_tor_identity():
                print(f"✅ [{worker_id}] TOR rotated after connection error")
                time.sleep(3)  # Wait for new circuit
            else:
                print(f"⚠️ [{worker_id}] TOR rotation failed after connection error")
        return []
    finally:
        if driver:
            try:
                print(f"🔒 [{worker_id}] Closing browser for {url}")
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
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            import json as _json
            data = _json.loads(response.choices[0].message['content'])
            return data
    except Exception as e:
        # Fallback with comprehensive fake data
        import random, string
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        password = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%^&*', k=14))
        email = username + '@protonmail.com'
        btc_address = '1' + ''.join(random.choices(string.ascii_letters + string.digits, k=33))
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
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()
            prompt = (
                "This is a captcha image from a dark web site. "
                "Please read the text and return only the captcha code."
            )
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
                    ]}
                ],
                max_tokens=10
            )
            return response.choices[0].message['content'].strip()
    except Exception as e:
        return ""
    return ""

def ai_handle_login_enhanced(driver, url, categories=None):
    """Enhanced login form detection - more aggressive for high-priority sites"""
    try:
        # Determine if this is a high-priority site
        high_priority = categories and any(cat in ['csam', 'human trafficking', 'carding', 'weapons', 'drugs'] for cat in categories)
        
        # Look for ALL forms on the page
        forms = driver.find_elements(By.TAG_NAME, 'form')
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        links = driver.find_elements(By.TAG_NAME, 'a')
        
        # For high-priority sites, be more aggressive
        if high_priority:
            print(f"🚨 High-priority site detected: {categories}. Aggressive form detection enabled.")
            
            # Try to fill ANY form, not just login forms
            for form in forms:
                if attempt_form_fill(driver, form, url, "login"):
                    return True
            
            # Try to fill any input fields that look like login
            if attempt_input_fill(driver, inputs, url, "login"):
                return True
                
            # Try clicking any buttons that might trigger forms
            if attempt_button_clicks(driver, buttons, url):
                return True
                
            # Try clicking links that might lead to login
            if attempt_link_clicks(driver, links, url):
                return True
                
            # Try JavaScript-based form detection
            if attempt_js_form_detection(driver, url):
                return True
        else:
            # Standard detection for regular sites
            for form in forms:
                form_html = form.get_attribute('outerHTML').lower()
                if any(keyword in form_html for keyword in ['login', 'signin', 'access', 'enter', 'continue']):
                    if attempt_form_fill(driver, form, url, "login"):
                        return True
        
        return False
    except Exception as e:
        print(f"⚠️ Enhanced login detection failed: {e}")
        return False

def ai_handle_registration_enhanced(driver, url, categories=None):
    """Enhanced registration form detection - more aggressive for high-priority sites"""
    try:
        # Determine if this is a high-priority site
        high_priority = categories and any(cat in ['csam', 'human trafficking', 'carding', 'weapons', 'drugs'] for cat in categories)
        
        # Look for ALL forms on the page
        forms = driver.find_elements(By.TAG_NAME, 'form')
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        
        # For high-priority sites, be more aggressive
        if high_priority:
            print(f"🚨 High-priority site detected: {categories}. Aggressive registration detection enabled.")
            
            # Try to fill ANY form, not just registration forms
            for form in forms:
                if attempt_form_fill(driver, form, url, "registration"):
                    return True
            
            # Try to fill any input fields that look like registration
            if attempt_input_fill(driver, inputs, url, "registration"):
                return True
                
            # Try clicking any buttons that might trigger registration
            if attempt_button_clicks(driver, buttons, url):
                return True
        else:
            # Standard detection for regular sites
            for form in forms:
                form_html = form.get_attribute('outerHTML').lower()
                if any(keyword in form_html for keyword in ['register', 'signup', 'join', 'create', 'new', 'registration']):
                    if attempt_form_fill(driver, form, url, "registration"):
                        return True
        
        return False
    except Exception as e:
        print(f"⚠️ Enhanced registration detection failed: {e}")
        return False

def attempt_form_fill(driver, form, url, form_type):
    """Attempt to fill any form with fake data"""
    try:
        creds = ai_generate_fake_user()
        
        # Get all input fields
        inputs = form.find_elements(By.TAG_NAME, 'input')
        textareas = form.find_elements(By.TAG_NAME, 'textarea')
        all_fields = inputs + textareas
        
        fields_filled = 0
        for field in all_fields:
            name = field.get_attribute('name') or ''
            id_attr = field.get_attribute('id') or ''
            placeholder = field.get_attribute('placeholder') or ''
            typ = field.get_attribute('type') or ''
            
            # Combine all attributes for matching
            field_text = f"{name} {id_attr} {placeholder} {typ}".lower()
            
            # Try to match field to appropriate fake data
            if any(word in field_text for word in ['user', 'login', 'name']) and typ != 'password':
                field.clear()
                field.send_keys(creds['username'])
                fields_filled += 1
            elif any(word in field_text for word in ['email', 'mail']):
                field.clear()
                field.send_keys(creds['email'])
                fields_filled += 1
            elif any(word in field_text for word in ['pass', 'pwd']):
                field.clear()
                field.send_keys(creds['password'])
                fields_filled += 1
            elif any(word in field_text for word in ['btc', 'bitcoin', 'wallet', 'address']):
                field.clear()
                field.send_keys(creds['btc_address'])
                fields_filled += 1
            elif any(word in field_text for word in ['pin', 'code', 'security']):
                field.clear()
                field.send_keys(creds['pin'])
                fields_filled += 1
            elif any(word in field_text for word in ['invite', 'referral', 'code']):
                field.clear()
                field.send_keys(creds['invite_code'])
                fields_filled += 1
            elif any(word in field_text for word in ['pgp', 'key', 'public']):
                field.clear()
                field.send_keys(creds['pgp_key'])
                fields_filled += 1
            elif any(word in field_text for word in ['telegram', 'signal', 'wickr']):
                field.clear()
                field.send_keys(creds['telegram'])
                fields_filled += 1
            elif any(word in field_text for word in ['age', 'birth', 'year']):
                field.clear()
                field.send_keys(creds['age'])
                fields_filled += 1
            elif any(word in field_text for word in ['country', 'location', 'region']):
                field.clear()
                field.send_keys(creds['country'])
                fields_filled += 1
            # For high-priority sites, fill ANY text field
            elif typ == 'text' and not any(word in field_text for word in ['search', 'query']):
                field.clear()
                field.send_keys(creds['username'])
                fields_filled += 1
        
        # Submit form if we filled any fields
        if fields_filled > 0:
            try:
                form.submit()
            except:
                # Try to find submit button
                submit_buttons = form.find_elements(By.XPATH, ".//button[@type='submit'] | .//input[@type='submit']")
                if submit_buttons:
                    submit_buttons[0].click()
            
            time.sleep(MEDIUM_WAIT)
            
            # Log the attempt
            if form_type == "login":
                write_to_csv_threadsafe([url, creds['username'], creds['password'], fields_filled, datetime.utcnow().isoformat()], 'login_attempts.csv')
            else:
                write_to_csv_threadsafe([url, creds['username'], creds['password'], creds['email'], fields_filled, datetime.utcnow().isoformat()], 'registration_attempts.csv')
            
            print(f"✅ Filled {form_type} form with {fields_filled} fields")
            return True
        
        return False
    except Exception as e:
        print(f"⚠️ Form fill attempt failed: {e}")
        return False

def attempt_input_fill(driver, inputs, url, form_type):
    """Attempt to fill any input fields that look like forms"""
    try:
        creds = ai_generate_fake_user()
        
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
                    write_to_csv_threadsafe([url, creds['username'], creds['password'], fields_filled, datetime.utcnow().isoformat()], 'login_attempts.csv')
                else:
                    write_to_csv_threadsafe([url, creds['username'], creds['password'], creds['email'], fields_filled, datetime.utcnow().isoformat()], 'registration_attempts.csv')
                
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
    """Classify site based on content analysis"""
    try:
        # Combine all text for analysis
        text_to_analyze = f"{url} {title} {html_content}".lower()
        
        scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_to_analyze)
            if score > 0:
                scores[category] = score
        
        # Sort by score and return top categories
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_categories:
            # Return top 2-3 categories with scores above threshold
            top_categories = [cat for cat, score in sorted_categories[:3] if score >= 2]
            if top_categories:
                return top_categories
        
        # Fallback categories based on common patterns
        if any(word in text_to_analyze for word in ["market", "shop", "store", "vendor"]):
            return ["marketplace"]
        elif any(word in text_to_analyze for word in ["forum", "board", "community"]):
            return ["darknet forum profile"]
        elif any(word in text_to_analyze for word in ["card", "cc", "dumps"]):
            return ["carding"]
        elif any(word in text_to_analyze for word in ["child", "loli", "teen"]):
            return ["csam"]
        else:
            return ["darknet"]  # Default fallback
    except Exception as e:
        print(f"⚠️ Category classification failed: {e}")
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
    Solves visual captchas like "Press the red circle".
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
                instruction_text = elem.text
                print(f"   -> Instruction found: '{instruction_text}'")
                break
        
        if not instruction_text:
            print("   -> ❌ Could not find instruction text. Aborting visual captcha solver.")
            return False

        # 2. Parse the instruction to get the target color and shape
        match = re.search(r'(?:Press|Click) the (\\w+) (\\w+)', instruction_text, re.IGNORECASE)
        if not match:
            print(f"   -> ❌ Could not parse instruction: '{instruction_text}'. Aborting.")
            return False
        
        target_color_name = match.group(1).lower()
        target_shape = match.group(2).lower()
        print(f"   -> Target identified: Color='{target_color_name}', Shape='{target_shape}'")

        # 3. Define a color map (name to RGB)
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

        # 4. Find all potential clickable elements (circles, squares, etc.)
        # This is a generic approach; might need tuning for specific sites.
        # We'll assume they are divs for now, as in the example.
        candidate_elements = driver.find_elements(By.XPATH, "//div[@onclick or contains(@style, 'background-color')] | //span[@onclick or contains(@style, 'background-color')] | //button")

        if not candidate_elements:
            print("   -> ❌ Could not find any candidate clickable elements. Aborting.")
            return False
        
        print(f"   -> Found {len(candidate_elements)} candidate elements to analyze.")

        # 5. Helper function to calculate color difference
        def get_color_distance(rgb1, rgb2):
            return sum([(c1 - c2) ** 2 for c1, c2 in zip(rgb1, rgb2)]) ** 0.5

        # 6. Iterate through elements, find the best color match
        best_match_element = None
        smallest_distance = float('inf')

        for i, elem in enumerate(candidate_elements):
            try:
                # Method A: Get color from CSS (most reliable)
                elem_color_str = elem.value_of_css_property('background-color')
                
                # Parse RGBA string like 'rgba(255, 0, 0, 1)'
                rgb_match = re.search(r'rgba?\((\\d+), (\\d+), (\\d+)', elem_color_str)
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

        # 7. Click the best match if it's good enough
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

def main():
    """Main parallel processing function"""
    global urls_since_rotation
    
    print("🚀 Starting Fast Parallel Scraper...")
    print(f"📁 Input: {INPUT_CSV}")
    print(f"📁 Output: {OUTPUT_CSV}")
    print(f"📸 Screenshots: {SCREENSHOT_DIR}")
    print(f"🔧 Workers: {MAX_WORKERS}")
    print(f"⚡ Fast Mode: {FAST_MODE}")
    print(f"👻 Headless: {HEADLESS_MODE}")
    print(f"⏱️  Timeouts: {PAGE_LOAD_TIMEOUT}s page load, {SHORT_WAIT}s short wait")
    print(f"🔄 TOR Rotation: Every {ROTATE_EVERY_N} URLs")
    print("=" * 60)
    
    # Initialize TOR rotation counter
    urls_since_rotation = 0
    
    # Create output CSV with headers if it doesn't exist
    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['url', 'title', 'chain', 'address', 'timestamp', 'screenshot', 'categories'])
        print(f"📁 Created new output file: {OUTPUT_CSV}")
    
    # Read URLs from CSV
    urls = []
    try:
        with open(INPUT_CSV, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].startswith('http'):
                    urls.append(row[0])
    except Exception as e:
        print(f"❌ Error reading input file: {e}")
        return
    
    print(f"📊 Found {len(urls)} URLs to process")
    print(f"🔄 Starting parallel processing with {MAX_WORKERS} workers...")
    print("=" * 60)
    
    # Process URLs in parallel
    all_results = []
    seen_addresses = set()
    processed_count = 0
    success_count = 0
    error_count = 0
    start_time = datetime.utcnow()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all URLs
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
                print("-" * 40)
            
            try:
                results = future.result()
                if results:
                    success_count += 1
                    for result in results:
                        addr = result['address']
                        if addr not in seen_addresses:
                            seen_addresses.add(addr)
                            all_results.append(result)
                            # Write to CSV immediately
                            write_to_csv_threadsafe([
                                result['url'], result['title'], result['chain'], 
                                result['address'], result['timestamp'], result['screenshot'], result['categories']
                            ], OUTPUT_CSV)
                            print(f"💾 [{processed_count}] Saved new {result['chain']} address to CSV")
                        else:
                            # Log duplicate
                            write_to_csv_threadsafe([
                                result['url'], result['chain'], result['address'], 
                                datetime.utcnow().isoformat()
                            ], "duplicate_addresses_fast.csv")
                            print(f"⏭️ [{processed_count}] Skipped duplicate {result['chain']} address")
                else:
                    success_count += 1  # Still counts as successful processing
                        
            except Exception as e:
                error_count += 1
                print(f"❌ [{processed_count}] Error processing {url}: {e}")
    
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
    print(f"📸 Screenshots saved to: {SCREENSHOT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main() 