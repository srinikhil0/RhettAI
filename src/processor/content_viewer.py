import os
import sys
from typing import Dict, List, Optional
from datetime import datetime
from src.database.content_db import ContentDatabase

class ContentViewer:
    def __init__(self):
        """Initialize the content viewer with database connection."""
        self.db = ContentDatabase()
        # Migrate existing JSON data if database is empty
        if not self.db.list_files():
            self.db.migrate_from_json()

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def format_date(self, date_str: str) -> str:
        """Format date string to a more readable format."""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return date_str

    def list_processed_files(self) -> None:
        """List all processed files with enhanced information."""
        files = self.db.list_files()
        if not files:
            print("\nNo processed files found.")
            return

        print("\nProcessed Files:")
        print("-" * 100)
        print(f"{'File Name':<40} {'Type':<10} {'Size':<10} {'Modified':<20} {'Slides/Pages':<15}")
        print("-" * 100)
        
        for file in files:
            size = self.format_file_size(file['file_size'])
            modified = self.format_date(file['modified_time'])
            content_count = file['total_slides'] or file['total_pages'] or 0
            
            print(f"{file['file_name']:<40} "
                  f"{file['file_type']:<10} "
                  f"{size:<10} "
                  f"{modified:<20} "
                  f"{content_count:<15}")

    def get_file_content(self, file_id: str) -> None:
        """Display content of a specific file with better formatting."""
        file_data = self.db.get_file(file_id)
        if not file_data:
            print(f"\nFile not found: {file_id}")
            return

        print(f"\nFile: {file_data['file_name']}")
        print(f"Type: {file_data['content']['type']}")
        print(f"Modified: {self.format_date(file_data['modified_time'])}")
        print(f"Processed: {self.format_date(file_data['processed_time'])}")
        print("-" * 80)

        for item in file_data['content']['content']:
            slide_num = item.get('slide_number', '')
            page_num = item.get('page_number', '')
            num = slide_num or page_num
            
            print(f"\n{'Slide' if slide_num else 'Page'} {num}:")
            print("-" * 40)
            print(item['text'])
            print("-" * 40)

    def search_content(self, query: str) -> None:
        """Search through content with enhanced results display."""
        results = self.db.search_content(query)
        if not results:
            print(f"\nNo matches found for: {query}")
            return

        print(f"\nSearch Results for: {query}")
        print("=" * 80)
        
        for file_result in results:
            print(f"\nFile: {file_result['file_name']}")
            print("-" * 80)
            
            for match in file_result['matches']:
                print(f"\nSlide {match['slide_number']}:")
                print("-" * 40)
                
                # Highlight the matching text
                text = match['text']
                # Simple highlighting - you could make this more sophisticated
                print(text)
                print("-" * 40)

def main():
    viewer = ContentViewer()
    
    while True:
        print("\nContent Viewer Menu:")
        print("1. List all processed files")
        print("2. View file content")
        print("3. Search content")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            viewer.list_processed_files()
        
        elif choice == "2":
            files = viewer.db.list_files()
            if not files:
                print("\nNo files available to view.")
                continue
                
            print("\nAvailable files:")
            for i, file in enumerate(files, 1):
                print(f"{i}. {file['file_name']}")
            
            try:
                file_num = int(input("\nEnter file number to view: ").strip())
                if 1 <= file_num <= len(files):
                    viewer.get_file_content(files[file_num-1]['file_id'])
                else:
                    print("\nInvalid file number.")
            except ValueError:
                print("\nPlease enter a valid number.")
        
        elif choice == "3":
            query = input("\nEnter search query: ").strip()
            if query:
                viewer.search_content(query)
            else:
                print("\nPlease enter a search query.")
        
        elif choice == "4":
            print("\nGoodbye!")
            break
        
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main() 