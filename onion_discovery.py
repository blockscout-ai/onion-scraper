import os
import re
import csv
import time
import socket
import random
import threading
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------
# Configuration
# ----------------------------
TOR_SOCKS_PROXY = "socks5h://127.0.0.1:9050"
TOR_CONTROL_PORT = 9051
TOR_CONTROL_PASSWORD = 'Jasoncomer1$'
CONTROL_TIMEOUT = 3

SEED_URLS = [
    "xcprh4cjas33jnxgs3zhakof6mctilfxigwjcsevdfap7vtyj57lmjad.onion",
    "torchqsxkllrj2eqaitp5xvcgfeg3g5dr3hr2wnuvnj76bbxkxfiwxqd.onion",
    "stealthwduyals3krxqizgoarfbvliftof4po52ywabrmjy5m6ebzmyd.onion", 
    "darkon6d23lmnx3ttnenhbjkthfdsxthimxvoimwyt43yvxsjqb3read.onion",
    "3fzh7yuupdfyjhwt3ugzqqof6ulbcl27ecev33knxe3u7goi3vfn2qqd.onion",
    "ahmiavptbjnubgitmgooytrieoxj4dml7ufc73lox2jzelgtcyjwmjyd.onion",
    "no6m4wzdexe3auiupv2zwif7rm6qwxcyhslkcnzisxgeiw6pvjsgafad.onion",
    "tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion",
    "amnesia7kx7gcdhuaykmlv5jdget57kbeplowfeezjnwdt67jrehgnid.onion",
    "digitald7wil4jiylocoorw43sg6ndzzirq63cnl6prm43vzb44lmaqd.onion",
    "yacxfm6xzn3uhdxuup2pzjic3sykkk7in32nu6cunm4g3q43pp6vfdad.onion",
    "rczml4qtvhfxlwck4jlmky6aa4a7vdbqy3a3ndowv25z5n3wxqweqfyd.onion",
    "torbookp6ougjm42lzt4gzki3ozprktiekhqydwavp26d5m3ewjr3fad.onion",
    "5v3gmrwx3zai57pa3wezs5nwqljk22473zli2weysg3qmefiv7cfafyd.onion",
    "oniondxi5gral57k2eyqbydoj2sfsxisw43sgpquksfyapkw5r76tbid.onion",
    "u5b722sge6bfllcze53ypta2le2ffiuwibqdqaa7obh5w7zbdo6sarqd.onion",
    "searchg2oql3s7c3ypoyp46yrxblsdpnlaywa6ixrebrtoketjdyrpqd.onion",
    "torchac4h5bchwcxnnl566u5uuaclrufmaecv7ll2n64aggzsy5of2yd.onion",
    "tornadodkfspkjc7u7q5gyit3idosor6gqgfopdjovriiyvkud7456qd.onion",
    "kn3hl4xw5cf4kbmxesqhryla3ja3fnatq4367nkln5jt5fbrkdag6vid.onion",
    "lolipornrgrqfiuro7xs6lidbd6waqfjyvn3kbwlwa2b27tn4tlkpxid.onion",
    "2222222kfx27lcsh7iiugnbprjj7e4zcm254ef3qd5piagebixcgpnid.onion",
    "z3jnsdrjgpvinjgmpjaxmoa7ote3xe4fvpcdmdphzk7hl7fffjeecwqd.onion",
    "metagerv65pwclop2rsfzg4jwowpavpwd6grhhlvdgsswvo6ii4akgyd.onion",
    "tornetuembmmub3weidqdzm7sxyezltb7a6jd3nigo276klxrgfz3myd.onion",
    "findtoreoxjrfz3ohn57a44rcwmyya4cbj6tirrn56l7dyvzxpufymyd.onion",
    "hhfrdjsr5fmlt472abc3p7ztxkwus42v6vmmqud2vmi7ytnxtzne3eid.onion",
    "jhwvlvwzdhnk66lf3jlr3pi52vjm53giwckrlc2zov2jga57m5qq5qid.onion",
    "ghn4d5bzesixa3bmfusyobaavavg2ez33okec7uk6li673uaqg6vywqd.onion",
    "r6ogx3w3s6rg3gxm3kprurn77z2oim665yr5pcxhr76yit4g65y76zad.onion",
    "findtorroveq5wdnipkaojfpqulxnkhblymc7aramjzajcvpptd4rjqd.onion",
    "d6szp2mjrl3o6xavacqyrapifxwne7w5xexmsk6nolrlvit3j3l2hoad.onion",
    "d4qhcwt4yejwl4bi7fjkgib44mskgcerqcz2j6upj4gslwm4ppgfdhid.onion",
    "zoozle4qppglzctcpulgh47fpefiaetqoui7pgbfhulyn2lzmorx4fqd.onion",
    "q5rl55ixr6zqfa7ddg2dlw6xkz3m6ivnacrhf2rfolhnvintmm2gllqd.onion",
    "haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion",
    "heypoh347ftlageml6ysaphsohctxjqwyod3k5f7kypnex4kyjrwk4id.onion",
    "search7gfmgygnzcmfuepuu32e2fframtptmatxbjh3h2nfbgrr5eeyd.onion",
    "searchesqafmar2ocusr443hnolhmrxek5xu3hrw3wliwlzmdywvjtqd.onion"
]

OUTPUT_FILE = f"discovered_onions_{datetime.utcnow().strftime('%Y%m%d')}.csv"
KEYWORDS = [
    'loli', 'boys', 'girls', 'sex', 'sexy', 'rape', 'lolita', 'loliporn',
    'cp', 'cp video', 'child porn', 'child xxx', 'preteen', 'child', 'red room', 'teen', 'cute boys',
    'childxxx', 'preteen', 'child'
]
MAX_DEPTH = 3
SLEEP_BETWEEN_REQUESTS = (5, 15)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
ROTATE_EVERY_N = 17
MAX_WORKERS = 5  # Number of concurrent workers

# ----------------------------
# Setup Requests via Tor
# ----------------------------
session = requests.Session()
session.proxies = {
    "http": TOR_SOCKS_PROXY,
    "https": TOR_SOCKS_PROXY
}
session.headers.update({"User-Agent": USER_AGENT})

# Thread-safe data structures
seen_lock = threading.Lock()
discovered_lock = threading.Lock()
file_lock = threading.Lock()
page_counter_lock = threading.Lock()
seen = set()
discovered = set()
page_counter = 0

# ----------------------------
# Functions
# ----------------------------
def rotate_tor_identity():
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

def extract_clean_onion(domain):
    match = re.search(r"([a-z2-7]{56})\.onion", domain)
    return match.group(0) if match else None

def extract_onion_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a['href'])
        parsed = urlparse(href)
        if parsed.hostname and ".onion" in parsed.hostname:
            clean = extract_clean_onion(parsed.hostname)
            if clean:
                links.add(clean)
    return links

def extract_title(html):
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    return title_tag.text.strip() if title_tag else ""

def process_url(url, depth, max_depth):
    """Worker function to process a single URL"""
    global seen, discovered, page_counter
    
    raw_host = urlparse(url).hostname
    if not raw_host:
        print(f"❌ Invalid URL format: {url}")
        return []
    
    clean_host = extract_clean_onion(raw_host)
    if not clean_host:
        return []
    
    # Thread-safe check for seen URLs
    with seen_lock:
        if clean_host in seen or depth > max_depth:
            return []
        seen.add(clean_host)
    
    print(f"🌐 Visiting: {url} | Depth: {depth}")
    
    try:
        # Create a new session for each thread to avoid conflicts
        thread_session = requests.Session()
        thread_session.proxies = {
            "http": TOR_SOCKS_PROXY,
            "https": TOR_SOCKS_PROXY
        }
        thread_session.headers.update({"User-Agent": USER_AGENT})
        
        resp = thread_session.get(url, timeout=30)
        new_links = []
        
        if any(keyword in resp.text.lower() for keyword in KEYWORDS):
            title = extract_title(resp.text)
            print(f"📝 Title: {title}")
            extracted_links = extract_onion_links(resp.text, url)
            
            for link in extracted_links:
                with discovered_lock:
                    if link not in discovered:
                        discovered.add(link)
                        row = [f"http://{link}", url, depth, datetime.utcnow().isoformat(), title]
                        print(f"➕ Found: {link}")
                        
                        # Thread-safe file writing
                        with file_lock:
                            with open(OUTPUT_FILE, "a", newline='') as f:
                                writer = csv.writer(f)
                                writer.writerow(row)
                        
                        if depth + 1 <= max_depth:
                            new_links.append((f"http://{link}", depth + 1))
        
        # Thread-safe page counter update
        with page_counter_lock:
            global page_counter
            page_counter += 1
            if page_counter % ROTATE_EVERY_N == 0:
                rotate_tor_identity()
        
        sleep_time = random.randint(*SLEEP_BETWEEN_REQUESTS)
        print(f"⏳ Sleeping {sleep_time}s")
        time.sleep(sleep_time)
        
        return new_links
        
    except Exception as e:
        print(f"❌ Error visiting {url}: {e}")
        return []

def crawl(start_urls, max_depth=2):
    # Ensure URLs have http:// prefix
    queue = [(url if url.startswith('http') else f"http://{url}", 0) for url in start_urls]
    
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["onion_url", "source", "depth", "timestamp", "title"])

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while queue:
            # Submit up to MAX_WORKERS tasks
            futures = []
            for _ in range(min(MAX_WORKERS, len(queue))):
                if queue:
                    url, depth = queue.pop(0)
                    future = executor.submit(process_url, url, depth, max_depth)
                    futures.append(future)
            
            # Collect results and add new URLs to queue
            for future in as_completed(futures):
                try:
                    new_links = future.result()
                    queue.extend(new_links)
                except Exception as e:
                    print(f"❌ Worker error: {e}")
            
            # Small delay to prevent overwhelming the system
            if queue:
                time.sleep(1)

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    crawl(SEED_URLS, MAX_DEPTH)