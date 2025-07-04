#!/usr/bin/env python3
"""
Main entry point for the Onion Scraper 2 system.
This script provides easy access to all main functionality.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def main():
    parser = argparse.ArgumentParser(
        description="Onion Scraper 2 - Main Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py scraper --resume --verbose
  python run.py discovery --no-search
  python run.py api --port 8080
  python run.py utils check-duplicates
  python run.py maintenance optimize-agents
        """
    )
    
    parser.add_argument('command', choices=[
        'scraper', 'discovery', 'api', 'agents', 'analysis', 
        'utils', 'maintenance', 'utilities', 'help'
    ], help='Main command to run')
    
    parser.add_argument('subcommand', nargs='?', help='Subcommand for utils/maintenance/utilities')
    
    # Scraper options
    parser.add_argument('--resume', action='store_true', help='Resume from previous state')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--quiet', action='store_true', help='Enable quiet logging')
    parser.add_argument('--no-search', action='store_true', help='Skip keyword search phase')
    
    # API options
    parser.add_argument('--host', default='localhost', help='API host (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='API port (default: 8000)')
    parser.add_argument('--debug', action='store_true', help='Enable API debug mode')
    
    args = parser.parse_args()
    
    if args.command == 'help':
        parser.print_help()
        return
    
    try:
        if args.command == 'scraper':
            run_scraper(args)
        elif args.command == 'discovery':
            run_discovery(args)
        elif args.command == 'api':
            run_api(args)
        elif args.command == 'agents':
            run_agents(args)
        elif args.command == 'analysis':
            run_analysis(args)
        elif args.command == 'utils':
            run_utils(args)
        elif args.command == 'maintenance':
            run_maintenance(args)
        elif args.command == 'utilities':
            run_utilities(args)
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the project root directory and dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running {args.command}: {e}")
        sys.exit(1)

def run_scraper(args):
    """Run the main scraper"""
    print("🚀 Starting Onion Scraper...")
    
    # Build command line arguments
    cmd_args = []
    if args.resume:
        cmd_args.append('--resume')
    if args.verbose:
        cmd_args.append('--verbose')
    if args.quiet:
        cmd_args.append('--quiet')
    if args.no_search:
        cmd_args.append('--no-search')
    
    # Import and run scraper
    from core.scraper_fast import main as scraper_main
    scraper_main()

def run_discovery(args):
    """Run onion discovery"""
    print("🔍 Starting Onion Discovery...")
    
    # Build command line arguments
    cmd_args = []
    if args.resume:
        cmd_args.append('--resume')
    if args.verbose:
        cmd_args.append('--verbose')
    if args.quiet:
        cmd_args.append('--quiet')
    if args.no_search:
        cmd_args.append('--no-search')
    
    # Import and run discovery
    from discovery.onion_discovery import crawl, SEED_URLS, MAX_DEPTH
    crawl(SEED_URLS, MAX_DEPTH, resume=args.resume, no_search=args.no_search)

def run_api(args):
    """Run the API server"""
    print(f"🌐 Starting API server on {args.host}:{args.port}...")
    
    # Import and run API server
    from api.api_server import app
    import uvicorn
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug
    )

def run_agents(args):
    """Run AI agents"""
    print("🤖 Starting AI Agents...")
    
    # Import and run agents
    from agents.integrated_agent_system_optimized import main as agent_main
    agent_main()

def run_analysis(args):
    """Run analysis tools"""
    print("📊 Starting Analysis Tools...")
    
    # Import and run analysis
    from analysis.multi_step_transaction_learner import main as analysis_main
    analysis_main()

def run_utils(args):
    """Run utility functions"""
    if not args.subcommand:
        print("❌ Please specify a utility subcommand:")
        print("  check-duplicates")
        print("  check-coverage")
        print("  clean-urls")
        print("  sort-titles")
        print("  migrate-data")
        return
    
    print(f"🔧 Running utility: {args.subcommand}")
    
    if args.subcommand == 'check-duplicates':
        from utils.check_duplicates import main as util_main
        util_main()
    elif args.subcommand == 'check-coverage':
        from utils.check_address_coverage import main as util_main
        util_main()
    elif args.subcommand == 'clean-urls':
        from utils.clean_csv_urls import main as util_main
        util_main()
    elif args.subcommand == 'sort-titles':
        from utils.sort_onion_titles import main as util_main
        util_main()
    elif args.subcommand == 'migrate-data':
        from utils.migrate_extraction_data import main as util_main
        util_main()
    else:
        print(f"❌ Unknown utility: {args.subcommand}")

def run_maintenance(args):
    """Run maintenance scripts"""
    if not args.subcommand:
        print("❌ Please specify a maintenance subcommand:")
        print("  cleanup-code")
        print("  optimize-codebase")
        print("  optimize-agents")
        print("  fix-trash")
        return
    
    print(f"🔧 Running maintenance: {args.subcommand}")
    
    if args.subcommand == 'cleanup-code':
        from scripts.maintenance.cleanup_unused_code import main as maint_main
        maint_main()
    elif args.subcommand == 'optimize-codebase':
        from scripts.maintenance.optimize_codebase import main as maint_main
        maint_main()
    elif args.subcommand == 'optimize-agents':
        from scripts.maintenance.optimize_ai_agents import main as maint_main
        maint_main()
    elif args.subcommand == 'fix-trash':
        from scripts.maintenance.fix_trash_recovery import main as maint_main
        maint_main()
    else:
        print(f"❌ Unknown maintenance command: {args.subcommand}")

def run_utilities(args):
    """Run utility scripts"""
    if not args.subcommand:
        print("❌ Please specify a utility script subcommand:")
        print("  upload-screenshots")
        print("  gdrive-manager")
        print("  test-sheets")
        print("  fix-sheets")
        print("  sheets-pipeline")
        return
    
    print(f"🔧 Running utility script: {args.subcommand}")
    
    if args.subcommand == 'upload-screenshots':
        from scripts.utilities.upload_existing_screenshots import main as util_main
        util_main()
    elif args.subcommand == 'gdrive-manager':
        from scripts.utilities.gdrive_screenshot_manager import main as util_main
        util_main()
    elif args.subcommand == 'test-sheets':
        from scripts.utilities.test_google_sheets import main as util_main
        util_main()
    elif args.subcommand == 'fix-sheets':
        from scripts.utilities.fix_google_sheets import main as util_main
        util_main()
    elif args.subcommand == 'sheets-pipeline':
        from scripts.utilities.google_sheets_pipeline import main as util_main
        util_main()
    else:
        print(f"❌ Unknown utility script: {args.subcommand}")

if __name__ == "__main__":
    main() 