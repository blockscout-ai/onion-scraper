#!/usr/bin/env python3
"""
Script to check for duplicate addresses between Google Sheet darknet_automation tab 
and crypto_addresses_fast.csv file, then create a file with the duplicates.
"""

import gspread
import pandas as pd
import os
import csv
from datetime import datetime

# Configuration
SERVICE_ACCOUNT_FILE = '/Users/jasoncomer/Desktop/blockscout_python/ofac-automation-52b699a4735a.json'
GOOGLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/14ApkAb5jHTv-wzP8CFJTax31UXYkFb0ebDDd6Bg1EC8/edit#gid=1998112463'
SHEET_NAME = 'darknet_automation'
CSV_FILE = 'crypto_addresses_fast.csv'
DUPLICATES_FILE = 'duplicated_address_0702.csv'

def authenticate_gsheets():
    """Authenticate with Google Sheets using the service account."""
    try:
        print("🔑 Authenticating with Google Sheets...")
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        print("✅ Authentication successful.")
        return gc
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def get_google_sheet_addresses(gc):
    """Get all addresses from the Google Sheet darknet_automation tab."""
    try:
        print(f"📄 Opening Google Sheet: '{SHEET_NAME}'")
        workbook = gc.open_by_url(GOOGLE_SHEET_URL)
        worksheet = workbook.worksheet(SHEET_NAME)
        
        # Get all values from the sheet
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            print("⚠️  Google Sheet appears to be empty or has no data rows.")
            return set()
        
        # Find the deposit_address column index
        header_row = all_values[1]  # Row 2 (0-indexed)
        try:
            address_col_index = header_row.index('deposit_address')
        except ValueError:
            print("❌ Could not find 'deposit_address' column in Google Sheet")
            return set()
        
        # Extract addresses from the column (skip header rows)
        addresses = set()
        for row in all_values[2:]:  # Skip first two rows (headers)
            if len(row) > address_col_index and row[address_col_index].strip():
                addresses.add(row[address_col_index].strip())
        
        print(f"✅ Found {len(addresses)} unique addresses in Google Sheet")
        return addresses
        
    except Exception as e:
        print(f"❌ Error reading Google Sheet: {e}")
        return set()

def get_csv_addresses():
    """Get all addresses from the CSV file."""
    try:
        if not os.path.exists(CSV_FILE):
            print(f"❌ CSV file '{CSV_FILE}' not found")
            return set()
        
        print(f"📥 Reading addresses from '{CSV_FILE}'...")
        
        # Use a more robust CSV reader to handle malformed data
        addresses = set()
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            header = next(csv_reader)  # Skip header
            
            # Find the address column index
            try:
                address_col_index = header.index('address')
            except ValueError:
                print("❌ 'address' column not found in CSV file")
                return set()
            
            for row_num, row in enumerate(csv_reader, start=2):
                if len(row) > address_col_index:
                    address = row[address_col_index].strip()
                    if address and address != 'nan':
                        addresses.add(address)
        
        print(f"✅ Found {len(addresses)} unique addresses in CSV file")
        return addresses
        
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return set()

def find_duplicates(google_addresses, csv_addresses):
    """Find addresses that exist in both Google Sheet and CSV."""
    duplicates = google_addresses.intersection(csv_addresses)
    print(f"🔍 Found {len(duplicates)} duplicate addresses")
    return duplicates

def create_duplicates_file(duplicate_addresses, google_addresses, csv_addresses):
    """Create a CSV file with the duplicate addresses in the same format as crypto_addresses_fast.csv."""
    try:
        # Read the original CSV using csv reader to handle malformed data
        duplicate_rows = []
        
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            header = next(csv_reader)  # Get header
            
            # Find column indices
            try:
                address_col_index = header.index('address')
            except ValueError:
                print("❌ 'address' column not found in CSV file")
                return
            
            # Read all rows and filter for duplicates
            for row in csv_reader:
                if len(row) > address_col_index:
                    address = row[address_col_index].strip()
                    if address in duplicate_addresses:
                        duplicate_rows.append(row)
        
        if not duplicate_rows:
            print("⚠️  No duplicate rows found to write to file")
            return
        
        # Write to the duplicates file with the same header
        with open(DUPLICATES_FILE, 'w', newline='', encoding='utf-8') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(header)  # Write header
            csv_writer.writerows(duplicate_rows)  # Write duplicate rows
        
        print(f"✅ Created '{DUPLICATES_FILE}' with {len(duplicate_rows)} duplicate rows")
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"   - Google Sheet addresses: {len(google_addresses)}")
        print(f"   - CSV file addresses: {len(csv_addresses)}")
        print(f"   - Duplicate addresses: {len(duplicate_addresses)}")
        print(f"   - Duplicate rows written to: {DUPLICATES_FILE}")
        
        # Show some examples of duplicates
        if len(duplicate_addresses) > 0:
            print(f"\n🔍 Sample duplicate addresses:")
            for i, addr in enumerate(list(duplicate_addresses)[:5]):
                print(f"   {i+1}. {addr}")
            if len(duplicate_addresses) > 5:
                print(f"   ... and {len(duplicate_addresses) - 5} more")
        
    except Exception as e:
        print(f"❌ Error creating duplicates file: {e}")

def main():
    """Main function to check for duplicates and create the duplicates file."""
    print("🚀 Starting duplicate address check...")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 CSV file: {CSV_FILE}")
    print(f"📊 Google Sheet: {SHEET_NAME}")
    print(f"📄 Output file: {DUPLICATES_FILE}")
    print("-" * 60)
    
    # 1. Authenticate with Google Sheets
    gc = authenticate_gsheets()
    if not gc:
        return
    
    # 2. Get addresses from Google Sheet
    google_addresses = get_google_sheet_addresses(gc)
    if not google_addresses:
        print("⚠️  No addresses found in Google Sheet, skipping duplicate check")
        return
    
    # 3. Get addresses from CSV file
    csv_addresses = get_csv_addresses()
    if not csv_addresses:
        print("⚠️  No addresses found in CSV file, skipping duplicate check")
        return
    
    # 4. Find duplicates
    duplicate_addresses = find_duplicates(google_addresses, csv_addresses)
    
    # 5. Create duplicates file
    if duplicate_addresses:
        create_duplicates_file(duplicate_addresses, google_addresses, csv_addresses)
    else:
        print("✅ No duplicate addresses found!")
        print(f"\n📊 Summary:")
        print(f"   - Google Sheet addresses: {len(google_addresses)}")
        print(f"   - CSV file addresses: {len(csv_addresses)}")
        print(f"   - Duplicate addresses: 0")

if __name__ == "__main__":
    main() 