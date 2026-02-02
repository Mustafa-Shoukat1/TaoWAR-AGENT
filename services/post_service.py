from database.connection import get_connection
import sqlite3

def get_all_saved_tweet_ids():
    """Returns a set of tweet IDs stored in either the posts, selected, or garbage_posts tables."""
    conn = get_connection()
    cursor = conn.cursor()
    saved_tweet_ids = set()
    try:
        cursor.execute("SELECT tweet_id FROM posts")
        saved_tweet_ids.update(row[0] for row in cursor.fetchall())
        cursor.execute("SELECT tweet_id FROM garbage_posts")
        saved_tweet_ids.update(row[0] for row in cursor.fetchall())
        cursor.execute("SELECT tweet_id FROM selected")
        saved_tweet_ids.update(row[0] for row in cursor.fetchall())
    except Exception as e:
        print(f"⚠️ Error fetching all saved tweet IDs: {e}")
    finally:
        conn.close()
    return saved_tweet_ids

def save_garbage_posts(posts):
    """Stores posts that are not the most relevant in the garbage_posts table."""
    if not posts:
        print("⚠️ No garbage posts to save.")
        return
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for post in posts:
            cursor.execute('''
                INSERT INTO garbage_posts (tweet_id, username, text, link, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (post["id"], post["username"], post["text"], post["link"], post["created_at"]))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"⚠️ Some garbage posts already exist in the database.")
    except Exception as e:
        print(f"⚠️ Error saving garbage posts: {e}")
    finally:
        conn.close()

def get_garbage_posts():
    """Fetches non-relevant (garbage) posts from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    garbage_posts = []
    try:
        cursor.execute("SELECT tweet_id, username, text, link, created_at FROM garbage_posts ORDER BY created_at DESC")
        garbage_posts = [{"tweet_id": row[0], "username": row[1], "text": row[2], "link": row[3], "created_at": row[4]} 
                         for row in cursor.fetchall()]
    except Exception as e:
        print(f"⚠️ Error fetching garbage posts: {e}")
    finally:
        conn.close()
    return garbage_posts

import json

def save_relevant_posts(posts, table):
    """Saves relevant tweets into the given table (posts or selected)."""
    if not posts:
        return
    saved_tweet_ids = get_all_saved_tweet_ids()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for post in posts:
            if post["id"] not in saved_tweet_ids:
                # Prepare data, using .get() with default None
                retweet_count = post.get("retweet_count")
                like_count = post.get("like_count")
                reply_count = post.get("reply_count")
                quote_count = post.get("quote_count")
                hashtags = ",".join(post.get("hashtags", [])) if post.get("hashtags") else None
                # Use json.dumps for context_annotations
                context_annotations = json.dumps(post.get("context_annotations")) if post.get("context_annotations") else None

                cursor.execute(f'''
                    INSERT INTO {table} (
                        tweet_id, username, text, link, created_at,
                        retweet_count, like_count, reply_count, quote_count,
                        hashtags, context_annotations
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post["id"], post["username"], post["text"], post["link"], post["created_at"],
                    retweet_count, like_count, reply_count, quote_count, hashtags, context_annotations
                ))
        conn.commit()
    except Exception as e:
        print(f"⚠️ Error saving relevant posts: {e}")
    finally:
        conn.close()


def get_relevant_posts():
    """Fetches relevant posts from the selected table."""
    conn = get_connection()
    cursor = conn.cursor()
    posts = []
    try:
        cursor.execute("SELECT tweet_id, username, text, link, created_at FROM selected ORDER BY created_at DESC")
        posts = [{"tweet_id": row[0], "username": row[1], "text": row[2], "link": row[3], "created_at": row[4]} 
                 for row in cursor.fetchall()]
    except Exception as e:
        print(f"⚠️ Error fetching posts: {e}")
    finally:
        conn.close()
    return posts

def get_all_posts():
    """Fetches all garbage posts from the database (used for visualization)."""
    conn = get_connection()
    cursor = conn.cursor()
    posts = []
    try:
        cursor.execute("SELECT tweet_id, username, text, link, created_at FROM garbage_posts ORDER BY created_at DESC")
        posts = [{"tweet_id": row[0], "username": row[1], "text": row[2], "link": row[3], "created_at": row[4]} 
                 for row in cursor.fetchall()]
    except Exception as e:
        print(f"⚠️ Error fetching posts: {e}")
    finally:
        conn.close()
    return posts

def delete_post(tweet_id):
    """Deletes a tweet from the posts table after replying."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM posts WHERE tweet_id = ?", (tweet_id,))
        conn.commit()
        print(f"🗑 Post {tweet_id} successfully deleted from posts table.")
    except Exception as e:
        print(f"⚠️ Error deleting post {tweet_id}: {e}")
    finally:
        conn.close()


def fetch_post_text(tweet_id: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM posts WHERE tweet_id = ?", (tweet_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""
