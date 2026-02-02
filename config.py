import os
import tweepy
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# ✅ Twitter API Credentials
bearer_token = os.getenv('X_API_BEARER_TOKEN')
api_key = os.getenv('X_CONSUMER_KEY')
api_secret = os.getenv('X_CONSUMER_SECRET')
access_token = os.getenv('X_ACCESS_TOKEN')
access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')

# ✅ OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Load environment variables
load_dotenv()

# Twitter API Credentials (v2)
bearer_token = os.getenv('X_API_BEARER_TOKEN')
api_key = os.getenv('X_CONSUMER_KEY')
api_secret = os.getenv('X_CONSUMER_SECRET')
access_token = os.getenv('X_ACCESS_TOKEN')
access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')

# Create a custom session with a default timeout
class TimeoutSession(requests.Session):
    def request(self, *args, **kwargs):
        kwargs.setdefault('timeout', 240)  # 180 seconds timeout
        return super().request(*args, **kwargs)

# Instantiate the Tweepy Client normally
client_v2 = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
    wait_on_rate_limit=True
)

# Replace the internal session with your custom TimeoutSession
client_v2._session = TimeoutSession()

# Now any request made by client_v2 should use a 120-second timeout by default.

auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
api_v1 = tweepy.API(auth)
image_path = "assets/lady_kaede_img.jpg"  
# Upload media to v1.1 API
media = api_v1.media_upload(image_path)

# Authenticate with OAuth 2.0 for v2 API (posting tweet)
client_v2_media = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)




# ✅ Scraping Constraints
DB = "TaoWar-X.db"
MAX_INFLUENCERS = 120  # Max influencers per month
TWEETS_PER_SCRAPE = 10  # Default tweets per scrape
DAILY_SCRAPES_PER_INFLUENCER = 2  # Scrape each influencer twice per day
SKIP_SCRAPE_PERCENTAGE = 10  # 10% of influencers will have one scrape skipped daily
API_LIMIT = 12000   # Monthly API limit
BATCH_SWITCH_INTERVAL_DAYS = 30  # Switch influencer batch every 30 days

# ✅ Time Scheduling
SCRAPE_WINDOWS = {
    "morning": (6, 12),
    "evening": (18, 24),
}

# ✅ Hardcoded Crypto Keywords (Dynamically updated later)
CRYPTO_KEYWORDS = ["Bitcoin", "Ethereum", "DeFi", "Web3", "Crypto", "Blockchain", "NFT"]

LOCAL_IMAGE_PATH = os.path.join("assets", "img.png")