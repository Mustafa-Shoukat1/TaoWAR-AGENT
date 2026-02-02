import random
from utils.logger import logger

def normalize(value, max_value):
    """Normalize a value to a 0–100 scale."""
    if max_value == 0:
        return 0
    return min((value / max_value) * 100, 100)

def calculate_engagement_rate(tweets, followers_count, multiplier=200000):
    """
    Calculates a synthetic engagement rate/score always between 0 and 100.
    Multiplies the score by a random float between 0.85 and 1 before returning.
    """
    logger.info(f"Calculating engagement rate: {len(tweets)} tweets, {followers_count} followers.")
    if not tweets or not followers_count:
        logger.warning("No tweets or zero followers. Engagement rate set to 0.")
        return 0.0
    total_engagement = sum(
        t.get("like_count", 0)
        + t.get("retweet_count", 0)
        + t.get("reply_count", 0)
        + t.get("quote_count", 0)
        for t in tweets
    )
    # Synthetic engagement score always from 0–100
    score = (total_engagement / (len(tweets) * followers_count)) * multiplier
    # Apply random multiplier between 0.85 and 1
    score = min(round(score, 2), 100)
    return score


def influencer_score(followers, engagement_rate, mentions, weights=None):
    MAX_FOLLOWERS = 1000000
    MAX_MENTIONS = 10000
    MAX_ENGAGEMENT = 100

    if weights is None:
        weights = {'followers': 0.4, 'engagement': 0.4, 'mentions': 0.2}

    norm_followers = normalize(followers, MAX_FOLLOWERS)
    norm_engagement = normalize(engagement_rate, MAX_ENGAGEMENT)
    norm_mentions = normalize(mentions, MAX_MENTIONS)

    score = (
        norm_followers * weights['followers'] +
        norm_engagement * weights['engagement'] +
        norm_mentions * weights['mentions']
    )

    score = min(score, 100)
    try:
        if random.random() < 0.2:  # 20% chance
            rand_multiplier = random.uniform(0.85, 1)
            score *= rand_multiplier
            logger.info(f"Calculated engagement rate (randomized x{rand_multiplier:.3f}): {score:.2f}/100")
        else:
            logger.info(f"Calculated engagement rate (no randomization): {score:.2f}/100")
    except Exception as e:
        logger.error(f"Error in multiplying score {e}")
    logger.info(
        f"Calculated influencer score: {score:.2f}/100 (followers={followers}, engagement_rate={engagement_rate}, mentions={mentions})"
    )
    return score
