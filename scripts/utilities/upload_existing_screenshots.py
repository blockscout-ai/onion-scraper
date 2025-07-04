#!/usr/bin/env python3
"""
Upload existing screenshots to Google Drive without deleting local files.
This allows verification before cleanup.
"""

import os
import sys
import time
from gdrive_screenshot_manager import GoogleDriveScreenshotManager

def upload_existing_screenshots(screenshot_dir="screenshots_fast", folder_id="1X5iXBO1AtQ8-VHK5cdVQkwkNByEnATSa"):
    """
    Upload all existing screenshots to Google Drive without deleting local files.
    
    Args:
        screenshot_dir (str): Directory containing screenshots to upload
        folder_id (str): Google Drive folder ID to upload to
    """
    print("🚀 Starting screenshot upload to Google Drive...")
    print(f"📁 Source directory: {screenshot_dir}")
    print(f"☁️  Destination folder ID: {folder_id}")
    print()
    
    # Initialize the manager
    manager = GoogleDriveScreenshotManager(folder_id=folder_id)
    
    if not manager.drive_service:
        print("❌ Failed to initialize Google Drive service. Exiting.")
        return False
    
    # Check if source directory exists
    if not os.path.exists(screenshot_dir):
        print(f"❌ Source directory '{screenshot_dir}' does not exist.")
        return False
    
    # Count files first
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
    files_to_upload = []
    
    for root, dirs, files in os.walk(screenshot_dir):
        for file in files:
            if os.path.splitext(file)[1].lower() in image_extensions:
                files_to_upload.append(os.path.join(root, file))
    
    if not files_to_upload:
        print(f"❌ No image files found in '{screenshot_dir}'")
        return False
    
    print(f"📊 Found {len(files_to_upload)} screenshots to upload")
    print("⚠️  Files will NOT be deleted after upload - manual verification required")
    print()
    
    # Ask for confirmation
    response = input("Continue with upload? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Upload cancelled.")
        return False
    
    # Upload files (without deleting)
    print("\n📤 Starting upload process...")
    results = manager.upload_screenshot_batch(screenshot_dir, delete_after_upload=False)
    
    # Print results
    print("\n" + "="*50)
    print("📊 UPLOAD RESULTS")
    print("="*50)
    print(f"Total files found: {results['total_files']}")
    print(f"Successful uploads: {results['successful_uploads']}")
    print(f"Failed uploads: {results['failed_uploads']}")
    print(f"Skipped (already uploaded): {manager.upload_stats['skipped_uploads']}")
    
    if results['successful_uploads'] > 0:
        total_size_mb = manager.upload_stats['total_size_uploaded'] / (1024 * 1024)
        print(f"Total size uploaded: {total_size_mb:.1f}MB")
    
    print("\n" + "="*50)
    print("🔍 NEXT STEPS")
    print("="*50)
    print("1. Check Google Drive to verify all files uploaded correctly")
    print("2. Verify entity_id folders were created properly")
    print("3. Run cleanup script to delete local files (optional)")
    print()
    
    if results['successful_uploads'] > 0:
        print("✅ Upload completed successfully!")
        print("🔗 Check your Google Drive folder to verify uploads")
        return True
    else:
        print("❌ No files were uploaded successfully.")
        return False

def cleanup_after_verification(screenshot_dir="screenshots_fast", days_old=1):
    """
    Clean up local screenshots after verification.
    Only deletes files older than specified days AND confirmed to exist in Google Drive.
    """
    print("🧹 Starting cleanup of local screenshots...")
    print(f"📁 Directory: {screenshot_dir}")
    print(f"⏰ Only deleting files older than {days_old} day(s) and confirmed in Google Drive")
    print()
    response = input("Are you sure you want to delete local screenshots? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Cleanup cancelled.")
        return
    manager = GoogleDriveScreenshotManager()
    cutoff_time = time.time() - (days_old * 24 * 60 * 60)
    deleted_count = 0
    kept_count = 0
    for root, dirs, files in os.walk(screenshot_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getmtime(file_path) < cutoff_time:
                if manager.file_exists_in_drive(file_path):
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        print(f"🗑️ Deleted local file (confirmed in Drive): {file}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete {file}: {e}")
                else:
                    kept_count += 1
                    print(f"⏭️ Kept local file (not found in Drive): {file}")
    print(f"🧹 Cleanup complete. Deleted: {deleted_count}, Kept: {kept_count}")

if __name__ == "__main__":
    # Default to the folder ID we found
    FOLDER_ID = "1X5iXBO1AtQ8-VHK5cdVQkwkNByEnATSa"
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "upload":
            # Upload screenshots
            success = upload_existing_screenshots(folder_id=FOLDER_ID)
            if success:
                print("\n🎉 Upload completed! Check Google Drive to verify.")
            else:
                print("\n❌ Upload failed. Check errors above.")
                
        elif command == "cleanup":
            # Clean up after verification
            cleanup_after_verification()
            
        elif command == "both":
            # Upload then cleanup
            success = upload_existing_screenshots(folder_id=FOLDER_ID)
            if success:
                print("\n" + "="*50)
                print("🧹 Ready for cleanup phase...")
                print("="*50)
                cleanup_after_verification()
            else:
                print("\n❌ Skipping cleanup due to upload failures.")
        else:
            print("Usage: python3 upload_existing_screenshots.py [upload|cleanup|both]")
            print("  upload  - Upload screenshots to Google Drive")
            print("  cleanup - Delete local screenshots after verification")
            print("  both    - Upload then cleanup")
    else:
        # Default: just upload
        upload_existing_screenshots(folder_id=FOLDER_ID) 