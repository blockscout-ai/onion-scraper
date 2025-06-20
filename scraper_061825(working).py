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
chromedriver_autoinstaller.install()

# ---[ Config ]---
TOR_PROXY = "socks5://127.0.0.1:9050"
INPUT_CSV = "discovered_onions_20250618.csv"
OUTPUT_CSV = "addresses_sample_2.csv"
SCREENSHOT_DIR = "screenshots_sample_2"
CAPTCHA_FAILED_CSV = "captcha_failed_sample.csv"
UNSOLVED_DIR = "unsolved_captchas"
MAX_DEPTH = 3
PAGE_LOAD_TIMEOUT = 45

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(UNSOLVED_DIR, exist_ok=True)

PATTERNS = {
    "BTC": re.compile(r"\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b"),
    "ETH": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "XMR": re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b"),
    "TRON": re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b"),
    "SOL": re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
}

KEYWORDS = ["buy", "checkout", "payment", "wallet", "order", "access", "rent", "trial", "continue", "enter"]

chrome_options = Options()
# chrome_options.add_argument("--headless=new")  # Uncomment for headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(f"--proxy-server={TOR_PROXY}")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")

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

# ---[ Utilities ]---
def wait_for_address_in_dom(driver, timeout=10):
    def check(_driver):
        return any(p.search(_driver.page_source) for p in PATTERNS.values())
    try:
        WebDriverWait(driver, timeout).until(check)
    except:
        pass

def get_internal_links(soup, base_url):
    links = []
    base = urlparse(base_url)
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a['href'])
        if not urlparse(href).netloc or urlparse(href).netloc == base.netloc:
            links.append(href)
    return links

def sanitize_filename(s):
    return re.sub(r'[^a-zA-Z0-9_-]', '', s)

def write_to_csv(row, file):
    with open(file, 'a', newline='') as f:
        csv.writer(f).writerow(row)

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
            "//a[contains(@href, 'buy')]"            # Any buy links
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
                time.sleep(3)
                # Try buttons again after navigation
                for selector in button_selectors:
                    try:
                        buttons = driver.find_elements(By.XPATH if selector.startswith("//") else By.CSS_SELECTOR, selector)
                        if buttons:
                            buy_button = buttons[0]
                            break
                    except:
                        continue

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
            
            time.sleep(3)  # Wait for modal to appear

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
                    "//button[contains(@class, 'submit')]"
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
                    time.sleep(3)  # Wait for crypto address to appear
                    
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

# ---[ Initialize CSV ]---
if not os.path.exists(OUTPUT_CSV):
    write_to_csv(['url', 'title', 'chain', 'address', 'timestamp', 'screenshot'], OUTPUT_CSV)
if not os.path.exists(CAPTCHA_FAILED_CSV):
    write_to_csv(['url'], CAPTCHA_FAILED_CSV)

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

# ---[ Main Loop ]---
with open(INPUT_CSV, newline='') as f:
    for idx, row in enumerate(csv.reader(f), start=1):
        base_url = row[0].strip()
        if not base_url.startswith("http://"):
            base_url = "http://" + base_url
        print(f"\n🔍 [{idx}] Scanning {base_url}")
        visited = set()
        to_visit = [(base_url, 0)]
        while to_visit:
            current_url, depth = to_visit.pop(0)
            if current_url in visited or depth > MAX_DEPTH:
                continue
            visited.add(current_url)
            try:
                print(f"🌐 Visiting: {current_url} (depth {depth})")
                driver.get(current_url)
                time.sleep(3)
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                addresses = extract_addresses(html)
                title = soup.title.string.strip() if soup.title else "NoTitle"

                # ✅ 1. Extract addresses first
                if addresses:
                    print(f"🔍 Found {len(addresses)} addresses on {current_url}")
                    print(f"📂 Root URL: {base_url}")
                    print(f"📍 Addresses found: {addresses}")
                    hostname = urlparse(current_url).hostname or ''
                    # Get 6 chars before .onion, or last 6 chars if no .onion
                    if hostname.endswith('.onion'):
                        suffix = hostname[:-6][-6:]  # Remove .onion, then get last 6 chars
                    else:
                        suffix = hostname[-6:]
                    title_prefix = sanitize_filename(title[:10])
                    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                    for i, (chain, addr) in enumerate(addresses):
                        print(f"🔍 Processing: {chain} - {addr[:10]}...")
                        if addr in seen:
                            print(f"⏭️ Skipping duplicate address: {addr[:10]}...")
                            # Log duplicate to separate file
                            write_to_csv([
                                current_url, chain, addr, datetime.utcnow().isoformat()
                            ], "duplicate_addresses.csv")
                            continue
                        seen.add(addr)
                        screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                        highlight_and_save(driver, addr, screenshot_path)
                        print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                        write_to_csv([
                            current_url, title, chain, addr,
                            datetime.utcnow().isoformat(), screenshot_path
                        ], OUTPUT_CSV)
                    continue  # Don't check captcha/login if address found

                # ✅ 2. Try payment modal workflow
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
                                write_to_csv([
                                    current_url, chain, addr, datetime.utcnow().isoformat()
                                ], "duplicate_addresses.csv")
                                continue
                            seen.add(addr)
                            screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                            screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                            highlight_and_save(driver, addr, screenshot_path)
                            print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                            write_to_csv([
                                current_url, title, chain, addr,
                                datetime.utcnow().isoformat(), screenshot_path
                            ], OUTPUT_CSV)
                        continue  # Skip CAPTCHA if we found addresses in modal
                except Exception as e:
                    print(f"❌ Payment modal workflow failed: {e}")

                # 🔐 3. No addresses → check for CAPTCHA or login
                lower_html = html.lower()
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

                if "captcha" in lower_html:
                    print(f"[🧩] CAPTCHA detected at {current_url}")
                    solution = solve_captcha(driver)
                    if solution:
                        try_submit_captcha(driver, solution)
                        time.sleep(2)
                        html_retry = driver.page_source
                        addresses = extract_addresses(html_retry)
                        if addresses:
                            hostname = urlparse(current_url).hostname or ''
                            # Get 6 chars before .onion, or last 6 chars if no .onion
                            if hostname.endswith('.onion'):
                                suffix = hostname[:-6][-6:]  # Remove .onion, then get last 6 chars
                            else:
                                suffix = hostname[-6:]
                            title_prefix = sanitize_filename(title[:10])
                            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                            for i, (chain, addr) in enumerate(addresses):
                                print(f"🔍 Processing: {chain} - {addr[:10]}...")
                                if addr in seen:
                                    print(f"⏭️ Skipping duplicate address: {addr[:10]}...")
                                    # Log duplicate to separate file
                                    write_to_csv([
                                        current_url, chain, addr, datetime.utcnow().isoformat()
                                    ], "duplicate_addresses.csv")
                                    continue
                                seen.add(addr)
                                screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                highlight_and_save(driver, addr, screenshot_path)
                                print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                write_to_csv([
                                    current_url, title, chain, addr,
                                    datetime.utcnow().isoformat(), screenshot_path
                                ], OUTPUT_CSV)
                        else:
                            print("❌ CAPTCHA solved but no addresses found.")
                            print("🔄 Trying back button and page reload...")
                            try:
                                # Click back button
                                driver.back()
                                time.sleep(5)  # Wait longer for page to load
                                # Wait for page to load completely
                            except Exception as e:
                                print(f"❌ Error navigating back: {e}")
                                WebDriverWait(driver, 15).until(
                                    lambda d: d.execute_script("return document.readyState") == "complete"
                                )
                                # Additional wait for dynamic content
                                time.sleep(3)
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
                                            write_to_csv([
                                                current_url, chain, addr, datetime.utcnow().isoformat()
                                            ], "duplicate_addresses.csv")
                                            continue
                                        seen.add(addr)
                                        screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                        highlight_and_save(driver, addr, screenshot_path)
                                        print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                        write_to_csv([
                                            current_url, title, chain, addr,
                                            datetime.utcnow().isoformat(), screenshot_path
                                        ], OUTPUT_CSV)
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
                                                    write_to_csv([
                                                        current_url, chain, addr, datetime.utcnow().isoformat()
                                                    ], "duplicate_addresses.csv")
                                                    continue
                                                seen.add(addr)
                                                screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                                screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                                highlight_and_save(driver, addr, screenshot_path)
                                                print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                                write_to_csv([
                                                    current_url, title, chain, addr,
                                                    datetime.utcnow().isoformat(), screenshot_path
                                                ], OUTPUT_CSV)
                                        else:
                                            write_to_csv([current_url], "captcha_failed_final.csv")
                                    except Exception as e:
                                        print(f"❌ Payment modal workflow failed: {e}")
                                        write_to_csv([current_url], "captcha_failed_final.csv")
                    else:
                        print("❌ CAPTCHA solve failed. Retrying entire page...")
                        try:
                            # Reload the entire page
                            driver.get(current_url)
                            time.sleep(5)
                            # Wait for page to load completely
                            WebDriverWait(driver, 15).until(
                                lambda d: d.execute_script("return document.readyState") == "complete"
                            )
                            # Recheck for addresses after page reload
                            html_retry = driver.page_source
                            addresses_retry = extract_addresses(html_retry)
                            if addresses_retry:
                                print(f"✅ Found {len(addresses_retry)} addresses after page reload!")
                                hostname = urlparse(current_url).hostname or ''
                                if hostname.endswith('.onion'):
                                    suffix = hostname[:-6][-6:]
                                else:
                                    suffix = hostname[-6:]
                                title_prefix = sanitize_filename(title[:10])
                                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                                for i, (chain, addr) in enumerate(addresses_retry):
                                    print(f"🔍 Processing: {chain} - {addr[:10]}...")
                                    if addr in seen:
                                        print(f"⏭️ Skipping duplicate address: {addr[:10]}...")
                                        write_to_csv([
                                            current_url, chain, addr, datetime.utcnow().isoformat()
                                        ], "duplicate_addresses.csv")
                                        continue
                                    seen.add(addr)
                                    screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                    highlight_and_save(driver, addr, screenshot_path)
                                    print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                    write_to_csv([
                                        current_url, title, chain, addr,
                                        datetime.utcnow().isoformat(), screenshot_path
                                    ], OUTPUT_CSV)
                            else:
                                print("❌ Still no addresses found after page reload.")
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
                                                write_to_csv([
                                                    current_url, chain, addr, datetime.utcnow().isoformat()
                                                ], "duplicate_addresses.csv")
                                                continue
                                            seen.add(addr)
                                            screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                            screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                            highlight_and_save(driver, addr, screenshot_path)
                                            print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                            write_to_csv([
                                                current_url, title, chain, addr,
                                                datetime.utcnow().isoformat(), screenshot_path
                                            ], OUTPUT_CSV)
                                    else:
                                        write_to_csv([current_url], "captcha_failed_final.csv")
                                except Exception as e:
                                    print(f"❌ Payment modal workflow failed: {e}")
                                    write_to_csv([current_url], "captcha_failed_final.csv")
                        except Exception as e:
                            print(f"❌ Page reload failed: {e}")
                            print("🔄 Trying payment modal workflow as last resort...")
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
                                            write_to_csv([
                                                current_url, chain, addr, datetime.utcnow().isoformat()
                                            ], "duplicate_addresses.csv")
                                            continue
                                        seen.add(addr)
                                        screenshot_name = f"{title_prefix}_{suffix}_{timestamp}_{i}.png"
                                        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                                        highlight_and_save(driver, addr, screenshot_path)
                                        print(f"🏦 Found {chain} address: {addr[:4]}...{addr[-4:]} → 📸 {screenshot_name}")
                                        write_to_csv([
                                            current_url, title, chain, addr,
                                            datetime.utcnow().isoformat(), screenshot_path
                                        ], OUTPUT_CSV)
                                else:
                                    write_to_csv([current_url], "captcha_failed_final.csv")
                            except Exception as e:
                                print(f"❌ Payment modal workflow failed: {e}")
                                write_to_csv([current_url], "captcha_failed_final.csv")

                # Log login pages but don't stop crawling
                if any(k in lower_html for k in ["login", "log in", "sign in", "password"]):
                    print(f"[🔐] Login page detected at {current_url} - logging but continuing crawl")
                    screenshot_path = os.path.join(SCREENSHOT_DIR, f"login_{timestamp}.png")
                    driver.save_screenshot(screenshot_path)
                    write_to_csv([
                        current_url, title, datetime.utcnow().isoformat(), screenshot_path
                    ], "login_required.csv")

                # Continue crawling if depth allows
                if depth < MAX_DEPTH:
                    for link in get_internal_links(soup, current_url):
                        if any(k in link.lower() for k in KEYWORDS):
                            to_visit.append((link, depth + 1))

            except Exception as e:
                print(f"❌ Failed: {e}")
                write_to_csv([current_url], "manual_review.csv")

driver.quit()
print("🎉 Done. Results saved to", OUTPUT_CSV)