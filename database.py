
import sqlite3
import os

# Create database folder if it does not exist
DATABASE_FOLDER = "database"
os.makedirs(DATABASE_FOLDER, exist_ok=True)

DATABASE_PATH = os.path.join(
    DATABASE_FOLDER,
    "waste_management.db"
)


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS collection_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            waste_type TEXT NOT NULL,
            collection_date TEXT NOT NULL,
            instructions TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def save_request(name, phone, address, waste_type,
                 collection_date, instructions):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO collection_requests
        (name, phone, address, waste_type,
         collection_date, instructions)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        phone,
        address,
        waste_type,
        collection_date,
        instructions
    ))

    connection.commit()
    connection.close()
