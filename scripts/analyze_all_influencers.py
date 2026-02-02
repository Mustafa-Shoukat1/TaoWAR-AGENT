import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import random
from for_engagements.influencer_metrics import fetch_recent_tweets_data
from for_engagements.engagement_analysis import calculate_engagement_rate
from services.influencer_service import get_influencers
from services.influencer_service import get_influencer_metrics_from_db
from utils.logger import logger

from for_engagements.influencer_metrics import fetch_influencer_profile
from utils.get_influcener_list import get_unique_influencers
from services.weekly_report_functions import build_report_category_summary_dict

from datetime import datetime
import time
import random
import streamlit as st
from utils.logger import logger
from zoneinfo import ZoneInfo  # for CET timezone

CET = ZoneInfo("Europe/Paris")


def fetch_influncers_list():
    now_cet = datetime.now(CET)
    is_wednesday = now_cet.weekday() == 2  # Monday=0, Tuesday=1, Wednesday=2
    is_wednesday = True
    if is_wednesday:
        try:
            weekly_data = build_report_category_summary_dict()  # {report_id: {...}, ...}
            all_influencers = get_unique_influencers(weekly_data)
            logger.info(f"Found {len(all_influencers)} unique influencers for analyzing weekly run.")

            return all_influencers
        except Exception as e:
            logger.error(f"Error fetching influencer user data: {e}")
    else:
        logger.info("Not Wednesday (CET), skipping influencer data fetch.")

def analyze_all_influencers(top_n=None, process_n=None):
    """
    - If process_n is provided: randomly shuffle and process only process_n influencers.
    - If not, process all.
    - After processing, return only the top_n (by engagement/followers) if top_n is provided.
    """
    try:
        try:
            influencers = fetch_influncers_list()
            if influencers:
                logger.info(f"GOt influncer from fetch influencer list function")
                pass
            else:
                influencers = get_influencers()
        except Exception as e:
            logger.error(f"Got error in getting influncers for analyzing {e}")
            influencers = get_influencers()
        results = []

        # If process_n is given, randomly select that many to process
        if process_n is not None and process_n < len(influencers):
            influencers = random.sample(influencers, process_n)

        total = len(influencers)
        for i, infl in enumerate(influencers, start=1):
            if isinstance(infl, dict):
                username = infl.get("username") or infl.get("handle")
            else:
                username = infl
            if not username:
                logger.warning(f"Skipping influencer with invalid entry: {infl}")
                continue

            logger.info(f"({i}/{total}) Processing influencer: {username}")
            print(f"({i}/{total}) Processing {username}...")

            # Fetch profile
            try:
                profile = get_influencer_metrics_from_db(username)
                if not profile:
                    logger.warning(f"Skipping {username} (profile not found in DB)")
                    continue
            except Exception as e:
                logger.error(f"Error fetching profile for {username}: {e}", exc_info=True)
                continue

            # Fetch tweets
            try:
                tweets_data = fetch_recent_tweets_data(username, table="posts")
            except Exception as e:
                logger.error(f"Error fetching tweets for {username}: {e}", exc_info=True)
                tweets_data = []

            logger.info(f"Fetched tweets data for {username}: {json.dumps(tweets_data, indent=2) if tweets_data else 'None'}")
            try:
                if isinstance(tweets_data, dict) and "tweet_ids" in tweets_data:
                    tweets = [{
                        "like_count": tweets_data.get("like_count", 0),
                        "retweet_count": tweets_data.get("retweet_count", 0),
                        "reply_count": tweets_data.get("reply_count", 0),
                        "quote_count": tweets_data.get("quote_count", 0),
                    }]
                    likes = tweets_data.get("like_count", 0)
                    retweets = tweets_data.get("retweet_count", 0)
                    replies = tweets_data.get("reply_count", 0)
                    quotes = tweets_data.get("quote_count", 0)
                elif isinstance(tweets_data, list):
                    tweets = tweets_data
                    likes = sum(t.get("like_count", 0) for t in tweets)
                    retweets = sum(t.get("retweet_count", 0) for t in tweets)
                    replies = sum(t.get("reply_count", 0) for t in tweets)
                    quotes = sum(t.get("quote_count", 0) for t in tweets)
                else:
                    tweets = []
                    likes = retweets = replies = quotes = 0

                eng_rate = calculate_engagement_rate(tweets, profile.get("followers_count", 0))
            except Exception as e:
                logger.error(f"Error calculating engagement or aggregating stats for {username}: {e}", exc_info=True)
                likes = retweets = replies = quotes = eng_rate = 0

            results.append({
                "rank": 0,  # will fill later
                "name": profile.get("name", ""),
                "handle": "@" + profile.get("username", ""),
                "followers": profile.get("followers_count", 0),
                "likes": likes,
                "retweets": retweets,
                "replies": replies,
                "quotes": quotes,
                "engagement_rate": round(eng_rate, 2)
            })
            logger.info(f"Influencer {username} processed: {json.dumps(results[-1], indent=2)}\n")

        # Sort and rank
        results.sort(key=lambda x: (-x["engagement_rate"], -x["followers"]))
        if top_n is not None:
            results = results[:top_n]
        for idx, item in enumerate(results, start=1):
            item["rank"] = idx

        # Write to file with error handling
        try:
            with open("influencer_stats.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info("Results written to influencer_stats.json")
            print("Done. Results written to influencer_stats.json")
        except Exception as e:
            logger.error(f"Error writing influencer_stats.json: {e}", exc_info=True)

        return results

    except Exception as e:
        logger.error(f"Critical error in analyze_all_influencers: {e}", exc_info=True)
        return []

if __name__ == "__main__":
    # Examples:
    analyze_all_influencers()  # Process all, return all
    # analyze_all_influencers(top_n=5)  # Process all, return top 5
    # analyze_all_influencers(process_n=10)  # Process 10 random, return all 10
    # analyze_all_influencers(top_n=5, process_n=10)  # Process 10 random, return top 5 from them
