#!/usr/bin/env python3
"""
Script to sort crypto_addresses_fast.csv so that entries with ".onion" in the title
are moved to the top for easy identification of problematic entries.
"""

import csv
import os
import shutil
from datetime import datetime

def sort_csv_by_onion_titles(input_file="crypto_addresses_fast.csv", backup=True):
    """Sort CSV file to put entries with '.onion' in title at the top"""
    
    if not os.path.exists(input_file):
        print(f"❌ Input file {input_file} not found!")
        return
    
    # Create backup
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{input_file}.backup_{timestamp}"
        shutil.copy2(input_file, backup_file)
        print(f"✅ Created backup: {backup_file}")
    
    # Read all rows
    rows = []
    onion_title_rows = []
    other_rows = []
    
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  # Get header row
        
        for row in reader:
            if len(row) >= 2:  # Ensure we have at least URL and title columns
                title = row[1].lower() if row[1] else ""
                if ".onion" in title:
                    onion_title_rows.append(row)
                else:
                    other_rows.append(row)
            else:
                other_rows.append(row)  # Keep malformed rows at bottom
    
    # Combine rows: onion titles first, then others
    sorted_rows = onion_title_rows + other_rows
    
    # Write back to file
    with open(input_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(sorted_rows)
    
    print(f"✅ Sorted {len(sorted_rows)} rows in {input_file}")
    print(f"   📊 Entries with '.onion' in title: {len(onion_title_rows)}")
    print(f"   📊 Other entries: {len(other_rows)}")
    
    if len(onion_title_rows) > 0:
        print(f"\n🔍 First few entries with '.onion' in title:")
        for i, row in enumerate(onion_title_rows[:5]):
            title = row[1] if len(row) > 1 else "No title"
            url = row[0] if len(row) > 0 else "No URL"
            print(f"   {i+1}. Title: '{title}' | URL: {url}")
    
    print(f"\n✅ Sorting complete!")

if __name__ == "__main__":
    print("🔄 CSV Title Sorting Script")
    print("=" * 50)
    sort_csv_by_onion_titles() 