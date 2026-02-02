from twitter_client import get_twitter_clients
from influencer_metrics import fetch_influencer_profile, fetch_recent_tweets, fetch_mentions
from engagement_analysis import calculate_engagement_rate, influencer_score
from logger import setup_logger

logger = setup_logger(__name__)

def analyze_influencer(username):
    logger.info(f"Starting analysis for influencer: {username}")
    client_v2, _ = get_twitter_clients()
    profile = fetch_influencer_profile(client_v2, username)
    if not profile:
        logger.error(f"Profile not found for username: {username}")
        print(f"User not found: {username}")
        return None
    tweets = fetch_recent_tweets(client_v2, profile["id"])
    eng_rate = calculate_engagement_rate(tweets, profile["followers_count"])
    # Aggregate engagement stats
    likes = sum(t["like_count"] for t in tweets)
    retweets = sum(t["retweet_count"] for t in tweets)
    replies = sum(t["reply_count"] for t in tweets)
    quotes = sum(t["quote_count"] for t in tweets)
    return {
        "name": profile["name"],
        "handle": "@" + profile["username"],
        "followers": profile["followers_count"],
        "likes": likes,
        "retweets": retweets,
        "replies": replies,
        "quotes": quotes,
        "engagement_rate": round(eng_rate, 2)
    }

if __name__ == "__main__":
    result = analyze_influencer("elonmusk")
    print(result)
