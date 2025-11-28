from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from models.loan_models import (
    LoanCreate, LoanUpdate, LoanResponse, LoanFilter, LoanStats,
    NotificationCreate, NotificationResponse, UserResponse,
    LoanType, LoanStatus, NotificationType
)
from lib.mysql_db import get_db_connection
from controllers.notification_controller import create_loan_notifications

def create_loan(lender_id: int, loan_data: LoanCreate) -> Dict[str, Any]:
    """Crea un nuevo préstamo"""
    try:
        connection = get_db_connection()
        if not connection:
            return {"success": False, "message": "Error de conexión a la base de datos"}
        
        cursor = connection.cursor()
        
        # Verificar que el prestamista existe
        cursor.execute("SELECT id FROM users WHERE id = %s", (lender_id,))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return {"success": False, "message": "Prestamista no encontrado"}
        
        # Verificar que el prestatario existe
        cursor.execute("SELECT id FROM users WHERE id = %s", (loan_data.borrower_id,))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return {"success": False, "message": "Prestatario no encontrado"}
        
        # Insertar el préstamo
        cursor.execute("""
            INSERT INTO loans (lender_id, borrower_id, loan_type, amount, object_name, 
                             object_description, object_image, loan_date, due_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            lender_id, loan_data.borrower_id, loan_data.loan_type.value,
            loan_data.amount, loan_data.object_name, loan_data.object_description,
            loan_data.object_image, loan_data.loan_date, loan_data.due_date, loan_data.notes
        ))
        
        loan_id = cursor.lastrowid
        
        # Crear notificaciones para prestatario y prestamista
        create_loan_notifications(
            loan_id=loan_id,
            lender_id=lender_id,
            borrower_id=loan_data.borrower_id,
            loan_type=loan_data.loan_type.value,
            amount=loan_data.amount,
            object_name=loan_data.object_name
        )
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {"success": True, "message": "Préstamo creado exitosamente", "loan_id": loan_id}
        
    except Exception as e:
        return {"success": False, "message": f"Error al crear préstamo: {str(e)}"}

def get_loans_by_lender(lender_id: int, filters: Optional[LoanFilter] = None) -> List[LoanResponse]:
    """Obtiene todos los préstamos de un prestamista"""
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # Construir la consulta con filtros
        query = """
            SELECT l.*, 
                   lender.name as lender_name,
                   borrower.name as borrower_name
            FROM loans l
            JOIN users lender ON l.lender_id = lender.id
            JOIN users borrower ON l.borrower_id = borrower.id
            WHERE l.lender_id = %s
        """
        params = [lender_id]
        
        if filters:
            if filters.status:
                query += " AND l.status = %s"
                params.append(filters.status.value)
            
            if filters.loan_type:
                query += " AND l.loan_type = %s"
                params.append(filters.loan_type.value)
            
            if filters.borrower_id:
                query += " AND l.borrower_id = %s"
                params.append(filters.borrower_id)
            
            if filters.date_from:
                query += " AND l.loan_date >= %s"
                params.append(filters.date_from)
            
            if filters.date_to:
                query += " AND l.loan_date <= %s"
                params.append(filters.date_to)
            
            if filters.search:
                query += " AND (l.object_name LIKE %s OR l.notes LIKE %s OR borrower.name LIKE %s)"
                search_term = f"%{filters.search}%"
                params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY l.created_at DESC"
        
        cursor.execute(query, params)
        loans = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return [LoanResponse(**loan) for loan in loans]
        
    except Exception as e:
        print(f"Error al obtener préstamos: {e}")
        return []

def get_loans_by_borrower(borrower_id: int, filters: Optional[LoanFilter] = None) -> List[LoanResponse]:
    """Obtiene todos los préstamos de un prestatario"""
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # Construir la consulta con filtros
        query = """
            SELECT l.*, 
                   lender.name as lender_name,
                   borrower.name as borrower_name
            FROM loans l
            JOIN users lender ON l.lender_id = lender.id
            JOIN users borrower ON l.borrower_id = borrower.id
            WHERE l.borrower_id = %s
        """
        params = [borrower_id]
        
        if filters:
            if filters.status:
                query += " AND l.status = %s"
                params.append(filters.status.value)
            
            if filters.loan_type:
                query += " AND l.loan_type = %s"
                params.append(filters.loan_type.value)
            
            if filters.lender_id:
                query += " AND l.lender_id = %s"
                params.append(filters.lender_id)
            
            if filters.date_from:
                query += " AND l.loan_date >= %s"
                params.append(filters.date_from)
            
            if filters.date_to:
                query += " AND l.loan_date <= %s"
                params.append(filters.date_to)
            
            if filters.search:
                query += " AND (l.object_name LIKE %s OR l.notes LIKE %s OR lender.name LIKE %s)"
                search_term = f"%{filters.search}%"
                params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY l.created_at DESC"
        
        cursor.execute(query, params)
        loans = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return [LoanResponse(**loan) for loan in loans]
        
    except Exception as e:
        print(f"Error al obtener préstamos: {e}")
        return []

def update_loan(loan_id: int, lender_id: int, update_data: LoanUpdate) -> Dict[str, Any]:
    """Actualiza un préstamo existente"""
    try:
        connection = get_db_connection()
        if not connection:
            return {"success": False, "message": "Error de conexión a la base de datos"}
        
        cursor = connection.cursor()
        
        # Verificar que el préstamo existe y pertenece al prestamista
        cursor.execute("SELECT id FROM loans WHERE id = %s AND lender_id = %s", (loan_id, lender_id))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return {"success": False, "message": "Préstamo no encontrado o no autorizado"}
        
        # Construir la consulta de actualización
        fields = []
        params = []
        
        for field, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                fields.append(f"{field} = %s")
                params.append(value)
        
        if not fields:
            cursor.close()
            connection.close()
            return {"success": False, "message": "No hay campos para actualizar"}
        
        params.append(loan_id)
        query = f"UPDATE loans SET {', '.join(fields)} WHERE id = %s"
        
        cursor.execute(query, params)
        connection.commit()
        cursor.close()
        connection.close()
        
        return {"success": True, "message": "Préstamo actualizado exitosamente"}
        
    except Exception as e:
        return {"success": False, "message": f"Error al actualizar préstamo: {str(e)}"}

def mark_loan_returned(loan_id: int, lender_id: int) -> Dict[str, Any]:
    """Marca un préstamo como devuelto"""
    try:
        connection = get_db_connection()
        if not connection:
            return {"success": False, "message": "Error de conexión a la base de datos"}
        
        cursor = connection.cursor()
        
        # Verificar que el préstamo existe y pertenece al prestamista
        cursor.execute("SELECT borrower_id FROM loans WHERE id = %s AND lender_id = %s", (loan_id, lender_id))
        loan = cursor.fetchone()
        if not loan:
            cursor.close()
            connection.close()
            return {"success": False, "message": "Préstamo no encontrado o no autorizado"}
        
        borrower_id = loan[0]
        
        # Actualizar el préstamo
        cursor.execute("""
            UPDATE loans 
            SET status = %s, return_date = %s 
            WHERE id = %s
        """, (LoanStatus.RETURNED.value, date.today(), loan_id))
        
        # Crear notificación para el prestatario
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, loan_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            borrower_id,
            "Préstamo marcado como devuelto",
            f"El préstamo #{loan_id} ha sido marcado como devuelto",
            NotificationType.SUCCESS.value,
            loan_id
        ))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {"success": True, "message": "Préstamo marcado como devuelto"}
        
    except Exception as e:
        return {"success": False, "message": f"Error al marcar préstamo como devuelto: {str(e)}"}

def delete_loan(loan_id: int, lender_id: int) -> Dict[str, Any]:
    """Elimina un préstamo si pertenece al prestamista"""
    try:
        connection = get_db_connection()
        if not connection:
            return {"success": False, "message": "Error de conexión a la base de datos"}

        cursor = connection.cursor()

        # Comprobar propiedad
        cursor.execute("SELECT id FROM loans WHERE id = %s AND lender_id = %s", (loan_id, lender_id))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return {"success": False, "message": "Préstamo no encontrado o no autorizado"}

        # Eliminar
        cursor.execute("DELETE FROM loans WHERE id = %s", (loan_id,))
        connection.commit()
        cursor.close()
        connection.close()
        return {"success": True, "message": "Préstamo eliminado"}
    except Exception as e:
        return {"success": False, "message": f"Error al eliminar préstamo: {str(e)}"}


def get_upcoming_loans(user_id: int, days: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    """Devuelve préstamos que vencen pronto para prestatario y prestamista"""
    try:
        connection = get_db_connection()
        if not connection:
            return {"as_lender": [], "as_borrower": []}

        cursor = connection.cursor(dictionary=True)
        today = date.today()
        end_date = today + timedelta(days=days)

        # Como prestamista
        cursor.execute(
            """
            SELECT l.*, borrower.name AS borrower_name
            FROM loans l
            JOIN users borrower ON l.borrower_id = borrower.id
            WHERE l.lender_id = %s
              AND l.status = %s
              AND l.due_date BETWEEN %s AND %s
            ORDER BY l.due_date ASC
            """,
            (user_id, LoanStatus.ACTIVE.value, today, end_date),
        )
        lender_loans = cursor.fetchall()

        # Como prestatario
        cursor.execute(
            """
            SELECT l.*, lender.name AS lender_name
            FROM loans l
            JOIN users lender ON l.lender_id = lender.id
            WHERE l.borrower_id = %s
              AND l.status = %s
              AND l.due_date BETWEEN %s AND %s
            ORDER BY l.due_date ASC
            """,
            (user_id, LoanStatus.ACTIVE.value, today, end_date),
        )
        borrower_loans = cursor.fetchall()

        cursor.close()
        connection.close()

        return {
            "as_lender": lender_loans,
            "as_borrower": borrower_loans,
        }
    except Exception as e:
        print(f"Error al obtener préstamos próximos a vencer: {e}")
        return {"as_lender": [], "as_borrower": []}


def get_loan_report_summary(user_id: int) -> Dict[str, Any]:
    """Devuelve métricas agregadas para reportes (prestamista y prestatario)"""
    try:
        connection = get_db_connection()
        if not connection:
            return {}

        cursor = connection.cursor(dictionary=True)

        # Totales como prestamista
        cursor.execute(
            """
            SELECT
                loan_type,
                status,
                COUNT(*) AS total_count,
                COALESCE(SUM(CASE WHEN loan_type = 'money' THEN amount ELSE 0 END), 0) AS total_amount
            FROM loans
            WHERE lender_id = %s
            GROUP BY loan_type, status
            """,
            (user_id,),
        )
        lender_rows = cursor.fetchall()

        # Totales como prestatario
        cursor.execute(
            """
            SELECT
                loan_type,
                status,
                COUNT(*) AS total_count,
                COALESCE(SUM(CASE WHEN loan_type = 'money' THEN amount ELSE 0 END), 0) AS total_amount
            FROM loans
            WHERE borrower_id = %s
            GROUP BY loan_type, status
            """,
            (user_id,),
        )
        borrower_rows = cursor.fetchall()

        cursor.close()
        connection.close()

        def build_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
            summary = {
                "by_status": {},
                "by_type": {},
                "total_amount": 0,
                "total_count": 0,
            }
            for row in rows:
                status = row["status"]
                loan_type = row["loan_type"]
                count = row["total_count"]
                amount = float(row["total_amount"] or 0)

                summary["by_status"].setdefault(status, {"count": 0, "amount": 0.0})
                summary["by_status"][status]["count"] += count
                summary["by_status"][status]["amount"] += amount

                summary["by_type"].setdefault(loan_type, {"count": 0, "amount": 0.0})
                summary["by_type"][loan_type]["count"] += count
                summary["by_type"][loan_type]["amount"] += amount

                summary["total_count"] += count
                summary["total_amount"] += amount
            return summary

        return {
            "as_lender": build_summary(lender_rows),
            "as_borrower": build_summary(borrower_rows),
        }
    except Exception as e:
        print(f"Error al obtener resumen de reportes: {e}")
        return {}

def get_loan_stats(user_id: int) -> LoanStats:
    """Obtiene estadísticas de préstamos de un usuario"""
    try:
        connection = get_db_connection()
        if not connection:
            return LoanStats(
                total_active_loans=0, total_returned_loans=0, total_overdue_loans=0,
                total_amount_lent=0.0, total_amount_returned=0.0, pending_amount=0.0
            )
        
        cursor = connection.cursor()
        
        # Estadísticas como prestamista
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_lent,
                COUNT(CASE WHEN status = 'returned' THEN 1 END) as returned_lent,
                COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue_lent,
                COALESCE(SUM(CASE WHEN status = 'active' AND loan_type = 'money' THEN amount ELSE 0 END), 0) as pending_lent,
                COALESCE(SUM(CASE WHEN status = 'returned' AND loan_type = 'money' THEN amount ELSE 0 END), 0) as returned_amount_lent
            FROM loans WHERE lender_id = %s
        """, (user_id,))
        
        lender_stats = cursor.fetchone()
        
        # Estadísticas como prestatario
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_borrowed,
                COUNT(CASE WHEN status = 'returned' THEN 1 END) as returned_borrowed,
                COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue_borrowed,
                COALESCE(SUM(CASE WHEN status = 'active' AND loan_type = 'money' THEN amount ELSE 0 END), 0) as pending_borrowed,
                COALESCE(SUM(CASE WHEN status = 'returned' AND loan_type = 'money' THEN amount ELSE 0 END), 0) as returned_amount_borrowed
            FROM loans WHERE borrower_id = %s
        """, (user_id,))
        
        borrower_stats = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return LoanStats(
            total_active_loans=(lender_stats[0] or 0) + (borrower_stats[0] or 0),
            total_returned_loans=(lender_stats[1] or 0) + (borrower_stats[1] or 0),
            total_overdue_loans=(lender_stats[2] or 0) + (borrower_stats[2] or 0),
            total_amount_lent=(lender_stats[3] or 0) + (lender_stats[4] or 0),
            total_amount_returned=(lender_stats[4] or 0) + (borrower_stats[4] or 0),
            pending_amount=(lender_stats[3] or 0) + (borrower_stats[3] or 0)
        )
        
    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
        return LoanStats(
            total_active_loans=0, total_returned_loans=0, total_overdue_loans=0,
            total_amount_lent=0.0, total_amount_returned=0.0, pending_amount=0.0
        )

def get_overdue_loans(user_id: int) -> List[LoanResponse]:
    """Obtiene préstamos vencidos de un usuario"""
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT l.*, 
                   lender.name as lender_name,
                   borrower.name as borrower_name
            FROM loans l
            JOIN users lender ON l.lender_id = lender.id
            JOIN users borrower ON l.borrower_id = borrower.id
            WHERE (l.lender_id = %s OR l.borrower_id = %s) 
            AND l.status = 'active' 
            AND l.due_date < %s
            ORDER BY l.due_date ASC
        """, (user_id, user_id, date.today()))
        
        loans = cursor.fetchall()
        
        # Actualizar estado a vencido
        for loan in loans:
            cursor.execute("UPDATE loans SET status = 'overdue' WHERE id = %s", (loan['id'],))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return [LoanResponse(**loan) for loan in loans]
        
    except Exception as e:
        print(f"Error al obtener préstamos vencidos: {e}")
        return []

def get_all_users(search: Optional[str] = None) -> List[UserResponse]:
    """Obtiene todos los usuarios para selección en préstamos"""
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT id, name, username, email, phone, address, profile_image, created_at FROM users"
        params = []
        
        if search:
            query += " WHERE name LIKE %s OR username LIKE %s OR email LIKE %s"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY name ASC"
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return [UserResponse(**user) for user in users]
        
    except Exception as e:
        print(f"Error al obtener usuarios: {e}")
        return []
