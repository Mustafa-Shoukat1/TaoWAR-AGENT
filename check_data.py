import json
import datetime
import sqlite3
DB = "TaoWar-X.db"

def get_connection():
    return sqlite3.connect(DB)

def fetch_post_text(tweet_id: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM posts WHERE tweet_id = ?", (tweet_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""

def fetch_categorized_posts_by_batch(batch_no: int):
    """
    Fetch categorized posts for the current date and specified batch.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT influencer, tweet_id, categories
        FROM categorized_posts
        WHERE batch_no = ? AND date = ?
    ''', (batch_no, datetime.date.today()))
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

def fetch_grouped_by_category(batch_no: int):
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

def make_tweet_link(influencer: str, tweet_id: str) -> str:
    return f"https://x.com/{influencer}/status/{tweet_id}"

def fetch_selected_category_posts(batch_no: int, categories: list) -> dict:
    # Fetch posts grouped by category (for today)
    categorized = fetch_grouped_by_category(batch_no)

    result = {}

    for cat in categories:
        posts = []
        for post in categorized.get(cat, []):
            tweet_id = post["tweet_id"]
            influencer = post["influencer"]
            text = fetch_post_text(tweet_id)
            link = make_tweet_link(influencer, tweet_id)
            posts.append({
                "influencer": influencer,
                "tweet_id": tweet_id,
                "text": text,
                "link": link
            })
        result[cat] = posts

    return result

import json
import datetime

def fetch_selected_category_posts(batch_no: int, categories: list) -> dict:
    # Fetch posts grouped by category (for today)
    categorized = fetch_grouped_by_category(batch_no)
    result = {}
    for cat in categories:
        posts = []
        for post in categorized.get(cat, []):
            tweet_id = post["tweet_id"]
            influencer = post["influencer"]
            text = fetch_post_text(tweet_id)
            link = make_tweet_link(influencer, tweet_id)
            posts.append({
                "influencer": influencer,
                "tweet_id": tweet_id,
                "text": text,
                "link": link
            })
        result[cat] = posts
    return result

if __name__ == "__main__":
    BATCH_NO = 1

    ALL_CATEGORIES = [
        "Crypto Market Trends",
        "Artificial Intelligence",
        "Blockchain Technology",
        "DeFi (Decentralized Finance)",
        "Regulation & Policy",
        "Crypto Adoption",
        "Trading & Investment Strategies",
        "Macro Economics",
        "Stablecoins",
        "Security & Scams",
    ]

    data = fetch_selected_category_posts(BATCH_NO, ALL_CATEGORIES)

    print(json.dumps(data, indent=2, ensure_ascii=False))

    # Use today's date for the file name
    today = datetime.date.today().isoformat()
    filename = f"all_category_posts_{today}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
