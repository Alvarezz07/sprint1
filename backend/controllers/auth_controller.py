import hashlib
from typing import Optional
from pydantic import BaseModel
from lib.mysql_db import (
    get_user_by_username, create_user, init_database, check_database_exists,
    hash_password, verify_password, update_user_profile as update_user_profile_db, get_user_by_id
)

class UserCreate(BaseModel):
    name: str
    username: str
    email: str
    password: str
    phone: Optional[str] = None
    address: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: str
    phone: Optional[str]
    address: Optional[str]
    profile_image: Optional[str]
    created_at: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_image: Optional[str] = None

def hash_password(password: str) -> str:
    """Genera un hash seguro de la contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash"""
    return hash_password(password) == hashed_password

def register_user(user_data: UserCreate) -> dict:
    """Registra un nuevo usuario"""
    # Verificar si la base de datos existe
    if not check_database_exists():
        init_database()
    
    # Verificar si el usuario ya existe
    existing_user = get_user_by_username(user_data.username)
    if existing_user:
        return {"success": False, "message": "El usuario ya existe"}
    
    # Crear hash de la contraseña
    password_hash = hash_password(user_data.password)
    
    # Crear el usuario
    success = create_user(
        user_data.name, 
        user_data.username, 
        user_data.email, 
        password_hash,
        user_data.phone,
        user_data.address
    )
    
    if success:
        return {"success": True, "message": "Usuario creado exitosamente"}
    else:
        return {"success": False, "message": "Error al crear el usuario"}

def login_user(login_data: UserLogin) -> dict:
    """Autentica un usuario"""
    # Verificar si la base de datos existe
    if not check_database_exists():
        return {"success": False, "message": "Base de datos no encontrada"}
    
    # Buscar el usuario
    user = get_user_by_username(login_data.username)
    if not user:
        return {"success": False, "message": "Usuario no encontrado"}
    
    # Verificar la contraseña
    if verify_password(login_data.password, user['password_hash']):
        return {
            "success": True, 
            "message": "Login exitoso",
            "user": {
                "id": user['id'],
                "name": user['name'],
                "username": user['username'],
                "email": user['email'],
                "phone": user.get('phone'),
                "address": user.get('address'),
                "profile_image": user.get('profile_image'),
                "created_at": str(user['created_at'])
            }
        }
    else:
        return {"success": False, "message": "Contraseña incorrecta"}

def check_database_status() -> dict:
    """Verifica el estado de la base de datos"""
    exists = check_database_exists()
    return {
        "database_exists": exists,
        "message": "Base de datos encontrada" if exists else "Base de datos no encontrada"
    }

def update_user_profile(user_id: int, update_data: UserUpdate) -> dict:
    """Actualiza el perfil de un usuario"""
    try:
        # Verificar que el usuario existe
        user = get_user_by_id(user_id)
        if not user:
            return {"success": False, "message": "Usuario no encontrado"}
        
        # Actualizar el perfil en la base de datos
        success = update_user_profile_db(user_id, **update_data.dict(exclude_unset=True))
        
        if success:
            return {"success": True, "message": "Perfil actualizado exitosamente"}
        else:
            return {"success": False, "message": "Error al actualizar el perfil"}
            
    except Exception as e:
        return {"success": False, "message": f"Error al actualizar perfil: {str(e)}"}

def get_user_profile(user_id: int) -> dict:
    """Obtiene el perfil de un usuario"""
    try:
        user = get_user_by_id(user_id)
        if not user:
            return {"success": False, "message": "Usuario no encontrado"}
        
        return {
            "success": True,
            "user": {
                "id": user['id'],
                "name": user['name'],
                "username": user['username'],
                "email": user['email'],
                "phone": user.get('phone'),
                "address": user.get('address'),
                "profile_image": user.get('profile_image'),
                "created_at": str(user['created_at'])
            }
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error al obtener perfil: {str(e)}"}
