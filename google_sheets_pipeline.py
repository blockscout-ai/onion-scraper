import gspread
import pandas as pd
import os
import re

# ---[ Configuration ]---
SERVICE_ACCOUNT_FILE = '/Users/jasoncomer/Desktop/blockscout_python/ofac-automation-52b699a4735a.json'
GOOGLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/14ApkAb5jHTv-wzP8CFJTax31UXYkFb0ebDDd6Bg1EC8/edit#gid=1998112463'
SHEET_NAME = 'darknet_automation'
SOURCE_CSV_FILE = '/Users/jasoncomer/onion_scraper_2/crypto_addresses_fast.csv'

# Column mapping from CSV header to Google Sheet column letter
COLUMN_MAPPING = {
    'url': 'F',
    'title': 'D',
    'chain': 'L',
    'address': 'N',
    'screenshot': 'O',
    'entity_id': 'H',
    'entity_type': 'E'
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

def authenticate_gsheets():
    """Authenticate with Google Sheets using the service account."""
    try:
        print("🔑 Authenticating with Google Sheets...")
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        print("✅ Authentication successful.")
        return gc
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("   Please ensure the service account file path is correct and has the right permissions.")
        return None

def main():
    """Main function to run the pipeline."""
    print("🚀 Starting Google Sheets data pipeline...")
    
    # 1. Authenticate
    gc = authenticate_gsheets()
    if not gc:
        return

    # 2. Open the workbook and worksheet
    try:
        print(f"📄 Opening Google Sheet: '{SHEET_NAME}'")
        workbook = gc.open_by_url(GOOGLE_SHEET_URL)
        worksheet = workbook.worksheet(SHEET_NAME)
        print("✅ Sheet opened successfully.")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"❌ Error: The Google Sheet at the specified URL was not found.")
        return
    except gspread.exceptions.WorksheetNotFound:
        print(f"❌ Error: The worksheet '{SHEET_NAME}' was not found in the spreadsheet.")
        return
    except Exception as e:
        print(f"❌ An error occurred while opening the sheet: {e}")
        return

    # 3. Read existing addresses from Google Sheet to prevent duplicates
    print("🔎 Fetching existing addresses from Google Sheet...")
    try:
        header_row_for_index = worksheet.row_values(2)
        address_col_index = header_row_for_index.index('deposit_address') + 1
        existing_addresses = set(worksheet.col_values(address_col_index)[2:])
        print(f"✅ Found {len(existing_addresses)} existing unique addresses.")
    except Exception as e:
        print(f"⚠️  Could not fetch existing addresses, proceeding without duplicate check. Error: {e}")
        existing_addresses = set()

    # 4. Read the source CSV file and filter for unique rows
    if not os.path.exists(SOURCE_CSV_FILE):
        print(f"❌ Error: The source CSV file was not found at '{SOURCE_CSV_FILE}'.")
        return
        
    print(f"📥 Reading data from '{SOURCE_CSV_FILE}'...")
    try:
        # Define the expected columns to handle parsing errors from inconsistent CSVs.
        expected_columns = ['url', 'title', 'chain', 'address', 'timestamp', 'screenshot', 'categories']
        # Read the CSV without relying on its header and force the defined column names.
        df = pd.read_csv(SOURCE_CSV_FILE, engine='python', header=None, names=expected_columns)

        # If the first row was a header, it will be read as data. Check and remove it.
        if df.iloc[0]['url'] == 'url':
            df = df.iloc[1:].reset_index(drop=True)
        
        if df.empty:
            print("🤷 Source CSV is empty. Nothing to upload.")
            return

        original_count = len(df)
        df = df[~df['address'].isin(existing_addresses)]
        
        if df.empty:
            print("✅ All addresses from the CSV already exist in the sheet. No new data to upload.")
            return

        print(f"📊 Found {original_count} rows in CSV, {len(df)} are new and will be uploaded.")
        
    except Exception as e:
        print(f"❌ Error reading or filtering CSV file: {e}")
        return

    # 5. Prepare data for upload
    upload_data = []
    
    try:
        header_row = worksheet.row_values(2)
    except Exception as e:
        print(f"❌ Could not read header row from Google Sheet: {e}")
        return
        
    # Map CSV columns to their target index in the Google Sheet
    col_map_index = {
        'url': header_row.index('url') if 'url' in header_row else -1,
        'title': header_row.index('ent_name') if 'ent_name' in header_row else -1,
        'chain': header_row.index('chain_selection') if 'chain_selection' in header_row else -1,
        'address': header_row.index('deposit_address') if 'deposit_address' in header_row else -1,
        'screenshot': header_row.index('screenshot') if 'screenshot' in header_row else -1,
        'entity_id': header_row.index('entity_id') if 'entity_id' in header_row else -1,
        'entity_type': header_row.index('entity_type') if 'entity_type' in header_row else -1
    }

    # Verify all columns were found
    if any(v == -1 for v in col_map_index.values()):
        missing = [k for k, v in col_map_index.items() if v == -1]
        print(f"❌ Error: Could not find the following columns in the sheet's header (row 2): {missing}")
        return

    for index, row in df.iterrows():
        # Create a list with the correct number of empty strings
        new_row = [''] * len(header_row)
        # Place data in the correct positions based on the header map
        new_row[col_map_index['url']] = row.get('url', '')
        new_row[col_map_index['title']] = row.get('title', '')
        new_row[col_map_index['chain']] = row.get('chain', '')
        new_row[col_map_index['address']] = row.get('address', '')
        
        screenshot_path = row.get('screenshot', '')
        new_row[col_map_index['screenshot']] = screenshot_path
        
        # Generate and place the entity_id
        entity_id = generate_entity_id(screenshot_path)
        new_row[col_map_index['entity_id']] = entity_id
        
        # Add the entity_type from the 'categories' column, leave blank if not present
        entity_type = row.get('categories', '')
        if pd.isna(entity_type): # Handle pandas NaN values for empty cells
            entity_type = ''
        new_row[col_map_index['entity_type']] = entity_type
        
        upload_data.append(new_row)

    # 6. Append data to the Google Sheet
    if not upload_data:
        print("✅ No new data to upload.")
        return
        
    try:
        print(f"📤 Appending {len(upload_data)} new rows to the sheet...")

        # Find the first empty row by counting all existing rows in the sheet.
        # This avoids parsing headers with get_all_records(), which fails on duplicate column names.
        all_values = worksheet.get_all_values()
        next_row = len(all_values) + 1

        # Per user, data starts on row 3. Ensure we don't try to write over the headers.
        if next_row < 3:
            next_row = 3

        def colnum_to_a1(n):
            """Convert a column number to A1 notation (e.g., 1 -> A, 27 -> AA)."""
            string = ""
            while n > 0:
                n, remainder = divmod(n - 1, 26)
                string = chr(65 + remainder) + string
            return string

        # Determine the full range to update, starting from column A
        last_col_letter = colnum_to_a1(len(header_row))
        update_range = f'A{next_row}:{last_col_letter}{next_row + len(upload_data) - 1}'

        print(f"   -> Updating exact range: {update_range}")
        worksheet.update(update_range, upload_data, value_input_option='USER_ENTERED')

        print("🎉 Successfully appended data to Google Sheet!")
    except Exception as e:
        print(f"❌ An error occurred during the upload: {e}")

if __name__ == "__main__":
    main() 