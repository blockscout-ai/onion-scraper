#!/usr/bin/env python3
"""
Ultra-Fast AI-Enhanced Onion Scraper
- Optimized for speed and reliability
- AI captcha solving, login, registration
- Multi-threaded with connection pooling
- Smart retry logic and error recovery
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
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from eth_utils import is_checksum_address
from solders.pubkey import Pubkey
import chromedriver_autoinstaller
import json
import random
import openai
import anthropic
import io

chromedriver_autoinstaller.install()

# ---[ Ultra-Optimized Configuration ]---
TOR_PROXY = "socks5://127.0.0.1:9050"
INPUT_CSV = "discovered_onions_20250618.csv"
OUTPUT_CSV = "crypto_addresses_ultra_fast.csv"
SCREENSHOT_DIR = "screenshots_ultra_fast"
LOGIN_ATTEMPTS_CSV = "login_attempts_ultra.csv"
REGISTRATION_ATTEMPTS_CSV = "registration_attempts_ultra.csv"

# Performance settings
MAX_WORKERS = 12  # Increased for better throughput
PAGE_LOAD_TIMEOUT = 8  # Reduced timeout
HEADLESS_MODE = True
FAST_MODE = True

# ---[ Enhanced AI Configuration ]---
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Enhanced AI models for better intelligence
AI_MODELS = {
    "gpt-4-vision-preview": "gpt-4-vision-preview",
    "gpt-4-vision-preview-2": "gpt-4-vision-preview-2",
    "gpt-4-vision-preview-3": "gpt-4-vision-preview-3",
    "gpt-4-vision-preview-4": "gpt-4-vision-preview-4",
    "gpt-4-vision-preview-5": "gpt-4-vision-preview-5",
    "gpt-4-vision-preview-6": "gpt-4-vision-preview-6",
    "gpt-4-vision-preview-7": "gpt-4-vision-preview-7",
    "gpt-4-vision-preview-8": "gpt-4-vision-preview-8",
    "gpt-4-vision-preview-9": "gpt-4-vision-preview-9",
    "gpt-4-vision-preview-10": "gpt-4-vision-preview-10"
}

try:
    openai.api_key = OPENAI_API_KEY
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    AI_ENABLED = True
    print("🤖 AI agents enabled")
except Exception as e:
    print(f"⚠️ AI agents disabled: {e}")
    AI_ENABLED = False

# AI Interactive Settings
ENABLE_CAPTCHA_SOLVING = True
ENABLE_LOGIN = True
ENABLE_REGISTRATION = True
ENABLE_FORM_FILLING = True

# Timing settings
SHORT_WAIT = 0.3
MEDIUM_WAIT = 0.8
LONG_WAIT = 1.5

# Thread-safe structures
csv_lock = threading.Lock()
stats_lock = threading.Lock()
stats = {
    'processed': 0,
    'success': 0,
    'errors': 0,
    'addresses_found': 0,
    'start_time': time.time()
}

# Multi-vendor markets to skip
MULTI_VENDOR_MARKETS = [
    "torbuy", "undermarket", "alphabay", "dream", "empire", "monopoly",
    "versus", "cannazon", "dark0de", "berlusconi", "cryptonia", "nightmare",
    "silkroad", "agora", "evolution", "nucleus", "abraxas", "middleearth",
    "outlaw", "blackbank", "sheep", "hydra", "ramp", "omerta", "valhalla",
    "samsara", "cyberpunk", "apollon", "deepdotweb", "darknetlive"
]

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Enhanced regex patterns
PATTERNS = {
    "BTC": re.compile(r"\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b"),
    "ETH": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "XMR": re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b"),
    "TRON": re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b"),
    "SOL": re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{44}\b")
}

def generate_fake_user_data():
    """Generate realistic fake user data"""
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

def ai_solve_captcha(driver):
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
        
        # Use OCR first (faster)
        try:
            ocr_text = pytesseract.image_to_string(captcha_image, config='--psm 8')
            ocr_text = re.sub(r'[^a-zA-Z0-9]', '', ocr_text)
            if len(ocr_text) >= 3:
                return True, ocr_text
        except:
            pass
        
        # Use AI vision if OCR fails
        try:
            buffered = BytesIO()
            captcha_image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "This is a captcha image. Read the text/numbers and respond with ONLY the text/numbers, no other characters."
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
                return True, solution
                
        except Exception as e:
            print(f"❌ AI captcha solving failed: {e}")
        
        return False, "AI solving failed"
        
    except Exception as e:
        return False, f"Captcha error: {e}"

def ai_fill_form(driver, form_type="login"):
    """Use AI to fill forms intelligently"""
    if not AI_ENABLED or not ENABLE_FORM_FILLING:
        return False, "AI disabled"
    
    try:
        user_data = generate_fake_user_data()
        
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
        login_selectors = [
            "a[href*='login']",
            "a[href*='signin']",
            "button[onclick*='login']",
            ".login",
            "#login"
        ]
        
        for selector in login_selectors:
            try:
                login_link = driver.find_element(By.CSS_SELECTOR, selector)
                if login_link.is_displayed():
                    login_link.click()
                    time.sleep(SHORT_WAIT)
                    
                    success, message = ai_fill_form(driver, "login")
                    if success:
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
                                    
                                    # Handle captcha after submission
                                    time.sleep(SHORT_WAIT)
                                    captcha_success, captcha_solution = ai_solve_captcha(driver)
                                    if captcha_success:
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
        reg_selectors = [
            "a[href*='register']",
            "a[href*='signup']",
            "button[onclick*='register']",
            ".register",
            "#register"
        ]
        
        for selector in reg_selectors:
            try:
                reg_link = driver.find_element(By.CSS_SELECTOR, selector)
                if reg_link.is_displayed():
                    reg_link.click()
                    time.sleep(SHORT_WAIT)
                    
                    success, message = ai_fill_form(driver, "registration")
                    if success:
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
                                    
                                    # Handle captcha after submission
                                    time.sleep(SHORT_WAIT)
                                    captcha_success, captcha_solution = ai_solve_captcha(driver)
                                    if captcha_success:
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

def create_optimized_driver():
    """Create an ultra-optimized Chrome driver"""
    chrome_options = Options()
    if HEADLESS_MODE:
        chrome_options.add_argument("--headless=new")
    
    # Performance optimizations
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
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-css")
    chrome_options.add_argument("--disable-javascript")  # Disable JS for speed
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-save-password-bubble")
    chrome_options.add_argument("--disable-single-click-autofill")
    chrome_options.add_argument("--disable-autofill-keyboard-accessory-view")
    chrome_options.add_argument("--disable-component-update")
    chrome_options.add_argument("--disable-domain-reliability")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-component-extensions-with-background-pages")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-sync-preferences")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-extensions-except")
    chrome_options.add_argument("--disable-extensions-file-access-check")
    chrome_options.add_argument("--disable-extensions-http-throttling")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-features=BlinkGenPropertyTrees")
    chrome_options.add_argument("--disable-features=BlinkSchedulerDfs")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNG")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreading")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForMainThread")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForCompositor")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForIO")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForUtility")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForRenderer")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForGPU")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForNetwork")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForStorage")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForAudio")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForVideo")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForMedia")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForWebRTC")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForWebGL")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForCanvas")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForSVG")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForMathML")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForXSLT")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForXPath")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForXSL")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForXQuery")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForXPointer")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForXLink")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForXInclude")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForXForms")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForXHTML")
    chrome_options.add_argument("--disable-features=BlinkSchedulerUseNGThreadingForXML")
    
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
    
    skip_keywords = [
        "bitcoin generator", "btc generator", "bitcoin exploit", "btc exploit",
        "bitcoin hack", "btc hack", "bitcoin cracker", "btc cracker",
        "bitcoin multiplier", "btc multiplier", "free bitcoin generator",
        "bitcoin doubler", "btc doubler", "bitcoin mining generator",
        "fake bitcoin generator", "private key generator", "private key hack",
        "private key exploit", "private key cracker", "private key finder",
        "private key brute force", "private key recovery", "private key extractor",
        "private key stealer", "private key grabber", "private key scanner",
        "private key database", "private key dump", "private key leak",
        "private key crack", "private key brute", "private key force",
        "private key attack", "private key vulnerability", "private key exploit",
        "private key hack tool", "private key cracking", "private key breaking",
        "private key stealing", "private key extraction", "private key recovery tool",
        "private key shop", "scam list", "buy stolen bitcoin wallets",
        "bitcoin wallet market", "stolen bitcoin wallets", "wallet market",
        "private key market", "stolen wallets", "wallet shop", "bitcoin wallet shop"
    ]
    
    for keyword in skip_keywords:
        if (keyword in url_lower or 
            keyword in title_lower or 
            keyword in html_lower):
            return True, f"Contains '{keyword}'"
    
    return False, ""

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

def sanitize_filename(s):
    """Sanitize filename"""
    return re.sub(r'[^\w\-_\.]', '_', s)

def take_screenshot(driver, url, address):
    """Take screenshot with highlighted address"""
    try:
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3]
        filename = f"{sanitize_filename(url)}_{timestamp}_{random.randint(0,999)}.png"
        screenshot_path = os.path.join(SCREENSHOT_DIR, filename)
        
        driver.save_screenshot(screenshot_path)
        return screenshot_path
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return None

def update_stats(success=True, addresses_found=0):
    """Update thread-safe statistics"""
    with stats_lock:
        stats['processed'] += 1
        if success:
            stats['success'] += 1
        else:
            stats['errors'] += 1
        stats['addresses_found'] += addresses_found

def print_progress():
    """Print current progress"""
    with stats_lock:
        processed = stats['processed']
        success = stats['success']
        errors = stats['errors']
        addresses = stats['addresses_found']
        elapsed = time.time() - stats['start_time']
        
        if processed > 0:
            rate = processed / elapsed
            eta_minutes = (141953 - processed) / rate / 60 if rate > 0 else 0
            print(f"📈 Progress: {processed}/141953 ({processed/141953*100:.1f}%) | "
                  f"⏱️ Rate: {rate:.1f} URLs/sec, ETA: {eta_minutes:.1f} minutes | "
                  f"✅ Success: {success}, ❌ Errors: {errors} | "
                  f"🏦 Addresses found: {addresses}")

def process_url_ultra_fast(url, worker_id):
    """Ultra-fast URL processing with AI capabilities"""
    driver = None
    try:
        # Check if it's a multi-vendor market
        if is_multi_vendor_market(url):
            update_stats(success=True)
            return []
        
        driver = create_optimized_driver()
        driver.get(url)
        
        # Quick check for basic content
        title = driver.title
        html = driver.page_source
        
        # Check if page should be skipped
        should_skip, reason = should_skip_page(url, title, html)
        if should_skip:
            update_stats(success=True)
            return []
        
        # AI Interactive Features (quick attempts)
        if AI_ENABLED:
            # Quick login attempt
            if ENABLE_LOGIN:
                login_success, login_message = ai_handle_login(driver, url)
                if login_success:
                    log_login_attempt(url, True, login_message)
            
            # Quick registration attempt
            if ENABLE_REGISTRATION:
                reg_success, reg_message = ai_handle_registration(driver, url)
                if reg_success:
                    log_registration_attempt(url, True, reg_message)
            
            # Quick captcha solving
            if ENABLE_CAPTCHA_SOLVING:
                captcha_success, captcha_message = ai_solve_captcha(driver)
        
        # Extract addresses
        addresses = extract_addresses_fast(html)
        
        if addresses:
            # Process found addresses
            for address in addresses:
                screenshot_path = take_screenshot(driver, url, address)
                
                # Save to CSV
                timestamp = datetime.utcnow().isoformat()
                row = [url, address[0], address[1], title, screenshot_path, timestamp]
                write_to_csv_threadsafe(row, OUTPUT_CSV)
            
            update_stats(success=True, addresses_found=len(addresses))
            return addresses
        else:
            update_stats(success=True)
            return []
        
    except Exception as e:
        update_stats(success=False)
        return []
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    """Main function with ultra-fast processing"""
    print("🚀 Starting Ultra-Fast AI-Enhanced Onion Scraper")
    print(f"🤖 AI Features: Captcha={ENABLE_CAPTCHA_SOLVING}, Login={ENABLE_LOGIN}, Registration={ENABLE_REGISTRATION}")
    print(f"⚡ Workers: {MAX_WORKERS}, Timeout: {PAGE_LOAD_TIMEOUT}s, Headless: {HEADLESS_MODE}")
    
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
    
    # Process URLs with ultra-fast processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, url in enumerate(urls):
            future = executor.submit(process_url_ultra_fast, url, i % MAX_WORKERS)
            futures.append(future)
            
            # Progress tracking every 100 URLs
            if (i + 1) % 100 == 0:
                print_progress()
        
        # Wait for completion
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ Worker error: {e}")
    
    print("✅ Ultra-fast scraping completed!")
    print_progress()

if __name__ == "__main__":
    main() 