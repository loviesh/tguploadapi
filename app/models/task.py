from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from uuid import uuid4

from app.database.setup import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    url = Column(String, nullable=False)
    channel_message_id = Column(String, nullable=True)  # Message ID in the private channel
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    error_message = Column(String, nullable=True)
    force_document = Column(Boolean, default=False)  # Whether to force send as document 