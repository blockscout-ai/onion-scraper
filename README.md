# Onion Scraper 2

A comprehensive system for discovering, scraping, and analyzing onion sites with advanced AI/ML capabilities for content classification and cryptocurrency address extraction.

## 🚀 Quick Start

```bash
# Run the main scraper
python run.py scraper --resume --verbose

# Discover new onion sites
python run.py discovery --no-search

# Start the API server
python run.py api --port 8000

# Check for duplicates in your data
python run.py utils check-duplicates
```

## 📁 Project Structure

The project has been organized for easy navigation and maintenance:

```
onion_scraper_2/
├── run.py                    # 🎯 Main entry point - start here!
├── src/                      # Source code
│   ├── core/                 # Core scraping functionality
│   ├── agents/               # AI/ML agents
│   ├── discovery/            # Onion discovery tools
│   ├── analysis/             # Content analysis
│   ├── utils/                # Utility functions
│   ├── api/                  # API server
│   └── frontend/             # Frontend files
├── data/                     # Data files
│   ├── raw/                  # Raw data (CSVs, screenshots)
│   ├── processed/            # Processed data (JSONs)
│   └── archives/             # Historical data
├── config/                   # Configuration files
├── logs/                     # Log files
├── docs/                     # Documentation
├── scripts/                  # Utility scripts
└── tests/                    # Test files
```

## 🎯 Main Features

### Core Functionality
- **High-performance scraping** with parallel processing
- **Intelligent onion discovery** using search engines and crawling
- **Content classification** for CSAM, trafficking, and scam detection
- **Cryptocurrency address extraction** from multiple chains
- **Screenshot capture** for visual analysis

### AI/ML Capabilities
- **Learning agents** that improve over time
- **Pattern recognition** for transaction analysis
- **Content signature analysis** for classification
- **Smart interaction handling** for complex sites

### Data Management
- **Google Drive integration** for data storage
- **Automated backups** and archiving
- **Duplicate detection** and cleanup
- **Data validation** and quality checks

## 📖 Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get up and running fast
- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Detailed structure explanation
- **[API Documentation](src/frontend/FRONTEND_README.md)** - API usage guide

## 🛠️ Installation

1. **Install dependencies**
   ```bash
   pip install -r config/requirements.txt
   ```

2. **Set up environment**
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env with your settings
   ```

3. **Start Tor service**
   ```bash
   tor
   ```

## 🚀 Usage Examples

### Basic Scraping
```bash
# Run the main scraper
python run.py scraper

# Resume from where you left off
python run.py scraper --resume

# Verbose output for debugging
python run.py scraper --verbose
```

### Discovery
```bash
# Discover new onion sites
python run.py discovery

# Skip keyword search (faster)
python run.py discovery --no-search
```

### API Server
```bash
# Start API server
python run.py api

# Custom port
python run.py api --port 8080

# Debug mode
python run.py api --debug
```

### Utilities
```bash
# Check for duplicate addresses
python run.py utils check-duplicates

# Check address coverage
python run.py utils check-coverage

# Clean CSV URLs
python run.py utils clean-urls
```

### Maintenance
```bash
# Optimize AI agents
python run.py maintenance optimize-agents

# Clean up unused code
python run.py maintenance cleanup-code

# Fix Google Drive issues
python run.py maintenance fix-trash
```

### Google Drive Integration
```bash
# Upload screenshots
python run.py utilities upload-screenshots

# Manage Google Drive
python run.py utilities gdrive-manager

# Test Google Sheets
python run.py utilities test-sheets
```

## 📊 Data Organization

### Raw Data (`data/raw/`)
- CSV files with scraped data
- Screenshot images
- Debug HTML files
- Captcha images

### Processed Data (`data/processed/`)
- JSON files with processed data
- Knowledge bases
- Learning patterns
- Configuration files

### Logs (`logs/`)
- Debug logs: `logs/debug/`
- Error logs: `logs/errors/`
- Progress logs: `logs/progress/`

## ⚙️ Configuration

### Main Settings (`config/settings.py`)
```python
# Tor configuration
TOR_SOCKS_PROXY = 'socks5h://127.0.0.1:9050'
TOR_CONTROL_PORT = 9051

# Scraping settings
MAX_WORKERS = 15
SLEEP_BETWEEN_REQUESTS = (2, 8)
MAX_DEPTH = 4
```

### Environment Variables (`config/.env`)
```bash
TOR_CONTROL_PASSWORD=your_password
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
API_HOST=localhost
API_PORT=8000
```

## 🔧 Troubleshooting

### Common Issues

1. **Tor connection failed**
   - Ensure Tor service is running
   - Check `config/settings.py` for correct proxy settings

2. **Import errors**
   - Make sure you're in the project root directory
   - Install dependencies: `pip install -r config/requirements.txt`

3. **File not found**
   - Check if files were moved to new locations
   - Use `config/settings.py` for file paths

### Getting Help

1. **Check logs**: Look in `logs/` directory
2. **Review documentation**: See `docs/` directory
3. **Check configuration**: Verify `config/settings.py`

## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/
```

## 📈 Performance

- **Parallel processing** with configurable worker count
- **Smart rate limiting** to avoid detection
- **Memory management** with automatic cleanup
- **Disk space monitoring** to prevent overflow

## 🔒 Security

- **Tor integration** for anonymous access
- **Content filtering** for sensitive material
- **Encrypted storage** options
- **Access control** for API endpoints

## 🤝 Contributing

1. Follow the project structure
2. Add tests for new features
3. Update documentation
4. Use the centralized configuration

## 📄 License

This project is for law enforcement and research purposes only.

## 🆘 Support

- Check `docs/` for detailed documentation
- Review `logs/` for error information
- Use `scripts/maintenance/` for troubleshooting tools

---

**🎯 Start with `python run.py help` to see all available commands!** 