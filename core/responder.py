import tweepy
from openai import OpenAI
from config import OPENAI_API_KEY, bearer_token, api_key, api_secret, access_token, access_token_secret
from services.keyword_service import get_keywords
from services.post_service import delete_post
from utils.logger import logger

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_most_relevant_index(posts):
    """
    Sends the list of tweets to OpenAI and returns a single integer indicating the index 
    (starting from 0) of the most relevant tweet. Returns -1 if none are deemed relevant.
    """
    if not posts:
        return -1

    keywords = get_keywords()
    keywords_list = ', '.join(keywords) if keywords else "Bitcoin, Ethereum, DeFi, Web3"

    prompt = (
    "Review the following tweets and determine which one is most relevant to any cryptocurrency "
    f"(including, but not limited to, Bitcoin, Ethereum, etc.) and the following keywords: {keywords_list}. "
    "Return only a single number representing the 0-based index of the tweet that best matches these criteria. "
    "If no tweet is relevant, return -1., you must return atleast one index\n"
)


    for i, post in enumerate(posts):
        print(f"{i}: {post['text']}\n")
        prompt += f"{i}: {post['text']}\n"

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI that selects the most relevant tweet from a list."},
                {"role": "user", "content": prompt},
            ],
            timeout=30
        )
        raw_response = response.choices[0].message.content.strip()
        most_relevant_index = int(raw_response) if raw_response.isdigit() else -1
    except Exception as e:
        print(f"⚠️ OpenAI request error: {e}")
        most_relevant_index = -1

    return most_relevant_index

TONE_DESCRIPTIONS = {
    "Tactical & Strategic": (
        "Scenario: Serious Market Analysis → Tone: Tactical & Strategic.\n"
        "Use data-driven insights and calculated strategies to strengthen market positioning.\n"
        "Example:\n"
        "Influencer: 'Bitcoin is showing signs of a breakout. What are we thinking?'\n"
        "Response: '“Opportunities multiply as they are seized.” This is where we press the advantage. Volume is key—watch for surges. #TaoWAR #CryptoTactics'\n"
    ),
    "Sharp & Witty": (
        "Scenario: Meme Wars & Rival Engagement → Tone: Sharp & Witty.\n"
        "Employ humor and quick wit to outmaneuver competition while staying on brand.\n"
        "Example:\n"
        "PEPE Holder: 'Pepe is the true king of memes. $tWAR is weak.'\n"
        "Response: '“Every battle is won before it is fought.” We set the rules; others merely follow. Ready to test that claim? #TaoWAR #MemeWarfare'\n"
    ),
    "Commanding & Engaging": (
        "Scenario: Community Building & Motivation → Tone: Commanding & Engaging.\n"
        "Speak with authority to unify and inspire decisive action within the community.\n"
        "Example:\n"
        "User: 'Why should I buy $tWAR instead of another meme coin?'\n"
        "Response: '“Know the terrain, know the enemy, and you need not fear the result of a hundred battles.” $tWAR isn’t just a token; it’s a movement. Choose wisely. #TaoWAR'\n"
    )
}


def generate_response(text, tone=None):
    """
    Generates a response for a given tweet text using TaoWAR AI principles and Sun Tzu's strategies.
    The response adapts to the chosen tone and must include a relevant Sun Tzu quote.
    """
    if tone is None or tone not in TONE_DESCRIPTIONS:
        tone_instruction = f"""Analyze the tweet and select the most appropriate tone: Tactical, Witty, or Engaging.
        these are the tones
        {TONE_DESCRIPTIONS}"""
    else:
        tone_instruction = TONE_DESCRIPTIONS[tone]  # Default tone if invalid key is passed
    


    prompt = f"""TaoWAR AI Agent – Response Generation Prompt

                Guiding Principles:
                • Keep responses short, direct, and strategic—like a war general giving commands.
                • Use clear, concise, and impactful language with no fluff or over-explanation.
                • Engage aggressively, but strategically—TaoWAR is not passive; it moves with purpose.
                • Every response must include a relevant Sun Tzu quote, reinforcing the philosophy of strategic warfare.
                • Meme wars require adaptability—match tone to the original post (serious, witty, or tactical).
                • No unnecessary qualifiers or corporate buzzwords—TaoWAR speaks with authority.

                Formatting Rules:
                - Use short, declarative sentences.
                - Frequent line breaks for readability and impact.
                - Bullet points or structured flow when needed for clarity.
                - Use direct engagement tactics—call out names when relevant.
                - Never use passive voice—TaoWAR leads, it does not follow.
                - Ask strategic questions only when it drives action.
                - Avoid filler words, weak phrasing, and unnecessary softeners.

                Banned Words & Phrases:
                - No corporate-speak, unnecessary adverbs, or vague filler words.
                - No overuse of adjectives—TaoWAR doesn’t embellish; it commands.
                - No weak transitional words (e.g., accordingly, moreover, thus).
                - No overused, meaningless crypto hype unless appropriate (e.g., next-gen, groundbreaking).

                Strategic Execution:
                1. Every reply is a battlefield move. No wasted words, no hesitation.
                2. TaoWAR does not argue—it dictates the strategy.
                3. If a post lacks relevance, TaoWAR doesn’t engage. It picks its battles wisely.
                4. Every response reinforces TaoWAR’s position—no aimless hype, only tactical strikes.

                Final Directive:
                TaoWAR commands the battlefield of crypto discussions with Sun Tzu’s wisdom, real-time strategy, and AI-driven precision. Every post, every reply, and every engagement is a calculated strike toward dominance.

                Tone Instruction:
                {tone_instruction}

                ---
                Tweet: {text}

                Generate a response that follows these principles and matches the specified tone.
                Use only these hastags that are provided in tone according to tone of reply
                #TaoWAR #CryptoTactics #TaoWAR #MemeWarfare  #TaoWAR
                """


    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strategic AI agent following Sun Tzu's principles."
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ],
            timeout=30
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"⚠️ OpenAI request error: {e}")
        return "⚠️ Failed to generate response."


def post_reply(tweet_id, reply_text):
    """
    Posts a reply to a tweet using Twitter API v2.
    Ensures the tweet is correctly associated with the original tweet.
    After a successful reply, deletes the post from the database.
    """
    
    # ✅ Authenticate Tweepy v1.1 API (For older API calls)
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
    api_v1 = tweepy.API(auth)

    # ✅ Authenticate Tweepy v2 API (Preferred for replies & new features)
    client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
    client_id = client.get_me().data.id  # ✅ Get the bot's Twitter user ID

    try:
        if not tweet_id or not reply_text:
            logger.error("⚠️ Error: Tweet ID or reply text is missing.")
            print("⚠️ Error: Tweet ID or reply text is missing.")
            return None

        # ✅ Post reply using Twitter API v2
        response = client.create_tweet(
            in_reply_to_tweet_id=tweet_id,  # ✅ Correct way to reply
            text=reply_text
        )

        if response:
            logger.info(f"✅ Successfully replied to tweet ID {tweet_id}: {reply_text}")
            print(f"✅ Successfully replied to tweet ID {tweet_id}: {reply_text}")
            
            # ✅ Delete the post from database after a successful reply
            # delete_post(tweet_id)
            # print(f"🗑 Deleted post ID {tweet_id} from database after replying.")

        return response

    except tweepy.TweepyException as e:
        print(f"⚠️ Error replying to tweet ID {tweet_id}: {e}")
        logger.error(f"⚠️ Error replying to tweet ID {tweet_id}: {e}")
        
        return None  # Indicate failure
