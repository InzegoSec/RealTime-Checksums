import sqlite3
import os
import time
from config import DB_PATH


def initializeDatabase() -> None:
    """Crea la base de datos y la tabla si no existen."""
    os.makedirs("./data/", exist_ok=True)
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hashes (
                    ab_path   TEXT PRIMARY KEY,
                    hash      TEXT,
                    mtime     INTEGER,
                    timestamp INTEGER,
                    status    TEXT DEFAULT 'ok'
                );
            """)
            # Agrega la columna status si la BD ya existia sin ella
            try:
                cursor.execute("ALTER TABLE hashes ADD COLUMN status TEXT DEFAULT 'ok'")
            except sqlite3.OperationalError:
                pass
    except sqlite3.Error:
        return None


def insertHashRecord(filePath, fileHash, mtime) -> None:
    """Inserta un nuevo registro en la tabla."""
    timestamp = int(time.time())
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO hashes VALUES (?, ?, ?, ?, ?)",
                (filePath, fileHash, mtime, timestamp, "ok")
            )
    except sqlite3.Error:
        return None


def getHashRecord(filePath) -> tuple | None:
    """Retorna el registro de un archivo por su ruta absoluta."""
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM hashes WHERE ab_path = ?", (filePath,))
            result = cursor.fetchone()
            return result
    except sqlite3.Error:
        return None


def updateHashRecord(filePath, fileHash, mtime) -> None:
    """Actualiza el hash y mtime de un archivo existente."""
    timestamp = int(time.time())
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE hashes SET hash = ?, mtime = ?, timestamp = ?, status = 'ok' WHERE ab_path = ?",
                (fileHash, mtime, timestamp, filePath)
            )
    except sqlite3.Error:
        return None


def markAsDeleted(filePath: str) -> None:
    """Marca un archivo como eliminado sin borrarlo de la BD."""
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE hashes SET status = 'deleted' WHERE ab_path = ?",
                (filePath,)
            )
    except sqlite3.Error:
        return None