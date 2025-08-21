#!/usr/bin/env python3
"""
Script para inicializar la base de datos y crear tablas
"""
import sys
import os

# Agregar el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
from app.models.models import User, MedicalRecord, UploadedFile

def create_tables():
    """Crear todas las tablas en la base de datos"""
    try:
        print("🚀 Creando tablas en la base de datos...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error al crear las tablas: {e}")
        return False

if __name__ == "__main__":
    if create_tables():
        print("🎉 Base de datos inicializada correctamente")
        print("Ahora puedes ejecutar create_users.py para crear usuarios de prueba")
    else:
        print("❌ Error al inicializar la base de datos")
