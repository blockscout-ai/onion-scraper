import gspread
import pandas as pd
import os
import re
import time
import socket

# ---[ Configuration ]---
SERVICE_ACCOUNT_FILE = '/Users/jasoncomer/Downloads/ofac-automation-234e5a9169fd.json'  # Put your service account file here
SOURCE_CSV_FILE = '/Users/jasoncomer/onion_scraper_2/crypto_addresses_fast.csv'

# First Google Sheet (darknet_automation)
SHEET1_URL = 'https://docs.google.com/spreadsheets/d/14ApkAb5jHTv-wzP8CFJTax31UXYkFb0ebDDd6Bg1EC8/edit#gid=1998112463'
SHEET1_NAME = 'darknet_automation'
SHEET1_COLUMN_MAPPING = {
    'url': 'url',
    'title': 'ent_name', 
    'timestamp': 'date',  # Map timestamp to 'date' column (column K)
    'chain': 'chain_selection',
    'address': 'deposit_address',
    'screenshot': 'screenshot',
    'entity_id': 'entity_id',
    'entity_type': 'entity_type'
}

# Second Google Sheet (SoT)
SHEET2_URL = 'https://docs.google.com/spreadsheets/d/1L87aWWnokU84mz_VbALqnTsqu1RhqJoHjWQnO-dVvJw/edit?pli=1&gid=425098716#gid=425098716'
SHEET2_NAME = 'SoT'  # This should be the tab name within the workbook
SHEET2_COLUMN_MAPPING = {
    'url': 'url',
    'title': 'proper_name',  # Map title to proper_name
    'entity_id': 'entity_id',
    'entity_type': 'entity_type'
}

# Entity type keywords for classification
ENTITY_TYPE_KEYWORDS = {
    'CSAM': [
        'csam', 'child', 'children', 'cp', 'porn', 'pedo', 'underage', 'teen', 'young', 'minor', 'kid', 'childporn',
        'girls', 'boys', 'sex', 'sexual', 'preteen', 'boy', 'girl'
    ],
    'carding': ['card', 'cc', 'credit', 'dumps', 'cvv', 'stripe', 'paypal', 'bank', 'carding', 'fraud', 'steal'],
    'darknet': ['darknet', 'dark', 'onion', 'tor', 'hidden', 'underground', 'illegal', 'drug', 'weapon']
}

def generate_entity_id(screenshot_filename):
    """
    Parses a screenshot filename to extract and sanitize an entity_id.
    Example: 'screenshots_fast/_10_Trial__aqd4yd_20250620104000856_0.png' -> '_10_trial_aqd4yd'
    """
    if not screenshot_filename or pd.isna(screenshot_filename):
        return ""
    
    try:
        # Get just the filename, not the full path
        base_name = os.path.basename(str(screenshot_filename))
        
        # The entity_id is the part before the long timestamp
        # Find the timestamp (e.g., _20250620104000856_)
        match = re.search(r'_\d{17,}', base_name)
        
        if match:
            raw_id = base_name[:match.start()]
        else:
            # Fallback if no timestamp is found: take everything before the last underscore
            raw_id = base_name.rsplit('_', 1)[0]

        # Sanitize to snake_case: lowercase, replace spaces/hyphens with underscores, remove other invalid chars
        sanitized_id = raw_id.lower()
        sanitized_id = re.sub(r'[\s\-]+', '_', sanitized_id) # Replace spaces and hyphens with underscores
        sanitized_id = re.sub(r'[^a-z0-9_]', '', sanitized_id) # Remove any remaining invalid characters
        
        return sanitized_id
    except Exception as e:
        print(f"⚠️  Could not generate entity_id for '{screenshot_filename}': {e}")
        return ""

def classify_entity_type(title, existing_entity_type):
    """
    Classify entity type based on title keywords and priority logic.
    Priority: CSAM > carding > darknet
    """
    if not title or pd.isna(title):
        title = ""
    
    title_lower = str(title).lower()
    
    # Check for CSAM keywords first (highest priority)
    for keyword in ENTITY_TYPE_KEYWORDS['CSAM']:
        if keyword in title_lower:
            return 'CSAM'
    
    # Check for carding keywords second
    for keyword in ENTITY_TYPE_KEYWORDS['carding']:
        if keyword in title_lower:
            return 'carding'
    
    # Default to darknet for everything else
    return 'darknet'

def authenticate_gsheets():
    """Authenticate with Google Sheets using the service account with retry logic."""
    max_retries = 3
    timeout_seconds = 30
    
    for attempt in range(max_retries):
        try:
            print(f"🔑 Authenticating with Google Sheets (attempt {attempt + 1}/{max_retries})...")
            
            # Set timeout for the authentication
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(timeout_seconds)
            
            try:
                gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
                
                # Test the connection by trying to access a sheet
                print("🔍 Testing connection...")
                workbook = gc.open_by_url(SHEET2_URL)
                _ = workbook.worksheet(SHEET2_NAME)
                
                print("✅ Authentication and connection test successful.")
                return gc
                
            finally:
                # Restore original timeout
                socket.setdefaulttimeout(old_timeout)
                
        except Exception as e:
            print(f"⚠️  Authentication attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # Exponential backoff: 5, 10, 15 seconds
                print(f"🔄 Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"❌ Authentication failed after {max_retries} attempts.")
                print("   Possible solutions:")
                print("   1. Check your internet connection")
                print("   2. Verify the service account file is correct")
                print("   3. Ensure the service account has access to the Google Sheets")
                print("   4. Try again later if Google APIs are experiencing issues")
                return None
    
    return None

def get_existing_records(worksheet, sheet_name):
    """Get existing records to prevent duplicates."""
    try:
        print(f"🔎 Fetching existing records from '{sheet_name}'...")
        
        if sheet_name == SHEET1_NAME:
            # For sheet1, use deposit_address as unique identifier
            # Try multiple rows to find the header
            header_found = False
            header_row = None
            header_row_num = None
            
            # Check rows 1-5 for headers
            for row_num in range(1, 6):
                try:
                    row_values = worksheet.row_values(row_num)
                    print(f"🔍 Row {row_num} values: {row_values}")
                    if 'deposit_address' in row_values:
                        header_row = row_values
                        header_row_num = row_num
                        header_found = True
                        print(f"✅ Found 'deposit_address' in row {row_num}")
                        break
                except Exception as e:
                    print(f"⚠️ Could not read row {row_num}: {e}")
                    continue
            
            if not header_found:
                # If we can't find 'deposit_address', try to find any column that might contain addresses
                print("⚠️ Could not find 'deposit_address' column, searching for address-like columns...")
                for row_num in range(1, 6):
                    try:
                        row_values = worksheet.row_values(row_num)
                        for i, col_name in enumerate(row_values):
                            if col_name and any(keyword in col_name.lower() for keyword in ['address', 'addr', 'wallet', 'btc', 'eth', 'crypto']):
                                print(f"🔍 Found potential address column '{col_name}' at index {i} in row {row_num}")
                                # Check if this column contains what looks like addresses
                                col_values = worksheet.col_values(i + 1)[row_num:]  # +1 because col_values is 1-indexed
                                address_like_values = [v for v in col_values if v and (v.startswith(('1', '3', 'bc1', '0x', '4', 'T')) or len(v) > 20)]
                                if address_like_values:
                                    print(f"✅ Column '{col_name}' contains {len(address_like_values)} address-like values")
                                    existing_records = set(address_like_values)
                                    print(f"✅ Found {len(existing_records)} existing addresses in {sheet_name}.")
                                    return existing_records
                    except Exception as e:
                        print(f"⚠️ Could not read row {row_num}: {e}")
                        continue
                
                print("❌ Could not find any address-like columns, proceeding without duplicate check")
                return set()
            
            # Found the header, now get the address column
            address_col_index = header_row.index('deposit_address')
            print(f"🔍 Address column index: {address_col_index}")
            
            # Get all values from the address column, starting from the row after the header
            col_values = worksheet.col_values(address_col_index + 1)[header_row_num:]  # +1 because col_values is 1-indexed
            existing_records = set([v for v in col_values if v and v.strip()])  # Filter out empty values
            
            print(f"✅ Found {len(existing_records)} existing addresses in {sheet_name}.")
            if len(existing_records) > 0:
                print(f"🔍 Sample existing addresses: {list(existing_records)[:5]}")
            return existing_records
            
        else:
            # For sheet2, use entity_id + url combination, using header names
            all_values = worksheet.get_all_values()
            if len(all_values) < 2:  # Only header or empty
                return set()
            header_row = all_values[0]  # Assume header is in row 1
            print(f"🔍 [Duplicates] Header row for {sheet_name}: {header_row}")
            try:
                entity_id_idx = header_row.index('entity_id')
                url_idx = header_row.index('url')
            except ValueError as e:
                print(f"❌ Could not find 'entity_id' or 'url' in header: {e}")
                return set()
            existing_records = set()
            for row in all_values[1:]:  # Skip header row
                if len(row) > max(entity_id_idx, url_idx):
                    entity_id = row[entity_id_idx]
                    url = row[url_idx]
                    if entity_id and url:
                        existing_records.add(f"{entity_id}|{url}")
            print(f"✅ Found {len(existing_records)} existing entity_id+url combinations in {sheet_name}.")
            return existing_records
        
    except Exception as e:
        print(f"⚠️  Could not fetch existing records from {sheet_name}, proceeding without duplicate check. Error: {e}")
        return set()

def find_actual_last_data_row(worksheet):
    """Find the actual last row with meaningful data, ignoring validation/formatting rows."""
    try:
        all_values = worksheet.get_all_values()
        
        # Work backwards from the end to find the last row with substantial data
        actual_last_row = 0
        for i in range(len(all_values) - 1, -1, -1):
            row = all_values[i]
            # Count non-empty cells that contain meaningful data
            non_empty_cells = [cell.strip() for cell in row if cell.strip()]
            
            # Consider it a data row if it has multiple non-empty cells or substantive content
            if len(non_empty_cells) >= 3:  # At least 3 filled columns suggests real data
                actual_last_row = i + 1  # Convert to 1-based indexing
                break
            elif len(non_empty_cells) >= 1:
                # Check if the single cell has substantial content (not just validation/formatting)
                substantive_content = any(len(cell) > 10 or 
                                        any(keyword in cell.lower() for keyword in ['http', 'onion', '@', '.com', 'btc', 'eth']) 
                                        for cell in non_empty_cells)
                if substantive_content:
                    actual_last_row = i + 1
                    break
        
        print(f"🔍 Found actual last data row: {actual_last_row} (vs get_all_values length: {len(all_values)})")
        return actual_last_row
        
    except Exception as e:
        print(f"⚠️  Error finding actual last row, falling back to get_all_values: {e}")
        return len(worksheet.get_all_values())

def expand_sheet_if_needed(worksheet, needed_rows):
    """Expand the sheet if it doesn't have enough rows."""
    try:
        current_rows = worksheet.row_count
        if needed_rows > current_rows:
            additional_rows = needed_rows - current_rows + 100  # Add some buffer
            print(f"📏 Expanding sheet from {current_rows} to {needed_rows + 100} rows...")
            worksheet.add_rows(additional_rows)
            print(f"✅ Sheet expanded successfully!")
            return True
    except Exception as e:
        print(f"⚠️  Could not expand sheet: {e}")
        return False
    return True

def upload_to_sheet(gc, sheet_url, sheet_name, column_mapping, data, existing_records):
    """Upload data to a specific Google Sheet."""
    try:
        print(f"📄 Opening Google Sheet: '{sheet_name}'")
        workbook = gc.open_by_url(sheet_url)
        
        # List available worksheets for debugging
        available_worksheets = [ws.title for ws in workbook.worksheets()]
        print(f"📋 Available worksheets in workbook: {available_worksheets}")
        
        worksheet = workbook.worksheet(sheet_name)
        print("✅ Sheet opened successfully.")
        
        # Debug: Show the actual header row and check multiple rows
        header_row = worksheet.row_values(2)
        print(f"🔍 Header row in {sheet_name} (row 2): {header_row}")
        
        # If header row is empty, try row 1
        if not header_row or all(cell == '' for cell in header_row):
            header_row = worksheet.row_values(1)
            print(f"🔍 Header row in {sheet_name} (row 1): {header_row}")
        
        # If still empty, check if the sheet is completely empty
        all_values = worksheet.get_all_values()
        print(f"📊 Total rows in {sheet_name}: {len(all_values)}")
        if len(all_values) > 0:
            print(f"📊 First few rows: {all_values[:3]}")
        
    except Exception as e:
        print(f"❌ Error opening sheet '{sheet_name}': {e}")
        print(f"   Available worksheets: {available_worksheets if 'available_worksheet' in locals() else 'Could not retrieve'}")
        print(f"   Make sure '{sheet_name}' exists as a tab in the workbook.")
        return False

    if not data:
        print(f"✅ No new data to upload to {sheet_name} (all were duplicates).")
        return True

    # Filter out duplicates for both sheets since both now append
    if sheet_name == SHEET1_NAME:
        print(f"🔍 Filtering duplicates for {sheet_name} (by address)...")
        print(f"🔍 Existing records count: {len(existing_records)}")
        if len(existing_records) > 0:
            print(f"🔍 Sample existing records: {list(existing_records)[:5]}")
        
        filtered_data = []
        duplicates_found = 0
        
        for i, row in enumerate(data):
            address = row.get('address', '')
            if address:
                if address not in existing_records:
                    filtered_data.append(row)
                    print(f"✅ Row {i}: Address '{address[:10]}...' is NEW")
                else:
                    duplicates_found += 1
                    print(f"⏭️ Row {i}: Address '{address[:10]}...' is DUPLICATE")
            else:
                print(f"⚠️ Row {i}: No address found")
                duplicates_found += 1
        
        print(f"✅ Filtered {len(data)} rows: {len(filtered_data)} new, {duplicates_found} duplicates")
        data = filtered_data  # Use filtered data for upload
        
        if not data:
            print(f"✅ No new data to upload to {sheet_name} (all were duplicates).")
            return True
    
    elif sheet_name == SHEET2_NAME:
        print(f"🔍 Filtering duplicates for {sheet_name} (by entity_id+url)...")
        filtered_data = []
        duplicates_found = 0
        
        for row in data:
            entity_id = row.get('entity_id', '')
            url = row.get('url', '')
            combination = f"{entity_id}|{url}"
            if combination and combination not in existing_records:
                filtered_data.append(row)
            else:
                duplicates_found += 1
        
        print(f"✅ Filtered {len(data)} rows: {len(filtered_data)} new, {duplicates_found} duplicates")
        data = filtered_data  # Use filtered data for upload
        
        if not data:
            print(f"✅ No new data to upload to {sheet_name} (all were duplicates).")
            return True

    print(f"📤 Uploading {len(data)} rows to {sheet_name}...")

    try:
        # Get header row to map columns
        # For darknet_scraper, use header names, not column letters
        if sheet_name == SHEET2_NAME:
            # Try row 1 first for header
            header_row = worksheet.row_values(1)
            print(f"🔍 [Upload] Using header row (row 1) for {sheet_name}: {header_row}")
        else:
            header_row = worksheet.row_values(2)

        # For darknet_automation, use fixed column positions instead of header mapping
        if sheet_name == SHEET1_NAME:
            print(f"🔍 Using fixed column positions for {sheet_name}")
            # Prepare data for upload using fixed positions
            upload_data = []
            for i, row in enumerate(data):
                new_row = [''] * len(header_row)
                
                # Fixed column positions for darknet_automation based on schema
                # Columns 0-2 stay empty (proposed_ent_name, proposed_type, dead?)
                new_row[3] = row.get('title', '')         # Column D: ent_name (title)
                new_row[4] = row.get('entity_type', '')   # Column E: entity_type
                new_row[5] = row.get('url', '')           # Column F: url
                # Column 6 stays empty (custodian)
                new_row[7] = row.get('entity_id', '')     # Column H: entity_id
                # Columns 8-9 stay empty (beneficial_owner, entity_type duplicate)
                new_row[10] = row.get('timestamp', '')    # Column K: date
                new_row[11] = row.get('chain', '')        # Column L: chain_selection
                # Column 12 stays empty (address_type)
                new_row[13] = row.get('address', '')      # Column N: deposit_address
                new_row[14] = row.get('screenshot', '')   # Column O: screenshot
                # Columns 15-20 stay empty (initiator, creator, withdraw_to, withdraw_sender_att, notes, user)
                
                if row.get('timestamp', ''):
                    print(f"📅 Row {i}: Setting timestamp '{row.get('timestamp', '')}' at index 10")
                
                upload_data.append(new_row)
        else:
            # For darknet_scraper, use header mapping as before
            col_map_index = {}
            for csv_col, sheet_col in column_mapping.items():
                if sheet_col in header_row:
                    col_map_index[csv_col] = header_row.index(sheet_col)
                    print(f"✅ Mapped '{csv_col}' -> '{sheet_col}' (index {header_row.index(sheet_col)})")
                else:
                    print(f"⚠️  Column '{sheet_col}' not found in {sheet_name} header")
                    col_map_index[csv_col] = -1

            print(f"🔍 Column mapping for {sheet_name}: {col_map_index}")

            # Prepare data for upload
            upload_data = []
            for i, row in enumerate(data):
                new_row = [''] * len(header_row)
                for csv_col, col_index in col_map_index.items():
                    if col_index >= 0:
                        new_row[col_index] = row.get(csv_col, '')
                
                # For darknet_scraper, add checkbox (TRUE) in column D (index 3)
                if len(new_row) > 3:
                    new_row[3] = 'TRUE'  # Column D checkbox
                
                # Add "Darknet Entity" to associate_country_1 column
                if 'associate_country_1' in header_row:
                    country_col_index = header_row.index('associate_country_1')
                    if len(new_row) > country_col_index:
                        new_row[country_col_index] = 'Darknet Entity'
                
                upload_data.append(new_row)

        # Convert column numbers to A1 notation
        def colnum_to_a1(n):
            string = ""
            while n > 0:
                n, remainder = divmod(n - 1, 26)
                string = chr(65 + remainder) + string
            return string

        # For both sheets, append new records
        if True:  # Both sheets now use append mode
            # Find the actual last row with data (ignoring validation/formatting rows)
            current_rows = find_actual_last_data_row(worksheet)
            needed_rows = current_rows + len(upload_data)
            
            # Check current sheet limits and expand if needed
            max_rows = worksheet.row_count
            max_cols = worksheet.col_count
            
            print(f"📊 Sheet info: {current_rows} current data rows, {max_rows} max sheet rows, {max_cols} max cols")
            print(f"📊 Need to add {len(upload_data)} rows (will reach {needed_rows} total rows)")
            
            # If we're approaching the limit, try to expand
            if needed_rows > max_rows:
                print(f"📏 Sheet needs expansion: current max {max_rows}, needed {needed_rows}")
                if not expand_sheet_if_needed(worksheet, needed_rows):
                    print(f"❌ Cannot expand sheet. Please manually add rows to the Google Sheet.")
                    return False
            
            next_row = current_rows + 1
            if next_row < 2:
                next_row = 2

            last_col_letter = colnum_to_a1(len(header_row))
            update_range = f'A{next_row}:{last_col_letter}{next_row + len(upload_data) - 1}'

            print(f"   -> Updating range: {update_range}")
            # Fixed: Use named parameters to avoid deprecation warning
            worksheet.update(range_name=update_range, values=upload_data, value_input_option='USER_ENTERED')

        print(f"🎉 Successfully uploaded data to {sheet_name}!")
        return True

    except Exception as e:
        print(f"❌ Error uploading to {sheet_name}: {e}")
        if "exceeds grid limits" in str(e) or "Range" in str(e) and "exceeds" in str(e):
            print(f"💡 Grid limits exceeded. Attempting to expand sheet...")
            try:
                # Try to expand and retry using actual data row count
                current_rows = find_actual_last_data_row(worksheet)
                needed_rows = current_rows + len(upload_data) + 100
                if expand_sheet_if_needed(worksheet, needed_rows):
                    print(f"✅ Sheet expanded, retrying upload...")
                    # Retry the upload
                    next_row = current_rows + 1
                    last_col_letter = colnum_to_a1(len(header_row))
                    update_range = f'A{next_row}:{last_col_letter}{next_row + len(upload_data) - 1}'
                    worksheet.update(range_name=update_range, values=upload_data, value_input_option='USER_ENTERED')
                    print(f"🎉 Successfully uploaded data to {sheet_name} after expansion!")
                    return True
                else:
                    print(f"❌ Could not expand sheet. Please manually expand the Google Sheet.")
                    return False
            except Exception as e2:
                print(f"❌ Retry after expansion failed: {e2}")
                return False
        return False

def check_sot_exclusions(gc, sheet_url):
    """Check SoT tab column F for entity_ids to exclude from darknet_scraper upload."""
    try:
        print("🔍 Checking SoT tab for exclusions...")
        workbook = gc.open_by_url(sheet_url)
        worksheet = workbook.worksheet('SoT')
        
        # Get all values from SoT tab
        all_values = worksheet.get_all_values()
        if len(all_values) < 2:  # Only header or empty
            print("✅ SoT tab is empty, no exclusions found")
            return set()
        
        header_row = all_values[0]
        data_rows = all_values[1:]
        
        # Find column F index (should be index 5 for column F)
        try:
            col_f_idx = 5  # Column F is index 5 (0-based)
            if len(header_row) > col_f_idx:
                print(f"🔍 Using column F (index {col_f_idx}) for SoT exclusions")
            else:
                print(f"⚠️  Column F not found in SoT, using index 5")
        except Exception as e:
            print(f"❌ Error finding column F in SoT: {e}")
            return set()
        
        # Extract last 6 characters from column F values
        excluded_suffixes = set()
        for row in data_rows:
            if len(row) > col_f_idx:
                value = str(row[col_f_idx]).strip()
                if len(value) >= 6:
                    last_6 = value[-6:]
                    excluded_suffixes.add(last_6)
        
        print(f"✅ Found {len(excluded_suffixes)} unique 6-character suffixes in SoT column F")
        return excluded_suffixes
        
    except Exception as e:
        print(f"❌ Error checking SoT exclusions: {e}")
        return set()

def check_entity_id_exclusion(entity_id, excluded_suffixes):
    """Check if entity_id should be excluded based on SoT suffixes."""
    if not entity_id or len(entity_id) < 6:
        return False
    
    last_6 = entity_id[-6:]
    return last_6 in excluded_suffixes

def parse_csv_robustly(file_path):
    """Parse CSV file with robust handling of malformed rows."""
    import csv
    
    print(f"📥 Reading CSV with robust parsing from '{file_path}'...")
    
    # Expected columns based on header
    expected_columns = ['url', 'title', 'chain', 'address', 'timestamp', 'screenshot', 'entity_type', 'description']
    
    data_rows = []
    skipped_rows = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Read header first
            header_line = f.readline().strip()
            print(f"📋 CSV Header: {header_line}")
            
            # Parse header to see actual columns
            header_reader = csv.reader([header_line])
            actual_header = next(header_reader)
            print(f"📋 Parsed header columns ({len(actual_header)}): {actual_header}")
            
            # Read data lines
            line_num = 1
            for line in f:
                line_num += 1
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                try:
                    # Parse the line with CSV reader to handle quotes properly
                    csv_reader = csv.reader([line])
                    row = next(csv_reader)
                    
                    # Handle missing columns - pad with empty strings
                    while len(row) < len(expected_columns):
                        row.append('')
                    
                    # Create row dictionary
                    row_dict = {}
                    for i, col_name in enumerate(expected_columns):
                        row_dict[col_name] = row[i] if i < len(row) else ''
                    
                    # Basic validation - require at least URL and title
                    if row_dict.get('url', '').strip() and row_dict.get('title', '').strip():
                        data_rows.append(row_dict)
                    else:
                        skipped_rows += 1
                        if line_num <= 10:  # Only show first few skipped rows
                            print(f"⚠️  Skipping row {line_num}: missing URL or title")
                        
                except Exception as e:
                    skipped_rows += 1
                    if line_num <= 10:  # Only show first few errors
                        print(f"⚠️  Skipping malformed row {line_num}: {e}")
                    continue
        
        print(f"✅ Successfully parsed {len(data_rows)} valid rows, skipped {skipped_rows} malformed/invalid rows")
        return pd.DataFrame(data_rows)
        
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return pd.DataFrame()

def main():
    """Main function to run the unified pipeline."""
    print("🚀 Starting Unified Google Sheets Data Pipeline...")
    
    # 1. Authenticate
    gc = authenticate_gsheets()
    if not gc:
        return

    # 2. Read and process CSV data with robust parsing
    if not os.path.exists(SOURCE_CSV_FILE):
        print(f"❌ Error: The source CSV file was not found at '{SOURCE_CSV_FILE}'.")
        return
        
    # Use robust CSV parsing
    df = parse_csv_robustly(SOURCE_CSV_FILE)
    
    if df.empty:
        print("🤷 Source CSV is empty or all rows were invalid. Nothing to upload.")
        return

    print(f"📊 Successfully processed {len(df)} valid rows from CSV.")

    # 3. Process data for both sheets
    sheet1_data = []
    sheet2_data = []
    
    print(f"🔍 Processing {len(df)} rows for sheet preparation...")
    
    for index, row in df.iterrows():
        # Generate entity_id from screenshot
        screenshot_path = row.get('screenshot', '')
        entity_id = generate_entity_id(screenshot_path)
        
        # Classify entity type based on title
        title = row.get('title', '')
        entity_type = classify_entity_type(title, row.get('entity_type', ''))
        
        # Debug timestamp data
        timestamp_value = row.get('timestamp', '')
        if timestamp_value:
            print(f"📅 Row {index}: Found timestamp '{timestamp_value}'")
        
        # Prepare data for sheet1 (darknet_automation)
        sheet1_row = {
            'url': row.get('url', ''),
            'title': row.get('title', ''),
            'timestamp': timestamp_value,
            'chain': row.get('chain', ''),
            'address': row.get('address', ''),
            'screenshot': screenshot_path,
            'entity_id': entity_id,
            'entity_type': row.get('entity_type', '')  # Use original categories
        }
        sheet1_data.append(sheet1_row)
        
        # Prepare data for sheet2 (darknet_scraper)
        sheet2_row = {
            'url': row.get('url', ''),
            'title': row.get('title', ''),
            'entity_id': entity_id,
            'entity_type': entity_type  # Use classified entity type
        }
        sheet2_data.append(sheet2_row)

    # Deduplicate data from the source CSV before uploading
    print("\n🔍 Deduplicating data from CSV before upload...")
    unique_sheet2_data = []
    seen_combinations = set()
    for row in sheet2_data:
        entity_id = row.get('entity_id', '')
        url = row.get('url', '')
        combination = f"{entity_id}|{url}"
        if combination not in seen_combinations:
            seen_combinations.add(combination)
            unique_sheet2_data.append(row)

    print(f"📊 Found {len(sheet2_data)} source rows for darknet_scraper, {len(unique_sheet2_data)} are unique.")
    sheet2_data = unique_sheet2_data  # Overwrite with the deduplicated list

    # 4. Upload to both sheets
    print("\n📤 Starting uploads...")
    
    # Upload to sheet1 (darknet_automation)
    try:
        print(f"📄 Opening Google Sheet: '{SHEET1_NAME}'")
        workbook1 = gc.open_by_url(SHEET1_URL)
        worksheet1 = workbook1.worksheet(SHEET1_NAME)
        existing_records1 = get_existing_records(worksheet1, SHEET1_NAME)
        upload_to_sheet(gc, SHEET1_URL, SHEET1_NAME, SHEET1_COLUMN_MAPPING, sheet1_data, existing_records1)
    except Exception as e:
        print(f"❌ Error with sheet1: {e}")
    
    # Upload to sheet2 (darknet_scraper)
    try:
        print(f"📄 Opening Google Sheet: '{SHEET2_NAME}'")
        workbook2 = gc.open_by_url(SHEET2_URL)
        worksheet2 = workbook2.worksheet(SHEET2_NAME)
        
        # Get existing records from SoT to avoid duplicates
        existing_records2 = get_existing_records(worksheet2, SHEET2_NAME)
        
        print(f"📤 Uploading {len(sheet2_data)} rows to {SHEET2_NAME} (checking for duplicates first)")
        
        # For SoT, we append new records after checking for duplicates
        upload_to_sheet(gc, SHEET2_URL, SHEET2_NAME, SHEET2_COLUMN_MAPPING, sheet2_data, existing_records2)
    except Exception as e:
        print(f"❌ Error with sheet2: {e}")
    
    print("\n✅ Unified pipeline completed!")

if __name__ == "__main__":
    main() 