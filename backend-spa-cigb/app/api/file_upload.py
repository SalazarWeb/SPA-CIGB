from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.services.file_service import FileService
from app.services.medical_record_service import MedicalRecordService
from app.services.user_service import UserService
from app.schemas.user import User
from app.schemas.file import UploadedFile, FileUploadResponse

router = APIRouter()

@router.post("/upload-multiple-to-patient-record", response_model=FileUploadResponse)
async def upload_multiple_files_to_patient_record(
    files: List[UploadFile] = File(...),
    patient_record_id: int = Form(...),
    medical_record_id: Optional[int] = Form(None),
    descriptions: Optional[List[str]] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Subir múltiples archivos a un registro de paciente"""
    file_service = FileService(db)
    
    # Verificar que el registro de paciente existe
    from app.services.patient_service import PatientService
    patient_service = PatientService(db)
    patient_record = patient_service.get_patient(patient_record_id)
    
    if not patient_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de paciente no encontrado"
        )
    
    # Verificar permisos: doctores solo pueden subir archivos a sus propios pacientes
    if current_user.role == "doctor" and patient_record.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para subir archivos a este paciente"
        )
    elif current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para subir archivos"
        )

    # Verificar tipos y tamaños de archivos
    for file in files:
        if not file_service.is_allowed_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de archivo no permitido: {file.filename}"
            )
        
        if file.size > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo muy grande: {file.filename}"
            )

    # Verificar el registro médico si se proporciona
    if medical_record_id:
        medical_record_service = MedicalRecordService(db)
        medical_record = medical_record_service.get_medical_record(medical_record_id)
        if not medical_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro médico no encontrado"
            )

    # Subir archivos
    try:
        uploaded_files = []
        for i, file in enumerate(files):
            description = descriptions[i] if descriptions and i < len(descriptions) else None
            
            uploaded_file = await file_service.save_file_to_patient_record(
                file=file,
                user_id=current_user.id,
                patient_record_id=patient_record_id,
                description=description,
                medical_record_id=medical_record_id
            )
            uploaded_files.append(uploaded_file)

        return FileUploadResponse(
            message=f"Se subieron {len(uploaded_files)} archivo(s) exitosamente",
            files=uploaded_files
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir archivos: {str(e)}"
        )

@router.post("/upload-multiple", response_model=FileUploadResponse)
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    patient_id: int = Form(...),
    medical_record_id: Optional[int] = Form(None),
    descriptions: Optional[List[str]] = Form(None),
    photo_ids: Optional[List[int]] = Form(None),  # Para asociar fotos existentes
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Subir múltiples archivos al sistema"""
    file_service = FileService(db)
    user_service = UserService(db)
    
    # Verificar que el paciente existe
    patient = user_service.get_user(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )
    
    # Verificar permisos: solo admin, doctor asignado o el mismo paciente pueden subir archivos
    if current_user.role == "admin":
        # Admin puede subir archivos para cualquier paciente
        pass
    elif current_user.id == patient_id:
        # El paciente puede subir sus propios archivos
        pass
    elif current_user.role == "doctor":
        # Verificar que el doctor tenga acceso al paciente
        if not user_service.doctor_has_access_to_patient(current_user.id, patient_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para subir archivos para este paciente"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para subir archivos"
        )
    
    # Verificar tipos y tamaños de archivos
    for file in files:
        if not file_service.is_allowed_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de archivo no permitido: {file.filename}. Tipos permitidos: {', '.join(settings.allowed_extensions_list)}"
            )
        
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo {file.filename} es demasiado grande. Tamaño máximo: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
            )
        file.file.seek(0)  # Restablecer puntero
    
    # Verificar permisos del registro médico si se especifica
    if medical_record_id:
        medical_service = MedicalRecordService(db)
        if not medical_service.can_access_record(medical_record_id, current_user.id, current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para asociar archivos a este registro médico"
            )
    
    try:
        uploaded_files = await file_service.save_uploaded_files(
            files=files,
            user_id=current_user.id,
            patient_id=patient_id,
            medical_record_id=medical_record_id,
            descriptions=descriptions
        )
        
        # Si se proporcionaron photo_ids y hay un medical_record_id, asociar fotos existentes
        if photo_ids and medical_record_id:
            if not file_service.associate_photos_with_medical_record(photo_ids, medical_record_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error al asociar fotos con el registro médico"
                )
        
        return FileUploadResponse(
            message=f"Se subieron {len(uploaded_files)} archivo(s) exitosamente",
            files=uploaded_files
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir los archivos: {str(e)}"
        )

@router.get("/", response_model=List[UploadedFile])
async def get_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None),
    medical_record_id: Optional[int] = Query(None),
    file_type: Optional[str] = Query(None),  # 'photo' o 'medical_record'
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de archivos"""
    file_service = FileService(db)
    user_service = UserService(db)
    
    if patient_id:
        # Verificar permisos para acceder a archivos del paciente
        if current_user.role == "admin":
            # Admin puede ver archivos de cualquier paciente
            pass
        elif current_user.id == patient_id:
            # El paciente puede ver sus propios archivos
            pass
        elif current_user.role == "doctor":
            # Verificar que el doctor tenga acceso al paciente
            if not user_service.doctor_has_access_to_patient(current_user.id, patient_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para ver los archivos de este paciente"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver archivos de pacientes"
            )
        
        # Filtrar por tipo de archivo si se especifica
        if file_type == "photo":
            return file_service.get_photos_by_patient(patient_id)
        elif file_type == "medical_record":
            return file_service.get_medical_records_by_patient(patient_id)
        else:
            return file_service.get_files_by_patient(patient_id)
    
    elif medical_record_id:
        # Verificar permisos para el registro médico
        medical_service = MedicalRecordService(db)
        if not medical_service.can_access_record(medical_record_id, current_user.id, current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver los archivos de este registro médico"
            )
        
        return file_service.get_files_by_medical_record(medical_record_id)
    
    else:
        # Obtener archivos del usuario actual
        return file_service.get_files_by_user(current_user.id, skip, limit)

@router.get("/patients", response_model=List[User])
async def get_patients_with_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de pacientes que tienen archivos"""
    user_service = UserService(db)
    
    if current_user.role == "admin":
        return user_service.get_patients_with_files()
    elif current_user.role == "doctor":
        return user_service.get_doctor_patients_with_files(current_user.id)
    else:
        # Pacientes solo pueden ver sus propios archivos
        patient = user_service.get_user(current_user.id)
        return [patient] if patient else []

@router.get("/{file_id}", response_model=UploadedFile)
async def get_file_info(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener información de un archivo"""
    file_service = FileService(db)
    
    if not file_service.can_access_file(file_id, current_user.id, current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a este archivo"
        )
    
    file = file_service.get_file(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )
    
    return file

@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Descargar archivo"""
    file_service = FileService(db)
    
    if not file_service.can_access_file(file_id, current_user.id, current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a este archivo"
        )
    
    file = file_service.get_file(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )
    
    if not os.path.exists(file.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo físico no existe"
        )
    
    return FileResponse(
        path=file.file_path,
        filename=file.original_filename,
        media_type=file.mime_type
    )

@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar archivo"""
    file_service = FileService(db)
    
    file = file_service.get_file(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )
    
    # Solo el propietario del archivo o un admin pueden eliminarlo
    if current_user.role != "admin" and file.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar este archivo"
        )
    
    if not file_service.delete_file(file_id):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el archivo"
        )
    
    return {"message": "Archivo eliminado exitosamente"}
