from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_user
from app.services.medical_record_service import MedicalRecordService
from app.services.user_service import UserService
from app.schemas.user import User
from app.schemas.medical_record import MedicalRecord, MedicalRecordCreate, MedicalRecordUpdate

router = APIRouter()

@router.get("/", response_model=List[MedicalRecord])
async def get_medical_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener registros médicos"""
    medical_service = MedicalRecordService(db)
    user_service = UserService(db)
    
    if current_user.role == "patient":
        # Los pacientes solo pueden ver sus propios registros
        records = medical_service.get_medical_records_by_patient(current_user.id, skip, limit)
    elif current_user.role == "doctor":
        if patient_id:
            # Doctores pueden ver registros de pacientes específicos
            records = medical_service.get_medical_records_by_patient(patient_id, skip, limit)
        else:
            # Doctores pueden ver todos los registros que han creado
            records = medical_service.get_medical_records_by_doctor(current_user.id, skip, limit)
    else:  # admin
        if patient_id:
            records = medical_service.get_medical_records_by_patient(patient_id, skip, limit)
        else:
            records = medical_service.get_all_medical_records(skip, limit)
    
    # Agregar nombres de paciente y doctor
    result = []
    for record in records:
        patient = user_service.get_user(record.patient_id)
        doctor = user_service.get_user(record.doctor_id)
        
        record_dict = record.__dict__.copy()
        record_dict['patient_name'] = f"{patient.first_name} {patient.last_name}" if patient else None
        record_dict['doctor_name'] = f"{doctor.first_name} {doctor.last_name}" if doctor else None
        
        result.append(MedicalRecord(**record_dict))
    
    return result

@router.get("/{record_id}", response_model=MedicalRecord)
async def get_medical_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener un registro médico específico"""
    medical_service = MedicalRecordService(db)
    user_service = UserService(db)
    
    record = medical_service.get_medical_record(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro médico no encontrado"
        )
    
    # Verificar permisos
    if not medical_service.can_access_record(record_id, current_user.id, current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a este registro"
        )
    
    # Agregar nombres de paciente y doctor
    patient = user_service.get_user(record.patient_id)
    doctor = user_service.get_user(record.doctor_id)
    
    record_dict = record.__dict__.copy()
    record_dict['patient_name'] = f"{patient.first_name} {patient.last_name}" if patient else None
    record_dict['doctor_name'] = f"{doctor.first_name} {doctor.last_name}" if doctor else None
    
    return MedicalRecord(**record_dict)

@router.post("/", response_model=MedicalRecord)
async def create_medical_record(
    record: MedicalRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nuevo registro médico (solo doctores)"""
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los doctores pueden crear registros médicos"
        )
    
    medical_service = MedicalRecordService(db)
    user_service = UserService(db)
    
    # Verificar que el paciente existe
    patient = user_service.get_user(record.patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )
    
    if patient.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario especificado no es un paciente"
        )
    
    db_record = medical_service.create_medical_record(record, current_user.id)
    
    # Agregar nombres para la respuesta
    record_dict = db_record.__dict__.copy()
    record_dict['patient_name'] = f"{patient.first_name} {patient.last_name}"
    record_dict['doctor_name'] = f"{current_user.first_name} {current_user.last_name}"
    
    return MedicalRecord(**record_dict)

@router.put("/{record_id}", response_model=MedicalRecord)
async def update_medical_record(
    record_id: int,
    record_update: MedicalRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar registro médico"""
    medical_service = MedicalRecordService(db)
    user_service = UserService(db)
    
    record = medical_service.get_medical_record(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro médico no encontrado"
        )
    
    # Solo el doctor que creó el registro o un admin pueden editarlo
    if current_user.role != "admin" and record.doctor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para editar este registro"
        )
    
    updated_record = medical_service.update_medical_record(record_id, record_update)
    if not updated_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error al actualizar el registro"
        )
    
    # Agregar nombres para la respuesta
    patient = user_service.get_user(updated_record.patient_id)
    doctor = user_service.get_user(updated_record.doctor_id)
    
    record_dict = updated_record.__dict__.copy()
    record_dict['patient_name'] = f"{patient.first_name} {patient.last_name}" if patient else None
    record_dict['doctor_name'] = f"{doctor.first_name} {doctor.last_name}" if doctor else None
    
    return MedicalRecord(**record_dict)

@router.delete("/{record_id}")
async def delete_medical_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar registro médico (solo doctores que lo crearon o admin)"""
    medical_service = MedicalRecordService(db)
    
    record = medical_service.get_medical_record(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro médico no encontrado"
        )
    
    # Solo el doctor que creó el registro o un admin pueden eliminarlo
    if current_user.role != "admin" and record.doctor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar este registro"
        )
    
    if not medical_service.delete_medical_record(record_id):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el registro"
        )
    
    return {"message": "Registro médico eliminado exitosamente"}
