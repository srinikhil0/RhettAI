import os
from dotenv import load_dotenv
from src.drive.monitor import DriveMonitor
from src.drive.downloader import DriveDownloader

def handle_new_files(files):
    """Callback function to handle newly detected files."""
    print(f"New files detected: {[f['name'] for f in files]}")
    downloader = DriveDownloader(monitor.service)
    downloaded_files = downloader.download_files(files)
    print(f"Downloaded files: {downloaded_files}")

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
    
    # Initialize and start the monitor
    global monitor
    monitor = DriveMonitor(folder_id)
    
    # Start monitoring for changes
    print("Starting file monitor...")
    monitor.start_monitoring(handle_new_files)

if __name__ == "__main__":
    main() 