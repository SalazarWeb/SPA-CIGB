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
from app.schemas.user import User
from app.schemas.file import UploadedFile, FileUploadResponse

router = APIRouter()

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    medical_record_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Subir archivo al sistema"""
    file_service = FileService(db)
    
    # Verificar tipo de archivo
    if not file_service.is_allowed_file_type(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Tipos permitidos: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Verificar tamaño del archivo
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo es demasiado grande. Tamaño máximo: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
        )
    
    # Restablecer el puntero del archivo
    file.file.seek(0)
    
    # Verificar permisos del registro médico si se especifica
    if medical_record_id:
        medical_service = MedicalRecordService(db)
        if not medical_service.can_access_record(medical_record_id, current_user.id, current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para asociar archivos a este registro médico"
            )
    
    try:
        uploaded_file = await file_service.save_uploaded_file(
            file=file,
            user_id=current_user.id,
            medical_record_id=medical_record_id,
            description=description
        )
        
        return FileUploadResponse(
            message="Archivo subido exitosamente",
            file=uploaded_file
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir el archivo: {str(e)}"
        )

@router.get("/", response_model=List[UploadedFile])
async def get_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    medical_record_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de archivos del usuario"""
    file_service = FileService(db)
    
    if medical_record_id:
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
