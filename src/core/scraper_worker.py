import os
import re
import csv
import time
import socket
import base58
from datetime import datetime
from urllib.parse import urljoin, urlparse
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import sys

# ------------------------------
# Configuration
# ------------------------------
TOR_PROXY = "socks5://127.0.0.1:9050"
TOR_CONTROL_PORT = 9051
TOR_CONTROL_PASSWORD = 'Jasoncomer1$'

INPUT_CSV = "onion_sample.csv"
OUTPUT_CSV = "addresses_20250616.csv"
VISITED_LINKS_CSV = "visited_links_20250616.csv"
FAILED_LINKS_CSV = "failed_20250616.csv"
SCREENSHOT_DIR = "screenshots_20250616"
MAX_DEPTH = 3
PAGE_LOAD_TIMEOUT = 45
KEYWORDS = ["buy", "checkout", "choose", "trial" "payment", "wallet", "order", "access", "rent", "register", "login", "market", "loli", "boys", "girls", "sex", "rape", "bitcoin", "lolita", "loliporn", "cp", "cp video", "drugs", "cocaine", "fentanyl", "products"]

if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

chrome_options = Options()
#chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(f"--proxy-server={TOR_PROXY}")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")
driver = webdriver.Chrome(options=chrome_options)
driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

PATTERNS = {
    "BTC": re.compile(r"\b((bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39})\b"),
    "ETH": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "XMR": re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b")
}

# ------------------------------
# Utilities
# ------------------------------
def rotate_tor_identity():
    try:
        with socket.create_connection(("127.0.0.1", TOR_CONTROL_PORT), timeout=3) as s:
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

def is_valid_btc_address(address):
    if address.startswith("1") or address.startswith("3"):
        try:
            base58.b58decode_check(address)
            return True
        except Exception:
            return False
    elif address.startswith("bc1") and re.fullmatch(r"(bc1)[0-9a-z]{11,71}", address):
        return True
    return False

def extract_addresses(text):
    found = []
    for chain, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            addr = match[0] if isinstance(match, tuple) else match
            if 26 <= len(addr) <= 100:
                if chain == "BTC" and not is_valid_btc_address(addr):
                    continue
                found.append((chain, addr))
    return found

def get_internal_links(soup, base_url):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.scheme.startswith("http") and parsed.hostname and parsed.hostname.endswith(".onion"):
            links.add(full_url)
    return list(links)

def sanitize_filename(s):
    return re.sub(r'[^a-zA-Z0-9_-]', '', s)

def write_to_csv(path, row):
    with open(path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(row)

def submit_generic_form(driver):
    try:
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for field in inputs:
            name = field.get_attribute("name") or ""
            field.send_keys("NA")
        submit = driver.find_element(By.XPATH, '//input[@type="submit"] | //button[@type="submit"]')
        submit.click()
        time.sleep(5)
    except:
        pass

def solve_captcha_if_present(driver):
    try:
        if "captcha" in driver.page_source.lower():
            print("🛑 CAPTCHA detected, attempting OCR...")
            captcha_img = driver.find_element(By.XPATH, '//img[contains(@src, "captcha")]')
            location = captcha_img.location_once_scrolled_into_view
            size = captcha_img.size
            full_screenshot_path = "_captcha_fullpage.png"
            driver.save_screenshot(full_screenshot_path)
            image = Image.open(full_screenshot_path)
            left = int(location['x'])
            top = int(location['y'])
            right = left + int(size['width'])
            bottom = top + int(size['height'])
            captcha_crop = image.crop((left, top, right, bottom))
            captcha_text = pytesseract.image_to_string(captcha_crop).strip()
            print(f"🔍 OCR Solved CAPTCHA as: {captcha_text}")
            input_box = driver.find_element(By.XPATH, '//input[@type="text" or contains(@placeholder,"captcha")]')
            input_box.clear()
            input_box.send_keys(captcha_text)
            submit_button = driver.find_element(By.XPATH, '//button[contains(text(), "submit") or contains(text(), "ok") or @type="submit"]')
            ActionChains(driver).move_to_element(submit_button).click().perform()
            time.sleep(3)
        else:
            print("✅ No CAPTCHA found on this page.")
    except Exception as e:
        print(f"⚠️ CAPTCHA solving failed or not found: {e}")

# ------------------------------
# File Prep
# ------------------------------
for file, headers in [
    (OUTPUT_CSV, ['onion_base', 'title', 'chain', 'address', 'timestamp', 'screenshot']),
    (VISITED_LINKS_CSV, ['visited_url']),
    (FAILED_LINKS_CSV, ['url'])
]:
    if not os.path.exists(file):
        with open(file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

failed_urls = []
seen_by_onion_host = {}

# ------------------------------
# Main Loop
# ------------------------------
with open(INPUT_CSV, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for idx, row in enumerate(reader, start=1):
        url = row[0].strip()
        if not url.startswith("http"):
            url = "http://" + url

        visited = set()
        to_visit = [(url, 0)]

        while to_visit:
            current_url, depth = to_visit.pop(0)
            if current_url in visited or depth > MAX_DEPTH:
                continue
            visited.add(current_url)

            print(f"\n🌐 Visiting: {current_url} | Depth: {depth}")
            write_to_csv(VISITED_LINKS_CSV, [current_url])

            try:
                driver.get(current_url)
                solve_captcha_if_present(driver)
                time.sleep(2)
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                addresses = extract_addresses(page_source)

                if not addresses and soup.find_all("form"):
                    submit_generic_form(driver)
                    time.sleep(2)
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    addresses = extract_addresses(driver.page_source)

                title = soup.title.string.strip() if soup.title else "NoTitle"
                parsed_url = urlparse(current_url)
                onion_host = parsed_url.hostname or ""
                onion_clean = onion_host.split('.')[-2] if onion_host.endswith(".onion") else onion_host
                onion_base = f"http://{onion_host}"

                if onion_clean not in seen_by_onion_host:
                    seen_by_onion_host[onion_clean] = set()

                timestamp_base = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
                title_prefix = sanitize_filename(title[:10])
                onion_suffix = onion_clean[-6:] if len(onion_clean) >= 6 else onion_clean

                for i, (chain, addr) in enumerate(addresses):
                    if addr in seen_by_onion_host[onion_clean]:
                        continue
                    seen_by_onion_host[onion_clean].add(addr)

                    print(f"🔗 Found address → {chain}: {addr}")
                    screenshot_name = f"{title_prefix}_{onion_suffix}_{timestamp_base}_{i}.png"
                    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
                    driver.save_screenshot(screenshot_path)
                    print(f"📸 Screenshot saved: {screenshot_path}")

                    row_data = [
                        onion_base,
                        title,
                        chain,
                        addr,
                        datetime.utcnow().isoformat(),
                        screenshot_path
                    ]
                    write_to_csv(OUTPUT_CSV, row_data)

                if depth < MAX_DEPTH:
                    for link in get_internal_links(soup, current_url):
                        if any(keyword in link.lower() for keyword in KEYWORDS):
                            to_visit.append((link, depth + 1))

                time.sleep(3)
                rotate_tor_identity()

            except Exception as e:
                print(f"❌ Failed to load {current_url}: {str(e)}")
                failed_urls.append(current_url)

if failed_urls:
    with open(FAILED_LINKS_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        for url in failed_urls:
            writer.writerow([url])

driver.quit()