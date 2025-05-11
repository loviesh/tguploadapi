from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime

class UploadRequest(BaseModel):
    url: HttpUrl
    force_document: bool = False

class TaskResponse(BaseModel):
    id: str
    url: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class FileResponse(BaseModel):
    id: str
    channel_message_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProgressResponse(BaseModel):
    id: str
    status: str
    message: str 