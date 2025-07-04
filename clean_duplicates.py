#!/usr/bin/env python3
"""
Script to clean up duplicate entries in discovered_onions CSV files
and demonstrate the enhanced duplicate prevention functionality.
"""

import csv
import os
import glob
from urllib.parse import urlparse
import re

def extract_clean_onion(domain):
    """Extract clean onion domain from URL."""
    # Try the strict 56-character format first
    match = re.search(r"([a-z2-7]{56})\.onion", domain)
    if match:
        return match.group(0)
    
    # Try shorter onion addresses (some are 16 characters)
    match = re.search(r"([a-z2-7]{16})\.onion", domain)
    if match:
        return match.group(0)
    
    # Try any onion address format
    match = re.search(r"([a-z2-7]{10,56})\.onion", domain)
    if match:
        return match.group(0)
    
    return None

def clean_csv_file(filename):
    """Remove duplicates from a CSV file."""
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found")
        return
    
    print(f"🔍 Cleaning duplicates from {filename}...")
    
    # Read all rows
    rows = []
    seen_onions = set()
    duplicates_found = 0
    total_rows = 0
    
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Keep header
            rows.append(header)
            
            for row in reader:
                total_rows += 1
                if len(row) > 0:
                    onion_url = row[0]
                    parsed_url = urlparse(onion_url)
                    if parsed_url.hostname:
                        clean_onion = extract_clean_onion(parsed_url.hostname)
                        if clean_onion and clean_onion not in seen_onions:
                            seen_onions.add(clean_onion)
                            rows.append(row)
                        elif clean_onion:
                            duplicates_found += 1
                            print(f"⚠️  Found duplicate: {clean_onion}")
                    else:
                        rows.append(row)  # Keep rows without valid onion URLs
                else:
                    rows.append(row)  # Keep empty rows
        
        # Write back the deduplicated data
        if duplicates_found > 0:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            print(f"✅ Removed {duplicates_found} duplicates from {filename}")
            print(f"📊 Before: {total_rows} rows, After: {len(rows)-1} rows (excluding header)")
        else:
            print(f"✅ No duplicates found in {filename}")
            
    except Exception as e:
        print(f"❌ Error cleaning {filename}: {e}")

def analyze_csv_file(filename):
    """Analyze a CSV file for duplicates and statistics."""
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found")
        return
    
    print(f"📊 Analyzing {filename}...")
    
    seen_onions = set()
    duplicate_onions = set()
    total_rows = 0
    valid_rows = 0
    
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header
            
            for row in reader:
                total_rows += 1
                if len(row) > 0:
                    onion_url = row[0]
                    parsed_url = urlparse(onion_url)
                    if parsed_url.hostname:
                        clean_onion = extract_clean_onion(parsed_url.hostname)
                        if clean_onion:
                            valid_rows += 1
                            if clean_onion in seen_onions:
                                duplicate_onions.add(clean_onion)
                            else:
                                seen_onions.add(clean_onion)
        
        print(f"📈 Statistics for {filename}:")
        print(f"   Total rows: {total_rows}")
        print(f"   Valid onion URLs: {valid_rows}")
        print(f"   Unique onions: {len(seen_onions)}")
        print(f"   Duplicate onions: {len(duplicate_onions)}")
        
        if duplicate_onions:
            print(f"   Duplicate onion domains:")
            for onion in sorted(duplicate_onions):
                print(f"     - {onion}")
            
    except Exception as e:
        print(f"❌ Error analyzing {filename}: {e}")

def main():
    """Main function to clean and analyze CSV files."""
    print("🧹 CSV Duplicate Cleaner")
    print("=" * 50)
    
    # Find all discovery CSV files
    csv_files = glob.glob("discovered_onions_*.csv")
    
    if not csv_files:
        print("❌ No discovered_onions CSV files found")
        return
    
    print(f"📁 Found {len(csv_files)} CSV files:")
    for f in csv_files:
        print(f"   - {f}")
    
    print("\n" + "=" * 50)
    
    # Analyze each file first
    for filename in csv_files:
        analyze_csv_file(filename)
        print()
    
    print("=" * 50)
    
    # Ask user if they want to clean duplicates
    response = input("🧹 Do you want to remove duplicates from these files? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print("\n🧹 Cleaning duplicates...")
        for filename in csv_files:
            clean_csv_file(filename)
            print()
        
        print("✅ Duplicate cleaning completed!")
        
        # Show final statistics
        print("\n📊 Final statistics:")
        for filename in csv_files:
            analyze_csv_file(filename)
            print()
    else:
        print("⏭️  Skipping duplicate removal")

if __name__ == "__main__":
    main() 