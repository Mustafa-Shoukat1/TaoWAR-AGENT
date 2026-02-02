from database.connection import get_connection
import datetime

def get_keywords():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT keyword FROM keywords")
    keywords = [row[0] for row in cursor.fetchall()]
    conn.close()
    return keywords

def update_keywords(new_keywords):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM keywords")
    for keyword in new_keywords:
        cursor.execute("INSERT INTO keywords (keyword, updated_at) VALUES (?, ?)", (keyword, datetime.datetime.utcnow()))
    conn.commit()
    conn.close()

def delete_keyword(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM keywords WHERE keyword = ?", (keyword,))
    conn.commit()
    conn.close()
