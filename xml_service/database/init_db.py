"""
Database initialization and schema setup
Creates relational tables in Supabase PostgreSQL
"""
from database.connection import db_manager


def init_database():
    """Initialize database with required tables in Supabase PostgreSQL"""
    
    create_tables_sql = """
    -- Create collision_documents table with XML column (Relational DB)
    -- This stores the XML documents created from CSV data
    CREATE TABLE IF NOT EXISTS collision_documents (
        id SERIAL PRIMARY KEY,
        request_id VARCHAR(100) UNIQUE NOT NULL,
        xml_documento XML NOT NULL,
        data_criacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        mapper_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
        status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
        validation_errors TEXT,
        source_file VARCHAR(255),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create index on status for faster queries
    CREATE INDEX IF NOT EXISTS idx_collision_status ON collision_documents(status);
    
    -- Create index on request_id for faster lookups
    CREATE INDEX IF NOT EXISTS idx_collision_request_id ON collision_documents(request_id);
    
    -- Create index on data_criacao for time-based queries
    CREATE INDEX IF NOT EXISTS idx_collision_data_criacao ON collision_documents(data_criacao);
    
    -- Create webhook_logs table to track notifications
    CREATE TABLE IF NOT EXISTS webhook_logs (
        id SERIAL PRIMARY KEY,
        request_id VARCHAR(100) NOT NULL,
        document_id INTEGER REFERENCES collision_documents(id),
        status VARCHAR(50) NOT NULL,
        webhook_url TEXT,
        response_code INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create processing_history table to track data processing
    CREATE TABLE IF NOT EXISTS processing_history (
        id SERIAL PRIMARY KEY,
        source_bucket VARCHAR(100),
        source_file VARCHAR(255),
        document_id INTEGER REFERENCES collision_documents(id),
        records_processed INTEGER DEFAULT 0,
        status VARCHAR(50) NOT NULL,
        error_message TEXT,
        started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP WITH TIME ZONE
    );
    """
    
    try:
        with db_manager.get_cursor(dict_cursor=False) as cursor:
            cursor.execute(create_tables_sql)
        print("✅ Database tables initialized successfully in Supabase PostgreSQL")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False


def drop_tables():
    """Drop all tables (use with caution)"""
    drop_sql = """
    DROP TABLE IF EXISTS webhook_logs CASCADE;
    DROP TABLE IF EXISTS processing_history CASCADE;
    DROP TABLE IF EXISTS collision_documents CASCADE;
    """
    
    try:
        with db_manager.get_cursor(dict_cursor=False) as cursor:
            cursor.execute(drop_sql)
        print("✅ Tables dropped successfully")
        return True
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        return False


if __name__ == "__main__":
    init_database()
