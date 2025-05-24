from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
from typing import Dict, Optional
import mimetypes

class DriveDownloader:
    def __init__(self, service):
        self.service = service
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)

    def get_file_extension(self, mime_type: str, file_name: str) -> str:
        """Get the appropriate file extension based on mime type and file name."""
        if mime_type == 'application/vnd.google-apps.document':
            return '.docx'
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            return '.xlsx'
        elif mime_type == 'application/vnd.google-apps.presentation':
            return '.pptx'
        else:
            # Try to get extension from mime type
            ext = mimetypes.guess_extension(mime_type)
            if ext:
                return ext
            # Fallback to getting extension from file name
            return os.path.splitext(file_name)[1] or '.txt'

    def download_file(self, file_metadata: Dict) -> Optional[str]:
        """
        Download a file from Google Drive.
        
        Args:
            file_metadata: Dictionary containing file information (id, name, mimeType)
            
        Returns:
            Path to the downloaded file or None if download failed
        """
        try:
            file_id = file_metadata['id']
            file_name = file_metadata['name']
            mime_type = file_metadata['mimeType']

            # Handle Google Workspace files (Docs, Sheets, Slides)
            if mime_type.startswith('application/vnd.google-apps'):
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='application/pdf'
                )
                file_name = f"{os.path.splitext(file_name)[0]}.pdf"
            else:
                request = self.service.files().get_media(fileId=file_id)

            # Create file path
            file_extension = self.get_file_extension(mime_type, file_name)
            file_path = os.path.join(
                self.download_dir,
                f"{os.path.splitext(file_name)[0]}{file_extension}"
            )

            # Download the file
            fh = io.FileIO(file_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%")

            fh.close()
            print(f"Downloaded: {file_path}")
            return file_path

        except Exception as e:
            print(f"Error downloading file {file_name}: {e}")
            return None

    def download_files(self, files: list) -> list:
        """
        Download multiple files from Google Drive.
        
        Args:
            files: List of file metadata dictionaries
            
        Returns:
            List of paths to downloaded files
        """
        downloaded_files = []
        for file in files:
            file_path = self.download_file(file)
            if file_path:
                downloaded_files.append(file_path)
        return downloaded_files 