from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Esquemas para Patient
class PatientBase(BaseModel):
    first_name: str
    last_name: str
    initial_diagnosis: Optional[str] = None

class PatientCreate(PatientBase):
    admin_password: str

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    initial_diagnosis: Optional[str] = None

class PatientInDB(PatientBase):
    id: int
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Patient(PatientInDB):
    pass
