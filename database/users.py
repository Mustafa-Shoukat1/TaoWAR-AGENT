from database.connection import get_connection
import sqlite3

def add_default_users():
    """Adds default users to the users table if they do not already exist."""
    default_users = [
        ("admin", "admin"),
        ("Mikedoyle@invluencer.com", "Dude3288*TW01!"),
        ("Kiddoyles@gmail.com", "Dude3288*TW02!"),
        ("Drpatrickdoyle@gmail.com", "Dude3288*TW03!"),
        ("marcperkinsism@gmail.com", "Dude3288*TW04!"),
        ("paul@keyko.io", "Dude3288*TW05!"),
    ]

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for username, password in default_users:
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                print(f"✅ Added user: {username}")
            except sqlite3.IntegrityError:
                print(f"⚠️ User '{username}' already exists, skipping.")

        conn.commit()
    except Exception as e:
        print(f"⚠️ Error adding default users: {e}")
    finally:
        conn.close()


def check_user_credentials(username, password):
    """Checks if provided credentials match an existing user."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        return user is not None
    finally:
        conn.close()


def get_all_users():
    """Get all users from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username FROM users")
        rows = cursor.fetchall()
        return [{"id": row[0], "username": row[1]} for row in rows]
    except Exception as e:
        print(f"⚠️ Error getting users: {e}")
        return []
    finally:
        conn.close()

