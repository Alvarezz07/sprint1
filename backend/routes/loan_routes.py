from fastapi import APIRouter, HTTPException, Depends, Query, Header
from typing import Optional, List
from controllers.loan_controller import (
    create_loan,
    get_loans_by_lender,
    get_loans_by_borrower,
    update_loan,
    mark_loan_returned,
    get_loan_stats,
    get_overdue_loans,
    get_all_users,
    delete_loan,
    get_upcoming_loans,
    get_loan_report_summary,
)
from controllers.auth_controller import get_user_profile
from controllers.notification_controller import get_user_notifications
import logging

logger = logging.getLogger(__name__)
from models.loan_models import (
    LoanCreate, LoanUpdate, LoanResponse, LoanFilter, LoanStats,
    UserResponse, DashboardData
)
from datetime import date

router = APIRouter(prefix="/loans", tags=["loans"])

# Simulación de autenticación (en producción usarías JWT o sesiones)
def get_current_user_id(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
    qp_user_id: int | None = Query(default=None, alias="user_id")
) -> int:
    """Simula obtener el ID del usuario actual - en producción usarías JWT"""
    # Preferir header; si no, query param; si no, fallback 1
    uid = x_user_id or qp_user_id or 1
    return uid

@router.post("/", response_model=dict)
async def create_new_loan(loan_data: LoanCreate, user_id: int = Depends(get_current_user_id)):
    """Crea un nuevo préstamo"""
    lender_id = user_id
    logger.info(f"[POST /loans] user_id={lender_id} payload={loan_data.dict()}")
    result = create_loan(lender_id, loan_data)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.get("/my-loans", response_model=List[LoanResponse])
async def get_my_loans(
    status: Optional[str] = Query(None, description="Filtrar por estado: active, returned, overdue"),
    loan_type: Optional[str] = Query(None, description="Filtrar por tipo: money, object"),
    borrower_id: Optional[int] = Query(None, description="Filtrar por prestatario"),
    date_from: Optional[date] = Query(None, description="Fecha desde"),
    date_to: Optional[date] = Query(None, description="Fecha hasta"),
    search: Optional[str] = Query(None, description="Buscar en nombre de objeto o notas")
    , user_id: int = Depends(get_current_user_id)):
    """Obtiene los préstamos del usuario actual como prestamista"""
    lender_id = user_id
    logger.info(f"[GET /loans/my-loans] user_id={lender_id} filters={{'status': status, 'loan_type': loan_type}}")
    
    filters = LoanFilter(
        status=status,
        loan_type=loan_type,
        borrower_id=borrower_id,
        date_from=date_from,
        date_to=date_to,
        search=search
    )
    
    return get_loans_by_lender(lender_id, filters)

@router.get("/borrowed", response_model=List[LoanResponse])
async def get_borrowed_loans(
    status: Optional[str] = Query(None, description="Filtrar por estado: active, returned, overdue"),
    loan_type: Optional[str] = Query(None, description="Filtrar por tipo: money, object"),
    lender_id: Optional[int] = Query(None, description="Filtrar por prestamista"),
    date_from: Optional[date] = Query(None, description="Fecha desde"),
    date_to: Optional[date] = Query(None, description="Fecha hasta"),
    search: Optional[str] = Query(None, description="Buscar en nombre de objeto o notas")
    , user_id: int = Depends(get_current_user_id)):
    """Obtiene los préstamos del usuario actual como prestatario"""
    borrower_id = user_id
    logger.info(f"[GET /loans/borrowed] user_id={borrower_id} filters={{'status': status, 'loan_type': loan_type}}")
    
    filters = LoanFilter(
        status=status,
        loan_type=loan_type,
        lender_id=lender_id,
        date_from=date_from,
        date_to=date_to,
        search=search
    )
    
    return get_loans_by_borrower(borrower_id, filters)

@router.put("/{loan_id}", response_model=dict)
async def update_loan_info(loan_id: int, update_data: LoanUpdate, user_id: int = Depends(get_current_user_id)):
    """Actualiza un préstamo existente"""
    lender_id = user_id
    logger.info(f"[PUT /loans/{{loan_id}}] user_id={lender_id} loan_id={loan_id} update={update_data.dict(exclude_unset=True)}")
    result = update_loan(loan_id, lender_id, update_data)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.post("/{loan_id}/return", response_model=dict)
async def mark_loan_as_returned(loan_id: int, user_id: int = Depends(get_current_user_id)):
    """Marca un préstamo como devuelto"""
    lender_id = user_id
    logger.info(f"[POST /loans/{{loan_id}}/return] user_id={lender_id} loan_id={loan_id}")
    result = mark_loan_returned(loan_id, lender_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.delete("/{loan_id}", response_model=dict)
async def delete_loan_route(loan_id: int, user_id: int = Depends(get_current_user_id)):
    """Elimina un préstamo del prestamista actual"""
    result = delete_loan(loan_id, user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.get("/stats", response_model=LoanStats)
async def get_my_loan_stats(user_id: int = Depends(get_current_user_id)):
    """Obtiene estadísticas de préstamos del usuario actual"""
    stats = get_loan_stats(user_id)
    logger.info(f"[GET /loans/stats] user_id={user_id} stats={stats}")
    return stats

@router.get("/overdue", response_model=List[LoanResponse])
async def get_overdue_loans_list(user_id: int = Depends(get_current_user_id)):
    """Obtiene préstamos vencidos del usuario actual"""
    loans = get_overdue_loans(user_id)
    logger.info(f"[GET /loans/overdue] user_id={user_id} count={len(loans)}")
    return loans

@router.get("/users", response_model=List[UserResponse])
async def get_users_for_loans(search: Optional[str] = Query(None, description="Buscar usuarios")):
    """Obtiene usuarios para selección en préstamos"""
    return get_all_users(search)

@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(user_id: int = Depends(get_current_user_id)):
    """Obtiene datos del dashboard del usuario actual"""
    
    # Obtener información del usuario
    user_result = get_user_profile(user_id)
    if not user_result["success"]:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Obtener estadísticas
    stats = get_loan_stats(user_id)

    # Obtener préstamos recientes (últimos 5)
    recent_loans = get_loans_by_lender(user_id)[:5]

    # Obtener préstamos vencidos
    overdue_loans = get_overdue_loans(user_id)

    # Cargar notificaciones del usuario
    notifications = get_user_notifications(user_id, limit=5, unread_only=False)
    logger.info(
        f"[GET /loans/dashboard] user_id={user_id} recent={len(recent_loans)} overdue={len(overdue_loans)} notif={len(notifications)}"
    )

    return DashboardData(
        user=user_result["user"],
        stats=stats,
        recent_loans=recent_loans,
        overdue_loans=overdue_loans,
        notifications=notifications,
    )


@router.get("/upcoming")
async def get_upcoming(user_id: int = Depends(get_current_user_id), days: int = 3):
    """Préstamos próximos a vencer para alertas"""
    upcoming = get_upcoming_loans(user_id, days)
    logger.info(
        f"[GET /loans/upcoming] user_id={user_id} days={days} lender={len(upcoming['as_lender'])} borrower={len(upcoming['as_borrower'])}"
    )
    return upcoming


@router.get("/report")
async def get_report(user_id: int = Depends(get_current_user_id)):
    """Resumen agregado para módulo de reportes"""
    summary = get_loan_report_summary(user_id)
    lender_total = summary.get("as_lender", {}).get("total_count", 0)
    borrower_total = summary.get("as_borrower", {}).get("total_count", 0)
    logger.info(f"[GET /loans/report] user_id={user_id} lender_count={lender_total} borrower_count={borrower_total}")
    return summary
