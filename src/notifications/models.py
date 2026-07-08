from sqlalchemy import Column, Integer, String, Boolean, DateTime
from src.utils.db import Base
from datetime import datetime

class Notification(Base):
    __tablename__ = "notifications_table"
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, index=True)  # Links to user staff_id
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)