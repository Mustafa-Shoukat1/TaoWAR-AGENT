from database.connection import get_connection

def log_x_post(summary, tweet_ids, batch_no):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO x_post_logs (summary, tweet_ids, batch_no)
            VALUES (?, ?, ?)
        ''', (summary, ','.join(tweet_ids), batch_no))
        conn.commit()
    finally:
        conn.close()

def get_x_post_logs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, summary, tweet_ids, batch_no, posted_at FROM x_post_logs ORDER BY posted_at DESC")
    logs = cursor.fetchall()
    conn.close()
    return logs
