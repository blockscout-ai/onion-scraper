#!/usr/bin/env python3
"""
Script to clean up crypto_addresses_fast.csv to contain only base domains
instead of full URLs with paths.
"""

import csv
import os
from urllib.parse import urlparse
import shutil
from datetime import datetime

def get_base_domain(url):
    """Extract just the base domain from a URL"""
    try:
        parsed = urlparse(url)
        return parsed.hostname or url
    except:
        return url

def clean_csv_urls(input_file="crypto_addresses_fast.csv", backup=True):
    """Clean up CSV file to contain only base domains"""
    
    if not os.path.exists(input_file):
        print(f"❌ Input file {input_file} not found!")
        return
    
    # Create backup
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{input_file}.backup_{timestamp}"
        shutil.copy2(input_file, backup_file)
        print(f"✅ Created backup: {backup_file}")
    
    # Read the original file
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:  # Skip empty rows
                # Clean the URL (first column)
                if len(row) > 0:
                    original_url = row[0]
                    base_domain = get_base_domain(original_url)
                    row[0] = base_domain
                    rows.append(row)
    
    # Write back to the file
    with open(input_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    print(f"✅ Cleaned {len(rows)} rows in {input_file}")
    print(f"   URLs now contain only base domains (e.g., 'example.onion' instead of 'http://example.onion/payment/buy')")

def main():
    print("🧹 CSV URL Cleanup Script")
    print("=" * 50)
    
    # Check if file exists
    if not os.path.exists("crypto_addresses_fast.csv"):
        print("❌ crypto_addresses_fast.csv not found in current directory")
        return
    
    # Get file size before
    file_size_before = os.path.getsize("crypto_addresses_fast.csv")
    
    # Clean the file
    clean_csv_urls()
    
    # Get file size after
    file_size_after = os.path.getsize("crypto_addresses_fast.csv")
    
    print(f"\n📊 File size: {file_size_before:,} bytes → {file_size_after:,} bytes")
    print(f"   Reduction: {file_size_before - file_size_after:,} bytes")
    
    print("\n✅ Cleanup complete!")

if __name__ == "__main__":
    main() 