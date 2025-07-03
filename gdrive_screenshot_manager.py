import os
import json
import time
import argparse
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import mimetypes
import hashlib
import re

class GoogleDriveScreenshotManager:
    """
    Elegant Google Drive screenshot manager for automatic upload and organization.
    Integrates with existing scraper infrastructure.
    """
    
    def __init__(self, service_account_file='service_account.json', folder_id='1X5iXBO1AtQ8-VHK5cdVQkwkNByEnATSa'):
        """
        Initialize the Google Drive screenshot manager.
        
        Args:
            service_account_file (str): Path to service account JSON file
            folder_id (str): Google Drive folder ID where screenshots should be stored
        """
        self.service_account_file = service_account_file
        self.folder_id = folder_id
        self.drive_service = None
        self.upload_cache = {}  # Cache to avoid re-uploading same files
        self.upload_stats = {
            'total_uploads': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'skipped_uploads': 0,
            'total_size_uploaded': 0
        }
        
        # Initialize Google Drive API
        self._initialize_drive_service()
        self._verify_folder_access()
    
    def _initialize_drive_service(self):
        """Initialize Google Drive API service."""
        try:
            print("🔑 Initializing Google Drive API...")
            
            # Define the scope for Google Drive API
            SCOPES = ['https://www.googleapis.com/auth/drive']
            
            # Load credentials from service account file
            credentials = Credentials.from_service_account_file(
                self.service_account_file, scopes=SCOPES
            )
            
            # Build the Drive service
            self.drive_service = build('drive', 'v3', credentials=credentials)
            print("✅ Google Drive API initialized successfully.")
            
        except Exception as e:
            print(f"❌ Failed to initialize Google Drive API: {e}")
            self.drive_service = None
    
    def _verify_folder_access(self):
        """Verify access to the specified Google Drive folder."""
        if not self.drive_service:
            return
            
        try:
            # Try to get folder info
            folder = self.drive_service.files().get(fileId=self.folder_id).execute()
            print(f"✅ Access verified to folder: {folder.get('name', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Failed to access folder {self.folder_id}: {e}")
            print("   Please ensure the service account has access to this folder.")
    
    def _get_file_hash(self, file_path):
        """Generate MD5 hash of file for caching."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def _generate_entity_id(self, screenshot_filename):
        """
        Parse screenshot filename to extract entity_id.
        Example: 'screenshots_fast/_10_Trial__aqd4yd_20250620104000856_0.png' -> '_10_trial_aqd4yd'
        """
        if not screenshot_filename or screenshot_filename == '':
            return "unknown_entity"
        
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
            
            # Ensure it's not empty
            if not sanitized_id:
                sanitized_id = "unknown_entity"
                
            return sanitized_id
        except Exception as e:
            print(f"⚠️  Could not generate entity_id for '{screenshot_filename}': {e}")
            return "unknown_entity"
    
    def _get_or_create_entity_folder(self, entity_id):
        """Get or create a folder for the entity_id within the main folder."""
        if not self.drive_service:
            return None
            
        try:
            # Check if entity folder already exists
            query = f"name='{entity_id}' and mimeType='application/vnd.google-apps.folder' and '{self.folder_id}' in parents and trashed=false"
            results = self.drive_service.files().list(q=query, spaces='drive').execute()
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            else:
                # Create new entity folder
                folder_metadata = {
                    'name': entity_id,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.folder_id]
                }
                
                folder = self.drive_service.files().create(
                    body=folder_metadata, fields='id'
                ).execute()
                
                print(f"📁 Created new entity folder: {entity_id}")
                return folder.get('id')
                
        except Exception as e:
            print(f"⚠️ Failed to get/create entity folder {entity_id}: {e}")
            return None
    
    def upload_screenshot(self, local_file_path, entity_name=None, url=None):
        """
        Upload a screenshot to Google Drive with metadata.
        
        Args:
            local_file_path (str): Path to local screenshot file
            entity_name (str): Name of the entity (optional)
            url (str): URL where screenshot was taken (optional)
            
        Returns:
            dict: Upload result with status and Google Drive file info
        """
        if not self.drive_service:
            return {
                'success': False,
                'error': 'Google Drive service not initialized',
                'local_path': local_file_path
            }
        
        if not os.path.exists(local_file_path):
            return {
                'success': False,
                'error': 'Local file does not exist',
                'local_path': local_file_path
            }
        
        try:
            # Generate file hash for caching
            file_hash = self._get_file_hash(local_file_path)
            if file_hash in self.upload_cache:
                print(f"⏭️ Skipping {os.path.basename(local_file_path)} - already uploaded")
                self.upload_stats['skipped_uploads'] += 1
                return {
                    'success': True,
                    'skipped': True,
                    'file_id': self.upload_cache[file_hash],
                    'local_path': local_file_path
                }
            
            # Get file info
            file_size = os.path.getsize(local_file_path)
            file_name = os.path.basename(local_file_path)
            
            # Generate entity_id from filename
            entity_id = self._generate_entity_id(local_file_path)
            
            # Get or create entity folder
            entity_folder_id = self._get_or_create_entity_folder(entity_id)
            
            # Determine MIME type
            mime_type = mimetypes.guess_type(local_file_path)[0] or 'application/octet-stream'
            
            # Prepare file metadata
            file_metadata = {
                'name': file_name,
                'parents': [entity_folder_id] if entity_folder_id else [self.folder_id]
            }
            
            # Add custom properties for entity info
            properties = {
                'entity_id': entity_id,
                'upload_timestamp': datetime.now().isoformat()
            }
            
            if entity_name:
                properties['entity_name'] = entity_name
            
            if url:
                properties['source_url'] = url
                
            file_metadata['properties'] = properties
            
            # Upload file
            print(f"📤 Uploading {file_name} to {entity_id}/ ({file_size / 1024 / 1024:.1f}MB)...")
            
            media = MediaFileUpload(
                local_file_path,
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,size'
            ).execute()
            
            # Cache the upload
            if file_hash:
                self.upload_cache[file_hash] = file['id']
            
            # Update stats
            self.upload_stats['total_uploads'] += 1
            self.upload_stats['successful_uploads'] += 1
            self.upload_stats['total_size_uploaded'] += file_size
            
            print(f"✅ Uploaded: {file_name} -> {entity_id}/")
            
            return {
                'success': True,
                'file_id': file['id'],
                'file_name': file['name'],
                'entity_id': entity_id,
                'web_link': file['webViewLink'],
                'size': file.get('size', file_size),
                'local_path': local_file_path
            }
            
        except HttpError as e:
            error_msg = f"Google Drive API error: {e}"
            print(f"❌ {error_msg}")
            self.upload_stats['failed_uploads'] += 1
            return {
                'success': False,
                'error': error_msg,
                'local_path': local_file_path
            }
        except Exception as e:
            error_msg = f"Upload failed: {e}"
            print(f"❌ {error_msg}")
            self.upload_stats['failed_uploads'] += 1
            return {
                'success': False,
                'error': error_msg,
                'local_path': local_file_path
            }
    
    def upload_screenshot_batch(self, screenshot_dir, delete_after_upload=False):
        """
        Upload all screenshots from a directory to Google Drive.
        
        Args:
            screenshot_dir (str): Directory containing screenshots
            delete_after_upload (bool): Whether to delete local files after successful upload
            
        Returns:
            dict: Batch upload results
        """
        if not os.path.exists(screenshot_dir):
            return {
                'success': False,
                'error': f'Screenshot directory does not exist: {screenshot_dir}'
            }
        
        results = {
            'total_files': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'deleted_files': 0,
            'uploaded_files': []
        }
        
        # Get all image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
        files_to_upload = []
        
        for root, dirs, files in os.walk(screenshot_dir):
            for file in files:
                if os.path.splitext(file)[1].lower() in image_extensions:
                    files_to_upload.append(os.path.join(root, file))
        
        results['total_files'] = len(files_to_upload)
        print(f"📁 Found {len(files_to_upload)} screenshots to upload...")
        
        # Upload each file
        for file_path in files_to_upload:
            result = self.upload_screenshot(file_path)
            
            if result['success']:
                results['successful_uploads'] += 1
                results['uploaded_files'].append(result)
                
                # Delete local file if requested
                if delete_after_upload and not result.get('skipped', False):
                    try:
                        os.remove(file_path)
                        results['deleted_files'] += 1
                        print(f"🗑️ Deleted local file: {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete local file {file_path}: {e}")
            else:
                results['failed_uploads'] += 1
        
        return results
    
    def get_upload_stats(self):
        """Get current upload statistics."""
        return self.upload_stats.copy()
    
    def cleanup_old_local_screenshots(self, screenshot_dir, days_old=7):
        """
        Clean up old local screenshots to free disk space.
        
        Args:
            screenshot_dir (str): Directory containing screenshots
            days_old (int): Delete files older than this many days
        """
        if not os.path.exists(screenshot_dir):
            return
        
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        deleted_count = 0
        freed_space = 0
        
        for root, dirs, files in os.walk(screenshot_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) < cutoff_time:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        freed_space += file_size
                        print(f"🗑️ Deleted old file: {file}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete {file}: {e}")
        
        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} old files, freed {freed_space / 1024 / 1024:.1f}MB")
        else:
            print("🧹 No old files found to clean up")

# Convenience function for quick upload
def upload_screenshot_to_gdrive(local_file_path, entity_name=None, url=None):
    """
    Quick function to upload a single screenshot to Google Drive.
    
    Args:
        local_file_path (str): Path to screenshot file
        entity_name (str): Entity name (optional)
        url (str): Source URL (optional)
        
    Returns:
        dict: Upload result
    """
    manager = GoogleDriveScreenshotManager()
    return manager.upload_screenshot(local_file_path, entity_name, url)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Google Drive Screenshot Manager')
    parser.add_argument('--dir', default='screenshots_fast', help='Screenshot directory to upload (default: screenshots_fast)')
    parser.add_argument('--keep-local', action='store_true', help='Keep local files after upload (default: delete)')
    parser.add_argument('--cleanup-days', type=int, default=7, help='Delete local files older than N days (default: 7)')
    parser.add_argument('--cleanup-only', action='store_true', help='Only clean up old files, no upload')
    parser.add_argument('--stats-only', action='store_true', help='Show stats only, no upload')
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = GoogleDriveScreenshotManager()
    
    if args.stats_only:
        # Show stats only
        stats = manager.get_upload_stats()
        print(f"\n📊 Upload Statistics:")
        print(f"   Total uploads: {stats['total_uploads']}")
        print(f"   Successful: {stats['successful_uploads']}")
        print(f"   Failed: {stats['failed_uploads']}")
        print(f"   Skipped: {stats['skipped_uploads']}")
        print(f"   Total size: {stats['total_size_uploaded'] / 1024 / 1024:.1f}MB")
        exit(0)
    
    if args.cleanup_only:
        # Clean up old files only
        print(f"🧹 Cleaning up files older than {args.cleanup_days} days...")
        manager.cleanup_old_local_screenshots(args.dir, days_old=args.cleanup_days)
        exit(0)
    
    # Check if screenshots directory exists
    screenshot_dir = args.dir
    if os.path.exists(screenshot_dir):
        print(f"\n📁 Found screenshots directory: {screenshot_dir}")
        
        # Count files
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
        files_to_upload = []
        
        for root, dirs, files in os.walk(screenshot_dir):
            for file in files:
                if os.path.splitext(file)[1].lower() in image_extensions:
                    files_to_upload.append(os.path.join(root, file))
        
        print(f"📊 Found {len(files_to_upload)} screenshots to upload")
        
        if len(files_to_upload) > 0:
            print(f"\n🚀 Starting batch upload...")
            print(f"   Directory: {screenshot_dir}")
            print(f"   Keep local files: {args.keep_local}")
            
            # Upload all files from directory
            results = manager.upload_screenshot_batch(screenshot_dir, delete_after_upload=not args.keep_local)
            
            print(f"\n📈 Upload Results:")
            print(f"   Total files: {results['total_files']}")
            print(f"   Successful: {results['successful_uploads']}")
            print(f"   Failed: {results['failed_uploads']}")
            print(f"   Deleted locally: {results['deleted_files']}")
            
            # Show upload stats
            stats = manager.get_upload_stats()
            print(f"\n📊 Overall Stats:")
            print(f"   Total uploads: {stats['total_uploads']}")
            print(f"   Successful: {stats['successful_uploads']}")
            print(f"   Failed: {stats['failed_uploads']}")
            print(f"   Skipped: {stats['skipped_uploads']}")
            print(f"   Total size: {stats['total_size_uploaded'] / 1024 / 1024:.1f}MB")
            
        else:
            print("📭 No image files found in screenshots directory")
    else:
        print(f"❌ Screenshots directory not found: {screenshot_dir}")
        print("   Available options:")
        print("   --dir <directory>     Specify screenshot directory")
        print("   --keep-local          Keep local files after upload")
        print("   --cleanup-only        Only clean up old files")
        print("   --stats-only          Show upload statistics")
        print("   --cleanup-days <N>    Delete files older than N days")
    
    print("\n✅ Google Drive Screenshot Manager completed!") 