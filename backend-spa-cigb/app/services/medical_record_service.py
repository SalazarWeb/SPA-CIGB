from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.models import MedicalRecord, User
from app.schemas.medical_record import MedicalRecordCreate, MedicalRecordUpdate

class MedicalRecordService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_medical_record(self, record_id: int) -> Optional[MedicalRecord]:
        return self.db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    
    def get_medical_records_by_patient(self, patient_id: int, skip: int = 0, limit: int = 100) -> List[MedicalRecord]:
        return (
            self.db.query(MedicalRecord)
            .filter(MedicalRecord.patient_id == patient_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_medical_records_by_doctor(self, doctor_id: int, skip: int = 0, limit: int = 100) -> List[MedicalRecord]:
        return (
            self.db.query(MedicalRecord)
            .filter(MedicalRecord.doctor_id == doctor_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_all_medical_records(self, skip: int = 0, limit: int = 100) -> List[MedicalRecord]:
        return self.db.query(MedicalRecord).offset(skip).limit(limit).all()
    
    def create_medical_record(self, record: MedicalRecordCreate, doctor_id: int) -> MedicalRecord:
        db_record = MedicalRecord(
            patient_id=record.patient_id,
            doctor_id=doctor_id,
            title=record.title,
            description=record.description,
            diagnosis=record.diagnosis,
            treatment=record.treatment,
            notes=record.notes
        )
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record
    
    def update_medical_record(self, record_id: int, record_update: MedicalRecordUpdate) -> Optional[MedicalRecord]:
        db_record = self.get_medical_record(record_id)
        if not db_record:
            return None
        
        update_data = record_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_record, field, value)
        
        self.db.commit()
        self.db.refresh(db_record)
        return db_record
    
    def delete_medical_record(self, record_id: int) -> bool:
        db_record = self.get_medical_record(record_id)
        if not db_record:
            return False
        
        self.db.delete(db_record)
        self.db.commit()
        return True
    
    def can_access_record(self, record_id: int, user_id: int, user_role: str) -> bool:
        """Verificar si un usuario puede acceder a un registro médico"""
        record = self.get_medical_record(record_id)
        if not record:
            return False
        
        # Los administradores pueden acceder a todo
        if user_role == "admin":
            return True
        
        # Los doctores pueden acceder a los registros que crearon
        if user_role == "doctor" and record.doctor_id == user_id:
            return True
        
        # Los pacientes solo pueden acceder a sus propios registros
        if user_role == "patient" and record.patient_id == user_id:
            return True
        
        return False
