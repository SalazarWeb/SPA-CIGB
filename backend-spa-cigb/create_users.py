#!/usr/bin/env python3
"""
Script para crear un usuario administrador inicial
"""
import sys
import os

# Agregar el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.user_service import UserService
from app.schemas.user import UserCreate

def create_admin_user():
    """Crear usuario administrador inicial"""
    db = SessionLocal()
    user_service = UserService(db)
    
    try:
        # Verificar si ya existe un admin
        existing_admin = user_service.get_user_by_username("admin")
        if existing_admin:
            print("❌ El usuario administrador 'admin' ya existe")
            return
        
        # Crear usuario administrador
        admin_user = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        
        created_user = user_service.create_user(admin_user)
        print(f"✅ Usuario administrador creado exitosamente:")
        print(f"   Username: {created_user.username}")
        print(f"   Email: {created_user.email}")
        print(f"   Rol: {created_user.role}")
        print(f"   ID: {created_user.id}")
        print()
        print("⚠️  IMPORTANTE: Cambia la contraseña por defecto 'admin123' después del primer login")
        
    except Exception as e:
        print(f"❌ Error al crear el usuario administrador: {e}")
    finally:
        db.close()

def create_sample_doctor():
    """Crear usuario doctor de ejemplo"""
    db = SessionLocal()
    user_service = UserService(db)
    
    try:
        # Verificar si ya existe
        existing_doctor = user_service.get_user_by_username("doctor1")
        if existing_doctor:
            print("❌ El usuario doctor 'doctor1' ya existe")
            return
        
        # Crear usuario doctor
        doctor_user = UserCreate(
            username="doctor1",
            email="doctor@example.com",
            password="doctor123",
            first_name="Dr. Juan",
            last_name="Pérez",
            role="doctor"
        )
        
        created_user = user_service.create_user(doctor_user)
        print(f"✅ Usuario doctor creado exitosamente:")
        print(f"   Username: {created_user.username}")
        print(f"   Email: {created_user.email}")
        print(f"   Rol: {created_user.role}")
        print(f"   ID: {created_user.id}")
        
    except Exception as e:
        print(f"❌ Error al crear el usuario doctor: {e}")
    finally:
        db.close()

def create_sample_patient():
    """Crear usuario paciente de ejemplo"""
    db = SessionLocal()
    user_service = UserService(db)
    
    try:
        # Verificar si ya existe
        existing_patient = user_service.get_user_by_username("patient1")
        if existing_patient:
            print("❌ El usuario paciente 'patient1' ya existe")
            return
        
        # Crear usuario paciente
        patient_user = UserCreate(
            username="patient1",
            email="patient@example.com",
            password="patient123",
            first_name="María",
            last_name="García",
            role="patient"
        )
        
        created_user = user_service.create_user(patient_user)
        print(f"✅ Usuario paciente creado exitosamente:")
        print(f"   Username: {created_user.username}")
        print(f"   Email: {created_user.email}")
        print(f"   Rol: {created_user.role}")
        print(f"   ID: {created_user.id}")
        
    except Exception as e:
        print(f"❌ Error al crear el usuario paciente: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creando usuarios de ejemplo...")
    print()
    
    create_admin_user()
    create_sample_doctor()
    create_sample_patient()
    
    print()
    print("🎉 Proceso completado")
    print()
    print("Usuarios creados:")
    print("- admin/admin123 (Administrador)")
    print("- doctor1/doctor123 (Doctor)")
    print("- patient1/patient123 (Paciente)")
    print()
    print("⚠️  Recuerda cambiar las contraseñas por defecto en producción")
