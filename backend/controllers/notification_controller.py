from typing import List, Optional, Dict, Any
from datetime import datetime
from models.loan_models import NotificationCreate, NotificationResponse, NotificationType
from lib.mysql_db import get_db_connection

def create_notification(notification_data: NotificationCreate) -> Dict[str, Any]:
    """Crea una nueva notificación"""
    try:
        connection = get_db_connection()
        if not connection:
            return {"success": False, "message": "Error de conexión a la base de datos"}
        
        cursor = connection.cursor()
        
        # Verificar que el usuario existe
        cursor.execute("SELECT id FROM users WHERE id = %s", (notification_data.user_id,))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return {"success": False, "message": "Usuario no encontrado"}
        
        # Insertar la notificación
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, loan_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            notification_data.user_id,
            notification_data.title,
            notification_data.message,
            notification_data.type.value,
            notification_data.loan_id
        ))
        
        notification_id = cursor.lastrowid
        connection.commit()
        cursor.close()
        connection.close()
        
        return {"success": True, "message": "Notificación creada exitosamente", "notification_id": notification_id}
        
    except Exception as e:
        return {"success": False, "message": f"Error al crear notificación: {str(e)}"}

def get_user_notifications(user_id: int, limit: Optional[int] = None, unread_only: bool = False) -> List[NotificationResponse]:
    """Obtiene las notificaciones de un usuario"""
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT * FROM notifications 
            WHERE user_id = %s
        """
        params = [user_id]
        
        if unread_only:
            query += " AND is_read = FALSE"
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        cursor.execute(query, params)
        notifications = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return [NotificationResponse(**notification) for notification in notifications]
        
    except Exception as e:
        print(f"Error al obtener notificaciones: {e}")
        return []

def mark_notification_as_read(notification_id: int, user_id: int) -> Dict[str, Any]:
    """Marca una notificación como leída"""
    try:
        connection = get_db_connection()
        if not connection:
            return {"success": False, "message": "Error de conexión a la base de datos"}
        
        cursor = connection.cursor()
        
        # Verificar que la notificación existe y pertenece al usuario
        cursor.execute("""
            SELECT id FROM notifications 
            WHERE id = %s AND user_id = %s
        """, (notification_id, user_id))
        
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return {"success": False, "message": "Notificación no encontrada"}
        
        # Marcar como leída
        cursor.execute("""
            UPDATE notifications 
            SET is_read = TRUE 
            WHERE id = %s
        """, (notification_id,))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {"success": True, "message": "Notificación marcada como leída"}
        
    except Exception as e:
        return {"success": False, "message": f"Error al marcar notificación: {str(e)}"}

def mark_all_notifications_as_read(user_id: int) -> Dict[str, Any]:
    """Marca todas las notificaciones de un usuario como leídas"""
    try:
        connection = get_db_connection()
        if not connection:
            return {"success": False, "message": "Error de conexión a la base de datos"}
        
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE notifications 
            SET is_read = TRUE 
            WHERE user_id = %s AND is_read = FALSE
        """, (user_id,))
        
        affected_rows = cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        
        return {
            "success": True, 
            "message": f"{affected_rows} notificaciones marcadas como leídas"
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error al marcar notificaciones: {str(e)}"}

def get_unread_notifications_count(user_id: int) -> int:
    """Obtiene el número de notificaciones no leídas de un usuario"""
    try:
        connection = get_db_connection()
        if not connection:
            return 0
        
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM notifications 
            WHERE user_id = %s AND is_read = FALSE
        """, (user_id,))
        
        count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        
        return count
        
    except Exception as e:
        print(f"Error al obtener conteo de notificaciones: {e}")
        return 0

def create_loan_notifications(loan_id: int, lender_id: int, borrower_id: int, loan_type: str, amount: Optional[float] = None, object_name: Optional[str] = None) -> Dict[str, Any]:
    """Crea notificaciones automáticas para un préstamo"""
    try:
        # Notificación para el prestatario
        borrower_notification = NotificationCreate(
            user_id=borrower_id,
            title="Nuevo préstamo recibido",
            message=f"Has recibido un préstamo de {lender_id}. {'Monto: $' + str(amount) if amount else 'Objeto: ' + object_name}",
            type=NotificationType.INFO,
            loan_id=loan_id
        )
        
        # Notificación para el prestamista
        lender_notification = NotificationCreate(
            user_id=lender_id,
            title="Préstamo creado",
            message=f"Has creado un préstamo para {borrower_id}. {'Monto: $' + str(amount) if amount else 'Objeto: ' + object_name}",
            type=NotificationType.SUCCESS,
            loan_id=loan_id
        )
        
        # Crear ambas notificaciones
        borrower_result = create_notification(borrower_notification)
        lender_result = create_notification(lender_notification)
        
        if borrower_result["success"] and lender_result["success"]:
            return {"success": True, "message": "Notificaciones creadas exitosamente"}
        else:
            return {"success": False, "message": "Error al crear algunas notificaciones"}
            
    except Exception as e:
        return {"success": False, "message": f"Error al crear notificaciones: {str(e)}"}

def create_overdue_notification(loan_id: int, borrower_id: int, lender_name: str, object_name: Optional[str] = None, amount: Optional[float] = None) -> Dict[str, Any]:
    """Crea una notificación de préstamo vencido"""
    try:
        notification = NotificationCreate(
            user_id=borrower_id,
            title="Préstamo vencido",
            message=f"Tu préstamo de {lender_name} ha vencido. {'Monto: $' + str(amount) if amount else 'Objeto: ' + object_name}",
            type=NotificationType.WARNING,
            loan_id=loan_id
        )
        
        return create_notification(notification)
        
    except Exception as e:
        return {"success": False, "message": f"Error al crear notificación de vencimiento: {str(e)}"}

def create_return_notification(loan_id: int, lender_id: int, borrower_name: str, object_name: Optional[str] = None, amount: Optional[float] = None) -> Dict[str, Any]:
    """Crea una notificación de préstamo devuelto"""
    try:
        notification = NotificationCreate(
            user_id=lender_id,
            title="Préstamo devuelto",
            message=f"{borrower_name} ha devuelto el préstamo. {'Monto: $' + str(amount) if amount else 'Objeto: ' + object_name}",
            type=NotificationType.SUCCESS,
            loan_id=loan_id
        )
        
        return create_notification(notification)
        
    except Exception as e:
        return {"success": False, "message": f"Error al crear notificación de devolución: {str(e)}"}
