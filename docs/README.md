# Onion Discovery Tool

A comprehensive tool for discovering onion URLs through keyword-based search and crawling.

## Features

- **Keyword Search**: Searches multiple Tor search engines using predefined keywords
- **Deep Crawling**: Crawls discovered onion sites to find additional links
- **Cryptocurrency Detection**: Extracts cryptocurrency addresses from discovered sites
- **Progress Tracking**: Saves progress and allows resuming interrupted crawls
- **Tor Integration**: Uses Tor SOCKS proxy for anonymous browsing
- **Threading**: Multi-threaded crawling for improved performance

## Usage

### Basic Usage

```bash
# Start a new crawl with keyword search
python onion_discovery.py

# Resume from where you left off
python onion_discovery.py --resume

# Skip keyword search and only crawl seed URLs
python onion_discovery.py --no-search

# Verbose logging
python onion_discovery.py --verbose

# Quiet mode (minimal output)
python onion_discovery.py --quiet
```

### Command Line Options

- `--resume`: Resume from a previous crawl session
- `--no-search`: Skip the keyword search phase and only crawl seed URLs
- `--verbose`: Enable detailed logging
- `--quiet`: Enable minimal logging (warnings and errors only)

## Temporary File Management

To prevent codebase clutter from temporary fix scripts, tests, and one-time use files, use the built-in temporary file management system:

### Creating Temporary Scripts

```python
from temp_file_manager import create_temp_script

# Create a temporary script that auto-deletes after 24 hours
script_path = create_temp_script(
    name="quick_fix", 
    content="""
import pandas as pd
# Your temporary code here
print("This script will auto-delete!")
""",
    hours=24
)
```

### Command Line Usage

```bash
# Create a new temporary script
python temp_file_manager.py create my_test_script

# List all tracked temporary files
python temp_file_manager.py list

# Clean up expired files
python temp_file_manager.py cleanup

# Mark an existing file for automatic cleanup
python temp_file_manager.py mark old_script.py 2  # cleanup in 2 hours
```

### Features

- **Auto-cleanup**: Files automatically delete after expiration
- **Tracking**: Registry tracks all temporary files with metadata
- **Extensions**: Can extend file lifetime if needed
- **Safe patterns**: Files stored in `temp_files/` directory
- **Git-ignored**: Temporary files won't be committed to version control

### Best Practices

1. **Always use for temporary work**: Any script that's not permanent core functionality
2. **Set appropriate lifetimes**: Short for debugging, longer for ongoing work
3. **Clean regularly**: Run `python temp_file_manager.py cleanup` periodically
4. **Meaningful names**: Use descriptive names for easier tracking

## How It Works

### Phase 1: Keyword Search
The tool first searches each keyword on each configured search engine:
- Haystak
- Metagerv
- Narcoo
- On62jjk
- Tor66
- Iy3544
- Uquroy

This phase discovers initial onion URLs that match the search criteria.

### Phase 2: Deep Crawling
The tool then crawls all discovered URLs (from both keyword search and seed URLs) to find additional onion links.

### Output Files

- `discovered_onions_YYYYMMDD.csv`: All discovered onion URLs with metadata
- `crypto_addresses_YYYYMMDD.csv`: Cryptocurrency addresses found on sites
- `crawler_log_YYYYMMDD_HHMMSS.log`: Detailed log file
- `crawler_progress.json`: Progress tracking for resuming
- `max_depth_urls_YYYYMMDD_HHMMSS.txt`: URLs at maximum depth for deeper crawling

## Configuration

### Search Engines
Search engine URL patterns are defined in `SEARCH_ENGINE_PATTERNS`. The tool tries primary patterns first, then falls back to alternative patterns if needed.

### Keywords
Keywords are defined in the `KEYWORDS` list. These are used to search for relevant onion sites.

### Crawling Settings
- `MAX_DEPTH`: Maximum crawl depth (default: 4)
- `MAX_WORKERS`: Number of concurrent threads (default: 15)
- `SLEEP_BETWEEN_REQUESTS`: Random sleep between requests (default: 2-8 seconds)
- `ROTATE_EVERY_N`: Rotate Tor identity every N requests (default: 25)

## Testing

Run the test script to verify the keyword search functionality:

```bash
python test_keyword_search.py
```

## Requirements

- Python 3.6+
- Tor running on localhost:9050
- Required Python packages (install via pip):
  - requests
  - beautifulsoup4
  - urllib3

## Security Notes

- Always use this tool through Tor for anonymity
- The tool includes keywords related to illegal content for research purposes
- Use responsibly and in accordance with local laws
- Consider the ethical implications of automated crawling

## Disclaimer

This tool is for research and educational purposes only. Users are responsible for complying with all applicable laws and regulations. The authors are not responsible for any misuse of this tool. 