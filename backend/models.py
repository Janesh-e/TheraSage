from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime
from db import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

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