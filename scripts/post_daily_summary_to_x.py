from datetime import datetime
from services.categorized_summary_service import fetch_unposted_summaries, mark_summaries_as_posted
from services.duplication_prevention_service import (
    is_x_post_already_sent,
    mark_x_post_sent,
    get_daily_x_posts_count
)
from services.scheduler_state_service import update_scheduler_state, SchedulerStatus
from core.responder import post_reply
from config import api_key, api_secret, access_token, access_token_secret, bearer_token, client_v2_media, media
from ai_pipelines.header_generator import generate_header
from ai_pipelines.lady_kaedes_post import generate_mega_summary
import tweepy
import random
import time
import hashlib
from utils.logger import logger
from zoneinfo import ZoneInfo  # Python 3.9+

CET = ZoneInfo("Europe/Paris")

def post_category_summaries(batch, is_active, username="system"):
    """
    Post category summaries to social media

    Args:
        batch (int): Current batch number
        username (str): Username of the user who started the scheduler (for state tracking)
    """
    # Update state: starting to post
    update_scheduler_state(
        username, 
        is_active,
        SchedulerStatus.POSTING_SUMMARIES, 
        batch=batch,
        current_influencer=None,
        progress=0,
        details={
            "message": "Beginning to post summaries to X"
        }
    )
    summaries = fetch_unposted_summaries(batch)
    total_summaries = len(summaries)
    logger.info(f"Starting post summarization pipeline for batch {batch} with {total_summaries} summaries, datetime (CET): {datetime.now(CET).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # ✅ CRITICAL: Check daily X posting limit
    daily_posts_count = get_daily_x_posts_count('daily_summary')
    if daily_posts_count >= total_summaries + 1:  # +1 for header
        logger.warning(f"⚠️ Daily X posts limit reached ({daily_posts_count} posts already sent today)")
        update_scheduler_state(
            username, 
            is_active,
            SchedulerStatus.BATCH_COMPLETED, 
            batch=batch,
            current_influencer=None,
            progress=1.0,
            details={
                "message": f"Daily posting limit reached - {daily_posts_count} posts already sent",
                "status": "limited"
            }
        )
        return

    if not summaries:
        logger.info("✅ No unposted summaries found.")
        update_scheduler_state(
            username, 
            is_active,
            SchedulerStatus.BATCH_COMPLETED, 
            batch=batch,
            current_influencer=None,
            progress=1.0,
            details={
                "message": "No summaries to post",
                "status": "complete"
            }
        )
        return

    # Authenticate client for initial post (v2)
    client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
    first_post = (
        "Daily Crypto & Tradfi Update:\n\n"
        "Some of today’s insights on crypto and tradfi markets and trends. "
        "Follow General TaoWAR and Lady Kaede for key updates! #TaoWARSignals at https://taowar.ai"
    )
    header = generate_header(first_post)

    logger.info(f'\nsummaries {summaries}')

    try:
        # Update state before posting first summary
        update_scheduler_state(
            username, 
            is_active,
            SchedulerStatus.POSTING_SUMMARIES, 
            batch=batch,
            current_influencer=None,
            progress=0.2,
            details={
                "message": "Posting the header tweet",
                "total_summaries": len(summaries)
            }
        )

        # ✅ Post first summary
        response = client.create_tweet(text=header)
        time.sleep(random.uniform(2, 5))
        
        # Extract tweet ID safely
        try:
            main_tweet_id = response.data['id']
        except (AttributeError, KeyError, TypeError) as e:
            logger.error(f"❌ Failed to extract tweet ID from response: {e}")
            logger.error(f"Response type: {type(response)}, Response: {response}")
            raise Exception(f"Failed to extract tweet ID: {e}")
            
        logger.info(f"✅🐦Posted the header tweet with ID: {main_tweet_id}, for batch {batch}, at {datetime.now(CET).strftime('%Y-%m-%d %H:%M:%S %Z')} (CET)")

        sleep_seconds = random.uniform(100, 130)
        logger.info(f"Sleeping for {sleep_seconds:.0f} seconds to avoid rate limits ({int(sleep_seconds // 60)} minutes) [CET: {datetime.now(CET).strftime('%H:%M:%S')}]")
        time.sleep(sleep_seconds)

        # Update progress based on summaries summaries
        if summaries:
            for idx, item in enumerate(summaries):
                progress = 0.2 + 0.8 * ((idx + 1) / len(summaries))
                
                # ✅ CRITICAL: Check if this summary was already posted
                summary_hash = hashlib.sha256(item["summary"].encode()).hexdigest()[:16]
                category_name = item.get("category_name", "unknown")
                
                if is_x_post_already_sent(category_name, summary_hash, 'daily_summary'):
                    logger.warning(f"⚠️ Summary for {category_name} already posted today - skipping to prevent duplicate")
                    continue

                # Update state before posting reply
                update_scheduler_state(
                    username, 
                    is_active,
                    SchedulerStatus.POSTING_SUMMARIES, 
                    batch=batch,
                    current_influencer=None,
                    progress=progress,
                    details={
                        "message": f"Posting reply {idx + 1} of {len(summaries)}",
                        "summary_index": idx + 1,  
                        "total_summaries": len(summaries)
                    }
                )
                summary_sleep = random.uniform(100, 130)
                try:
                    # ✅ Post summaries as replies
                    reply = post_reply(main_tweet_id, item["summary"])
                    reply_sleep = random.uniform(2, 5)
                    # logger.info(f"Sleeping for {reply_sleep:.0f} seconds before next reply [CET: {datetime.now(CET).strftime('%H:%M:%S')}]")
                    time.sleep(reply_sleep)
                    if reply:
                        mark_summaries_as_posted([item["id"]])
                        
                        # ✅ CRITICAL: Fix Response object error - check if reply has 'data' attribute
                        reply_id = None
                        if hasattr(reply, 'data') and hasattr(reply.data, 'id'):
                            reply_id = reply.data.id
                        elif hasattr(reply, 'id'):
                            reply_id = reply.id
                        elif isinstance(reply, dict) and 'id' in reply:
                            reply_id = reply['id']
                        
                        # ✅ CRITICAL: Mark X post as sent to prevent duplicates
                        mark_x_post_sent(category_name, summary_hash, reply_id, 'daily_summary')
                        
                        logger.info(f"✅🐦 Replied to {main_tweet_id} to make thread and marked summary ID {item['id']} as posted., for batch {batch}")
                    else:
                        logger.error(f"⚠️🐦 Failed to post reply for summary ID {item['id']}, for batch {batch}")
                    summary_sleep = random.uniform(100, 130)
                    logger.info(f"Sleeping for {summary_sleep:.0f} seconds before next summary ({int(summary_sleep // 60)} minutes) [CET: {datetime.now(CET).strftime('%H:%M:%S')}]")
                    time.sleep(summary_sleep)  # Sleep to avoid rate limits
                except Exception as e:
                    logger.error(f"Got an error in posting the tweet, Error: {e}")
                    time.sleep(summary_sleep * 3)  
                    
            
            question = False
            first = random.randint(1, 4)
            second = random.randint(1, 4)
            if first == second:
                question = True
            thread_no = f'{total_summaries + 1}/{total_summaries + 1}'
            all_summaries_texts = [item["summary"] for item in summaries]
            mega_summary = generate_mega_summary(all_summaries_texts, question, thread_no)
            
            max_retries = 3
            retry_attempt = 0

            while retry_attempt < max_retries:
                try:
                    response = client_v2_media.create_tweet(
                        text=mega_summary,
                        media_ids=[media.media_id],
                        in_reply_to_tweet_id=main_tweet_id,
                    )
                    logger.info(f"✅🐦Posted the last tweet, at {datetime.now(CET).strftime('%Y-%m-%d %H:%M:%S %Z')} (CET),:: {mega_summary}")
                    break  # Exit loop if successful
                except Exception as e:
                    retry_attempt += 1
                    logger.error(f"❌ Error on attempt {retry_attempt} in the last tweet, at {datetime.now(CET).strftime('%Y-%m-%d %H:%M:%S %Z')} (CET),:: {mega_summary}")
                    if retry_attempt == max_retries:
                        logger.error(f"❗Failed after {max_retries} attempts: {e}")
                    else:
                        summary_sleep = random.uniform(100, 130)
                        logger.info(f"Sleeping for {summary_sleep:.0f} seconds before retrying, [CET: {datetime.now(CET).strftime('%H:%M:%S')}]")
                        time.sleep(summary_sleep)

        
        logger.info(f'All summaries posted, for batch {batch}, datetime (CET): {datetime.now(CET).strftime("%Y-%m-%d %H:%M:%S %Z")}')

        # Update state: Batch completed
        update_scheduler_state(
            username, 
            is_active,
            SchedulerStatus.BATCH_COMPLETED, 
            batch=batch,
            current_influencer=None,
            progress=1.0,
            details={
                "message": "All summaries posted successfully",
                "posted_summaries": len(summaries)
            }
        )

    except tweepy.TweepyException as e:
        logger.error(f"❌🐦 Error posting summaries: {e}")
        # Update state with error
        update_scheduler_state(
            username, 
            is_active,
            "error", 
            batch=batch,
            details={
                "message": "Error posting summaries",
                "error": str(e)
            }
        )
