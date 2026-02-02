from typing import Dict, Any, List
from utils.logger import logger
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
from database.connection import get_connection
from for_engagements.twitter_client import get_twitter_clients
from services.influencer_service import save_user_metrics

client_v2, _ = get_twitter_clients()


def fetch_influencer_profile(username: str) -> dict:
    logger.info(f"Fetching profile for user: {username}")
    try:
        response = client_v2.get_user(
            username=username,
            user_fields=["public_metrics", "description", "location", "created_at", "profile_image_url", "name"]
        )
        if not response.data:
            logger.warning(f"No profile data found for user: {username}")
            return {}
        user = response.data
        metrics = user.public_metrics
        profile = {
            "id": user.id,
            "username": username,
            "name": user.name,
            "bio": user.description,
            "location": user.location,
            "created_at": user.created_at,
            "profile_image_url": user.profile_image_url,
            "followers_count": metrics["followers_count"],
            "following_count": metrics["following_count"],
            "tweet_count": metrics["tweet_count"],
            "listed_count": metrics["listed_count"]
        }
        logger.info(f'\nGot data for {username}\n Data:\n {profile}')
        save_user_metrics(profile)   # <-- Save profile to DB here
        logger.info(f"Fetched and saved profile for {username}: {profile}")
        return profile
    except Exception as e:
        logger.exception(f"Error fetching profile for {username}: {e}")
        return {}


def fetch_recent_tweets_data(username: str, table: str = "posts") -> dict:
    """
    Fetches and aggregates tweet data for an influencer (username) for the past 7 days from the database.
    Returns a single dict with summed metrics and unique hashtags/context.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        today = datetime.now(ZoneInfo("Europe/Paris")).date()
        last_week = today - timedelta(days=6)
        # Fetch relevant tweets for the last 7 days
        cursor.execute(f'''
            SELECT 
                id,
                tweet_id,
                username,
                text,
                link,
                created_at,
                retweet_count,
                like_count,
                reply_count,
                quote_count,
                hashtags,
                context_annotations
            FROM {table}
            WHERE username = ?
              AND DATE(created_at) BETWEEN ? AND ?
            ORDER BY created_at DESC
        ''', (username, last_week.isoformat(), today.isoformat()))
        rows = cursor.fetchall()
        
        if not rows:
            return {}

        # Aggregation containers
        total_retweets = 0
        total_likes = 0
        total_replies = 0
        total_quotes = 0
        all_hashtags = set()
        all_contexts = set()
        tweet_ids = []
        texts = []
        links = []
        created_ats = []

        for row in rows:
            _, tweet_id, _, text, link, created_at, retweet_count, like_count, reply_count, quote_count, hashtags, context_annotations = row

            tweet_ids.append(tweet_id)
            texts.append(text)
            links.append(link)
            created_ats.append(created_at)

            total_retweets += retweet_count or 0
            total_likes += like_count or 0
            total_replies += reply_count or 0
            total_quotes += quote_count or 0

            # Handle hashtags (comma-separated)
            if hashtags:
                all_hashtags.update([tag.strip() for tag in hashtags.split(',') if tag.strip()])
            # Handle context_annotations (assumed as JSON list)
            if context_annotations:
                try:
                    ca_list = json.loads(context_annotations)
                    if isinstance(ca_list, list):
                        for ca in ca_list:
                            # You may need to change this depending on annotation format
                            if isinstance(ca, dict):
                                all_contexts.add(json.dumps(ca, sort_keys=True))
                            else:
                                all_contexts.add(str(ca))
                except Exception:
                    all_contexts.add(context_annotations)

        # Compose result (single dict)
        result = {
            "username": username,
            "tweet_ids": tweet_ids,
            "texts": texts,
            "links": links,
            "created_ats": created_ats,
            "retweet_count": total_retweets,
            "like_count": total_likes,
            "reply_count": total_replies,
            "quote_count": total_quotes,
            "hashtags": list(all_hashtags),
            "context_annotations": [json.loads(s) if s.startswith("{") or s.startswith("[") else s for s in all_contexts]
        }
        return result

    except Exception as e:
        print(f"⚠️ Error fetching recent tweet data: {e}")
        return {}
    finally:
        conn.close()


# fetch_mentions stays the same


def fetch_mentions(client_v2, influencer_username: str, max_results=20):
    logger.info(f"Searching for mentions of @{influencer_username}, up to {max_results} results.")
    try:
        query = f'@{influencer_username}'
        response = client_v2.search_recent_tweets(query=query, tweet_fields=["created_at"], max_results=max_results)
        if response.data:
            logger.info(f"Found {len(response.data)} mentions for @{influencer_username}.")
            return response.data
        else:
            logger.info(f"No mentions found for @{influencer_username}.")
            return []
    except Exception as e:
        logger.exception(f"Error fetching mentions for @{influencer_username}: {e}")
        return []
