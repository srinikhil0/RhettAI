import os
import json
import zlib
from typing import Dict, List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

class ContentDatabase:
    def __init__(self):
        """Initialize the database connection pool."""
        load_dotenv()
        
        # Get database configuration from environment variables
        self.db_config = {
            'dbname': os.getenv('POSTGRES_DB', 'rhettai'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', ''),
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        
        # Create connection pool
        self.pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **self.db_config
        )
        
        # Initialize database schema
        self._init_db()

    def _get_connection(self):
        """Get a connection from the pool."""
        return self.pool.getconn()

    def _return_connection(self, conn):
        """Return a connection to the pool."""
        self.pool.putconn(conn)

    def _init_db(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                # Create files table with additional metadata
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS files (
                        file_id TEXT PRIMARY KEY,
                        file_name TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        modified_time TIMESTAMP NOT NULL,
                        processed_time TIMESTAMP NOT NULL,
                        total_slides INTEGER,
                        total_pages INTEGER,
                        file_size BIGINT,
                        content_hash TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create content table with compression
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS content (
                        id SERIAL PRIMARY KEY,
                        file_id TEXT NOT NULL REFERENCES files(file_id) ON DELETE CASCADE,
                        slide_number INTEGER,
                        page_number INTEGER,
                        text_compressed BYTEA NOT NULL,
                        text_length INTEGER NOT NULL,
                        content_type TEXT,
                        text_uncompressed TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_name ON files(file_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_file ON content(file_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_slide ON content(slide_number)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_page ON content(page_number)')
                
                # Create full-text search index
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_content_text 
                    ON content USING gin(to_tsvector('english', text_compressed::text))
                ''')
                
                conn.commit()

    def _compress_text(self, text: str) -> bytes:
        """Compress text using zlib."""
        return zlib.compress(text.encode('utf-8'))

    def _decompress_text(self, compressed: bytes) -> str:
        """Decompress text using zlib."""
        return zlib.decompress(compressed).decode('utf-8')

    def store_file(self, file_data: Dict):
        """Store file metadata and its content in the database."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    # Calculate content hash
                    content_hash = hash(str(file_data['content']))
                    
                    # Get file size if file exists
                    file_size = 0
                    if os.path.exists(file_data.get('file_path', '')):
                        file_size = os.path.getsize(file_data['file_path'])
                    
                    # Store file metadata
                    cursor.execute('''
                        INSERT INTO files 
                        (file_id, file_name, file_type, modified_time, processed_time, 
                        total_slides, total_pages, file_size, content_hash, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (file_id) DO UPDATE SET
                            file_name = EXCLUDED.file_name,
                            file_type = EXCLUDED.file_type,
                            modified_time = EXCLUDED.modified_time,
                            processed_time = EXCLUDED.processed_time,
                            total_slides = EXCLUDED.total_slides,
                            total_pages = EXCLUDED.total_pages,
                            file_size = EXCLUDED.file_size,
                            content_hash = EXCLUDED.content_hash,
                            updated_at = CURRENT_TIMESTAMP
                    ''', (
                        file_data['file_id'],
                        file_data['file_name'],
                        file_data['content']['type'],
                        file_data['modified_time'],
                        file_data['processed_time'],
                        file_data['content'].get('total_slides'),
                        file_data['content'].get('total_pages'),
                        file_size,
                        str(content_hash)
                    ))
                    
                    # Delete existing content
                    cursor.execute('DELETE FROM content WHERE file_id = %s', (file_data['file_id'],))
                    
                    # Store content
                    for item in file_data['content']['content']:
                        text = item['text']
                        compressed = self._compress_text(text)
                        
                        cursor.execute('''
                            INSERT INTO content 
                            (file_id, slide_number, page_number, text_compressed, text_length, content_type, text_uncompressed)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            file_data['file_id'],
                            item.get('slide_number'),
                            item.get('page_number'),
                            compressed,
                            len(text),
                            file_data['content']['type'],
                            text
                        ))
                    
                    conn.commit()
                    
                except Exception as e:
                    conn.rollback()
                    raise Exception(f"Error storing file {file_data['file_name']}: {e}")

    def get_file(self, file_id: str) -> Optional[Dict]:
        """Retrieve a file and its content from the database."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Get file metadata
                cursor.execute('SELECT * FROM files WHERE file_id = %s', (file_id,))
                file_row = cursor.fetchone()
                if not file_row:
                    return None
                
                # Get content
                cursor.execute('''
                    SELECT slide_number, page_number, text_compressed, content_type 
                    FROM content 
                    WHERE file_id = %s 
                    ORDER BY COALESCE(slide_number, page_number)
                ''', (file_id,))
                content_rows = cursor.fetchall()
                
                # Construct response
                return {
                    'file_id': file_row['file_id'],
                    'file_name': file_row['file_name'],
                    'file_type': file_row['file_type'],
                    'modified_time': file_row['modified_time'].isoformat(),
                    'processed_time': file_row['processed_time'].isoformat(),
                    'content': {
                        'type': file_row['file_type'],
                        'total_slides': file_row['total_slides'],
                        'total_pages': file_row['total_pages'],
                        'content': [
                            {
                                'slide_number': row['slide_number'],
                                'page_number': row['page_number'],
                                'text': self._decompress_text(row['text_compressed'])
                            }
                            for row in content_rows
                        ]
                    }
                }

    def list_files(self) -> List[Dict]:
        """List all files in the database."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute('''
                    SELECT file_id, file_name, file_type, modified_time, processed_time, 
                           total_slides, total_pages, file_size
                    FROM files
                    WHERE status = 'active'
                    ORDER BY modified_time DESC
                ''')
                return [
                    {
                        'file_id': row['file_id'],
                        'file_name': row['file_name'],
                        'file_type': row['file_type'],
                        'modified_time': row['modified_time'].isoformat(),
                        'processed_time': row['processed_time'].isoformat(),
                        'total_slides': row['total_slides'],
                        'total_pages': row['total_pages'],
                        'file_size': row['file_size']
                    }
                    for row in cursor.fetchall()
                ]

    def search_content(self, query: str) -> List[Dict]:
        """Search through content using PostgreSQL full-text search on uncompressed text."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Use PostgreSQL's full-text search on text_uncompressed
                cursor.execute('''
                    SELECT f.file_id, f.file_name, c.slide_number, c.page_number, c.text_uncompressed
                    FROM files f
                    JOIN content c ON f.file_id = c.file_id
                    WHERE to_tsvector('english', c.text_uncompressed) @@ plainto_tsquery('english', %s)
                    ORDER BY f.modified_time DESC
                ''', (query,))
                
                results = []
                current_file = None
                
                for row in cursor.fetchall():
                    if not current_file or current_file['file_id'] != row['file_id']:
                        if current_file:
                            results.append(current_file)
                        current_file = {
                            'file_id': row['file_id'],
                            'file_name': row['file_name'],
                            'matches': []
                        }
                    
                    current_file['matches'].append({
                        'slide_number': row['slide_number'],
                        'page_number': row['page_number'],
                        'text': row['text_uncompressed']
                    })
                
                if current_file:
                    results.append(current_file)
                
                return results

    def migrate_from_json(self):
        """Migrate data from JSON files to the database."""
        json_dir = "processed_content"
        if not os.path.exists(json_dir):
            return
        
        for filename in os.listdir(json_dir):
            if filename.endswith('.json') and filename != 'metadata.json':
                file_path = os.path.join(json_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        file_data = json.load(f)
                        self.store_file(file_data)
                except Exception as e:
                    print(f"Error migrating {filename}: {e}")

    def __del__(self):
        """Clean up the connection pool when the object is destroyed."""
        if hasattr(self, 'pool'):
            self.pool.closeall() 