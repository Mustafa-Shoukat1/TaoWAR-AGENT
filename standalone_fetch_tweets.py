import tweepy
import os

# Fill in your own values:
BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAAP7F1AEAAAAAb0m4xsqA94iySbhVKXcYgCqmiNQ%3DH0jbJJvaoaRhSRkv7YYUQASwtjIlqMjLWATJAZVLHGMHb4ZHqP' #second

client_v2 = tweepy.Client(bearer_token=BEARER_TOKEN)

def fetch_tweets(username, num_posts, max_retries=3):
    retries = 0
    delay = 3
    while retries < max_retries:
        try:
            user = client_v2.get_user(username=username, user_fields=["id"])
            if not user or not user.data:
                print(f"Could not fetch user ID for {username}")
                return []
            user_id = user.data.id

            tweets = client_v2.get_users_tweets(
                id=user_id,
                max_results=num_posts,
                tweet_fields=["id", "created_at", "text", "conversation_id", "entities", "public_metrics", "context_annotations"],
                expansions=["referenced_tweets.id"],
                user_fields=["username"]
            )
            if not tweets or not tweets.data:
                print(f"No tweets found for {username}.")
                return []
            
            formatted_tweets = []
            for tweet in tweets.data:
                tm = tweet.public_metrics if hasattr(tweet, "public_metrics") else {}
                tweet_info = {
                    "id": tweet.id,
                    "username": username,
                    "text": tweet.text,
                    "created_at": str(tweet.created_at),
                    "retweet_count": tm.get("retweet_count", 0),
                    "like_count": tm.get("like_count", 0),
                    "reply_count": tm.get("reply_count", 0),
                    "quote_count": tm.get("quote_count", 0),
                }
                print(f"{tweet_info['created_at']} | Likes: {tweet_info['like_count']} | Retweets: {tweet_info['retweet_count']} | Replies: {tweet_info['reply_count']} | Quotes: {tweet_info['quote_count']}")
                print(f"Text: {tweet_info['text'][:80]}")
                print("-" * 50)
                formatted_tweets.append(tweet_info)
            return formatted_tweets

        except Exception as e:
            retries += 1
            print(f"Error fetching tweets for {username}: {e} (retry {retries}/{max_retries})")
            import time; time.sleep(delay)
    return []

if __name__ == "__main__":
    username = "vladtenev"  # Or any other
    tweets = fetch_tweets(username, 5)
    print(tweets)
