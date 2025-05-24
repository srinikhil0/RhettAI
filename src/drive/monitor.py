from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
from typing import List, Dict
import time
from datetime import datetime
from google.oauth2 import service_account

class DriveMonitor:
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, folder_id: str):
        self.folder_id = folder_id
        self.creds = None
        self.service = None
        self.last_check = None
        self.initialize_service()

    def initialize_service(self):
        """Initialize the Google Drive service with existing GCP credentials."""
        try:
            # Try to use existing service account credentials
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if credentials_path and os.path.exists(credentials_path):
                print(f"Using service account credentials from: {credentials_path}")
                self.creds = service_account.Credentials.from_service_account_file(
                    credentials_path, scopes=self.SCOPES)
            else:
                print("No service account credentials found, falling back to OAuth2")
                # Fallback to OAuth2 if no service account credentials found
                if os.path.exists('token.pickle'):
                    with open('token.pickle', 'rb') as token:
                        self.creds = pickle.load(token)

                if not self.creds or not self.creds.valid:
                    if self.creds and self.creds.expired and self.creds.refresh_token:
                        self.creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            'credentials.json', self.SCOPES)
                        self.creds = flow.run_local_server(port=0)
                    
                    with open('token.pickle', 'wb') as token:
                        pickle.dump(self.creds, token)

            self.service = build('drive', 'v3', credentials=self.creds)
            print("Successfully authenticated with Google Drive API")
            
        except Exception as e:
            print(f"Error initializing Google Drive service: {e}")
            raise

    def get_folder_contents(self) -> List[Dict]:
        """Get all files in the specified folder."""
        try:
            print(f"Fetching contents of folder: {self.folder_id}")
            results = self.service.files().list(
                q=f"'{self.folder_id}' in parents and trashed=false",
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            print(f"Found {len(files)} files in folder")
            for file in files:
                print(f"- {file['name']} ({file['mimeType']})")
            return files
        except Exception as e:
            print(f"Error fetching folder contents: {e}")
            return []

    def check_for_updates(self) -> List[Dict]:
        """Check for new or modified files since last check."""
        print("\nChecking for updates...")
        current_files = self.get_folder_contents()
        
        if not self.last_check:
            print("First check - all files are considered new")
            self.last_check = current_files
            return current_files

        new_files = []
        for current_file in current_files:
            current_time = datetime.fromisoformat(current_file['modifiedTime'].replace('Z', '+00:00'))
            
            # Find matching file in last check
            matching_file = next(
                (f for f in self.last_check if f['id'] == current_file['id']),
                None
            )
            
            if not matching_file:
                print(f"New file detected: {current_file['name']}")
                new_files.append(current_file)
            else:
                last_time = datetime.fromisoformat(matching_file['modifiedTime'].replace('Z', '+00:00'))
                if current_time > last_time:
                    print(f"Modified file detected: {current_file['name']}")
                    new_files.append(current_file)

        self.last_check = current_files
        return new_files

    def start_monitoring(self, callback, interval: int = 300):
        """
        Start monitoring the folder for changes.
        
        Args:
            callback: Function to call when new files are detected
            interval: Check interval in seconds (default: 5 minutes)
        """
        print(f"Starting to monitor folder {self.folder_id}")
        print(f"Check interval: {interval} seconds")
        while True:
            new_files = self.check_for_updates()
            if new_files:
                print(f"\nProcessing {len(new_files)} new/modified files...")
                callback(new_files)
            else:
                print("No new or modified files found")
            print(f"Waiting {interval} seconds until next check...")
            time.sleep(interval) 