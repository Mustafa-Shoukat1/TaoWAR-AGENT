from database.connection import get_connection

def get_influencers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM influencers")
    influencers = [{"username": row[0]} for row in cursor.fetchall()]
    conn.close()
    return influencers

def save_influencer(username):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO influencers (username) VALUES (?)", (username,))
        conn.commit()
    except:
        pass
    conn.close()

def delete_influencer(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM influencers WHERE username = ?", (username,))
    conn.commit()
    conn.close()

from database.connection import get_connection
from datetime import datetime
from zoneinfo import ZoneInfo

def save_user_metrics(profile: dict):
    """
    Insert or update user metrics in the user_metrics table (CET time).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cet_now = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO user_metrics (
                id, username, name, bio, location, created_at, profile_image_url,
                followers_count, following_count, tweet_count, listed_count, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username = excluded.username,
                name = excluded.name,
                bio = excluded.bio,
                location = excluded.location,
                created_at = excluded.created_at,
                profile_image_url = excluded.profile_image_url,
                followers_count = excluded.followers_count,
                following_count = excluded.following_count,
                tweet_count = excluded.tweet_count,
                listed_count = excluded.listed_count,
                last_updated = ?
        ''', (
            profile["id"],
            profile["username"],
            profile.get("name"),
            profile.get("bio"),
            profile.get("location"),
            str(profile.get("created_at")),
            profile.get("profile_image_url"),
            profile.get("followers_count", 0),
            profile.get("following_count", 0),
            profile.get("tweet_count", 0),
            profile.get("listed_count", 0),
            cet_now,          # Insert value
            cet_now           # Update value for last_updated
        ))
        conn.commit()
    finally:
        conn.close()


from database.connection import get_connection
from datetime import datetime
from zoneinfo import ZoneInfo

def get_influencer_metrics_from_db(username: str) -> dict:
    """
    Fetch today's metrics for the given influencer username from the user_metrics table.
    Returns a dict with the same structure as fetch_influencer_profile.
    Only fetches entries where last_updated is today in CET.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cet_today = datetime.now(ZoneInfo("Europe/Paris")).date().isoformat()  # 'YYYY-MM-DD'
        cursor.execute('''
            SELECT id, username, name, bio, location, created_at, profile_image_url,
                   followers_count, following_count, tweet_count, listed_count, last_updated
            FROM user_metrics
            WHERE username = ?
              AND date(last_updated) = ?
            ORDER BY last_updated DESC
            LIMIT 1
        ''', (username, cet_today))
        row = cursor.fetchone()
        if not row:
            return {}
        return {
            "id": row[0],
            "username": row[1],
            "name": row[2],
            "bio": row[3],
            "location": row[4],
            "created_at": row[5],
            "profile_image_url": row[6],
            "followers_count": row[7],
            "following_count": row[8],
            "tweet_count": row[9],
            "listed_count": row[10]
        }
    finally:
        conn.close()
