import mysql.connector
from mysql.connector import Error
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib

# Configuración de la base de datos MySQL
DB_CONFIG = {
    'host': 'localhost',  # Para ejecución directa en PC
    'port': 3306,
    'user': 'root',
    'password': 'vivacristorey',
    'database': 'loan_system',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def get_db_connection():
    """Obtiene una conexión a la base de datos MySQL"""
    try:
        print(f"Intentando conectar a MySQL: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"Base de datos: {DB_CONFIG['database']}")
        print(f"Usuario: {DB_CONFIG['user']}")
        
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("Conexion a MySQL exitosa")
            return connection
    except Error as e:
        print(f"❌ Error al conectar a MySQL: {e}")
        return None

def init_database():
    """Inicializa la base de datos y crea las tablas necesarias"""
    try:
        # Primero crear la base de datos si no existe
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        
        cursor = connection.cursor()
        print(f"Creando base de datos '{DB_CONFIG['database']}' si no existe...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"Base de datos '{DB_CONFIG['database']}' creada/verificada exitosamente")
        
        # Ahora conectar a la base de datos específica
        connection = get_db_connection()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Crear tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                address TEXT,
                profile_image VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Crear tabla de préstamos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                lender_id INT NOT NULL,
                borrower_id INT NOT NULL,
                loan_type ENUM('money', 'object') NOT NULL,
                amount DECIMAL(10,2) NULL,
                object_name VARCHAR(255) NULL,
                object_description TEXT NULL,
                object_image VARCHAR(500) NULL,
                loan_date DATE NOT NULL,
                due_date DATE NOT NULL,
                return_date DATE NULL,
                status ENUM('active', 'returned', 'overdue') DEFAULT 'active',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (lender_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (borrower_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_lender (lender_id),
                INDEX idx_borrower (borrower_id),
                INDEX idx_status (status),
                INDEX idx_due_date (due_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Crear tabla de notificaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type ENUM('info', 'warning', 'error', 'success') DEFAULT 'info',
                is_read BOOLEAN DEFAULT FALSE,
                loan_id INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE SET NULL,
                INDEX idx_user (user_id),
                INDEX idx_read (is_read),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("Base de datos MySQL inicializada correctamente")
        return True
        
    except Error as e:
        print(f"Error al inicializar la base de datos: {e}")
        return False

def check_database_exists() -> bool:
    """Verifica si la base de datos existe"""
    try:
        connection = get_db_connection()
        if connection:
            connection.close()
            return True
        return False
    except Error:
        return False

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Obtiene un usuario por su nombre de usuario"""
    try:
        connection = get_db_connection()
        if not connection:
            return None
            
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return user
    except Error as e:
        print(f"Error al obtener usuario: {e}")
        return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un usuario por su ID"""
    try:
        connection = get_db_connection()
        if not connection:
            return None
            
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return user
    except Error as e:
        print(f"Error al obtener usuario por ID: {e}")
        return None

def create_user(name: str, username: str, email: str, password_hash: str, phone: str = None, address: str = None) -> bool:
    """Crea un nuevo usuario en la base de datos"""
    try:
        connection = get_db_connection()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        cursor.execute(
            'INSERT INTO users (name, username, email, password_hash, phone, address) VALUES (%s, %s, %s, %s, %s, %s)',
            (name, username, email, password_hash, phone, address)
        )
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Error as e:
        print(f"Error al crear usuario: {e}")
        return False

def update_user_profile(user_id: int, **kwargs) -> bool:
    """Actualiza el perfil de un usuario"""
    try:
        connection = get_db_connection()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Construir la consulta dinámicamente
        fields = []
        values = []
        
        for key, value in kwargs.items():
            if value is not None:
                fields.append(f"{key} = %s")
                values.append(value)
        
        if not fields:
            return False
            
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
        
        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()
        
        return True
    except Error as e:
        print(f"Error al actualizar perfil: {e}")
        return False

def hash_password(password: str) -> str:
    """Hashea una contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verifica si una contraseña coincide con el hash"""
    return hash_password(password) == hashed
