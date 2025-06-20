#!/usr/bin/env python3
"""
AI-Enhanced Onion Scraper with Interactive Capabilities
- Captcha solving
- Login automation
- Registration automation
- Form filling
- Interactive site navigation
"""

import csv
import os
import re
import time
import base64
import requests
from io import BytesIO
from datetime import datetime
from urllib.parse import urljoin, urlparse
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from eth_utils import is_checksum_address
from solders.pubkey import Pubkey
import chromedriver_autoinstaller
import json
import random
import openai
import anthropic
import io

chromedriver_autoinstaller.install()

# ---[ Enhanced AI Configuration ]---
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

try:
    openai.api_key = OPENAI_API_KEY
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    AI_ENABLED = True
    print("🤖 AI agents enabled for interactive features")
except Exception as e:
    print(f"⚠️ AI agents disabled: {e}")
    AI_ENABLED = False

# ---[ Enhanced Configuration ]---
TOR_PROXY = "socks5://127.0.0.1:9050"
INPUT_CSV = "discovered_onions_20250618.csv"
OUTPUT_CSV = "crypto_addresses_ai_enhanced.csv"
SCREENSHOT_DIR = "screenshots_ai_enhanced"
CAPTCHA_FAILED_CSV = "captcha_failed_ai.csv"
UNSOLVED_DIR = "unsolved_captchas_ai"
LOGIN_ATTEMPTS_CSV = "login_attempts.csv"
REGISTRATION_ATTEMPTS_CSV = "registration_attempts.csv"

MAX_DEPTH = 2
PAGE_LOAD_TIMEOUT = 10
MAX_WORKERS = 8
FAST_MODE = True
HEADLESS_MODE = True
BATCH_SIZE = 20

# AI Interactive Settings
ENABLE_CAPTCHA_SOLVING = True
ENABLE_LOGIN = True
ENABLE_REGISTRATION = True
ENABLE_FORM_FILLING = True
MAX_LOGIN_ATTEMPTS = 3
MAX_REGISTRATION_ATTEMPTS = 2

# Safety and reliability settings
MAX_RETRIES = 1
SAVE_INTERVAL = 50
BACKUP_INTERVAL = 100
MEMORY_LIMIT = 1000

# Speed optimization settings
SHORT_WAIT = 0.5
MEDIUM_WAIT = 1
LONG_WAIT = 2

# Thread-safe structures
csv_lock = threading.Lock()
results_queue = Queue()

# Multi-vendor markets to skip
MULTI_VENDOR_MARKETS = [
    "torbuy", "undermarket", "alphabay", "dream", "empire", "monopoly",
    "versus", "cannazon", "dark0de", "berlusconi", "cryptonia", "nightmare",
    "silkroad", "agora", "evolution", "nucleus", "abraxas", "middleearth",
    "outlaw", "blackbank", "sheep", "hydra", "ramp", "omerta", "valhalla",
    "samsara", "cyberpunk", "apollon", "deepdotweb", "darknetlive"
]

SKIPPED_MARKETS_CSV = "skipped_multi_vendor_markets_ai.csv"
DISCOVERED_LINKS_CSV = "discovered_links_ai.csv"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(UNSOLVED_DIR, exist_ok=True)

# Enhanced regex patterns
PATTERNS = {
    "BTC": re.compile(r"\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b"),
    "ETH": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "XMR": re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b"),
    "TRON": re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b"),
    "SOL": re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{44}\b")
}

KEYWORDS = ["buy", "checkout", "payment", "wallet", "order", "access", "rent", "trial", "continue", "enter"]

# AI Form Data Generator
def generate_fake_user_data():
    """Generate realistic fake user data for registration"""
    first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa", "Robert", "Emma", "James", "Maria"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "protonmail.com"]
    
    return {
        "username": f"{random.choice(first_names).lower()}{random.randint(100,999)}",
        "email": f"{random.choice(first_names).lower()}{random.randint(100,999)}@{random.choice(domains)}",
        "password": f"Pass{random.randint(1000,9999)}!",
        "first_name": random.choice(first_names),
        "last_name": random.choice(last_names),
        "phone": f"+1{random.randint(200,999)}{random.randint(200,999)}{random.randint(1000,9999)}"
    }

def ai_solve_captcha(driver, captcha_element=None):
    """Use AI to solve captchas"""
    if not AI_ENABLED or not ENABLE_CAPTCHA_SOLVING:
        return False, "AI disabled"
    
    try:
        # Find captcha elements
        captcha_selectors = [
            "img[src*='captcha']",
            "img[alt*='captcha']",
            "img[class*='captcha']",
            "img[id*='captcha']",
            "canvas",
            ".captcha img",
            "#captcha img"
        ]
        
        captcha_img = None
        for selector in captcha_selectors:
            try:
                captcha_img = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except NoSuchElementException:
                continue
        
        if not captcha_img:
            return False, "No captcha found"
        
        # Take screenshot of captcha
        captcha_screenshot = captcha_img.screenshot_as_png
        captcha_image = Image.open(BytesIO(captcha_screenshot))
        
        # Use OCR first
        try:
            ocr_text = pytesseract.image_to_string(captcha_image, config='--psm 8')
            ocr_text = re.sub(r'[^a-zA-Z0-9]', '', ocr_text)
            if len(ocr_text) >= 3:
                print(f"🤖 OCR solved captcha: {ocr_text}")
                return True, ocr_text
        except:
            pass
        
        # Use AI vision if OCR fails
        try:
            # Convert to base64
            buffered = BytesIO()
            captcha_image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Use OpenAI Vision API
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "This is a captcha image. Please read the text or numbers visible in the image and respond with ONLY the text/numbers, no other characters or explanation."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=10
            )
            
            solution = response.choices[0].message.content.strip()
            solution = re.sub(r'[^a-zA-Z0-9]', '', solution)
            
            if solution:
                print(f"🤖 AI solved captcha: {solution}")
                return True, solution
                
        except Exception as e:
            print(f"❌ AI captcha solving failed: {e}")
        
        return False, "AI solving failed"
        
    except Exception as e:
        return False, f"Captcha solving error: {e}"

def ai_fill_form(driver, form_type="login"):
    """Use AI to fill forms intelligently"""
    if not AI_ENABLED or not ENABLE_FORM_FILLING:
        return False, "AI disabled"
    
    try:
        user_data = generate_fake_user_data()
        
        # Find form elements
        form_selectors = {
            "username": ["input[name*='user']", "input[id*='user']", "input[placeholder*='user']", "#username", "#user"],
            "email": ["input[type='email']", "input[name*='email']", "input[id*='email']", "#email"],
            "password": ["input[type='password']", "input[name*='pass']", "input[id*='pass']", "#password", "#pass"],
            "first_name": ["input[name*='first']", "input[name*='fname']", "input[id*='first']", "#firstname"],
            "last_name": ["input[name*='last']", "input[name*='lname']", "input[id*='last']", "#lastname"],
            "phone": ["input[type='tel']", "input[name*='phone']", "input[id*='phone']", "#phone"]
        }
        
        filled_fields = 0
        
        for field_type, selectors in form_selectors.items():
            for selector in selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed() and element.is_enabled():
                        element.clear()
                        element.send_keys(user_data.get(field_type, ""))
                        filled_fields += 1
                        print(f"🤖 Filled {field_type}: {user_data.get(field_type, '')}")
                        break
                except NoSuchElementException:
                    continue
        
        return filled_fields > 0, f"Filled {filled_fields} fields"
        
    except Exception as e:
        return False, f"Form filling error: {e}"

def ai_handle_login(driver, url):
    """Use AI to handle login processes"""
    if not AI_ENABLED or not ENABLE_LOGIN:
        return False, "AI disabled"
    
    try:
        # Look for login elements
        login_selectors = [
            "a[href*='login']",
            "a[href*='signin']",
            "button[onclick*='login']",
            ".login",
            "#login",
            "a:contains('Login')",
            "a:contains('Sign In')"
        ]
        
        for selector in login_selectors:
            try:
                login_link = driver.find_element(By.CSS_SELECTOR, selector)
                if login_link.is_displayed():
                    login_link.click()
                    print(f"🤖 Clicked login link: {selector}")
                    
                    # Wait for login form
                    time.sleep(MEDIUM_WAIT)
                    
                    # Fill login form
                    success, message = ai_fill_form(driver, "login")
                    if success:
                        # Look for submit button
                        submit_selectors = [
                            "input[type='submit']",
                            "button[type='submit']",
                            "button:contains('Login')",
                            "button:contains('Sign In')",
                            ".submit",
                            "#submit"
                        ]
                        
                        for submit_selector in submit_selectors:
                            try:
                                submit_btn = driver.find_element(By.CSS_SELECTOR, submit_selector)
                                if submit_btn.is_displayed():
                                    submit_btn.click()
                                    print("🤖 Submitted login form")
                                    
                                    # Check for captcha after submission
                                    time.sleep(SHORT_WAIT)
                                    captcha_success, captcha_solution = ai_solve_captcha(driver)
                                    if captcha_success:
                                        # Find captcha input and submit
                                        captcha_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name*='captcha'], input[id*='captcha']")
                                        for captcha_input in captcha_inputs:
                                            captcha_input.clear()
                                            captcha_input.send_keys(captcha_solution)
                                        
                                        # Submit again
                                        for submit_selector in submit_selectors:
                                            try:
                                                submit_btn = driver.find_element(By.CSS_SELECTOR, submit_selector)
                                                if submit_btn.is_displayed():
                                                    submit_btn.click()
                                                    print("🤖 Submitted with captcha solution")
                                                    break
                                            except NoSuchElementException:
                                                continue
                                    
                                    return True, "Login attempted"
                                    break
                            except NoSuchElementException:
                                continue
                    break
            except NoSuchElementException:
                continue
        
        return False, "No login form found"
        
    except Exception as e:
        return False, f"Login error: {e}"

def ai_handle_registration(driver, url):
    """Use AI to handle registration processes"""
    if not AI_ENABLED or not ENABLE_REGISTRATION:
        return False, "AI disabled"
    
    try:
        # Look for registration elements
        reg_selectors = [
            "a[href*='register']",
            "a[href*='signup']",
            "button[onclick*='register']",
            ".register",
            "#register",
            "a:contains('Register')",
            "a:contains('Sign Up')"
        ]
        
        for selector in reg_selectors:
            try:
                reg_link = driver.find_element(By.CSS_SELECTOR, selector)
                if reg_link.is_displayed():
                    reg_link.click()
                    print(f"🤖 Clicked registration link: {selector}")
                    
                    # Wait for registration form
                    time.sleep(MEDIUM_WAIT)
                    
                    # Fill registration form
                    success, message = ai_fill_form(driver, "registration")
                    if success:
                        # Look for submit button
                        submit_selectors = [
                            "input[type='submit']",
                            "button[type='submit']",
                            "button:contains('Register')",
                            "button:contains('Sign Up')",
                            ".submit",
                            "#submit"
                        ]
                        
                        for submit_selector in submit_selectors:
                            try:
                                submit_btn = driver.find_element(By.CSS_SELECTOR, submit_selector)
                                if submit_btn.is_displayed():
                                    submit_btn.click()
                                    print("🤖 Submitted registration form")
                                    
                                    # Check for captcha after submission
                                    time.sleep(SHORT_WAIT)
                                    captcha_success, captcha_solution = ai_solve_captcha(driver)
                                    if captcha_success:
                                        # Find captcha input and submit
                                        captcha_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name*='captcha'], input[id*='captcha']")
                                        for captcha_input in captcha_inputs:
                                            captcha_input.clear()
                                            captcha_input.send_keys(captcha_solution)
                                        
                                        # Submit again
                                        for submit_selector in submit_selectors:
                                            try:
                                                submit_btn = driver.find_element(By.CSS_SELECTOR, submit_selector)
                                                if submit_btn.is_displayed():
                                                    submit_btn.click()
                                                    print("🤖 Submitted registration with captcha solution")
                                                    break
                                            except NoSuchElementException:
                                                continue
                                    
                                    return True, "Registration attempted"
                                    break
                            except NoSuchElementException:
                                continue
                    break
            except NoSuchElementException:
                continue
        
        return False, "No registration form found"
        
    except Exception as e:
        return False, f"Registration error: {e}"

def create_driver():
    """Create an optimized Chrome driver for AI interactions"""
    chrome_options = Options()
    if HEADLESS_MODE:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--proxy-server={TOR_PROXY}")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
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
    # Keep JavaScript enabled for interactive features
    chrome_options.add_argument("--disable-images")  # Disable images for speed
    chrome_options.add_argument("--disable-css")  # Disable CSS for speed
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver

def write_to_csv_threadsafe(row, file):
    """Thread-safe CSV writing"""
    with csv_lock:
        with open(file, 'a', newline='') as f:
            csv.writer(f).writerow(row)

def log_login_attempt(url, success, message):
    """Log login attempts"""
    timestamp = datetime.utcnow().isoformat()
    write_to_csv_threadsafe([url, success, message, timestamp], LOGIN_ATTEMPTS_CSV)

def log_registration_attempt(url, success, message):
    """Log registration attempts"""
    timestamp = datetime.utcnow().isoformat()
    write_to_csv_threadsafe([url, success, message, timestamp], REGISTRATION_ATTEMPTS_CSV)

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
    try:
        # Validate Solana address format
        if len(addr) != 44:
            return False
        Pubkey.from_string(addr)
        return True
    except:
        return False

def is_valid_xmr_address(addr):
    return len(addr) == 95 and addr.startswith('4')

def extract_addresses_fast(text):
    """Extract crypto addresses from text"""
    addresses = []
    
    for crypto_type, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            # Validate address based on type
            is_valid = False
            if crypto_type == "BTC":
                is_valid = is_valid_btc_address(match)
            elif crypto_type == "ETH":
                is_valid = is_valid_eth_address(match)
            elif crypto_type == "TRON":
                is_valid = is_valid_tron_address(match)
            elif crypto_type == "SOL":
                is_valid = is_valid_solana_address(match)
            elif crypto_type == "XMR":
                is_valid = is_valid_xmr_address(match)
            
            if is_valid:
                addresses.append((crypto_type, match))
    
    return addresses

def normalize_url(url):
    """Normalize URL for comparison"""
    return url.rstrip('/')

def get_internal_links_fast(soup, base_url):
    """Get internal links from page"""
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a['href'])
        if href.startswith(base_url):
            links.add(normalize_url(href))
    return links

def sanitize_filename(s):
    """Sanitize filename"""
    return re.sub(r'[^\w\-_\.]', '_', s)

def wait_for_address_in_dom(driver, timeout=10):
    """Wait for crypto addresses to appear in DOM"""
    def check(_driver):
        try:
            page_source = _driver.page_source
            addresses = extract_addresses_fast(page_source)
            return len(addresses) > 0
        except:
            return False
    
    try:
        WebDriverWait(driver, timeout).until(check)
        return True
    except TimeoutException:
        return False

def highlight_address_on_screenshot(driver, address, screenshot_path):
    """Take screenshot with highlighted address"""
    try:
        # Take screenshot
        driver.save_screenshot(screenshot_path)
        
        # Load screenshot
        screenshot = Image.open(screenshot_path)
        draw = ImageDraw.Draw(screenshot)
        
        # Find address in page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Look for address in text nodes
        address_text = address[1]  # Get the actual address string
        text_nodes = soup.find_all(text=True)
        
        for text_node in text_nodes:
            if address_text in text_node:
                # Try to find the element and get its position
                try:
                    element = driver.find_element(By.XPATH, f"//*[contains(text(), '{address_text}')]")
                    location = element.location
                    size = element.size
                    
                    # Draw rectangle around address
                    x1 = location['x']
                    y1 = location['y']
                    x2 = x1 + size['width']
                    y2 = y1 + size['height']
                    
                    # Draw red rectangle
                    draw.rectangle([x1, y1, x2, y2], outline='red', width=3)
                    
                    # Add label
                    try:
                        font = ImageFont.truetype("Arial.ttf", 16)
                    except:
                        font = ImageFont.load_default()
                    
                    draw.text((x1, y1 - 20), f"{address[0]}: {address_text[:10]}...", fill='red', font=font)
                    break
                except:
                    continue
        
        # Save highlighted screenshot
        screenshot.save(screenshot_path)
        return True
        
    except Exception as e:
        print(f"❌ Screenshot highlighting failed: {e}")
        return False

def process_url_ai_enhanced(url, worker_id):
    """Enhanced URL processing with AI capabilities"""
    print(f"🔍 [{worker_id}] Processing: {url}")
    
    driver = None
    try:
        driver = create_driver()
        
        # Check if it's a multi-vendor market
        if is_multi_vendor_market(url):
            log_skipped_market(url)
            return []
        
        print(f"🌐 [{worker_id}] Loading page: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(SHORT_WAIT)
        
        # Get page title and content
        title = driver.title
        html = driver.page_source
        
        # Check if page should be skipped
        should_skip, reason = should_skip_page(url, title, html)
        if should_skip:
            print(f"⏭️ [{worker_id}] Skipping: {reason}")
            return []
        
        print(f"📄 [{worker_id}] Page title: {title}")
        
        # AI Interactive Features
        if AI_ENABLED:
            # Try to handle login if needed
            if ENABLE_LOGIN:
                login_success, login_message = ai_handle_login(driver, url)
                if login_success:
                    log_login_attempt(url, True, login_message)
                    print(f"🤖 [{worker_id}] Login attempted: {login_message}")
                    time.sleep(MEDIUM_WAIT)
            
            # Try to handle registration if needed
            if ENABLE_REGISTRATION:
                reg_success, reg_message = ai_handle_registration(driver, url)
                if reg_success:
                    log_registration_attempt(url, True, reg_message)
                    print(f"🤖 [{worker_id}] Registration attempted: {reg_message}")
                    time.sleep(MEDIUM_WAIT)
            
            # Handle any captchas that appear
            if ENABLE_CAPTCHA_SOLVING:
                captcha_success, captcha_message = ai_solve_captcha(driver)
                if captcha_success:
                    print(f"🤖 [{worker_id}] Captcha solved: {captcha_message}")
                    time.sleep(SHORT_WAIT)
        
        # Extract addresses from initial page load
        addresses = extract_addresses_fast(html)
        print(f"🔍 [{worker_id}] Initial scan found {len(addresses)} addresses")
        
        if addresses:
            # Take screenshots for each address
            for address in addresses:
                screenshot_filename = f"{sanitize_filename(url)}_{address[0]}_{address[1][:10]}.png"
                screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_filename)
                
                if highlight_address_on_screenshot(driver, address, screenshot_path):
                    print(f"📸 [{worker_id}] Screenshot saved: {screenshot_filename}")
                
                # Save to CSV
                timestamp = datetime.utcnow().isoformat()
                row = [url, address[0], address[1], title, screenshot_path, timestamp]
                write_to_csv_threadsafe(row, OUTPUT_CSV)
                print(f"💰 [{worker_id}] Found {address[0]}: {address[1]}")
        
        # Wait for dynamic content if no addresses found initially
        if not addresses:
            print(f"⏳ [{worker_id}] No addresses found initially, waiting for dynamic content...")
            if wait_for_address_in_dom(driver, timeout=10):
                # Re-extract addresses after dynamic content loads
                html = driver.page_source
                addresses = extract_addresses_fast(html)
                
                if addresses:
                    for address in addresses:
                        screenshot_filename = f"{sanitize_filename(url)}_{address[0]}_{address[1][:10]}.png"
                        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_filename)
                        
                        if highlight_address_on_screenshot(driver, address, screenshot_path):
                            print(f"📸 [{worker_id}] Screenshot saved: {screenshot_filename}")
                        
                        # Save to CSV
                        timestamp = datetime.utcnow().isoformat()
                        row = [url, address[0], address[1], title, screenshot_path, timestamp]
                        write_to_csv_threadsafe(row, OUTPUT_CSV)
                        print(f"💰 [{worker_id}] Found {address[0]}: {address[1]}")
            else:
                print(f"❌ [{worker_id}] No addresses appeared after waiting")
        
        # Look for /buy links if no addresses found
        if not addresses:
            print(f"🔍 [{worker_id}] No addresses found, checking for /buy links...")
            soup = BeautifulSoup(html, 'html.parser')
            internal_links = get_internal_links_fast(soup, url)
            buy_links = [link for link in internal_links if '/buy' in link.lower()]
            
            print(f"🔗 [{worker_id}] Found {len(internal_links)} internal links, {len(buy_links)} /buy links")
            
            if buy_links:
                log_discovered_links(url, buy_links, "buy")
                print(f"📝 [{worker_id}] Logged {len(buy_links)} /buy links to CSV")
                
                # Visit first buy link
                buy_url = buy_links[0]
                print(f"🛒 [{worker_id}] Visiting buy link: {buy_url}")
                driver.get(buy_url)
                time.sleep(MEDIUM_WAIT)
                
                # Extract addresses from buy page
                buy_html = driver.page_source
                buy_addresses = extract_addresses_fast(buy_html)
                
                if buy_addresses:
                    for address in buy_addresses:
                        screenshot_filename = f"{sanitize_filename(buy_url)}_{address[0]}_{address[1][:10]}.png"
                        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_filename)
                        
                        if highlight_address_on_screenshot(driver, address, screenshot_path):
                            print(f"📸 [{worker_id}] Buy page screenshot saved: {screenshot_filename}")
                        
                        # Save to CSV
                        timestamp = datetime.utcnow().isoformat()
                        row = [buy_url, address[0], address[1], f"Buy page from {url}", screenshot_path, timestamp]
                        write_to_csv_threadsafe(row, OUTPUT_CSV)
                        print(f"💰 [{worker_id}] Found {address[0]} on buy page: {address[1]}")
            else:
                print(f"❌ [{worker_id}] No /buy links found, skipping deeper crawl")
        
        # Log discovered links
        if internal_links:
            log_discovered_links(url, internal_links, "internal")
            print(f"📝 [{worker_id}] Logged {len(internal_links)} internal links to CSV")
        
        return []
        
    except Exception as e:
        print(f"❌ [{worker_id}] Error processing {url}: {e}")
        return []
    
    finally:
        if driver:
            print(f"🔒 [{worker_id}] Closing browser for {url}")
            try:
                driver.quit()
            except:
                pass

def main():
    """Main function with AI-enhanced processing"""
    print("🚀 Starting AI-Enhanced Onion Scraper")
    print(f"🤖 AI Features: Captcha={ENABLE_CAPTCHA_SOLVING}, Login={ENABLE_LOGIN}, Registration={ENABLE_REGISTRATION}")
    
    # Initialize CSV files
    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["url", "crypto_type", "address", "title", "screenshot", "timestamp"])
    
    if not os.path.exists(LOGIN_ATTEMPTS_CSV):
        with open(LOGIN_ATTEMPTS_CSV, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["url", "success", "message", "timestamp"])
    
    if not os.path.exists(REGISTRATION_ATTEMPTS_CSV):
        with open(REGISTRATION_ATTEMPTS_CSV, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["url", "success", "message", "timestamp"])
    
    # Read URLs from CSV
    urls = []
    try:
        with open(INPUT_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                urls.append(row['onion_url'])
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return
    
    print(f"📊 Loaded {len(urls)} URLs to process")
    
    # Process URLs with AI enhancement
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, url in enumerate(urls):
            future = executor.submit(process_url_ai_enhanced, url, i % MAX_WORKERS)
            futures.append(future)
            
            # Progress tracking
            if (i + 1) % 10 == 0:
                print(f"📈 Progress: {i + 1}/{len(urls)} URLs ({(i + 1) / len(urls) * 100:.1f}%)")
        
        # Wait for completion
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ Worker error: {e}")
    
    print("✅ AI-Enhanced scraping completed!")

if __name__ == "__main__":
    main() 