from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Esquemas base para User
class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: str = "patient"

class UserCreate(UserBase):
    password: str
    diagnosis: Optional[str] = None
    admin_password: Optional[str] = None

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[EmailStr] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class User(UserInDB):
    pass

# Esquemas para autenticación
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str
