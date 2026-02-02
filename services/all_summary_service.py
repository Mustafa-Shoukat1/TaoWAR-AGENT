from database.connection import get_connection
import datetime

def save_all_summary(summary, batch_no):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO all_summaries (batch_no, date, summary)
            VALUES (?, ?, ?)
        ''', (batch_no, datetime.date.today(), summary))
        conn.commit()
    finally:
        conn.close()

def get_all_summary_by_batch(batch_no):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT summary FROM all_summaries
        WHERE batch_no = ? AND date = ?
    ''', (batch_no, datetime.date.today()))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
