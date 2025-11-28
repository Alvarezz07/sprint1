from fastapi import APIRouter, HTTPException, Query, Header, Depends
from typing import Optional, List
from controllers.notification_controller import (
    get_user_notifications, mark_notification_as_read, mark_all_notifications_as_read,
    get_unread_notifications_count, create_notification
)
from models.loan_models import NotificationCreate, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Simulación de autenticación (en producción usarías JWT o sesiones)
def get_current_user_id(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
    qp_user_id: int | None = Query(default=None, alias="user_id")
) -> int:
    """Simula obtener el ID del usuario actual - en producción usarías JWT"""
    return x_user_id or qp_user_id or 1

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    limit: Optional[int] = Query(None, description="Límite de notificaciones a obtener"),
    unread_only: bool = Query(False, description="Solo notificaciones no leídas"),
    user_id: int = Depends(get_current_user_id)
):
    """Obtiene las notificaciones del usuario actual"""
    return get_user_notifications(user_id, limit, unread_only)

@router.get("/unread-count")
async def get_unread_count(user_id: int = Depends(get_current_user_id)):
    """Obtiene el número de notificaciones no leídas del usuario actual"""
    count = get_unread_notifications_count(user_id)
    return {"unread_count": count}

@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: int, user_id: int = Depends(get_current_user_id)):
    """Marca una notificación específica como leída"""
    result = mark_notification_as_read(notification_id, user_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.post("/mark-all-read")
async def mark_all_as_read(user_id: int = Depends(get_current_user_id)):
    """Marca todas las notificaciones del usuario actual como leídas"""
    result = mark_all_notifications_as_read(user_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.post("/", response_model=dict)
async def create_new_notification(notification_data: NotificationCreate):
    """Crea una nueva notificación"""
    result = create_notification(notification_data)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result
