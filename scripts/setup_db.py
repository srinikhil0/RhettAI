import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

def setup_database():
    """Set up PostgreSQL database and schema."""
    load_dotenv()
    
    # Get database configuration
    db_config = {
        'dbname': os.getenv('POSTGRES_DB', 'rhettai'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', ''),
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }
    
    try:
        # Connect to PostgreSQL server
        print(f"Connecting to PostgreSQL server at {db_config['host']}:{db_config['port']}...")
        conn = psycopg2.connect(
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config['port']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_config['dbname'],))
        exists = cursor.fetchone()
        
        if exists:
            print(f"Database '{db_config['dbname']}' already exists. Dropping it...")
            cursor.execute(f"DROP DATABASE {db_config['dbname']}")
        
        print(f"Creating database '{db_config['dbname']}'...")
        cursor.execute(f"CREATE DATABASE {db_config['dbname']}")
        print("Database created successfully!")
        
        # Close connection to default database
        cursor.close()
        conn.close()
        
        # Connect to the new database
        print(f"Connecting to database '{db_config['dbname']}'...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Create extensions
        print("Creating required extensions...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch")
        
        # Create tables
        print("Creating tables...")
        
        # Files table
        cursor.execute('''
            CREATE TABLE files (
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
        
        # Content table
        cursor.execute('''
            CREATE TABLE content (
                id SERIAL PRIMARY KEY,
                file_id TEXT NOT NULL REFERENCES files(file_id) ON DELETE CASCADE,
                slide_number INTEGER,
                page_number INTEGER,
                text_compressed BYTEA NOT NULL,
                text_length INTEGER NOT NULL,
                content_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute('CREATE INDEX idx_files_name ON files(file_name)')
        cursor.execute('CREATE INDEX idx_files_type ON files(file_type)')
        cursor.execute('CREATE INDEX idx_content_file ON content(file_id)')
        cursor.execute('CREATE INDEX idx_content_slide ON content(slide_number)')
        cursor.execute('CREATE INDEX idx_content_page ON content(page_number)')
        
        # Create full-text search index
        cursor.execute('''
            CREATE INDEX idx_content_text 
            ON content USING gin(to_tsvector('english', text_compressed::text))
        ''')
        
        conn.commit()
        print("\nDatabase setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    setup_database() 