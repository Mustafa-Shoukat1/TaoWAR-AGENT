import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import time
import tweepy
import streamlit as st

from config import client_v2  # Tweepy v2 client
from core.responder import get_most_relevant_index
from services.post_service import get_all_saved_tweet_ids, save_relevant_posts, save_garbage_posts
from utils.logger import logger

def fetch_tweets(username, num_posts, max_retries=5):
    retries = 0
    delay = 90  # You can adjust this
    while retries < max_retries:
        try:
            # Get user ID from username
            user = client_v2.get_user(username=username, user_fields=["id"])
            if not user or not user.data:
                st.error(f"⚠️ Could not fetch user ID for {username}. Check API permissions.")
                return []
            user_id = user.data.id

            # Fetch recent tweets
            tweets = client_v2.get_users_tweets(
                id=user_id, 
                max_results=num_posts,
                tweet_fields=["id", "created_at", "text", "conversation_id", "entities", "public_metrics", "context_annotations"],
                expansions=["referenced_tweets.id"],
                user_fields=["username"]
            )
            if not tweets or not tweets.data:
                st.warning(f"⚠️ No tweets found for {username}.")
                return []
            
            # Format tweets with all required info
            formatted_tweets = []
            for tweet in tweets.data:
                tweet_info = {
                    "id": tweet.id,
                    "username": username,
                    "text": tweet.text,
                    "created_at": tweet.created_at.isoformat() if hasattr(tweet.created_at, "isoformat") else str(tweet.created_at),
                    "conversation_id": getattr(tweet, "conversation_id", None),
                    "link": f"https://twitter.com/{username}/status/{tweet.id}",
                    "retweet_count": tweet.public_metrics.get("retweet_count", 0) if hasattr(tweet, "public_metrics") else 0,
                    "like_count": tweet.public_metrics.get("like_count", 0) if hasattr(tweet, "public_metrics") else 0,
                    "reply_count": tweet.public_metrics.get("reply_count", 0) if hasattr(tweet, "public_metrics") else 0,
                    "quote_count": tweet.public_metrics.get("quote_count", 0) if hasattr(tweet, "public_metrics") else 0,
                    "hashtags": [e["tag"] for e in getattr(tweet, "entities", {}).get("hashtags", [])] if getattr(tweet, "entities", None) else [],
                    "context_annotations": getattr(tweet, "context_annotations", []),
                }
                formatted_tweets.append(tweet_info)
            logger.info(f"\nFetch tweet data for {username}:\n {formatted_tweets}\n")
            return formatted_tweets

        except Exception as e:
            retries += 1
            st.error(f"Error fetching tweets for {username}: {e} (retry {retries}/{max_retries})")
            time.sleep(delay)
    return []

def scrape_influencers(influencer, num_posts):
    """Scrapes tweets, checks relevance using OpenAI, and stores them accordingly."""
    with st.spinner(f"🔄 Scraping tweets for @{influencer}..."):
        try:
            saved_tweet_ids = get_all_saved_tweet_ids()
            tweets = fetch_tweets(influencer, num_posts)

            if not tweets:
                st.warning(f"⚠️ No new tweets found for @{influencer}.")
                return ([], [])

            # ✅ Filter out already saved tweets
            new_tweets = [tw for tw in tweets if str(tw["id"]) not in saved_tweet_ids]

            if not new_tweets:
                st.info(f"✅ All recent tweets for @{influencer} are already in the database.")
                return ([], [])

            # ✅ Identify the most relevant tweet
            most_relevant_index = get_most_relevant_index(new_tweets)
            print(f'most relvent index= {most_relevant_index}')
            logger.info(f'most relvent index= {most_relevant_index}')
            

            if most_relevant_index < 0 or most_relevant_index >= len(new_tweets):
                selected_tweet = None
                garbage_tweets = new_tweets
            else:
                selected_tweet = new_tweets[most_relevant_index]
                garbage_tweets = [tw for i, tw in enumerate(new_tweets) if i != most_relevant_index]

            relevant_list = [selected_tweet] if selected_tweet else []

            # ✅ Save tweets in the database
            if selected_tweet:
                # save_relevant_posts([selected_tweet], "posts")
                save_relevant_posts([selected_tweet], "selected")

            if garbage_tweets:
                save_garbage_posts(garbage_tweets)

        except Exception as e:
            print(f"⚠️ Unexpected error during scraping: {e}")
            st.error(f"⚠️ Unexpected error during scraping: {e}")
            return ([], [])

    # ✅ Show scraping summary in UI AFTER loading completes
    st.success(f"✅ Scraping Completed for @{influencer}")
    st.markdown(f"**📌 Total Tweets Scraped:** {len(tweets)}")
    st.markdown(f"**🎯 Relevant Tweets Found:** {1 if selected_tweet else 0}")
    st.markdown(f"**🗑 Non-Relevant Tweets Stored:** {len(garbage_tweets)}")

    return (relevant_list, garbage_tweets)

# print(fetch_tweets("elon_musk", 10))