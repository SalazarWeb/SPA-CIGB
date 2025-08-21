from sqlalchemy.orm import Session
from typing import Optional, List
from sqlalchemy import exists
from app.models.models import User, UploadedFile, doctor_patient_association
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def get_patients(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).filter(User.role == "patient").offset(skip).limit(limit).all()
    
    def get_doctors(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).filter(User.role == "doctor").offset(skip).limit(limit).all()
    
    def get_patients_with_files(self) -> List[User]:
        """Obtener pacientes que tienen archivos subidos"""
        return (
            self.db.query(User)
            .filter(User.role == "patient")
            .filter(exists().where(UploadedFile.patient_id == User.id))
            .order_by(User.first_name, User.last_name)
            .all()
        )
    
    def get_doctor_patients_with_files(self, doctor_id: int) -> List[User]:
        """Obtener pacientes de un doctor específico que tienen archivos"""
        return (
            self.db.query(User)
            .filter(User.role == "patient")
            .filter(exists().where(UploadedFile.patient_id == User.id))
            .filter(exists().where(
                (doctor_patient_association.c.doctor_id == doctor_id) &
                (doctor_patient_association.c.patient_id == User.id)
            ))
            .order_by(User.first_name, User.last_name)
            .all()
        )
    
    def doctor_has_access_to_patient(self, doctor_id: int, patient_id: int) -> bool:
        """Verificar si un doctor tiene acceso a un paciente específico"""
        return self.db.query(doctor_patient_association).filter(
            doctor_patient_association.c.doctor_id == doctor_id,
            doctor_patient_association.c.patient_id == patient_id
        ).first() is not None
    
    def create_user(self, user: UserCreate) -> User:
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            address=user.address,
            role=user.role
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        
        db_user.is_active = False
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
