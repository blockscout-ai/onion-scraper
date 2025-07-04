#!/usr/bin/env python3
"""
Show summary of the consolidated onions file.
"""

import csv
import os

def show_consolidated_summary(filename):
    """Show summary of the consolidated file."""
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found")
        return
    
    print(f"📊 Summary of {filename}")
    print("=" * 60)
    
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            print(f"📋 Columns: {', '.join(header)}")
            print()
            
            # Count rows and show sample
            total_rows = 0
            sample_rows = []
            
            for row in reader:
                total_rows += 1
                if total_rows <= 5:  # Keep first 5 rows as sample
                    sample_rows.append(row)
            
            print(f"📈 Total rows: {total_rows:,}")
            print()
            
            print("📝 Sample rows:")
            print("-" * 60)
            for i, row in enumerate(sample_rows, 1):
                print(f"Row {i}:")
                print(f"  Onion URL: {row[0]}")
                print(f"  Source: {row[1][:80]}...")
                print(f"  Depth: {row[2]}")
                print(f"  Timestamp: {row[3]}")
                print(f"  Title: {row[4][:80]}...")
                print(f"  Discovery Count: {row[5]}")
                print(f"  Source Files: {row[6]}")
                print()
                
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    # Find the most recent consolidated file
    import glob
    consolidated_files = glob.glob("consolidated_onions_*.csv")
    
    if consolidated_files:
        latest_file = max(consolidated_files)  # Get the most recent one
        show_consolidated_summary(latest_file)
    else:
        print("❌ No consolidated files found") 