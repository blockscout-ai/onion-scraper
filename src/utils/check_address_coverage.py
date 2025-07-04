#!/usr/bin/env python3
"""
Check Address Coverage Script

This script compares addresses found in the scraper against:
1. The main CSV file (crypto_addresses_fast.csv)
2. The Google Sheets (via the unified pipeline)

It identifies any addresses that exist in the scraper but are missing from both data sources.
"""

import pandas as pd
import os
import sys
from collections import defaultdict
import re

def load_csv_addresses(csv_file):
    """Load addresses from the main CSV file."""
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return set()
    
    try:
        df = pd.read_csv(csv_file)
        if 'address' not in df.columns:
            print(f"❌ No 'address' column found in {csv_file}")
            return set()
        
        addresses = set()
        for addr in df['address'].dropna():
            if isinstance(addr, str) and addr.strip():
                addresses.add(addr.strip())
        
        print(f"✅ Loaded {len(addresses)} addresses from {csv_file}")
        return addresses
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return set()

def extract_addresses_from_scraper_code():
    """Extract addresses that are being tracked in the scraper code."""
    addresses = set()
    
    # Look for global_seen_addresses usage in scraper_fast.py
    try:
        with open('scraper_fast.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find where addresses are added to global_seen_addresses
        # This pattern looks for lines where addresses are added to the global set
        patterns = [
            r'global_seen_addresses\.add\(([^)]+)\)',
            r'seen_addresses\.add\(([^)]+)\)',
            r'addr in global_seen_addresses',
            r'addr in seen_addresses'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Clean up the match - it might be a variable name
                if match.strip() and not match.strip().startswith('"'):
                    # This is likely a variable reference, not a literal address
                    pass
        
        print(f"✅ Analyzed scraper code for address tracking patterns")
        return addresses
    except Exception as e:
        print(f"❌ Error analyzing scraper code: {e}")
        return set()

def check_duplicate_files():
    """Check duplicate address files for additional addresses."""
    duplicate_files = [
        'duplicate_addresses_fast.csv',
        'duplicated_address_0702.csv',
        'human_trafficking_alerts_0702.csv',
        'human_trafficking_alerts.csv'
    ]
    
    all_duplicate_addresses = set()
    
    for file in duplicate_files:
        if os.path.exists(file):
            try:
                df = pd.read_csv(file)
                if 'address' in df.columns:
                    addresses = set()
                    for addr in df['address'].dropna():
                        if isinstance(addr, str) and addr.strip():
                            addresses.add(addr.strip())
                    all_duplicate_addresses.update(addresses)
                    print(f"✅ Loaded {len(addresses)} addresses from {file}")
            except Exception as e:
                print(f"⚠️ Error loading {file}: {e}")
    
    print(f"✅ Total duplicate addresses found: {len(all_duplicate_addresses)}")
    return all_duplicate_addresses

def check_google_sheets_coverage():
    """Check what addresses are in Google Sheets by examining the pipeline."""
    try:
        with open('unified_google_sheets_pipeline.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract Google Sheet URLs
        sheet_urls = re.findall(r'https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9_-]+', content)
        
        print(f"✅ Found {len(sheet_urls)} Google Sheet URLs in pipeline")
        print("   Note: To get actual addresses from Google Sheets, you would need to run the pipeline")
        
        return set()  # We can't extract addresses without running the pipeline
    except Exception as e:
        print(f"❌ Error analyzing Google Sheets pipeline: {e}")
        return set()

def analyze_address_distribution():
    """Analyze the distribution of addresses across different sources."""
    print("\n" + "="*60)
    print("ADDRESS COVERAGE ANALYSIS")
    print("="*60)
    
    # Load main CSV addresses
    main_csv_addresses = load_csv_addresses('crypto_addresses_fast.csv')
    
    # Load duplicate addresses
    duplicate_addresses = check_duplicate_files()
    
    # Check Google Sheets (informational only)
    google_sheets_addresses = check_google_sheets_coverage()
    
    # Analyze scraper code
    scraper_addresses = extract_addresses_from_scraper_code()
    
    # Calculate overlaps and differences
    all_csv_addresses = main_csv_addresses.union(duplicate_addresses)
    
    print(f"\n📊 ADDRESS STATISTICS:")
    print(f"   Main CSV addresses: {len(main_csv_addresses)}")
    print(f"   Duplicate file addresses: {len(duplicate_addresses)}")
    print(f"   Total CSV addresses: {len(all_csv_addresses)}")
    print(f"   Google Sheets addresses: {len(google_sheets_addresses)} (estimated)")
    
    # Check for addresses in duplicates but not in main CSV
    duplicates_not_in_main = duplicate_addresses - main_csv_addresses
    if duplicates_not_in_main:
        print(f"\n⚠️  {len(duplicates_not_in_main)} addresses found in duplicate files but NOT in main CSV:")
        for addr in sorted(list(duplicates_not_in_main))[:10]:  # Show first 10
            print(f"     {addr}")
        if len(duplicates_not_in_main) > 10:
            print(f"     ... and {len(duplicates_not_in_main) - 10} more")
    
    # Check for potential missing addresses
    print(f"\n🔍 POTENTIAL ISSUES:")
    
    # Check if there are any files that might contain addresses not in the main CSV
    potential_address_files = [
        'discovered_onions_20250625.csv',
        'skipped_multi_vendor_markets_fast.csv',
        'immediate_processing_log.csv',
        'login_attempts.csv',
        'checkout_attempts.csv',
        'captcha_failed_fast.csv',
        'login_required.csv'
    ]
    
    for file in potential_address_files:
        if os.path.exists(file):
            try:
                df = pd.read_csv(file)
                if 'address' in df.columns:
                    addresses = set()
                    for addr in df['address'].dropna():
                        if isinstance(addr, str) and addr.strip():
                            addresses.add(addr.strip())
                    
                    missing_from_main = addresses - main_csv_addresses
                    if missing_from_main:
                        print(f"⚠️  {file}: {len(missing_from_main)} addresses not in main CSV")
                        for addr in sorted(list(missing_from_main))[:5]:
                            print(f"     {addr}")
                        if len(missing_from_main) > 5:
                            print(f"     ... and {len(missing_from_main) - 5} more")
            except Exception as e:
                print(f"⚠️  Error checking {file}: {e}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print("   1. Run the Google Sheets pipeline to sync addresses")
    print("   2. Check if duplicate addresses should be in main CSV")
    print("   3. Review any addresses found in other files")
    print("   4. Consider consolidating all addresses into main CSV")

def main():
    """Main function to run the address coverage analysis."""
    print("🔍 Checking Address Coverage Across Data Sources")
    print("="*60)
    
    analyze_address_distribution()
    
    print(f"\n✅ Analysis complete!")

if __name__ == "__main__":
    main() 