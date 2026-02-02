from database.connection import get_connection
from typing import List, Dict
from zoneinfo import ZoneInfo
from datetime import datetime

def get_paris_date():
    paris_tz = ZoneInfo("Europe/Paris")
    return datetime.now(paris_tz).date()


def get_paris_date():
    paris_tz = ZoneInfo("Europe/Paris")
    return datetime.now(paris_tz).date()

def save_categorized_post(influencer: str, tweet_id: str, categories: List[str], batch_no: int) -> None:
    """
    Save a single categorized post entry.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO categorized_posts (influencer, tweet_id, categories, batch_no, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            influencer,
            tweet_id,
            ','.join(categories),
            batch_no,
            get_paris_date()  # Use Paris/CET date
        ))
        conn.commit()
    finally:
        conn.close()

def fetch_categorized_posts_by_batch(batch_no: int) -> List[Dict]:
    """
    Fetch categorized posts for the current Paris date and specified batch.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT influencer, tweet_id, categories
        FROM categorized_posts
        WHERE batch_no = ? AND date = ?
    ''', (batch_no, get_paris_date()))  # Use Paris/CET date
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "influencer": row[0],
            "tweet_id": row[1],
            "categories": [cat.strip() for cat in row[2].split(",")]
        }
        for row in rows
    ]

def fetch_grouped_by_category(batch_no: int) -> Dict[str, List[Dict]]:
    """
    Group categorized posts by category for a given batch.
    """
    posts = fetch_categorized_posts_by_batch(batch_no)
    grouped = {}
    for post in posts:
        for category in post["categories"]:
            grouped.setdefault(category, []).append({
                "influencer": post["influencer"],
                "tweet_id": post["tweet_id"]
            })
    return grouped
