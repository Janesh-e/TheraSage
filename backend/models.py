from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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