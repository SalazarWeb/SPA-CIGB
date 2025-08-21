from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UploadedFileBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    description: Optional[str] = None

class UploadedFileCreate(UploadedFileBase):
    file_path: str
    user_id: int
    medical_record_id: Optional[int] = None

class UploadedFileInDB(UploadedFileBase):
    id: int
    file_path: str
    user_id: int
    medical_record_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UploadedFile(UploadedFileInDB):
    pass

class FileUploadResponse(BaseModel):
    message: str
    file: UploadedFile
