from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import date, datetime
from enum import Enum

class LoanType(str, Enum):
    MONEY = "money"
    OBJECT = "object"

class LoanStatus(str, Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"

class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

# Modelos para usuarios
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    profile_image: Optional[str] = Field(None, max_length=500)

class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: str
    phone: Optional[str]
    address: Optional[str]
    profile_image: Optional[str]
    created_at: datetime

# Modelos para préstamos
class LoanCreate(BaseModel):
    borrower_id: int
    loan_type: LoanType
    amount: Optional[float] = Field(None, gt=0)
    object_name: Optional[str] = Field(None, max_length=255)
    object_description: Optional[str] = Field(None, max_length=1000)
    object_image: Optional[str] = Field(None, max_length=500)
    loan_date: date
    due_date: date
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('due_date')
    def due_date_must_be_future(cls, v, values):
        if 'loan_date' in values and v <= values['loan_date']:
            raise ValueError('La fecha de vencimiento debe ser posterior a la fecha de préstamo')
        return v

    @validator('amount')
    def amount_required_for_money(cls, v, values):
        if values.get('loan_type') == LoanType.MONEY and (v is None or v <= 0):
            raise ValueError('El monto es requerido para préstamos de dinero')
        return v

    @validator('object_name')
    def object_name_required_for_object(cls, v, values):
        if values.get('loan_type') == LoanType.OBJECT and not v:
            raise ValueError('El nombre del objeto es requerido para préstamos de objetos')
        return v

class LoanUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    object_name: Optional[str] = Field(None, max_length=255)
    object_description: Optional[str] = Field(None, max_length=1000)
    object_image: Optional[str] = Field(None, max_length=500)
    due_date: Optional[date]
    return_date: Optional[date]
    status: Optional[LoanStatus]
    notes: Optional[str] = Field(None, max_length=1000)

class LoanResponse(BaseModel):
    id: int
    lender_id: int
    borrower_id: int
    loan_type: LoanType
    amount: Optional[float]
    object_name: Optional[str]
    object_description: Optional[str]
    object_image: Optional[str]
    loan_date: date
    due_date: date
    return_date: Optional[date]
    status: LoanStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    # Información adicional del usuario
    lender_name: Optional[str] = None
    borrower_name: Optional[str] = None

# Modelos para notificaciones
class NotificationCreate(BaseModel):
    user_id: int
    title: str = Field(..., max_length=255)
    message: str = Field(..., max_length=1000)
    type: NotificationType = NotificationType.INFO
    loan_id: Optional[int] = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: NotificationType
    is_read: bool
    loan_id: Optional[int]
    created_at: datetime

# Modelos para filtros y búsquedas
class LoanFilter(BaseModel):
    status: Optional[LoanStatus] = None
    loan_type: Optional[LoanType] = None
    borrower_id: Optional[int] = None
    lender_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    search: Optional[str] = None

class UserFilter(BaseModel):
    search: Optional[str] = None
    has_active_loans: Optional[bool] = None

# Modelos para estadísticas
class LoanStats(BaseModel):
    total_active_loans: int
    total_returned_loans: int
    total_overdue_loans: int
    total_amount_lent: float
    total_amount_returned: float
    pending_amount: float

class DashboardData(BaseModel):
    user: UserResponse
    stats: LoanStats
    recent_loans: list[LoanResponse]
    overdue_loans: list[LoanResponse]
    notifications: list[NotificationResponse]
