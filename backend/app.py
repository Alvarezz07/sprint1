from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from routes.auth_routes import router as auth_router
from routes.loan_routes import router as loan_router
from routes.notification_routes import router as notification_router
from lib.mysql_db import init_database

app = FastAPI(
    title="Sistema de Préstamos",
    description="Sistema completo de gestión de préstamos de objetos y dinero",
    version="2.0.0"
)

# Inicialización de base de datos al iniciar la app
@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Inicializando base de datos MySQL (creación de tablas si no existen)...")
    init_ok = init_database()
    if init_ok:
        logger.info("Base de datos lista.")
    else:
        logger.error("Fallo al inicializar la base de datos. Revisa credenciales y permisos.")

# Incluir las rutas de autenticación
app.include_router(auth_router)

# Incluir las rutas de préstamos
app.include_router(loan_router)

# Incluir las rutas de notificaciones
app.include_router(notification_router)

# Montar archivos estáticos del frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    """Endpoint raíz de la API"""
    return {
        "message": "Sistema de Préstamos funcionando",
        "endpoints": {
            "authentication": {
                "database_status": "/auth/db-status",
                "register": "/auth/register",
                "login": "/auth/login",
                "health": "/auth/health"
            },
            "loans": {
                "create_loan": "/loans/",
                "my_loans": "/loans/my-loans",
                "borrowed_loans": "/loans/borrowed",
                "loan_stats": "/loans/stats",
                "overdue_loans": "/loans/overdue",
                "dashboard": "/loans/dashboard"
            },
            "notifications": {
                "get_notifications": "/notifications/",
                "unread_count": "/notifications/unread-count",
                "mark_read": "/notifications/{id}/read",
                "mark_all_read": "/notifications/mark-all-read"
            },
            "frontend": {
                "login": "/login",
                "dashboard": "/dashboard",
                "new_loan": "/new-loan",
                "profile": "/profile",
                "my_loans": "/my-loans"
            }
        }
    }

@app.get("/login")
async def serve_login():
    """Servir la página de login"""
    logger.info("Serving login page")
    return FileResponse("frontend/login/login.html")

@app.get("/dashboard")
async def serve_dashboard():
    """Servir la página del dashboard"""
    return FileResponse("frontend/dashboard/dashboard.html")

@app.get("/new-loan")
async def serve_new_loan():
    """Servir la página de nuevo préstamo"""
    return FileResponse("frontend/new-loan/new-loan.html")

@app.get("/profile")
async def serve_profile():
    """Servir la página de perfil"""
    return FileResponse("frontend/profile/profile.html")

@app.get("/my-loans")
async def serve_my_loans():
    """Servir la página de mis préstamos"""
    return FileResponse("frontend/loans/my-loans.html")

@app.get("/reports")
async def serve_reports():
    """Servir la página de reportes"""
    return FileResponse("frontend/reports/reports.html")

if __name__ == "__main__":
    logger.info("Starting Sistema de Préstamos server on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
