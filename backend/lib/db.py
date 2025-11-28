import sqlite3
import os
from typing import Optional

DATABASE_PATH = "users.db"

def get_db_connection():
    """Obtiene una conexión a la base de datos SQLite"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Inicializa la base de datos y crea las tablas necesarias"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente")

def check_database_exists() -> bool:
    """Verifica si la base de datos existe"""
    return os.path.exists(DATABASE_PATH)

def get_user_by_username(username: str) -> Optional[dict]:
    """Obtiene un usuario por su nombre de usuario"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return dict(user)
    return None

def create_user(name: str, username: str, email: str, password_hash: str) -> bool:
    """Crea un nuevo usuario en la base de datos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO users (name, username, email, password_hash) VALUES (?, ?, ?, ?)',
            (name, username, email, password_hash)
        )
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
