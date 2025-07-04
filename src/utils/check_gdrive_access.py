import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def check_gdrive_access():
    """Check what Google Drive folders the service account can access."""
    try:
        print("🔑 Initializing Google Drive API...")
        
        # Define the scope for Google Drive API
        SCOPES = ['https://www.googleapis.com/auth/drive']
        
        # Load credentials from service account file
        credentials = Credentials.from_service_account_file(
            'service_account.json', scopes=SCOPES
        )
        
        # Build the Drive service
        drive_service = build('drive', 'v3', credentials=credentials)
        print("✅ Google Drive API initialized successfully.")
        
        # List all folders the service account can access
        print("\n📁 Checking accessible folders...")
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            pageSize=50,
            fields="files(id,name,webViewLink)"
        ).execute()
        
        folders = results.get('files', [])
        
        if folders:
            print(f"✅ Found {len(folders)} accessible folders:")
            for folder in folders:
                print(f"   📁 {folder['name']} (ID: {folder['id']})")
                print(f"      🔗 {folder['webViewLink']}")
                print()
        else:
            print("❌ No accessible folders found.")
            
        # Try to create a new folder
        print("🔧 Attempting to create a new folder...")
        folder_metadata = {
            'name': 'Onion_Scraper_Screenshots',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = drive_service.files().create(
            body=folder_metadata, fields='id,name,webViewLink'
        ).execute()
        
        print(f"✅ Successfully created folder: {folder['name']}")
        print(f"   📁 Folder ID: {folder['id']}")
        print(f"   🔗 Link: {folder['webViewLink']}")
        
        return folder['id']
        
    except HttpError as e:
        print(f"❌ Google Drive API error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    folder_id = check_gdrive_access()
    if folder_id:
        print(f"\n🎯 Use this folder ID in your configuration: {folder_id}") 