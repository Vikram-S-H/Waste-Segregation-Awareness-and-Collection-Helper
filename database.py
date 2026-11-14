
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
            user_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            waste_type TEXT NOT NULL,
            collection_date TEXT NOT NULL,
            instructions TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)

    # Check existing database columns
    cursor.execute("PRAGMA table_info(collection_requests)")
    columns = [column["name"] for column in cursor.fetchall()]

    # Add user_id if it does not exist
    if "user_id" not in columns:
        cursor.execute("""
            ALTER TABLE collection_requests
            ADD COLUMN user_id INTEGER
        """)

    # Add completed_at if it does not exist
    if "completed_at" not in columns:
        cursor.execute("""
            ALTER TABLE collection_requests
            ADD COLUMN completed_at TIMESTAMP
        """)

    connection.commit()
    connection.close()
def create_users_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

def register_user(name, phone, address, username, password):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users
        (name, phone, address, username, password)
        VALUES (?, ?, ?, ?, ?)
    """, (name, phone, address, username, password))

    connection.commit()
    connection.close()
def get_user_by_username(username):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM users
        WHERE username = ?
    """, (username,))

    user = cursor.fetchone()

    connection.close()

    return user

def get_user_by_id(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    connection.close()

    return user

def save_request(user_id, name, phone, address, waste_type,
                 collection_date, instructions):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO collection_requests
        (user_id, name, phone, address, waste_type,
         collection_date, instructions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        name,
        phone,
        address,
        waste_type,
        collection_date,
        instructions
    ))

    connection.commit()
    connection.close()
def update_request_status(request_id, status):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE collection_requests
        SET status = ?
        WHERE id = ?
    """, (status, request_id))

    connection.commit()
    connection.close()