# database_migration.py - Add summary and context tracking

from sqlalchemy import text
from db import engine

def add_summary_features():
    """Add enhanced summary and context features to existing database"""
    
    with engine.connect() as conn:
        # Add columns for better session context management
        try:
            # Check if columns exist before adding them (SQLite compatible)
            
            # Check if conversation_summary column exists
            result = conn.execute(text("PRAGMA table_info(chat_sessions)")).fetchall()
            columns = [row[1] for row in result]
            
            if 'conversation_summary' not in columns:
                conn.execute(text("""
                    ALTER TABLE chat_sessions 
                    ADD COLUMN conversation_summary TEXT;
                """))
            
            # Add context metadata column for tracking conversation flow (SQLite uses TEXT for JSON)
            if 'context_metadata' not in columns:
                conn.execute(text("""
                    ALTER TABLE chat_sessions 
                    ADD COLUMN context_metadata TEXT DEFAULT '{}';
                """))
            
            # Check if response_quality_score column exists in chat_messages
            result = conn.execute(text("PRAGMA table_info(chat_messages)")).fetchall()
            message_columns = [row[1] for row in result]
            
            if 'response_quality_score' not in message_columns:
                conn.execute(text("""
                    ALTER TABLE chat_messages 
                    ADD COLUMN response_quality_score FLOAT DEFAULT NULL;
                """))
            
            # Add conversation flow tracking (check if column exists first)
            if 'conversation_flow' not in message_columns:
                conn.execute(text("""
                    ALTER TABLE chat_messages 
                    ADD COLUMN conversation_flow VARCHAR(50) DEFAULT NULL;
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