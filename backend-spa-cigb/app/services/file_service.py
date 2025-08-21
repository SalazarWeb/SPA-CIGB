from sqlalchemy.orm import Session
from typing import Optional, List
import os
import uuid
from fastapi import UploadFile
from app.models.models import UploadedFile
from app.schemas.file import UploadedFileCreate
from app.core.config import settings

class FileService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_file(self, file_id: int) -> Optional[UploadedFile]:
        return self.db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    
    def get_files_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[UploadedFile]:
        return (
            self.db.query(UploadedFile)
            .filter(UploadedFile.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_files_by_medical_record(self, medical_record_id: int) -> List[UploadedFile]:
        return (
            self.db.query(UploadedFile)
            .filter(UploadedFile.medical_record_id == medical_record_id)
            .all()
        )
    
    async def save_uploaded_file(
        self, 
        file: UploadFile, 
        user_id: int, 
        medical_record_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> UploadedFile:
        """Guardar archivo subido al sistema"""
        
        # Generar nombre único para el archivo
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # Guardar archivo físicamente
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Crear registro en base de datos
        db_file = UploadedFile(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            description=description,
            user_id=user_id,
            medical_record_id=medical_record_id
        )
        
        self.db.add(db_file)
        self.db.commit()
        self.db.refresh(db_file)
        
        return db_file
    
    def delete_file(self, file_id: int) -> bool:
        """Eliminar archivo del sistema"""
        db_file = self.get_file(file_id)
        if not db_file:
            return False
        
        # Eliminar archivo físico
        try:
            if os.path.exists(db_file.file_path):
                os.remove(db_file.file_path)
        except OSError:
            pass
        
        # Eliminar registro de base de datos
        self.db.delete(db_file)
        self.db.commit()
        return True
    
    def is_allowed_file_type(self, filename: str) -> bool:
        """Verificar si el tipo de archivo está permitido"""
        if not filename:
            return False
        
        file_extension = os.path.splitext(filename)[1].lower().lstrip('.')
        return file_extension in [ext.lower() for ext in settings.ALLOWED_EXTENSIONS]
    
    def can_access_file(self, file_id: int, user_id: int, user_role: str) -> bool:
        """Verificar si un usuario puede acceder a un archivo"""
        db_file = self.get_file(file_id)
        if not db_file:
            return False
        
        # Los administradores pueden acceder a todo
        if user_role == "admin":
            return True
        
        # El propietario del archivo puede acceder
        if db_file.user_id == user_id:
            return True
        
        # Si el archivo está asociado a un registro médico, verificar permisos
        if db_file.medical_record_id:
            from app.services.medical_record_service import MedicalRecordService
            medical_service = MedicalRecordService(self.db)
            return medical_service.can_access_record(db_file.medical_record_id, user_id, user_role)
        
        return False
