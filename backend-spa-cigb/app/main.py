from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.api import auth, users, medical_records, file_upload

app = FastAPI(
    title="SPA CIGB API",
    description="API para el sistema de gestión de imágenes e historias clínicas",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploaded content
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(medical_records.router, prefix="/api/medical-records", tags=["medical-records"])
app.include_router(file_upload.router, prefix="/api/files", tags=["files"])

@app.get("/")
async def root():
    return {"message": "SPA CIGB API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
