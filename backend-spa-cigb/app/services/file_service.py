from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
import os
import uuid
from fastapi import UploadFile
from app.models.models import UploadedFile, User, photo_medical_record_association
from app.schemas.file import UploadedFileCreate, UploadedFile as UploadedFileSchema
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
    
    def get_files_by_patient(self, patient_id: int) -> List[UploadedFile]:
        """Obtener todos los archivos de un paciente"""
        return (
            self.db.query(UploadedFile)
            .options(
                joinedload(UploadedFile.user),
                joinedload(UploadedFile.patient)
            )
            .filter(UploadedFile.patient_id == patient_id)
            .order_by(UploadedFile.created_at.desc())
            .all()
        )
    
    def get_photos_by_patient(self, patient_id: int) -> List[UploadedFile]:
        """Obtener solo las fotos de un paciente"""
        return (
            self.db.query(UploadedFile)
            .filter(UploadedFile.patient_id == patient_id)
            .filter(UploadedFile.file_type == "photo")
            .order_by(UploadedFile.created_at.desc())
            .all()
        )
    
    def get_medical_records_by_patient(self, patient_id: int) -> List[UploadedFile]:
        """Obtener solo las historias clínicas de un paciente"""
        return (
            self.db.query(UploadedFile)
            .filter(UploadedFile.patient_id == patient_id)
            .filter(UploadedFile.file_type == "medical_record")
            .order_by(UploadedFile.created_at.desc())
            .all()
        )
    
    def get_files_by_medical_record(self, medical_record_id: int) -> List[UploadedFile]:
        return (
            self.db.query(UploadedFile)
            .filter(UploadedFile.medical_record_id == medical_record_id)
            .all()
        )
    
    def classify_file_type(self, filename: str, mime_type: str) -> str:
        """Clasificar el tipo de archivo basado en su extensión y mime type"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        image_mime_types = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff', 'image/webp']
        
        file_extension = os.path.splitext(filename)[1].lower()
        
        if file_extension in image_extensions or mime_type in image_mime_types:
            return "photo"
        else:
            return "medical_record"
    
    
    async def save_uploaded_files(
        self,
        files: List[UploadFile],
        user_id: int,
        patient_id: int,
        medical_record_id: Optional[int] = None,
        descriptions: Optional[List[str]] = None
    ) -> List[UploadedFile]:
        """Guardar múltiples archivos subidos al sistema"""
        
        uploaded_files = []
        
        for i, file in enumerate(files):
            # Obtener descripción si existe
            description = descriptions[i] if descriptions and i < len(descriptions) else None
            
            # Generar nombre único para el archivo
            file_extension = os.path.splitext(file.filename or "")[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
            
            # Leer contenido del archivo
            content = await file.read()
            
            # Guardar archivo físicamente
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # Clasificar tipo de archivo
            file_type = self.classify_file_type(file.filename or "", file.content_type or "")
            
            # Crear registro en base de datos
            db_file = UploadedFile(
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=len(content),
                mime_type=file.content_type,
                description=description,
                file_type=file_type,
                user_id=user_id,
                patient_id=patient_id,
                medical_record_id=medical_record_id if file_type == "medical_record" else None
            )
            
            self.db.add(db_file)
            uploaded_files.append(db_file)
        
        self.db.commit()
        
        # Refrescar objetos para obtener IDs generados
        for db_file in uploaded_files:
            self.db.refresh(db_file)
        
        return uploaded_files

    async def save_uploaded_file(
        self, 
        file: UploadFile, 
        user_id: int, 
        patient_id: int,
        medical_record_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> UploadedFile:
        """Guardar archivo único (mantener compatibilidad)"""
        
        files = await self.save_uploaded_files(
            files=[file],
            user_id=user_id,
            patient_id=patient_id,
            medical_record_id=medical_record_id,
            descriptions=[description] if description else None
        )
        
        return files[0]
    
    async def save_file_to_patient_record(
        self, 
        file: UploadFile, 
        user_id: int, 
        patient_record_id: int,
        medical_record_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> UploadedFileSchema:
        """Guardar archivo a un registro de paciente"""
        
        # Generar nombre único para el archivo
        file_extension = os.path.splitext(file.filename or "")[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # Leer contenido del archivo
        content = await file.read()
        
        # Guardar archivo físicamente
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Clasificar tipo de archivo
        file_type = self.classify_file_type(file.filename or "", file.content_type or "")
        
        # Crear registro en base de datos
        db_file = UploadedFile(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            description=description,
            file_type=file_type,
            user_id=user_id,
            patient_record_id=patient_record_id,
            medical_record_id=medical_record_id if file_type == "medical_record" else None
        )
        
        self.db.add(db_file)
        self.db.commit()
        self.db.refresh(db_file)
        
        return self.to_schema(db_file)
    
    def associate_photos_with_medical_record(self, photo_ids: List[int], medical_record_id: int) -> bool:
        """Asociar fotos existentes con un registro médico"""
        try:
            # Verificar que las fotos existan y sean del tipo correcto
            photos = (
                self.db.query(UploadedFile)
                .filter(UploadedFile.id.in_(photo_ids))
                .filter(UploadedFile.file_type == "photo")
                .all()
            )
            
            if len(photos) != len(photo_ids):
                return False
            
            # Insertar asociaciones
            for photo_id in photo_ids:
                association = photo_medical_record_association.insert().values(
                    photo_id=photo_id,
                    medical_record_id=medical_record_id
                )
                self.db.execute(association)
            
            self.db.commit()
            return True
        
        except Exception:
            self.db.rollback()
            return False
    
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
        return file_extension in [ext.lower() for ext in settings.allowed_extensions_list]
    
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

    def to_schema(self, db_file: UploadedFile) -> UploadedFileSchema:
        """Convertir un modelo de base de datos a esquema Pydantic"""
        # Obtener datos básicos
        data = {
            'id': db_file.id,
            'filename': db_file.filename,
            'original_filename': db_file.original_filename,
            'file_size': db_file.file_size,
            'mime_type': db_file.mime_type,
            'description': db_file.description,
            'file_type': db_file.file_type,
            'file_path': db_file.file_path,
            'user_id': db_file.user_id,
            'medical_record_id': db_file.medical_record_id,
            'created_at': db_file.created_at,
            'patient_name': None,
            'uploader_name': None
        }
        
        # Usar patient_record_id como patient_id para compatibilidad
        patient_id = getattr(db_file, 'patient_record_id', None) or getattr(db_file, 'patient_id', None)
        data['patient_id'] = patient_id
        
        # Obtener nombre del paciente
        try:
            if patient_id:
                from app.services.patient_service import PatientService
                patient_service = PatientService(self.db)
                patient = patient_service.get_patient(patient_id)
                if patient:
                    data['patient_name'] = f"{patient.first_name} {patient.last_name}"
            elif getattr(db_file, 'patient_id', None):
                patient = self.db.query(User).filter(User.id == db_file.patient_id).first()
                if patient:
                    data['patient_name'] = f"{patient.first_name} {patient.last_name}"
        except Exception:
            pass  # Silenciar errores de obtención de nombres
        
        # Obtener nombre del usuario que subió el archivo
        try:
            if db_file.user_id:
                uploader = self.db.query(User).filter(User.id == db_file.user_id).first()
                if uploader:
                    data['uploader_name'] = f"{uploader.first_name} {uploader.last_name}"
        except Exception:
            pass  # Silenciar errores de obtención de nombres
        
        return UploadedFileSchema(**data)
