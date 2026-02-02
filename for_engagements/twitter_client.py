import os
import tweepy
from dotenv import load_dotenv
from utils.logger import logger


def get_twitter_clients():
    load_dotenv()
    bearer_token = os.getenv('X_API_BEARER_TOKEN')
    api_key = os.getenv('X_CONSUMER_KEY')
    api_secret = os.getenv('X_CONSUMER_SECRET')
    access_token = os.getenv('X_ACCESS_TOKEN')
    access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')

    logger.info("Authenticating with Twitter API...")
    client_v2 = tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        wait_on_rate_limit=True
    )
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
    api_v1 = tweepy.API(auth)
    logger.info("Twitter API authenticated successfully.")
    return client_v2, api_v1
