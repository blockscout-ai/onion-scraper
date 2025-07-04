# Project Structure Documentation

This document explains the organized structure of the Onion Scraper 2 project.

## Overview

The project has been reorganized into a logical, maintainable structure that separates concerns and makes it easier for humans to navigate and understand the codebase.

## Directory Structure

```
onion_scraper_2/
├── src/                          # Source code
│   ├── core/                     # Core scraping functionality
│   │   ├── scraper_fast.py       # Main fast scraper
│   │   ├── scraper.py           # Original scraper
│   │   └── scraper_worker.py    # Worker processes
│   ├── agents/                   # AI/ML agents
│   │   ├── learning_agent.py
│   │   ├── learning_agent_optimized.py
│   │   ├── fixer_agent.py
│   │   ├── fixer_agent_optimized.py
│   │   ├── integrated_agent_system.py
│   │   ├── integrated_agent_system_optimized.py
│   │   └── ml_learning_system.py
│   ├── discovery/                # Onion discovery tools
│   │   └── onion_discovery.py
│   ├── analysis/                 # Content analysis tools
│   │   ├── multi_step_transaction_learner.py
│   │   ├── enhanced_content_signatures.py
│   │   ├── smart_interaction_executor.py
│   │   ├── enhanced_error_handler.py
│   │   ├── quota_manager.py
│   │   └── learning_integration.py
│   ├── utils/                    # Utility functions
│   │   ├── temp_file_manager.py
│   │   ├── disk_space_monitor.py
│   │   ├── check_gdrive_access.py
│   │   ├── check_address_coverage.py
│   │   ├── check_duplicates.py
│   │   ├── sort_onion_titles.py
│   │   ├── clean_csv_urls.py
│   │   └── migrate_extraction_data.py
│   ├── api/                      # API server
│   │   └── api_server.py
│   └── frontend/                 # Frontend files
│       ├── frontend_example.html
│       └── FRONTEND_README.md
├── data/                         # Data files
│   ├── raw/                      # Raw data (CSVs, screenshots, HTML)
│   │   ├── *.csv                 # All CSV data files
│   │   ├── screenshots_fast/     # Screenshot images
│   │   ├── debug_html/           # Debug HTML files
│   │   └── unsolved_captchas_fast/ # Captcha images
│   ├── processed/                # Processed data (JSONs, databases)
│   │   ├── *.json               # All JSON data files
│   │   ├── knowledge_base.json
│   │   ├── extraction_data.json
│   │   └── learned_transaction_patterns.json
│   └── archives/                 # Archived data
│       ├── discovered_onions_archive/
│       └── addresses_archive/
├── logs/                         # Log files
│   ├── debug/                    # Debug logs
│   ├── errors/                   # Error logs
│   └── progress/                 # Progress tracking logs
├── config/                       # Configuration files
│   ├── config.py                 # Original config
│   ├── settings.py               # Centralized settings
│   ├── .env                      # Environment variables
│   ├── requirements.txt          # Python dependencies
│   └── api_requirements.txt      # API-specific dependencies
├── backups/                      # Backup files
│   ├── daily/                    # Daily backups
│   └── weekly/                   # Weekly backups
├── docs/                         # Documentation
│   ├── README.md                 # Main README
│   ├── PROJECT_STRUCTURE.md      # This file
│   ├── api/                      # API documentation
│   ├── user_guides/              # User guides
│   └── technical/                # Technical documentation
├── tests/                        # Test files
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── scripts/                      # Utility scripts
│   ├── maintenance/              # Maintenance scripts
│   │   ├── cleanup_unused_code.py
│   │   ├── optimize_codebase.py
│   │   ├── optimize_ai_agents.py
│   │   ├── fix_trash_recovery.py
│   │   └── selective_recovery.sh
│   └── utilities/                # Utility scripts
│       ├── upload_existing_screenshots.py
│       ├── gdrive_screenshot_manager.py
│       ├── test_google_sheets.py
│       ├── fix_google_sheets.py
│       ├── google_sheets_pipeline.py
│       └── unified_google_sheets_pipeline.py
└── service_account.json          # Google service account (root level for security)
```

## File Categories

### Core Scraping (`src/core/`)
- **scraper_fast.py**: Main high-performance scraper
- **scraper.py**: Original scraper implementation
- **scraper_worker.py**: Worker processes for parallel scraping

### AI Agents (`src/agents/`)
- **learning_agent.py**: Machine learning agent for pattern recognition
- **fixer_agent.py**: Agent for fixing common issues
- **integrated_agent_system.py**: Combined agent system
- All optimized versions for better performance

### Discovery (`src/discovery/`)
- **onion_discovery.py**: Onion site discovery and crawling

### Analysis (`src/analysis/`)
- **multi_step_transaction_learner.py**: Transaction pattern learning
- **enhanced_content_signatures.py**: Content signature analysis
- **smart_interaction_executor.py**: Smart interaction handling
- **enhanced_error_handler.py**: Advanced error handling
- **quota_manager.py**: Rate limiting and quota management

### Utilities (`src/utils/`)
- **temp_file_manager.py**: Temporary file management
- **disk_space_monitor.py**: Disk space monitoring
- **check_gdrive_access.py**: Google Drive access verification
- **check_address_coverage.py**: Address coverage analysis
- **check_duplicates.py**: Duplicate detection
- Various data cleaning and processing utilities

### Data Organization

#### Raw Data (`data/raw/`)
- CSV files with scraped data
- Screenshot images
- Debug HTML files
- Captcha images

#### Processed Data (`data/processed/`)
- JSON files with processed data
- Knowledge bases
- Learning patterns
- Configuration files

#### Archives (`data/archives/`)
- Historical data backups
- Old discovery results
- Previous address collections

### Configuration (`config/`)
- **settings.py**: Centralized configuration (NEW)
- **config.py**: Original configuration
- **.env**: Environment variables
- **requirements.txt**: Dependencies

### Scripts (`scripts/`)
- **maintenance/**: Code cleanup, optimization, recovery
- **utilities/**: Google Drive integration, data processing

## How to Use This Structure

### For Developers
1. **Core functionality**: Look in `src/core/`
2. **AI/ML features**: Check `src/agents/` and `src/analysis/`
3. **Configuration**: Use `config/settings.py` for centralized config
4. **Utilities**: Find helper functions in `src/utils/`

### For Data Analysis
1. **Raw data**: Check `data/raw/` for CSV files and screenshots
2. **Processed data**: Look in `data/processed/` for JSON files
3. **Historical data**: Check `data/archives/`

### For Maintenance
1. **Cleanup scripts**: Use `scripts/maintenance/`
2. **Utility scripts**: Check `scripts/utilities/`
3. **Backups**: Find in `backups/`

### For Configuration
1. **Environment variables**: Edit `config/.env`
2. **Application settings**: Modify `config/settings.py`
3. **Dependencies**: Update `config/requirements.txt`

## Benefits of This Structure

1. **Separation of Concerns**: Each directory has a specific purpose
2. **Easy Navigation**: Humans can quickly find what they need
3. **Maintainability**: Related files are grouped together
4. **Scalability**: Easy to add new components
5. **Documentation**: Clear structure is self-documenting
6. **Testing**: Dedicated test directories
7. **Configuration**: Centralized settings management

## Migration Notes

- All original functionality is preserved
- File paths in code may need updates to use new structure
- Use `config/settings.py` for new configuration
- Import paths should be updated to reflect new structure

## Next Steps

1. Update import statements in Python files to use new paths
2. Update configuration references to use `config/settings.py`
3. Create additional documentation in `docs/`
4. Add unit tests in `tests/unit/`
5. Set up CI/CD pipeline configuration 