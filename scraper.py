# ---[ Imports ]---
import csv
import os
import re
import time
import base64
import requests
from io import BytesIO
from datetime import datetime
from urllib.parse import urljoin, urlparse

import base58
import pytesseract
import cv2
import numpy as np
from PIL import Image
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
chromedriver_autoinstaller.install()

# ---[ AI Configuration ]---
# Set your API keys here or use environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Initialize AI clients
try:
    openai.api_key = OPENAI_API_KEY
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    AI_ENABLED = True
    print("🤖 AI agents enabled")
except Exception as e:
    print(f"⚠️ AI agents disabled: {e}")
    AI_ENABLED = False

# ---[ Config ]---
TOR_PROXY = "socks5://127.0.0.1:9050"
INPUT_CSV = "discovered_onions_20250618.csv"
OUTPUT_CSV = "crypto_addresses_0619.csv"
SCREENSHOT_DIR = "screenshots_sample_2"
CAPTCHA_FAILED_CSV = "captcha_failed.csv"
UNSOLVED_DIR = "unsolved_captchas"
MAX_DEPTH = 3
PAGE_LOAD_TIMEOUT = 30  # Reduced from 45
MAX_WORKERS = 3  # Number of parallel browsers
FAST_MODE = True  # Enable speed optimizations
HEADLESS_MODE = True  # Run browsers headless
BATCH_SIZE = 10  # Batch CSV writes

# Speed optimization settings
if FAST_MODE:
    SHORT_WAIT = 1  # Reduced from 3
    MEDIUM_WAIT = 2  # Reduced from 5
    LONG_WAIT = 5   # Reduced from 8-15
    SCREENSHOT_ONLY_NEW = True  # Only screenshot new addresses
else:
    SHORT_WAIT = 3
    MEDIUM_WAIT = 5
    LONG_WAIT = 10
    SCREENSHOT_ONLY_NEW = False

# Multi-vendor markets to skip (these have multiple vendors and complex structures)
MULTI_VENDOR_MARKETS = [
    "torbuy",
    "undermarket", 
    "alphabay",
    "dream",
    "empire",
    "monopoly",
    "versus",
    "cannazon",
    "dark0de",
    "berlusconi",
    "cryptonia",
    "nightmare",
    "silkroad",
    "agora",
    "evolution",
    "nucleus",
    "abraxas",
    "middleearth",
    "outlaw",
    "blackbank",
    "sheep",
    "hydra",
    "ramp",
    "omerta",
    "valhalla",
    "samsara",
    "cyberpunk",
    "apollon",
    "deepdotweb",
    "darknetlive"
]

# CSV file for logging skipped multi-vendor markets
SKIPPED_MARKETS_CSV = "skipped_multi_vendor_markets.csv"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(UNSOLVED_DIR, exist_ok=True)

def write_to_csv(row, file):
    with open(file, 'a', newline='') as f:
        csv.writer(f).writerow(row)

def is_multi_vendor_market(url):
    """Check if the URL is a known multi-vendor market that should be skipped"""
    url_lower = url.lower()
    return any(market in url_lower for market in MULTI_VENDOR_MARKETS)

def log_skipped_market(url, reason="Multi-vendor market"):
    """Log skipped markets to CSV file"""
    timestamp = datetime.utcnow().isoformat()
    write_to_csv([url, reason, timestamp], SKIPPED_MARKETS_CSV)

PATTERNS = {
    "BTC": re.compile(r"\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b"),
    "ETH": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "XMR": re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b"),
    "TRON": re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b"),
    "SOL": re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
}

KEYWORDS = ["buy", "checkout", "payment", "wallet", "order", "access", "rent", "trial", "continue", "enter"]

chrome_options = Options()
if HEADLESS_MODE:
    chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(f"--proxy-server={TOR_PROXY}")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")
# Speed optimizations
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-plugins")
chrome_options.add_argument("--disable-javascript")  # Only enable if needed
chrome_options.add_argument("--disable-images")
chrome_options.add_argument("--disable-css")
chrome_options.add_argument("--disable-animations")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
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

try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
except Exception as e:
    print(f"🚨 Failed to launch Chrome: {e}")
    exit(1)

# ---[ Validators ]---
def is_valid_btc_address(addr):
    if addr.startswith("bc1"):
        return 14 <= len(addr) <= 74  # Bech32 or Taproot
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
        return str(Pubkey.from_string(addr)) == addr
    except:
        return False

def is_valid_xmr_address(addr):
    return addr.startswith("4") and len(addr) == 95

def extract_addresses(text):
    found = []
    for chain, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        if chain == "BTC":
            matches = [m for m in matches if is_valid_btc_address(m)]
        elif chain == "ETH":
            matches = [m for m in matches if is_valid_eth_address(m)]
        elif chain == "TRON":
            matches = [m for m in matches if is_valid_tron_address(m)]
        elif chain == "SOL":
            matches = [m for m in matches if is_valid_solana_address(m)]
        elif chain == "XMR":
            matches = [m for m in matches if is_valid_xmr_address(m)]
        for match in matches:
            found.append((chain, match))
    return found

# ---[ CAPTCHA Solver ]---
def solve_captcha(driver):
    try:
        img_elems = driver.find_elements(By.TAG_NAME, "img")
        if not img_elems:
            raise Exception("No <img> tags found.")
        target_img = max(img_elems, key=lambda el: el.size['height'] * el.size['width'])
        src = target_img.get_attribute("src")
        if not src:  # Handle None src
            raise Exception("Image src is None or empty")
        if src.startswith("data:image"):
            base64_data = src.split(",", 1)[1]
            img = Image.open(BytesIO(base64.b64decode(base64_data)))
        else:
            response = requests.get(src)
            img = Image.open(BytesIO(response.content))
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        img.save(f"{UNSOLVED_DIR}/captcha_{timestamp}.png")
        img = img.convert("L")
        img_np = np.array(img)
        _, thresh = cv2.threshold(img_np, 150, 255, cv2.THRESH_BINARY_INV)
        processed = Image.fromarray(thresh)
        text = pytesseract.image_to_string(processed, config='--psm 7')
        return ''.join(filter(str.isalnum, text))[:6]
    except Exception as e:
        print(f"❌ CAPTCHA solve failed: {e}")
        return None

def try_submit_captcha(driver, solution):
    try:
        input_box = driver.find_element(By.XPATH, "//input[@type='text' and contains(@placeholder, 'captcha')]")
        input_box.clear()
        input_box.send_keys(solution)
        input_box.send_keys(Keys.ENTER)
        WebDriverWait(driver, 10).until(lambda d: "captcha" not in d.page_source.lower())
        time.sleep(2)
    except Exception as e:
        print(f"❌ CAPTCHA submit failed: {e}")

# ---[ AI-Powered Functions ]---
def ai_solve_captcha(driver):
    """Use AI vision to solve complex CAPTCHAs"""
    if not AI_ENABLED:
        print("⚠️ AI not enabled, falling back to OCR")
        return solve_captcha(driver)
    
    try:
        print("🤖 Using AI to solve CAPTCHA...")
        
        # Take screenshot of the page
        screenshot = driver.get_screenshot_as_png()
        
        # Convert to base64 for API
        screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
        
        # Try OpenAI GPT-4V first
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Look at this webpage screenshot and solve any CAPTCHA you can see. Return only the solution text, nothing else. If there's no CAPTCHA, return 'NO_CAPTCHA'."},
                        {"type": "image_url", "image_url": f"data:image/png;base64,{screenshot_b64}"}
                    ]
                }],
                max_tokens=50
            )
            
            solution = response.choices[0].message.content.strip()
            
            if solution and solution != "NO_CAPTCHA":
                print(f"✅ AI solved CAPTCHA: {solution}")
                return solution
            else:
                print("🤖 AI detected no CAPTCHA")
                return None
                
        except Exception as e:
            print(f"⚠️ OpenAI failed: {e}")
            
            # Fallback to Claude
            try:
                response = anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=50,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64
                                }
                            },
                            "Look at this webpage screenshot and solve any CAPTCHA you can see. Return only the solution text, nothing else. If there's no CAPTCHA, return 'NO_CAPTCHA'."
                        ]
                    }]
                )
                
                solution = response.content[0].text.strip()
                
                if solution and solution != "NO_CAPTCHA":
                    print(f"✅ Claude solved CAPTCHA: {solution}")
                    return solution
                else:
                    print("🤖 Claude detected no CAPTCHA")
                    return None
                    
            except Exception as e2:
                print(f"⚠️ Claude failed: {e2}")
                return None
                
    except Exception as e:
        print(f"❌ AI CAPTCHA solving failed: {e}")
        return None

def ai_analyze_form(driver, form_type="registration"):
    """Use AI to analyze form structure and return field mappings"""
    if not AI_ENABLED:
        print("⚠️ AI not enabled, using default form handling")
        return None
    
    try:
        print(f"🤖 Using AI to analyze {form_type} form...")
        
        # Get page HTML
        html = driver.page_source
        
        # Take screenshot for context
        screenshot = driver.get_screenshot_as_png()
        screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
        
        # Create prompt based on form type
        if form_type == "registration":
            prompt = """Analyze this HTML form and return a JSON object mapping field types to their selectors. 
            Look for: username, email, password, password_confirm, name, phone, country, state, city, zip_code.
            Return format: {"username": ["//input[@name='username']"], "email": ["//input[@type='email']"], etc.}
            Only return the JSON, nothing else."""
        elif form_type == "checkout":
            prompt = """Analyze this checkout form and return a JSON object mapping field types to their selectors.
            Look for: email, full_name, first_name, last_name, street_address, city, state, zip_code, country, phone.
            Return format: {"email": ["//input[@type='email']"], "full_name": ["//input[@name='name']"], etc.}
            Only return the JSON, nothing else."""
        else:
            prompt = """Analyze this form and return a JSON object mapping field types to their selectors.
            Return format: {"field_name": ["//selector"], etc.}
            Only return the JSON, nothing else."""
        
        # Try Claude first (better for structured analysis)
        try:
            response = anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64
                            }
                        },
                        f"HTML: {html[:2000]}...\n\n{prompt}"
                    ]
                }]
            )
            
            result_text = response.content[0].text.strip()
            
            # Try to parse JSON from response
            try:
                # Extract JSON from response (handle markdown formatting)
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = result_text[json_start:json_end]
                    field_mappings = json.loads(json_str)
                    print(f"✅ AI analyzed form: {len(field_mappings)} fields found")
                    return field_mappings
                else:
                    print("⚠️ No JSON found in AI response")
                    return None
                    
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to parse AI response as JSON: {e}")
                print(f"Response: {result_text}")
                return None
                
        except Exception as e:
            print(f"⚠️ Claude form analysis failed: {e}")
            return None
            
    except Exception as e:
        print(f"❌ AI form analysis failed: {e}")
        return None

def ai_handle_unexpected_scenario(driver, error_description):
    """Use AI to handle unexpected errors and find solutions"""
    if not AI_ENABLED:
        print("⚠️ AI not enabled, cannot handle unexpected scenario")
        return False
    
    try:
        print(f"🤖 Using AI to handle unexpected scenario: {error_description}")
        
        # Get current page info
        current_url = driver.current_url
        page_title = driver.title
        html = driver.page_source[:1000]  # First 1000 chars
        
        # Take screenshot
        screenshot = driver.get_screenshot_as_png()
        screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
        
        prompt = f"""I'm scraping a dark web site and encountered this error: {error_description}
        
        Current URL: {current_url}
        Page Title: {page_title}
        HTML snippet: {html}
        
        What should I do next? Options:
        1. Try a different approach (specify what)
        2. Skip this site (if it's not worth the effort)
        3. Wait and retry
        4. Look for alternative elements
        
        Return only a number 1-4 and a brief explanation."""
        
        try:
            response = anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64
                            }
                        },
                        prompt
                    ]
                }]
            )
            
            ai_advice = response.content[0].text.strip()
            print(f"🤖 AI advice: {ai_advice}")
            
            # Parse the advice
            if "1" in ai_advice:
                print("🤖 AI suggests trying a different approach")
                return "retry_different"
            elif "2" in ai_advice:
                print("🤖 AI suggests skipping this site")
                return "skip"
            elif "3" in ai_advice:
                print("🤖 AI suggests waiting and retrying")
                time.sleep(MEDIUM_WAIT)
                return "retry"
            elif "4" in ai_advice:
                print("🤖 AI suggests looking for alternative elements")
                return "alternative"
            else:
                print("🤖 AI advice unclear, defaulting to retry")
                return "retry"
                
        except Exception as e:
            print(f"⚠️ AI error handling failed: {e}")
            return "retry"
            
    except Exception as e:
        print(f"❌ AI scenario handling failed: {e}")
        return False

# ---[ Utilities ]---
def wait_for_address_in_dom(driver, timeout=10):
    def check(_driver):
        return any(p.search(_driver.page_source) for p in PATTERNS.values())
    try:
        WebDriverWait(driver, timeout).until(check)
    except:
        pass

def normalize_url(url):
    """Normalize URL by removing fragments, query params, and trailing slashes"""
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if normalized != f"{parsed.scheme}://{parsed.netloc}/":
        normalized = normalized.rstrip('/')
    return normalized

def get_internal_links(soup, base_url):
    links = []
    base = urlparse(base_url)
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a['href'])
        parsed = urlparse(href)
        if not parsed.netloc or parsed.netloc == base.netloc:
            normalized = normalize_url(href)
            if normalized not in links:  # Deduplicate normalized URLs
                links.append(normalized)
    return links

def sanitize_filename(s):
    return re.sub(r'[^a-zA-Z0-9_-]', '', s)

def highlight_and_save(driver, addr, screenshot_path):
    try:
        el = driver.find_element(By.XPATH, f"//*[contains(., '{addr}')]")
        location = el.location_once_scrolled_into_view
        size = el.size
        png = driver.get_screenshot_as_png()
        img = Image.open(BytesIO(png))
        img_np = np.array(img)
        x, y = int(location['x']), int(location['y'])
        w, h = int(size['width']), int(size['height'])
        cv2.rectangle(img_np, (x, y), (x + w, y + h), (0, 0, 255), 2)
        Image.fromarray(img_np).save(screenshot_path)
    except Exception as e:
        print(f"⚠️ Highlight failed: {e} → Saving full screenshot instead.")
        img = Image.open(BytesIO(driver.get_screenshot_as_png()))
        img.save(screenshot_path)

def try_payment_modal(driver, current_url):
    """Try to trigger and extract addresses from payment modals"""
    try:
        # First, if we're already on a /buy page, try to extract addresses directly
        if '/buy' in current_url or current_url.endswith('#buy'):
            print("🛒 On /buy page, checking for addresses directly...")
            html = driver.page_source
            addresses = extract_addresses(html)
            if addresses:
                print(f"✅ Found {len(addresses)} addresses directly on /buy page!")
                return addresses
            
            # If no addresses found directly, try to trigger any payment forms
            print("🔄 No addresses found directly, trying to trigger payment forms...")
        
        # First try direct button clicks
        buy_button = None
        button_selectors = [
            "//span[contains(text(), 'Buy Now')]",  # Generic xpath for "Buy Now" text
            "//a[contains(@class, 'buy')]//span",    # Class containing "buy"
            "//button[contains(@class, 'buy')]",     # Button with buy class
            "//a[contains(text(), 'Buy Now')]",      # Direct link text
            "//button[contains(text(), 'Buy Now')]", # Direct button text
            "#buttons04 li a span.label",            # Specific selector from example
            "//a[contains(@href, '#buy')]",          # Hash-based buy links
            "//a[contains(@href, 'buy')]",           # Any buy links
            "//button[contains(text(), 'Buy')]",     # Generic buy button
            "//a[contains(text(), 'Buy')]",          # Generic buy link
            "//input[@value='Buy']",                 # Buy input button
            "//button[contains(@class, 'purchase')]", # Purchase button
            "//a[contains(@class, 'purchase')]"      # Purchase link
        ]
        
        for selector in button_selectors:
            try:
                buttons = driver.find_elements(By.XPATH if selector.startswith("//") else By.CSS_SELECTOR, selector)
                if buttons:
                    buy_button = buttons[0]
                    break
            except:
                continue

        if not buy_button:
            # If no button found and URL doesn't end with #buy, try navigating to #buy
            if not current_url.endswith('#buy'):
                print("🔄 No buy button found, trying #buy navigation...")
                driver.get(current_url + '#buy')
                time.sleep(SHORT_WAIT)
                # Try buttons again after navigation
                for selector in button_selectors:
                    try:
                        buttons = driver.find_elements(By.XPATH if selector.startswith("//") else By.CSS_SELECTOR, selector)
                        if buttons:
                            buy_button = buttons[0]
                            break
                    except:
                        continue
                
                # Also check for addresses directly after #buy navigation
                html = driver.page_source
                addresses = extract_addresses(html)
                if addresses:
                    print(f"✅ Found {len(addresses)} addresses after #buy navigation!")
                    return addresses

        if buy_button:
            print("🛒 Found Buy button, attempting to trigger payment modal...")
            try:
                # Try regular click first
                buy_button.click()
            except:
                try:
                    # If regular click fails, try JavaScript click
                    driver.execute_script("arguments[0].click();", buy_button)
                except Exception as e:
                    print(f"❌ Failed to click button: {e}")
                    return None
            
            time.sleep(SHORT_WAIT)  # Wait for modal to appear

            # Check for addresses immediately after clicking
            html = driver.page_source
            addresses = extract_addresses(html)
            if addresses:
                print(f"✅ Found {len(addresses)} addresses after clicking buy button!")
                return addresses

            # Try to find a payment modal input (usually email)
            email_input = None
            input_selectors = [
                "//input[@type='email']",
                "//input[contains(@placeholder, 'email')]",
                "//input[contains(@placeholder, 'mail')]",
                "//input[@type='text']"  # Fallback to any text input if no email-specific found
            ]
            
            for selector in input_selectors:
                try:
                    inputs = driver.find_elements(By.XPATH, selector)
                    if inputs:
                        email_input = inputs[0]
                        break
                except:
                    continue

            if email_input:
                print("📧 Found email input, submitting test email...")
                email_input.send_keys("test@example.com")
                
                # Try to find and click payment/continue button
                payment_button = None
                payment_selectors = [
                    "//span[contains(@id, 'blockoPayBtn')]",
                    "//button[contains(text(), 'Pay')]",
                    "//button[contains(text(), 'Continue')]",
                    "//a[contains(text(), 'Pay')]",
                    "//button[contains(@class, 'pay')]",
                    "//button[contains(@class, 'submit')]",
                    "//input[@type='submit']",
                    "//button[@type='submit']"
                ]
                
                for selector in payment_selectors:
                    try:
                        buttons = driver.find_elements(By.XPATH, selector)
                        if buttons:
                            payment_button = buttons[0]
                            break
                    except:
                        continue

                if payment_button:
                    print("💳 Found payment button, clicking to reveal address...")
                    try:
                        payment_button.click()
                    except:
                        driver.execute_script("arguments[0].click();", payment_button)
                    time.sleep(SHORT_WAIT)  # Wait for crypto address to appear
                    
                    # Get updated page content and look for addresses
                    html = driver.page_source
                    addresses = extract_addresses(html)
                    if addresses:
                        print(f"✅ Successfully found {len(addresses)} addresses in payment modal!")
                        return addresses
                    
        return None
    except Exception as e:
        print(f"❌ Payment modal extraction failed: {e}")
        return None

def try_registration_and_login(driver, current_url):
    """Try to register a new account and then login to access protected pages"""
    try:
        # First look for registration/signup links
        register_button = None
        register_selectors = [
            "//a[contains(text(), 'Register')]",
            "//a[contains(text(), 'Sign up')]",
            "//a[contains(text(), 'Create account')]",
            "//a[contains(@href, 'register')]",
            "//a[contains(@href, 'signup')]",
            "//a[contains(@href, 'signupc')]",  # Common variation
            "//button[contains(text(), 'Register')]",
            "//a[contains(text(), 'Not a member')]"
        ]

        for selector in register_selectors:
            try:
                buttons = driver.find_elements(By.XPATH, selector)
                if buttons:
                    register_button = buttons[0]
                    break
            except:
                continue

        if register_button:
            print("📝 Found registration link, attempting to register...")
            register_button.click()
            time.sleep(SHORT_WAIT)

            # Generate random credentials
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            username = f"user{timestamp}"
            password = f"pass{timestamp}"
            email = f"test{timestamp}@example.com"
            pin = "123456"

            # Try to fill registration form
            registration_fields = {
                "username": ["//input[contains(@name, 'username')]", 
                           "//input[contains(@placeholder, 'Username')]",
                           "//input[contains(@id, 'username')]",
                           "//input[contains(@name, 'user')]"],
                "password": ["//input[@type='password']",
                           "//input[contains(@name, 'password')]",
                           "//input[contains(@placeholder, 'Password')]"],
                "password_confirm": ["//input[contains(@name, 'confirm')]",
                                   "//input[contains(@placeholder, 'again')]",
                                   "//input[contains(@name, 'password2')]"],
                "email": ["//input[@type='email']",
                         "//input[contains(@name, 'email')]",
                         "//input[contains(@placeholder, 'email')]"],
                "pin": ["//input[contains(@name, 'pin')]",
                       "//input[contains(@name, 'withdraw')]",
                       "//input[contains(@placeholder, 'security')]"]
            }

            # Fill in registration form
            for field_type, selectors in registration_fields.items():
                for selector in selectors:
                    try:
                        field = driver.find_element(By.XPATH, selector)
                        if field_type == "username":
                            field.send_keys(username)
                        elif field_type == "password" or field_type == "password_confirm":
                            field.send_keys(password)
                        elif field_type == "email":
                            field.send_keys(email)
                        elif field_type == "pin":
                            field.send_keys(pin)
                        break
                    except:
                        continue

            # Try to find and click register/submit button
            submit_selectors = [
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(text(), 'Register')]",
                "//button[contains(text(), 'Sign up')]",
                "//button[contains(text(), 'Create')]"
            ]

            for selector in submit_selectors:
                try:
                    submit_button = driver.find_element(By.XPATH, selector)
                    submit_button.click()
                    print("✅ Registration form submitted")
                    time.sleep(MEDIUM_WAIT)  # Wait for registration to complete
                    
                    # Check for addresses immediately after registration
                    html = driver.page_source
                    addresses = extract_addresses(html)
                    if addresses:
                        print(f"✅ Found {len(addresses)} addresses after registration!")
                        return addresses
                    
                    # Debug: Check what's actually on the page
                    print("🔍 Debug: Checking page content after registration...")
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    if len(page_text) > 500:
                        print(f"📄 Page text preview: {page_text[:500]}...")
                    else:
                        print(f"📄 Full page text: {page_text}")
                    
                    # Look for any text that might contain addresses
                    lines = page_text.split('\n')
                    for i, line in enumerate(lines):
                        if any(keyword in line.lower() for keyword in ['bitcoin', 'btc', 'address', 'wallet', 'payment']):
                            print(f"🔍 Potential address line {i}: {line}")
                    
                    # Wait a bit more and check again (sometimes addresses load after a delay)
                    print("🔄 Waiting for addresses to load after registration...")
                    time.sleep(SHORT_WAIT)
                    html = driver.page_source
                    addresses = extract_addresses(html)
                    if addresses:
                        print(f"✅ Found {len(addresses)} addresses after additional wait!")
                        return addresses
                    
                    # Try scrolling the page to trigger any lazy-loaded content
                    print("🔄 Scrolling page to trigger lazy-loaded content...")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(2)
                    html = driver.page_source
                    addresses = extract_addresses(html)
                    if addresses:
                        print(f"✅ Found {len(addresses)} addresses after scrolling!")
                        return addresses
                    
                    break
                except:
                    continue

            # Now try to login with the new credentials
            print("🔑 Attempting login with new credentials...")
            
            # Navigate to login page if needed
            login_links = [
                "//a[contains(text(), 'Login')]",
                "//a[contains(text(), 'Sign in')]",
                "//a[contains(@href, 'login')]"
            ]
            
            for selector in login_links:
                try:
                    login_link = driver.find_element(By.XPATH, selector)
                    login_link.click()
                    time.sleep(SHORT_WAIT)
                    break
                except:
                    continue

            # Fill login form
            try:
                username_field = driver.find_element(By.XPATH, "//input[contains(@name, 'username')] | //input[@type='text']")
                password_field = driver.find_element(By.XPATH, "//input[@type='password']")
                
                username_field.send_keys(username)
                password_field.send_keys(password)
                
                # Try to find and click login button
                login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')] | //input[@type='submit']")
                login_button.click()
                
                print("✅ Login attempted with new credentials")
                time.sleep(MEDIUM_WAIT)  # Wait for login to complete
                
                # Check for addresses after login
                html = driver.page_source
                addresses = extract_addresses(html)
                if addresses:
                    print(f"✅ Found {len(addresses)} addresses after login!")
                    return addresses
                
                # Check if we're logged in by looking for typical post-login elements
                post_login_selectors = [
                    "//a[contains(text(), 'Logout')]",
                    "//a[contains(text(), 'Profile')]",
                    "//a[contains(text(), 'Account')]"
                ]
                
                for selector in post_login_selectors:
                    try:
                        if driver.find_elements(By.XPATH, selector):
                            print("✅ Successfully logged in!")
                            # Check for addresses one more time after confirming login
                            html = driver.page_source
                            addresses = extract_addresses(html)
                            if addresses:
                                print(f"✅ Found {len(addresses)} addresses after successful login!")
                                return addresses
                            break
                    except:
                        continue
                        
            except Exception as e:
                print(f"❌ Login attempt failed: {e}")
                
        return []
    except Exception as e:
        print(f"❌ Registration workflow failed: {e}")
        return []

def handle_new_tab(driver, original_window):
    """Handle scraping in a new tab/window and return to original"""
    try:
        # Switch to new tab if one exists
        if len(driver.window_handles) > 1:
            print("🔄 New tab detected, switching to it...")
            # Wait a bit for any new tabs to fully open
            time.sleep(MEDIUM_WAIT)
            
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    # Wait longer for new tab content to load
                    time.sleep(LONG_WAIT)  # Increased from 3 to 8 seconds
                    
                    # Get content from new tab
                    html = driver.page_source
                    addresses = extract_addresses(html)
                    
                    if addresses:
                        print(f"✅ Found {len(addresses)} addresses in new tab!")
                        
                    # Close new tab and switch back
                    driver.close()
                    driver.switch_to.window(original_window)
                    return addresses
    except Exception as e:
        print(f"⚠️ Error handling new tab: {str(e)}")
        try:
            driver.switch_to.window(original_window)
        except:
            pass
    return []

def try_cart_workflow(driver, current_url):
    """Try to add item to cart and complete checkout process"""
    try:
        # First check if we're on a product page by looking for price and add to cart
        product_indicators = [
            "//span[contains(@class, 'price')]",
            "//div[contains(@class, 'price')]",
            "//p[contains(@class, 'price')]",
            "//*[contains(text(), '$')]",
            "//button[contains(text(), 'Add to cart')]"
        ]
        
        is_product_page = False
        for selector in product_indicators:
            try:
                if driver.find_elements(By.XPATH, selector):
                    is_product_page = True
                    break
            except:
                continue

        # If not on product page, first try to find "See Products" or similar browsing links
        if not is_product_page:
            print("🛍️ Not on product page, looking for product browsing links...")
            product_browsing_selectors = [
                "//a[contains(text(), 'See Products')]",
                "//a[contains(text(), 'Browse Products')]",
                "//a[contains(text(), 'View Products')]",
                "//a[contains(text(), 'Shop')]",
                "//a[contains(text(), 'Store')]",
                "//a[contains(text(), 'Products')]",
                "//a[contains(@href, 'products')]",
                "//a[contains(@href, 'shop')]",
                "//a[contains(@href, 'store')]",
                "//button[contains(text(), 'See Products')]",
                "//button[contains(text(), 'Browse Products')]",
                "//button[contains(text(), 'Shop Now')]",
                "//div[contains(@class, 'products')]//a",
                "//div[contains(@class, 'shop')]//a",
                "//div[contains(@class, 'store')]//a"
            ]
            
            browsing_link_found = False
            for selector in product_browsing_selectors:
                try:
                    links = driver.find_elements(By.XPATH, selector)
                    if links:
                        print(f"✅ Found product browsing link: {links[0].text}")
                        links[0].click()
                        time.sleep(SHORT_WAIT)  # Wait for products page to load
                        browsing_link_found = True
                        break
                except:
                    continue
            
            if browsing_link_found:
                print("🔄 Now on products page, looking for individual products...")
                # After clicking browsing link, check if we're now on a product page
                for selector in product_indicators:
                    try:
                        if driver.find_elements(By.XPATH, selector):
                            is_product_page = True
                            break
                    except:
                        continue

        # If still not on product page, try to find and click first product
        if not is_product_page:
            print("📦 Still not on product page, looking for product links...")
            product_link_selectors = [
                "//a[contains(@class, 'product')]",
                "//div[contains(@class, 'product')]//a",
                "//a[contains(@href, 'product')]",
                "//a[.//span[contains(@class, 'price')]]",
                "//a[.//div[contains(@class, 'price')]]",
                # Look for links with price indicators
                "//a[contains(., '$')]",
                # Common product grid/list selectors
                "//div[contains(@class, 'products')]//a",
                "//div[contains(@class, 'product-grid')]//a",
                "//div[contains(@class, 'product-list')]//a",
                # Links with images that might be products
                "//a[.//img][contains(@href, 'product')]",
                "//div[contains(@class, 'product-item')]//a"
            ]

            product_found = False
            for selector in product_link_selectors:
                try:
                    products = driver.find_elements(By.XPATH, selector)
                    if products:
                        print("✅ Found product link, clicking first product...")
                        products[0].click()
                        time.sleep(SHORT_WAIT)  # Wait for product page to load
                        product_found = True
                        break
                except:
                    continue

            if not product_found:
                print("❌ Could not find any product links")
                return None

        # Now we should be on a product page
        # Check for quantity input and set to 1 if found
        try:
            quantity_inputs = driver.find_elements(By.XPATH, "//input[@type='number'] | //input[contains(@name, 'quantity')]")
            if quantity_inputs:
                quantity_inputs[0].clear()
                quantity_inputs[0].send_keys("1")
        except:
            pass

        # First try to find and click "Add to Cart" button
        add_to_cart_selectors = [
            "//button[contains(text(), 'Add to cart')]",
            "//button[contains(@class, 'add-to-cart')]",
            "//button[contains(@class, 'add_to_cart')]",
            "//input[@value='Add to cart']",
            "//a[contains(text(), 'Add to cart')]",
            "//button[contains(text(), 'Add to Cart')]",
            "//button[contains(text(), 'ADD TO CART')]",
            "//button[@name='add']",
            # Additional selectors for variations
            "//button[contains(@class, 'cart')]",
            "//input[contains(@class, 'cart')]",
            "//a[contains(@class, 'cart')]"
        ]

        print("🛒 Looking for Add to Cart button...")
        add_to_cart_clicked = False
        for selector in add_to_cart_selectors:
            try:
                buttons = driver.find_elements(By.XPATH, selector)
                if buttons:
                    print(f"✅ Found Add to Cart button")
                    buttons[0].click()
                    add_to_cart_clicked = True
                    time.sleep(SHORT_WAIT)  # Wait for cart update
                    
                    # Check for success indicators
                    success_indicators = [
                        "//div[contains(text(), 'added to cart')]",
                        "//p[contains(text(), 'added to cart')]",
                        "//div[contains(text(), 'Added to cart')]",
                        "//div[contains(@class, 'cart-success')]",
                        "//div[contains(@class, 'success')]"
                    ]
                    
                    success_found = False
                    for indicator in success_indicators:
                        try:
                            if driver.find_elements(By.XPATH, indicator):
                                print("✅ Confirmed item added to cart")
                                success_found = True
                                break
                        except:
                            continue
                            
                    if success_found:
                        break
                    else:
                        print("⚠️ Add to cart clicked but no confirmation found")
            except:
                continue

        if not add_to_cart_clicked:
            print("❌ Could not find Add to Cart button")
            return None

        # Look for and click checkout button
        checkout_selectors = [
            "//a[contains(text(), 'Proceed to Checkout')]",
            "//a[contains(text(), 'Proceed to checkout')]",
            "//button[contains(text(), 'Checkout')]",
            "//a[contains(text(), 'Checkout')]",
            "//a[contains(@href, 'checkout')]",
            "//button[contains(@class, 'checkout')]",
            "//input[@value='Checkout']"
        ]

        print("🔄 Looking for Checkout button...")
        checkout_clicked = False
        for selector in checkout_selectors:
            try:
                buttons = driver.find_elements(By.XPATH, selector)
                if buttons:
                    print("✅ Found Checkout button")
                    buttons[0].click()
                    checkout_clicked = True
                    time.sleep(SHORT_WAIT)  # Wait for checkout page
                    break
            except:
                continue

        if not checkout_clicked:
            print("❌ Could not find Checkout button")
            return None

        # Fill in checkout form
        print("📝 Attempting to fill checkout form...")
        
        # Try AI form analysis first
        ai_field_mappings = ai_analyze_form(driver, "checkout")
        if ai_field_mappings:
            print("🤖 Using AI-detected form fields...")
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            fake_email = f"buyer{timestamp}@protonmail.com"
            field_values = {
                'email': fake_email,
                'full_name': 'John Smith',
                'first_name': 'John',
                'last_name': 'Smith',
                'street_address': '3433 A St',
                'city': 'Bennington',
                'state': 'Nebraska',
                'zip_code': '68007',
                'country': 'United States',
                'phone': '402-555-0123'
            }
            fields_filled = 0
            for field_type, selectors in ai_field_mappings.items():
                if field_type in field_values:
                    value = field_values[field_type]
                    for selector in selectors:
                        try:
                            element = driver.find_element(By.XPATH, selector)
                            element.clear()
                            time.sleep(0.5)
                            element.send_keys(value)
                            print(f"✅ AI filled {field_type}: {value}")
                            fields_filled += 1
                            break
                        except:
                            continue
            if fields_filled >= 3:
                print(f"🤖 AI successfully filled {fields_filled} fields")
                # Continue with payment button
                return  # Skip manual filling if AI succeeded
            else:
                print("⚠️ AI form filling incomplete, falling back to manual...")
        # If AI failed or wasn't available, use manual form filling as before

    except Exception as e:
        print(f"⚠️ Error processing checkout: {str(e)}")
        return None

# ---[ Initialize CSV files ]---
if not os.path.exists(OUTPUT_CSV):
    write_to_csv(['url', 'title', 'chain', 'address', 'timestamp', 'screenshot'], OUTPUT_CSV)
if not os.path.exists(CAPTCHA_FAILED_CSV):
    write_to_csv(['url'], CAPTCHA_FAILED_CSV)
if not os.path.exists("skipped_multi_vendor_markets.csv"):
    write_to_csv(['url', 'reason', 'timestamp'], "skipped_multi_vendor_markets.csv")

# Initialize additional CSV files for new logging
if not os.path.exists("captcha_failed_final.csv"):
    write_to_csv(['url'], "captcha_failed_final.csv")
if not os.path.exists("manual_review.csv"):
    write_to_csv(['url'], "manual_review.csv")
if not os.path.exists("login_required.csv"):
    write_to_csv(['url', 'title', 'timestamp', 'screenshot'], "login_required.csv")
if not os.path.exists("duplicate_addresses.csv"):
    write_to_csv(['onion_url', 'chain', 'address', 'timestamp'], "duplicate_addresses.csv")

seen = set()
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, newline='') as f:
        for row in csv.reader(f):
            if row[0] != "url":
                # Only deduplicate based on the address itself, not URL/title
                seen.add(row[3])  # row[3] is the address

print("🚀 Starting scraper...")
print(f"📁 Input file: {INPUT_CSV}")
print(f"📁 Output file: {OUTPUT_CSV}")
print(f"📁 Screenshots: {SCREENSHOT_DIR}")

# Check if input file exists
if not os.path.exists(INPUT_CSV):
    print(f"❌ Input file {INPUT_CSV} not found!")
    print("Please create a CSV file with onion URLs to scan.")
    exit(1)

try:
    # Main execution starts here
    print("🔍 Starting main scraping loop...")
    
    # Main scraping loop
except Exception as e:
    print(f"❌ Error in main loop: {str(e)}")
    exit(1)
with open(INPUT_CSV, newline='') as f:
    for idx, row in enumerate(csv.reader(f), start=1):
        base_url = row[0].strip()
        if not base_url.startswith("http://"):
            base_url = "http://" + base_url
        print(f"\n🔍 [{idx}] Scanning {base_url}")
            
            # Check if this is a multi-vendor market to skip
            if is_multi_vendor_market(base_url):
                print(f"⏭️ Skipping multi-vendor market: {base_url}")
                log_skipped_market(base_url, "Multi-vendor market")
                continue
                
        visited = set()
        to_visit = [(base_url, 0)]
        while to_visit:
            current_url, depth = to_visit.pop(0)
                normalized_url = normalize_url(current_url)
                if normalized_url in visited or depth > MAX_DEPTH:
                continue
                visited.add(normalized_url)
            try:
                print(f"🌐 Visiting: {current_url} (depth {depth})")
                driver.get(current_url)
                    time.sleep(SHORT_WAIT)  # Reduced from 3
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                addresses = extract_addresses(html)
                title = soup.title.string.strip() if soup.title else "NoTitle"

                    # ✅ 1. Extract addresses first
                if addresses:
                        print(f"🔍 Found {len(addresses)} addresses on {current_url}")
                        hostname = urlparse(current_url).hostname or ''
                        if hostname.endswith('.onion'):
                            suffix = hostname[:-6][-6:]
                        else:
                            suffix = hostname[-6:]
                    title_prefix = sanitize_filename(title[:10])
                    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                    for i, (chain, addr) in enumerate(addresses):
                            print(f"🔍 Processing: {chain} - {addr[:10]}...")
                            if addr in seen:
                                print(f"⏭️ Skipping duplicate address: {addr[:10]}...")
                                write_to_csv([current_url, chain, addr, datetime.utcnow().isoformat()], "duplicate_addresses.csv")
                            continue
                            seen.add(addr)
                        screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                        highlight_and_save(driver, addr, screenshot_path)
                        print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                            write_to_csv([current_url, title, chain, addr, datetime.utcnow().isoformat(), screenshot_path], OUTPUT_CSV)
                        continue

                    # ✅ 2. Try cart workflow
                    print("🛒 Trying cart and checkout workflow...")
                    cart_addresses = try_cart_workflow(driver, current_url)
                    if cart_addresses:
                        print(f"✅ Found {len(cart_addresses)} addresses through cart workflow!")
                        hostname = urlparse(current_url).hostname or ''
                        if hostname.endswith('.onion'):
                            suffix = hostname[:-6][-6:]
                        else:
                            suffix = hostname[-6:]
                        title_prefix = sanitize_filename(title[:10])
                        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                        for i, (chain, addr) in enumerate(cart_addresses):
                            print(f"🔍 Processing: {chain} - {addr[:10]}...")
                            if addr in seen:
                                print(f"⏭️ Skipping duplicate address: {addr[:10]}...")
                                write_to_csv([current_url, chain, addr, datetime.utcnow().isoformat()], "duplicate_addresses.csv")
                                continue
                            seen.add(addr)
                            screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                            screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                            highlight_and_save(driver, addr, screenshot_path)
                            print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                            write_to_csv([current_url, title, chain, addr, datetime.utcnow().isoformat(), screenshot_path], OUTPUT_CSV)
                        continue

                    # ✅ 3. Try payment modal workflow
                    print("🔄 Trying payment modal workflow...")
                    try:
                        modal_addresses = try_payment_modal(driver, current_url)
                        if modal_addresses:
                            print(f"✅ Found {len(modal_addresses)} addresses in payment modal!")
                            hostname = urlparse(current_url).hostname or ''
                            if hostname.endswith('.onion'):
                                suffix = hostname[:-6][-6:]
                            else:
                                suffix = hostname[-6:]
                            title_prefix = sanitize_filename(title[:10])
                            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                            for i, (chain, addr) in enumerate(modal_addresses):
                                print(f"🔍 Processing: {chain} - {addr[:10]}...")
                                if addr in seen:
                                    print(f"⏭️ Skipping duplicate address: {addr[:10]}...")
                                    write_to_csv([current_url, chain, addr, datetime.utcnow().isoformat()], "duplicate_addresses.csv")
                                    continue
                                seen.add(addr)
                                screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                highlight_and_save(driver, addr, screenshot_path)
                                print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                write_to_csv([current_url, title, chain, addr, datetime.utcnow().isoformat(), screenshot_path], OUTPUT_CSV)
                            continue
                    except Exception as e:
                        print(f"❌ Payment modal workflow failed: {e}")

                    # ✅ 4. Direct /buy page check
                    if '/buy' in current_url:
                        print("🛒 On /buy page, performing direct address extraction...")
                        html = driver.page_source
                        addresses = extract_addresses(html)
                        if addresses:
                            print(f"✅ Found {len(addresses)} addresses directly on /buy page!")
                            hostname = urlparse(current_url).hostname or ''
                            if hostname.endswith('.onion'):
                                suffix = hostname[:-6][-6:]
                            else:
                                suffix = hostname[-6:]
                            title_prefix = sanitize_filename(title[:10])
                            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                            for i, (chain, addr) in enumerate(addresses):
                                print(f"🔍 Processing: {chain} - {addr[:10]}...")
                                if addr in seen:
                                    print(f"⏭️ Skipping duplicate address: {addr[:10]}...")
                                    write_to_csv([current_url, chain, addr, datetime.utcnow().isoformat()], "duplicate_addresses.csv")
                                    continue
                                seen.add(addr)
                                screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                highlight_and_save(driver, addr, screenshot_path)
                                print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                write_to_csv([current_url, title, chain, addr, datetime.utcnow().isoformat(), screenshot_path], OUTPUT_CSV)
                            continue

                    # 🔄 5. Reset and try registration/login workflow
                    print("🔄 No addresses found, resetting to original page and trying registration/login...")
                    try:
                        # Go back to the original page
                        driver.get(current_url)
                        time.sleep(SHORT_WAIT)
                        
                        # Wait for page to load completely
                        WebDriverWait(driver, 15).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                        
                        # Try registration and login workflow
                        print("📝 Attempting registration and login workflow...")
                        registration_addresses = try_registration_and_login(driver, current_url)
                        if registration_addresses:
                            print(f"✅ Found {len(registration_addresses)} addresses through registration!")
                            hostname = urlparse(current_url).hostname or ''
                            if hostname.endswith('.onion'):
                                suffix = hostname[:-6][-6:]
                            else:
                                suffix = hostname[-6:]
                            title_prefix = sanitize_filename(title[:10])
                            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                            for i, (chain, addr) in enumerate(registration_addresses):
                                print(f"🔍 Processing: {chain} - {addr[:10]}...")
                                if addr in seen:
                                    print(f"⏭️ Skipping duplicate address: {addr[:10]}...")
                                    write_to_csv([current_url, chain, addr, datetime.utcnow().isoformat()], "duplicate_addresses.csv")
                                    continue
                                seen.add(addr)
                                screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                highlight_and_save(driver, addr, screenshot_path)
                                print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                write_to_csv([current_url, title, chain, addr, datetime.utcnow().isoformat(), screenshot_path], OUTPUT_CSV)
                            continue
                        else:
                            print("❌ Registration/login workflow failed")
                    except Exception as e:
                        print(f"❌ Reset and registration attempt failed: {e}")

                    # 🔐 6. No addresses → check for CAPTCHA or login
                    lower_html = html.lower()
                    if "captcha" in lower_html:
                        print(f"[🧩] CAPTCHA detected at {current_url}")
                        solution = ai_solve_captcha(driver)
                        if solution:
                            try_submit_captcha(driver, solution)
                            time.sleep(2)
                            html_retry = driver.page_source
                            addresses = extract_addresses(html_retry)
                            if addresses:
                                print(f"✅ Found {len(addresses)} addresses after CAPTCHA!")
                                hostname = urlparse(current_url).hostname or ''
                                if hostname.endswith('.onion'):
                                    suffix = hostname[:-6][-6:]
                                else:
                                    suffix = hostname[-6:]
                                title_prefix = sanitize_filename(title[:10])
                                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                                for i, (chain, addr) in enumerate(addresses):
                                    print(f"🔍 Processing: {chain} - {addr[:10]}...")
                                    if addr in seen:
                                        print(f"⏭️ Skipping duplicate address: {addr[:10]}...")
                                        write_to_csv([current_url, chain, addr, datetime.utcnow().isoformat()], "duplicate_addresses.csv")
                                        continue
                                    seen.add(addr)
                                    screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                    highlight_and_save(driver, addr, screenshot_path)
                                    print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                    write_to_csv([current_url, title, chain, addr, datetime.utcnow().isoformat(), screenshot_path], OUTPUT_CSV)
                                continue
                            else:
                                print("❌ CAPTCHA solved but no addresses found.")
                                print("🔄 Trying back button and page reload...")
                                try:
                                    # Click back button
                                    driver.back()
                                    time.sleep(MEDIUM_WAIT)  # Wait longer for page to load
                                    # Wait for page to load completely
                                    WebDriverWait(driver, 15).until(
                                        lambda d: d.execute_script("return document.readyState") == "complete"
                                    )
                                    # Additional wait for dynamic content
                                    time.sleep(SHORT_WAIT)
                                    # Recheck for addresses after reload
                                    html_reload = driver.page_source
                                    addresses_reload = extract_addresses(html_reload)
                                    if addresses_reload:
                                        print(f"✅ Found {len(addresses_reload)} addresses after reload!")
                                        hostname = urlparse(current_url).hostname or ''
                                        if hostname.endswith('.onion'):
                                            suffix = hostname[:-6][-6:]
                                        else:
                                            suffix = hostname[-6:]
                                        title_prefix = sanitize_filename(title[:10])
                                        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                                        for i, (chain, addr) in enumerate(addresses_reload):
                                            print(f"🔍 Processing: {chain} - {addr[:10]}...")
                                            if addr in seen:
                                                print(f"⏭️ Skipping duplicate address: {addr[:10]}...")
                                                write_to_csv([current_url, chain, addr, datetime.utcnow().isoformat()], "duplicate_addresses.csv")
                                                continue
                                            seen.add(addr)
                                            screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                            screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                            highlight_and_save(driver, addr, screenshot_path)
                                            print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                            write_to_csv([current_url, title, chain, addr, datetime.utcnow().isoformat(), screenshot_path], OUTPUT_CSV)
                                        continue
                                    else:
                                        print("❌ Still no addresses found after reload.")
                                        print("🔄 Trying payment modal workflow...")
                                        try:
                                            modal_addresses = try_payment_modal(driver, current_url)
                                            if modal_addresses:
                                                print(f"✅ Found {len(modal_addresses)} addresses in payment modal!")
                                                hostname = urlparse(current_url).hostname or ''
                                                if hostname.endswith('.onion'):
                                                    suffix = hostname[:-6][-6:]
                                                else:
                                                    suffix = hostname[-6:]
                                                title_prefix = sanitize_filename(title[:10])
                                                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                                                for i, (chain, addr) in enumerate(modal_addresses):
                                                    print(f"🔍 Processing: {chain} - {addr[:10]}...")
                                                    if addr in seen:
                                                        print(f"⏭️ Skipping duplicate address: {addr[:10]}...")
                                                        write_to_csv([current_url, chain, addr, datetime.utcnow().isoformat()], "duplicate_addresses.csv")
                                                        continue
                                                    seen.add(addr)
                                                    screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                                    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                                    highlight_and_save(driver, addr, screenshot_path)
                                                    print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                                    write_to_csv([current_url, title, chain, addr, datetime.utcnow().isoformat(), screenshot_path], OUTPUT_CSV)
                                                continue
                                            else:
                                                write_to_csv([current_url], "captcha_failed_final.csv")
                                        except Exception as e:
                                            print(f"❌ Payment modal workflow failed: {e}")
                                    write_to_csv([current_url], "captcha_failed_final.csv")
                                except Exception as e:
                                    print(f"❌ Error navigating back: {e}")
                                    write_to_csv([current_url], "captcha_failed_final.csv")
                        else:
                            print("❌ CAPTCHA solve failed")
                            write_to_csv([current_url], CAPTCHA_FAILED_CSV)
                    else:
                        print("❌ CAPTCHA solve failed")
                        write_to_csv([current_url], CAPTCHA_FAILED_CSV)

                    # Log login pages but don't stop crawling
                    if any(k in lower_html for k in ["login", "log in", "sign in", "password"]):
                        print(f"[🔐] Login page detected at {current_url} - logging but continuing crawl")
                        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                        screenshot_path = os.path.join(SCREENSHOT_DIR, f"login_{timestamp}.png")
                        driver.save_screenshot(screenshot_path)
                        write_to_csv([
                            current_url, title, datetime.utcnow().isoformat(), screenshot_path
                        ], "login_required.csv")

                    # 🔗 7. Get internal links for deeper crawling
                    internal_links = get_internal_links(soup, current_url)
                    
                    # First, check if there are any /buy links and prioritize them
                    buy_links = [link for link in internal_links if '/buy' in link.lower()]
                    if buy_links:
                        print(f"🛒 Found {len(buy_links)} /buy links, prioritizing them...")
                        for link in buy_links:
                            if link not in visited and depth < MAX_DEPTH:
                                to_visit.insert(0, (link, depth + 1))  # Insert at beginning for priority
                    
                    # Then add other links
                    for link in internal_links:
                        if link not in visited and depth < MAX_DEPTH and link not in buy_links:
                            # Prioritize links with payment-related keywords
                        if any(k in link.lower() for k in KEYWORDS):
                            to_visit.append((link, depth + 1))
                            else:
                                to_visit.append((link, depth + 1))

            except Exception as e:
                print(f"❌ Failed: {e}")
                    write_to_csv([current_url], "manual_review.csv")
    
    print("✅ Scraping completed successfully!")
    
except KeyboardInterrupt:
    print("\n⏹️ Scraping interrupted by user")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
finally:
    try:
driver.quit()
        print("🔒 Browser closed")
    except:
        pass
print("🎉 Done. Results saved to", OUTPUT_CSV)