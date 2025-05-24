import os
import time
from dotenv import load_dotenv
from src.drive.monitor import DriveMonitor
from src.drive.downloader import DriveDownloader
from src.processor.processor import ContentProcessor
from src.database.content_db import ContentDatabase

def process_files(files, processor):
    """Process a list of files."""
    for file in files:
        file_path = os.path.join("downloads", file['name'])
        if os.path.exists(file_path):
            processor.process_file(
                file_path=file_path,
                file_id=file['id'],
                mime_type=file['mimeType'],
                modified_time=file['modifiedTime']
            )

def main():
    # Load environment variables
    load_dotenv()
    
    # Get folder ID from environment variable
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    if not folder_id:
        print("Error: GOOGLE_DRIVE_FOLDER_ID not found in environment variables")
        return

    # Check for GCP credentials
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        print("Warning: GOOGLE_APPLICATION_CREDENTIALS not set. Will try to use OAuth2 flow.")

    # Initialize components
    monitor = DriveMonitor(folder_id)
    downloader = DriveDownloader(monitor.service)
    processor = ContentProcessor()
    db = ContentDatabase()

    print("RhettAI - AI-powered educational assistant")
    print("=========================================")
    print("\nInitializing...")

    # Process any existing files in downloads directory
    if os.path.exists("downloads"):
        existing_files = []
        for filename in os.listdir("downloads"):
            # Get file metadata from Drive
            file_metadata = monitor.get_folder_contents()
            if file_metadata:
                existing_files.extend(file_metadata)
        
        if existing_files:
            print(f"\nProcessing {len(existing_files)} existing files...")
            process_files(existing_files, processor)

    print("\nStarting Drive monitor...")
    print("Press Ctrl+C to stop")

    try:
        while True:
            # Check for new or modified files
            changes = monitor.check_for_updates()
            
            if changes:
                print(f"\nFound {len(changes)} changes:")
                for change in changes:
                    print(f"- {change['name']} ({change['mimeType']})")
                
                # Download new/modified files
                for file in changes:
                    downloader.download_file(file)
                
                # Process the files
                process_files(changes, processor)
            
            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        print("\nStopping RhettAI...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("Goodbye!")

if __name__ == "__main__":
    main() 