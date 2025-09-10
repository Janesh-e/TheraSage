# database_migration.py - Add summary and context tracking

from sqlalchemy import text
from db import engine

def add_summary_features():
    """Add enhanced summary and context features to existing database"""
    
    with engine.connect() as conn:
        # Add columns for better session context management
        try:
            # Add session summary column if not exists
            conn.execute(text("""
                ALTER TABLE chat_sessions 
                ADD COLUMN IF NOT EXISTS conversation_summary TEXT;
            """))
            
            # Add context metadata column for tracking conversation flow
            conn.execute(text("""
                ALTER TABLE chat_sessions 
                ADD COLUMN IF NOT EXISTS context_metadata JSON DEFAULT '{}';
            """))
            
            # Add response quality tracking
            conn.execute(text("""
                ALTER TABLE chat_messages 
                ADD COLUMN IF NOT EXISTS response_quality_score FLOAT DEFAULT NULL;
            """))
            
            # Add conversation flow tracking
            conn.execute(text("""
                ALTER TABLE chat_messages 
                ADD COLUMN IF NOT EXISTS conversation_flow VARCHAR(50) DEFAULT NULL;
            """))
            
            # Add indexes for better performance
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sessions_summary 
                ON chat_sessions(user_id, last_message_at) 
                WHERE conversation_summary IS NOT NULL;
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_flow 
                ON chat_messages(session_id, conversation_flow, created_at);
            """))
            
            conn.commit()
            print("Database migration completed successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"Migration error: {e}")

if __name__ == "__main__":
    add_summary_features()