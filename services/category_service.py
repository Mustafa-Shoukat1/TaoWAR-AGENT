from database.connection import get_connection

def add_category(name, description):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
    except:
        pass
    conn.close()

def get_all_categories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM categories")
    rows = cursor.fetchall()
    conn.close()
    return [{"name": r[1], "description": r[2]} for r in rows]  # FIXED INDEXES


def delete_category(category_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE name = ?", (category_id,))
    conn.commit()
    conn.close()
