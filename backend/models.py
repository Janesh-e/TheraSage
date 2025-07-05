from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class ConversationMessage(Base):
    __tablename__ = 'conversation_messages'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    sender = Column(String)  # 'user' or 'assistant'
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class JournalEntry(Base):
    __tablename__ = 'journal_entries'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    entry_type = Column(String)  # 'cbt_summary', 'positive_reflection', etc.
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)