# Advanced Onion Scraper

This is a high-performance, parallel-processing web scraper designed to navigate Tor (.onion) websites, extract cryptocurrency addresses, and handle various anti-bot measures. It leverages Selenium with a TOR proxy and incorporates AI-driven logic to solve captchas, handle logins, and navigate complex sites.

## Key Features

- **Parallel Processing**: Utilizes a thread pool to scrape multiple URLs concurrently for maximum speed.
- **TOR Integration**: Routes all traffic through the TOR network and supports automatic identity rotation for anonymity.
- **Dynamic Content Handling**: Intelligently waits for JavaScript-rendered content and scrolls pages to trigger lazy-loading.
- **Advanced Address Extraction**: Uses optimized regex and validation for multiple cryptocurrencies (BTC, ETH, XMR, TRON, SOL).
- **AI-Powered Captcha Solving**:
  - Solves standard image-based captchas using OCR and an AI vision model.
  - Solves visual captchas (e.g., "Click the red circle") using color and element analysis.
- **Automated Login & Registration**: Proactively detects and attempts to fill login and registration forms with generated user data.
- **Smart Navigation**: Prioritizes crawling links related to payments, wallets, and checkouts.
- **Detailed Logging & Output**: Saves found addresses to a CSV file, takes highlighted screenshots for verification, and logs skipped sites and discovered links.

## Setup

1.  **Prerequisites**:
    *   Python 3.8+
    *   [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
    *   A running TOR service on port 9050/9051.

2.  **Installation**:
    ```bash
    # Clone the repository
    git clone https://github.com/blockscout-ai/onion-scraper.git
    cd onion-scraper

    # Install Python dependencies
    pip install -r requirements.txt
    ```

3.  **Configuration**:
    - Place your list of onion URLs into `discovered_onions_20250618.csv`.
    - (Optional) Set your `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` as environment variables if you wish to use the AI features.

## Usage

Once configured, run the scraper from your terminal:

```bash
python scraper_fast.py
```

The script will begin processing the URLs and output its findings into `crypto_addresses_fast.csv` and the `screenshots_fast/` directory. 