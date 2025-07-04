# Quick Start Guide

This guide will help you get started with the reorganized Onion Scraper 2 project.

## Prerequisites

1. Python 3.8 or higher
2. Tor browser/service running
3. Required Python packages (see `config/requirements.txt`)

## Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd onion_scraper_2
   ```

2. **Install dependencies**
   ```bash
   pip install -r config/requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env with your settings
   ```

4. **Ensure Tor is running**
   ```bash
   # Start Tor service
   tor
   ```

## Basic Usage

### Running the Main Scraper

```bash
# Run the fast scraper
python src/core/scraper_fast.py

# Run with specific options
python src/core/scraper_fast.py --resume --verbose
```

### Running Onion Discovery

```bash
# Discover new onion sites
python src/discovery/onion_discovery.py

# With options
python src/discovery/onion_discovery.py --resume --no-search
```

### Using the API Server

```bash
# Start the API server
python src/api/api_server.py

# Access the API at http://localhost:8000
```

## Finding Your Data

### Raw Data (CSVs, Screenshots)
- **Location**: `data/raw/`
- **Files**: All CSV files, screenshots, debug HTML
- **Example**: `data/raw/human_trafficking_alerts_0702.csv`

### Processed Data (JSONs, Databases)
- **Location**: `data/processed/`
- **Files**: Knowledge bases, learning patterns, configuration
- **Example**: `data/processed/knowledge_base.json`

### Logs
- **Debug logs**: `logs/debug/`
- **Error logs**: `logs/errors/`
- **Progress logs**: `logs/progress/`

## Common Tasks

### 1. Check Data Coverage
```bash
python src/utils/check_address_coverage.py
```

### 2. Find Duplicates
```bash
python src/utils/check_duplicates.py
```

### 3. Clean CSV URLs
```bash
python src/utils/clean_csv_urls.py
```

### 4. Upload Screenshots to Google Drive
```bash
python scripts/utilities/upload_existing_screenshots.py
```

### 5. Optimize AI Agents
```bash
python scripts/maintenance/optimize_ai_agents.py
```

## Configuration

### Main Settings
Edit `config/settings.py` for application-wide settings:

```python
# Tor configuration
TOR_SOCKS_PROXY = 'socks5h://127.0.0.1:9050'
TOR_CONTROL_PORT = 9051

# Scraping settings
MAX_WORKERS = 15
SLEEP_BETWEEN_REQUESTS = (2, 8)
MAX_DEPTH = 4
```

### Environment Variables
Edit `config/.env` for sensitive settings:

```bash
TOR_CONTROL_PASSWORD=your_password
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
API_HOST=localhost
API_PORT=8000
```

## Troubleshooting

### Common Issues

1. **Tor connection failed**
   - Ensure Tor service is running
   - Check `config/settings.py` for correct proxy settings

2. **Import errors**
   - Update import paths to use new structure
   - Use relative imports from `src/` directory

3. **File not found**
   - Check if files were moved to new locations
   - Use `config/settings.py` for file paths

### Getting Help

1. **Check logs**: Look in `logs/` directory
2. **Review documentation**: See `docs/` directory
3. **Check configuration**: Verify `config/settings.py`

## Advanced Usage

### Running Agents
```bash
# Learning agent
python src/agents/learning_agent.py

# Fixer agent
python src/agents/fixer_agent.py

# Integrated system
python src/agents/integrated_agent_system.py
```

### Analysis Tools
```bash
# Transaction learning
python src/analysis/multi_step_transaction_learner.py

# Content signatures
python src/analysis/enhanced_content_signatures.py
```

### Maintenance Scripts
```bash
# Clean up unused code
python scripts/maintenance/cleanup_unused_code.py

# Optimize codebase
python scripts/maintenance/optimize_codebase.py
```

## Data Flow

1. **Discovery**: `src/discovery/onion_discovery.py` finds new sites
2. **Scraping**: `src/core/scraper_fast.py` extracts data
3. **Analysis**: `src/analysis/` processes content
4. **Storage**: Data saved to `data/raw/` and `data/processed/`
5. **Export**: Use scripts in `scripts/utilities/` for Google Drive upload

## Next Steps

1. **Read the full documentation**: `docs/PROJECT_STRUCTURE.md`
2. **Explore the API**: Check `src/frontend/FRONTEND_README.md`
3. **Run tests**: Use files in `tests/` directory
4. **Customize configuration**: Modify `config/settings.py`

## Support

- Check `docs/` for detailed documentation
- Review `logs/` for error information
- Use `scripts/maintenance/` for troubleshooting tools 