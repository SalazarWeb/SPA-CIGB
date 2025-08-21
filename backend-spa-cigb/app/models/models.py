from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Tabla de asociación para médicos y pacientes
doctor_patient_association = Table(
    'doctor_patient_association',
    Base.metadata,
    Column('doctor_id', Integer, ForeignKey('users.id')),
    Column('patient_id', Integer, ForeignKey('users.id'))
)

# Tabla de asociación para fotos y registros médicos
photo_medical_record_association = Table(
    'photo_medical_record_association',
    Base.metadata,
    Column('photo_id', Integer, ForeignKey('uploaded_files.id')),
    Column('medical_record_id', Integer, ForeignKey('medical_records.id'))
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    role = Column(String(20), nullable=False, default="patient")  # patient, doctor, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    medical_records_as_patient = relationship("MedicalRecord", foreign_keys="MedicalRecord.patient_id", back_populates="patient")
    medical_records_as_doctor = relationship("MedicalRecord", foreign_keys="MedicalRecord.doctor_id", back_populates="doctor")
    
    # Relación muchos a muchos para médicos y pacientes
    patients = relationship(
        "User",
        secondary=doctor_patient_association,
        primaryjoin=id == doctor_patient_association.c.doctor_id,
        secondaryjoin=id == doctor_patient_association.c.patient_id,
        back_populates="doctors"
    )
    
    doctors = relationship(
        "User",
        secondary=doctor_patient_association,
        primaryjoin=id == doctor_patient_association.c.patient_id,
        secondaryjoin=id == doctor_patient_association.c.doctor_id,
        back_populates="patients"
    )
    
    uploaded_files = relationship("UploadedFile", foreign_keys="UploadedFile.user_id", back_populates="user")

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    diagnosis = Column(Text)
    treatment = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    patient = relationship("User", foreign_keys=[patient_id], back_populates="medical_records_as_patient")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="medical_records_as_doctor")
    files = relationship("UploadedFile", back_populates="medical_record")
    
    # Relación muchos a muchos con fotos
    associated_photos = relationship(
        "UploadedFile",
        secondary=photo_medical_record_association,
        primaryjoin=id == photo_medical_record_association.c.medical_record_id,
        secondaryjoin="and_(UploadedFile.id == photo_medical_record_association.c.photo_id, UploadedFile.file_type == 'photo')",
        viewonly=True
    )

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    description = Column(Text)
    file_type = Column(String(50), nullable=False)  # 'medical_record' o 'photo'
    
    # Relaciones
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Usuario que subió el archivo
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Paciente al que pertenece
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", foreign_keys=[user_id], back_populates="uploaded_files")
    patient = relationship("User", foreign_keys=[patient_id])
    medical_record = relationship("MedicalRecord", back_populates="files")
