from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_user
from app.services.patient_service import PatientService
from app.services.user_service import UserService
from app.schemas.patient import Patient, PatientCreate, PatientUpdate
from app.schemas.user import User
from app.core.security import verify_password

router = APIRouter()

@router.post("/", response_model=Patient)
async def create_patient(
    patient: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nuevo registro de paciente (solo para doctores y administradores)"""
    
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear registros de pacientes"
        )

    # Validar contraseña del usuario actual para mayor seguridad
    if not patient.admin_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere su contraseña para crear un registro de paciente"
        )

    user_service = UserService(db)
    current_user_db = user_service.get_user(current_user.id)
    
    if not current_user_db or not verify_password(patient.admin_password, current_user_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta"
        )

    patient_service = PatientService(db)
    return patient_service.create_patient(patient, current_user.id)

@router.get("/", response_model=List[Patient])
async def get_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de registros de pacientes"""
    
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver los registros de pacientes"
        )

    patient_service = PatientService(db)
    
    # Los doctores solo pueden ver sus propios pacientes, los admin pueden ver todos
    created_by_user_id = None if current_user.role == "admin" else current_user.id
    
    return patient_service.get_patients(skip=skip, limit=limit, created_by_user_id=created_by_user_id)

@router.get("/{patient_id}", response_model=Patient)
async def get_patient(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener información de un registro de paciente específico"""
    
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver registros de pacientes"
        )

    patient_service = PatientService(db)
    patient = patient_service.get_patient(patient_id)
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de paciente no encontrado"
        )

    # Los doctores solo pueden ver sus propios pacientes
    if current_user.role == "doctor" and patient.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver este registro de paciente"
        )

    return patient

@router.put("/{patient_id}", response_model=Patient)
async def update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar información de un registro de paciente"""
    
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar registros de pacientes"
        )

    patient_service = PatientService(db)
    patient = patient_service.get_patient(patient_id)
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de paciente no encontrado"
        )

    # Los doctores solo pueden actualizar sus propios pacientes
    if current_user.role == "doctor" and patient.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar este registro de paciente"
        )

    updated_patient = patient_service.update_patient(patient_id, patient_update)
    
    if not updated_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error al actualizar el registro de paciente"
        )

    return updated_patient

@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un registro de paciente"""
    
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar registros de pacientes"
        )

    patient_service = PatientService(db)
    patient = patient_service.get_patient(patient_id)
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de paciente no encontrado"
        )

    # Los doctores solo pueden eliminar sus propios pacientes
    if current_user.role == "doctor" and patient.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar este registro de paciente"
        )

    success = patient_service.delete_patient(patient_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error al eliminar el registro de paciente"
        )

    return {"message": "Registro de paciente eliminado exitosamente"}
