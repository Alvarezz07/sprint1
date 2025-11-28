from fastapi import APIRouter, HTTPException
from controllers.auth_controller import (
    register_user, 
    login_user, 
    check_database_status,
    update_user_profile,
    get_user_profile,
    UserCreate,
    UserLogin,
    UserUpdate
)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/db-status")
async def get_database_status():
    """Verifica si la base de datos existe"""
    return check_database_status()

@router.post("/register")
async def register(user_data: UserCreate):
    """Registra un nuevo usuario"""
    result = register_user(user_data)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.post("/login")
async def login(login_data: UserLogin):
    """Autentica un usuario"""
    result = login_user(login_data)
    
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    
    return result

@router.get("/health")
async def health_check():
    """Endpoint de salud para verificar que la API funciona"""
    return {"status": "ok", "message": "API de autenticación funcionando"}

@router.get("/profile")
async def get_profile():
    """Obtiene el perfil del usuario actual"""
    # Simulación de obtener usuario actual (en producción usarías JWT)
    user_id = 1  # Por ahora hardcodeado
    result = get_user_profile(user_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result

@router.put("/profile")
async def update_profile(update_data: UserUpdate):
    """Actualiza el perfil del usuario actual"""
    # Simulación de obtener usuario actual (en producción usarías JWT)
    user_id = 1  # Por ahora hardcodeado
    result = update_user_profile(user_id, update_data)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result
