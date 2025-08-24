from sqlalchemy.orm import Session
from app.models.models import Patient as PatientModel
from app.schemas.patient import PatientCreate, PatientUpdate
from typing import List, Optional

class PatientService:
    def __init__(self, db: Session):
        self.db = db

    def create_patient(self, patient: PatientCreate, created_by_user_id: int) -> PatientModel:
        """Crear nuevo registro de paciente"""
        db_patient = PatientModel(
            first_name=patient.first_name,
            last_name=patient.last_name,
            initial_diagnosis=patient.initial_diagnosis,
            created_by_user_id=created_by_user_id
        )
        self.db.add(db_patient)
        self.db.commit()
        self.db.refresh(db_patient)
        return db_patient

    def get_patient(self, patient_id: int) -> Optional[PatientModel]:
        """Obtener paciente por ID"""
        return self.db.query(PatientModel).filter(PatientModel.id == patient_id).first()

    def get_patients(self, skip: int = 0, limit: int = 100, created_by_user_id: Optional[int] = None) -> List[PatientModel]:
        """Obtener lista de pacientes"""
        query = self.db.query(PatientModel)
        
        if created_by_user_id:
            query = query.filter(PatientModel.created_by_user_id == created_by_user_id)
            
        return query.offset(skip).limit(limit).all()

    def update_patient(self, patient_id: int, patient_update: PatientUpdate) -> Optional[PatientModel]:
        """Actualizar información del paciente"""
        db_patient = self.get_patient(patient_id)
        if not db_patient:
            return None

        update_data = patient_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_patient, key, value)

        self.db.commit()
        self.db.refresh(db_patient)
        return db_patient

    def delete_patient(self, patient_id: int) -> bool:
        """Eliminar registro de paciente"""
        db_patient = self.get_patient(patient_id)
        if not db_patient:
            return False

        self.db.delete(db_patient)
        self.db.commit()
        return True

    def get_patients_with_files(self, created_by_user_id: Optional[int] = None) -> List[PatientModel]:
        """Obtener pacientes que tienen archivos asociados"""
        from app.models.models import UploadedFile
        
        query = self.db.query(PatientModel).join(
            UploadedFile, PatientModel.id == UploadedFile.patient_record_id
        ).distinct()
        
        if created_by_user_id:
            query = query.filter(PatientModel.created_by_user_id == created_by_user_id)
            
        return query.all()
