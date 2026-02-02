from database.connection import get_connection
import datetime

def log_api_call(count=1):
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.date.today().isoformat()
    cursor.execute("""
        INSERT INTO api_usage (date, count)
        VALUES (?, ?)
        ON CONFLICT(date) DO UPDATE SET count = count + ?
    """, (today, count, count))
    conn.commit()
    conn.close()

def get_api_usage_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(count) FROM api_usage WHERE date >= date('now', 'start of month')")
    result = cursor.fetchone()[0]
    conn.close()
    return result or 0
