from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MedicalRecordBase(BaseModel):
    title: str
    description: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None

class MedicalRecordCreate(MedicalRecordBase):
    patient_id: int

class MedicalRecordUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None

class MedicalRecordInDB(MedicalRecordBase):
    id: int
    patient_id: int
    doctor_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MedicalRecord(MedicalRecordInDB):
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
