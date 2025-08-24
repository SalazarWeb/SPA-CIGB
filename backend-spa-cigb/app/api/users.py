from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_user
from app.services.user_service import UserService
from app.schemas.user import User, UserUpdate, UserCreate

router = APIRouter()

@router.get("/", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = Query(None, regex="^(patient|doctor|admin)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de usuarios (solo para doctores y administradores)"""
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver la lista de usuarios"
        )
    
    user_service = UserService(db)
    
    if role == "patient":
        return user_service.get_patients(skip=skip, limit=limit)
    elif role == "doctor":
        return user_service.get_doctors(skip=skip, limit=limit)
    else:
        return user_service.get_users(skip=skip, limit=limit)

@router.get("/patients", response_model=List[User])
async def get_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de pacientes (solo para doctores y administradores)"""
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver la lista de pacientes"
        )
    
    user_service = UserService(db)
    return user_service.get_patients(skip=skip, limit=limit)

@router.get("/doctors", response_model=List[User])
async def get_doctors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de doctores"""
    user_service = UserService(db)
    return user_service.get_doctors(skip=skip, limit=limit)

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener información de un usuario específico"""
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Los usuarios solo pueden ver su propia información, excepto doctores y admins
    if current_user.role == "patient" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver este usuario"
        )
    
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar información de usuario"""
    user_service = UserService(db)
    
    # Los usuarios solo pueden actualizar su propia información, excepto admins
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar este usuario"
        )
    
    user = user_service.update_user(user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return user

@router.post("/", response_model=User)
async def create_user(
    user: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nuevo usuario (solo para administradores y doctores que crean pacientes)"""
    
    # Admins pueden crear cualquier tipo de usuario
    if current_user.role == "admin":
        pass
    # Doctores solo pueden crear pacientes
    elif current_user.role == "doctor" and user.role == "patient":
        # Validar contraseña del doctor para mayor seguridad
        if not user.admin_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere la contraseña del doctor para crear un paciente"
            )
        
        from app.core.security import verify_password
        from app.services.user_service import UserService
        user_service_temp = UserService(db)
        current_user_db = user_service_temp.get_user(current_user.id)
        
        if not current_user_db or not verify_password(user.admin_password, current_user_db.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña incorrecta"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear usuarios"
        )

    user_service = UserService(db)
    
    # Verificar si el usuario ya existe
    if user_service.get_user_by_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )
    
    if user_service.get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Crear el usuario
    new_user = user_service.create_user(user)
    
    # Si es un paciente y se proporciona diagnóstico, crear un registro médico inicial
    if user.role == "patient" and user.diagnosis and new_user:
        from app.services.medical_record_service import MedicalRecordService
        from app.schemas.medical_record import MedicalRecordCreate
        
        medical_record_service = MedicalRecordService(db)
        initial_record = MedicalRecordCreate(
            patient_id=new_user.id,
            doctor_id=current_user.id,
            title="Diagnóstico Inicial",
            description="Registro médico inicial creado al momento del ingreso del paciente",
            diagnosis=user.diagnosis,
            treatment="",
            notes="Paciente creado por: " + current_user.first_name + " " + current_user.last_name
        )
        medical_record_service.create_medical_record(initial_record)
    
    return new_user

@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Desactivar usuario (solo para administradores)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para desactivar usuarios"
        )
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede desactivar su propia cuenta"
        )
    
    user_service = UserService(db)
    user = user_service.deactivate_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return {"message": "Usuario desactivado exitosamente"}
