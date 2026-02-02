
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.influencer_service import get_influencers
from services.category_service import get_all_categories
from services.categorized_post_service import save_categorized_post, fetch_grouped_by_category
from services.categorized_summary_service import save_category_summary
from services.x_post_log_service import log_x_post
from services.scheduler_state_service import update_scheduler_state, SchedulerStatus
from services.duplication_prevention_service import (
    is_influencer_processed_today, 
    mark_influencer_processing_start, 
    mark_influencer_processing_complete,
    is_summary_already_generated,
    mark_summary_generated
)
from core.scraper import fetch_tweets
from services.post_service import save_relevant_posts, fetch_post_text, get_all_saved_tweet_ids

from ai_pipelines.categorize import categorize_posts_batch
from ai_pipelines.summarize import generate_category_summary
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

def fetch_data():
    now_cet = datetime.now(CET)
    is_wednesday = now_cet.weekday() == 2  # Monday=0, Tuesday=1, Wednesday=2

    if is_wednesday:
        try:
            weekly_data = build_report_category_summary_dict()  # {report_id: {...}, ...}
            all_influencers = get_unique_influencers(weekly_data)
            logger.info(f"Found {len(all_influencers)} unique influencers for weekly run.")

            for inf in all_influencers:
                try:
                    fetch_influencer_profile(inf)
                    # Consider reducing sleep if not needed (e.g., 5-10 seconds)
                    time.sleep(random.uniform(100, 130))
                except Exception as e:
                    logger.warning(f"Error fetching profile for influencer {inf}: {e}")
            logger.info("Fetched all influencer profiles successfully.")
        except Exception as e:
            logger.error(f"Error fetching influencer user data: {e}")
    else:
        logger.info("Not Wednesday (CET), skipping influencer data fetch.")

def run_pipeline(batch, is_active, influencers, username="system"):
    """
    Run the categorization and summarization pipeline

    Args:
        batch (int): Current batch number
        influencers (list): List of influencer usernames to process
        username (str): Username of the user who started the scheduler (for state tracking)
    """
    try:
        logger.info(f"Starting categorization pipeline for batch {batch} with {len(influencers)} influencers, datetime (CET): {datetime.now(CET).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        update_scheduler_state(
            username,
            is_active,
            SchedulerStatus.FETCHING_TWEETS,
            batch=batch,
            progress=0,
            details={"message": "Starting pipeline", "total_influencers": len(influencers)}
        )

        categories_raw = get_all_categories()
        logger.info(f'📦 Fetched {len(categories_raw)} categories for batch {batch}')
        categories_dict = {cat["name"]: cat["description"] for cat in categories_raw}

        # Process each influencer
        for idx, inf in enumerate(influencers):
            # Sleep for one hour after every 24 influencers processed
            if (idx + 1) == 24:
                logger.info(f"Processed {(idx + 1)} influencers, sleeping for 1 hour to avoid API rate limits (CET: {datetime.now(CET).strftime('%H:%M:%S')})")
                time.sleep(60)  # 1 hour
                # time.sleep(60 * 60)  # 1 hour

            try:
                # ✅ CRITICAL: Check if influencer already processed today
                if is_influencer_processed_today(inf, 'categorization'):
                    logger.warning(f"⚠️ Influencer {inf} already processed today - skipping to prevent duplicates")
                    continue
                
                # Mark processing start
                mark_influencer_processing_start(inf, 'categorization')
                
                progress = idx / len(influencers)
                update_scheduler_state(
                    username,
                    is_active,
                    SchedulerStatus.FETCHING_TWEETS,
                    batch=batch,
                    current_influencer=inf,
                    progress=progress,
                    details={
                        "message": f"Fetching tweets for {inf}",
                        "influencer_index": idx + 1,
                        "total_influencers": len(influencers)
                    }
                )

                logger.info(f'Processing influencer: {inf} ({idx + 1}/{len(influencers)}) for batch {batch} (CET: {datetime.now(CET).strftime("%Y-%m-%d %H:%M:%S %Z")})')
                tweets = fetch_tweets(inf, 10)
                time.sleep(5)

                logger.info(f'📦 Fetched {len(tweets)} tweets for {inf}')

                # Update state: Categorizing tweets
                update_scheduler_state(
                    username,
                    is_active,
                    SchedulerStatus.CATEGORIZING_TWEETS,
                    batch=batch,
                    current_influencer=inf,
                    progress=progress,
                    details={
                        "message": f"Categorizing tweets for {inf}",
                        "tweet_count": len(tweets),
                        "influencer_index": idx + 1,
                        "total_influencers": len(influencers)
                    }
                )

                saved_tweet_ids = get_all_saved_tweet_ids()
                new_tweets = [tweet for tweet in tweets if tweet["id"] not in saved_tweet_ids]

                if not new_tweets:
                    logger.info(f"No new tweets found for influencer {inf} in batch {batch}. Skipping...")
                    continue
                logger.info(f"Infleuncer {inf}: Data: {new_tweets}")
                save_relevant_posts(new_tweets, "posts")

                logger.info(f"Batch categorizing {len(new_tweets)} new tweets for {inf} for batch {batch}")
                categorization_results = categorize_posts_batch(new_tweets, categories_dict)
                print(f'\n Categorization results: {categorization_results}\n')

                for tweet_idx, tweet in enumerate(new_tweets):
                    tweet_progress = (idx + tweet_idx / len(new_tweets)) / len(influencers)
                    update_scheduler_state(
                        username,
                        is_active,
                        SchedulerStatus.CATEGORIZING_TWEETS,
                        batch=batch,
                        current_influencer=inf,
                        progress=tweet_progress,
                        details={
                            "message": f"Processing categorization for tweet {tweet_idx + 1} of {len(new_tweets)} for {inf}",
                            "tweet_index": tweet_idx + 1,
                            "total_tweets": len(new_tweets),
                            "influencer_index": idx + 1,
                            "total_influencers": len(influencers)
                        }
                    )

                    tweet_id = str(tweet["id"])
                    if tweet_id in categorization_results:
                        relevant_cats = categorization_results[tweet_id]
                        logger.info(f"🧠 Tweet {tweet_id} categorized with: {relevant_cats}")

                        if relevant_cats:
                            save_categorized_post(inf, tweet_id, relevant_cats, batch)
                            logger.info(f"✅ Saved categorized post for {inf} with tweet ID {tweet_id} and categories: {relevant_cats} for batch {batch}")
                        else:
                            logger.info(f"No relevant categories found for tweet {tweet_id} for batch {batch} - skipping")
                    else:
                        logger.warning(f"⚠️ No categorization result found for tweet {tweet_id}")

                logger.info(f"Completed processing for influencer {inf} for batch {batch}. Waiting before next influencer... (CET: {datetime.now(CET).strftime('%H:%M:%S')})")
                
                # ✅ Mark influencer processing complete
                mark_influencer_processing_complete(inf, 'categorization')
                
                summary_sleep = random.uniform(100, 130)
                logger.info(f"Sleeping for {summary_sleep:.0f} seconds ({int(summary_sleep // 60)} minutes) [CET: {datetime.now(CET).strftime('%H:%M:%S')}]")
                time.sleep(summary_sleep)  # Sleep to avoid rate limits

            except Exception as e:
                logger.error(f"Could not process influencer {inf}: {e} for batch {batch}", exc_info=True)
                update_scheduler_state(
                    username,
                    is_active,
                    "error",
                    batch=batch,
                    current_influencer=inf,
                    details={
                        "message": f"Could not process influencer {inf}",
                        "problem": str(e)
                    }
                )
                retry_sleep = random.uniform(7 * 60, 10 * 60)
                logger.info(f"Waiting for a while before retrying for influencer {inf}... ({int(retry_sleep // 60)} minutes) [CET: {datetime.now(CET).strftime('%H:%M:%S')}]")
                time.sleep(retry_sleep)
            

        logger.info(f"Completed fetching and categorizing tweets for all influencers in batch {batch}, datetime (CET): {datetime.now(CET).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Starting category summary generation phase for batch {batch}")

        update_scheduler_state(
            username,
            is_active,
            SchedulerStatus.GENERATING_SUMMARIES,
            batch=batch,
            current_influencer=None,
            progress=0.8,
            details={
                "message": "Generating category summaries",
                "status": "Starting summary generation"
            }
        )

        categorized = fetch_grouped_by_category(batch)
        total_categories = len(categorized)
        logger.info(f"Found {total_categories} categories with posts to summarize for batch {batch} datetime (CET): {datetime.now(CET).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        categories_in_dict = [category for category in categorized.keys() if category in categories_dict]
        count_in_dict = len(categories_in_dict)
        index = 0
        for idx, (category, posts) in enumerate(categorized.items()):
            if category in categories_dict:
                summary_progress = 0.8 + (index / total_categories) * 0.2
                update_scheduler_state(
                    username,
                    is_active,
                    SchedulerStatus.GENERATING_SUMMARIES,
                    batch=batch,
                    current_influencer=None,
                    progress=summary_progress,
                    details={
                        "message": f"Generating summary for category {category}",
                        "category_index": index + 1,
                        "total_categories": count_in_dict,
                        "post_count": len(posts)
                    }
                )

                logger.info(f"Generating summary for category '{category}' ({index + 1}/{count_in_dict}) with {len(posts)} posts")

                for post in posts:
                    post["text"] = fetch_post_text(post["tweet_id"])

                # ✅ CRITICAL: Check if summary already generated for this category today
                today_str = datetime.now(CET).date().isoformat()
                posts_content = "\n".join([post["text"] for post in posts])
                import hashlib
                summary_hash = hashlib.sha256(f"{category}_{posts_content}".encode()).hexdigest()[:16]
                
                if is_summary_already_generated(today_str, batch, category, summary_hash):
                    logger.warning(f"⚠️ Summary for category '{category}' already generated today - skipping to prevent duplicates")
                    continue

                influencers_in_category = list({p["influencer"] for p in posts})
                category_description = categories_dict.get(category, "")
                thread_no = f'{index + 1}/{count_in_dict + 1}'


                summary = generate_category_summary(category, category_description, posts, thread_no)
                logger.info(f"📝 Generated summary for category {category}: {summary}")

                save_category_summary(category, influencers_in_category, summary, batch)
                logger.info(f"✅ Saved summary for category {category} with batch number {batch}")
                
                # ✅ CRITICAL: Mark summary as generated to prevent duplicates
                mark_summary_generated(today_str, batch, category, summary_hash, f"Generated for {len(posts)} posts")
                
                index += 1
            else:
                logger.info(f'Skipping category as this does not belong to our category: {category}')

        logger.info(f"Successfully completed categorization and summary pipeline for batch {batch}, datetime (CET): {datetime.now(CET).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        update_scheduler_state(
            username,
            is_active,
            SchedulerStatus.BATCH_COMPLETED,
            batch=batch,
            current_influencer=None,
            progress=1.0,
            details={
                "message": "Batch completed successfully",
                "processed_influencers": len(influencers),
                "processed_categories": total_categories
            }
        )
        
        try:
            fetch_data()
        except Exception as e:
            logger.error(f"Error in fetching data of profiles {e}")

    except Exception as e:
        try:
            logger.error(f"❌ Error during categorization pipeline execution: {e}", exc_info=True)
            update_scheduler_state(
                username,
                is_active,
                "error",
                batch=batch,
                details={
                    "message": "Error during pipeline execution",
                    "error": str(e)
                }
            )
        except Exception as e:
            logger.error(f"Got error in Exception of categorization and summarization, Error: {e}")
        
