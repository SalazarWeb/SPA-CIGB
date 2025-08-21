from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UploadedFileBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    description: Optional[str] = None
    file_type: str  # 'medical_record' o 'photo'

class UploadedFileCreate(UploadedFileBase):
    file_path: str
    user_id: int
    patient_id: int
    medical_record_id: Optional[int] = None

class UploadedFileInDB(UploadedFileBase):
    id: int
    file_path: str
    user_id: int
    patient_id: int
    medical_record_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UploadedFile(UploadedFileInDB):
    patient_name: Optional[str] = None
    uploader_name: Optional[str] = None

class FileUploadResponse(BaseModel):
    message: str
    files: List[UploadedFile]  # Cambio para soportar múltiples archivos

class MultiFileUploadRequest(BaseModel):
    patient_id: int
    medical_record_id: Optional[int] = None
    photo_ids: Optional[List[int]] = None  # IDs de fotos a asociar con historia clínica
    descriptions: Optional[List[str]] = None
