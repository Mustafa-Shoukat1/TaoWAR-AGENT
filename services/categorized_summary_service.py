from database.connection import get_connection
from typing import List
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

def get_paris_date():
    paris_tz = ZoneInfo("Europe/Paris")
    now_paris = datetime.now(paris_tz)
    return now_paris.date()  # Returns a datetime.date object in Paris time

def get_paris_datetime():
    paris_tz = ZoneInfo("Europe/Paris")
    return datetime.now(paris_tz)  # Returns a datetime.datetime object


def save_category_summary(category, influencer_usernames, summary, batch_no):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO category_summaries (category, influencer_usernames, summary, batch_no, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            category,
            ','.join(influencer_usernames),
            summary,
            batch_no,
            get_paris_date()  # Use Paris date
        ))
        conn.commit()
    finally:
        conn.close()

def get_category_summaries_by_batch(batch_no):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM category_summaries
        WHERE batch_no = ? AND date = ?
    ''', (batch_no, get_paris_date()))  # Use Paris date
    summaries = cursor.fetchall()
    conn.close()
    return summaries

def fetch_unposted_summaries(batch_no: int) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, category, summary
        FROM category_summaries
        WHERE batch_no = ? AND date = ? AND posted_flag = 0
        ORDER BY id ASC
    """, (batch_no, get_paris_date()))  # Use Paris date
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": row[0], "category": row[1], "summary": row[2]}
        for row in rows
    ]

def mark_summaries_as_posted(ids: List[int]) -> None:
    if not ids:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        "UPDATE category_summaries SET posted_flag = 1 WHERE id = ?",
        [(i,) for i in ids]
    )
    conn.commit()
    conn.close()
