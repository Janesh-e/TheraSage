from db import SessionLocal
from models import JournalEntry
from datetime import datetime

def save_journal(user_id: str, content: str, entry_type: str = "cbt_summary"):
    db = SessionLocal()
    journal = JournalEntry(
        user_id=user_id,
        entry_type=entry_type,
        content=content,
        timestamp=datetime.utcnow()
    )
    db.add(journal)
    db.commit()
    db.close()

