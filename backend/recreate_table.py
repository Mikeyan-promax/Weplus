import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'weplus',
    'user': 'postgres',
    'password': 'postgres'
}

def recreate_table():
    print('Recreating document_chunks table...')
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Drop table if exists
        print('1. Dropping existing table...')
        cursor.execute("DROP TABLE IF EXISTS document_chunks CASCADE")
        
        # Create new table
        print('2. Creating new table...')
        cursor.execute("""
            CREATE TABLE document_chunks (
                id SERIAL PRIMARY KEY,
                document_id VARCHAR(255) NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                content_length INTEGER,
                embedding vector(2560),
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        print('3. Creating indexes...')
        cursor.execute("CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id)")
        cursor.execute("CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops)")
        
        conn.commit()
        print('4. Table recreated successfully!')
        
        # Verify table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print('5. New table structure:')
        for col in columns:
            print(f'   {col[0]}: {col[1]}')
        
        conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    recreate_table()