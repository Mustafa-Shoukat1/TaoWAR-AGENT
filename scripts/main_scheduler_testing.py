# Testing schedular

import time as time_module
import random
from services.scheduler_state_service import get_scheduler_state, update_scheduler_state, SchedulerStatus
from services.influencer_service import get_influencers
from scripts.post_categorization_and_summarization import run_pipeline as categorize_and_summarize
from scripts.post_daily_summary_to_x import post_category_summaries
from scripts.post_daily_report import run_pipeline as daily_report_pipeline
from scripts.post_weekly_report import run_weekly_pipeline
from utils.logger import logger
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

def is_processing_time():
    now = datetime.now(ZoneInfo("Europe/Paris"))
    # Processing allowed during minutes 0,1,2,3 of any hour
    return now.minute >= 0 and now.minute < 10

def is_posting_time():
    now = datetime.now(ZoneInfo("Europe/Paris"))
    # Posting allowed after minute 4
    return now.minute >= 15

def is_weekly_time():
    now = datetime.now(ZoneInfo("Europe/Paris"))
    # Weekly pipeline runs at minute 2 of any hour
    return now.minute >= 10

def run_user_scheduler(username: str, check_interval_minutes: int = 1):
    is_active = get_scheduler_state(username)

    logger.info(f"Initializing scheduler for user {username}")
    update_scheduler_state(
        username, 
        is_active,
        SchedulerStatus.IDLE, 
        details={
            "message": "Scheduler started, waiting for processing time",
            "check_interval_minutes": check_interval_minutes
        }
    )

    # Fetch 5 influencers only
    all_influencers = [inf["username"] for inf in get_influencers()][:5]
    # random.shuffle(all_influencers)
    logger.info(f"📋 Loaded {len(all_influencers)} influencers")

    current_position = 0
    daily_state = {
        "date": datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d"),
        "categorization_and_summarization": False,
        "posting_done": False,
        "weekly_done": False
    }

    while get_scheduler_state(username):
        today = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d")

        # Reset state for new day
        if today != daily_state["date"]:
            logger.info(f"🗓️ New day detected: {today}. Resetting daily processing state.")
            daily_state = {
                "date": today,
                "categorization_and_summarization": False,
                "posting_done": False,
                "weekly_done": False
            }

        print(f"Current time: {datetime.now(ZoneInfo('Europe/Paris')).strftime('%Y-%m-%d %H:%M:%S')}, Processing: {is_processing_time()}, Posting: {is_posting_time()}, Weekly: {is_weekly_time()}")

        # Processing
        if is_processing_time() and not daily_state["categorization_and_summarization"]:
            logger.info(f"🏁 Starting daily processing for {today}.")
            try:
                start_pos = current_position
                batch_size = min(5, len(all_influencers) - current_position)
                end_pos = start_pos + batch_size

                batch_influencers = all_influencers[start_pos:end_pos]

                if batch_influencers:
                    logger.info(f"📦 Processing {len(batch_influencers)} influencers (positions {start_pos} to {end_pos-1}).")
                    update_scheduler_state(
                        username, 
                        True,
                        SchedulerStatus.FETCHING_TWEETS, 
                        details={
                            "message": "Processing daily batch of influencers",
                            "influencer_count": len(batch_influencers),
                            "start_position": start_pos,
                            "end_position": end_pos - 1
                        }
                    )

                    categorize_and_summarize(batch=1, is_active=True, influencers=batch_influencers, username=username)
                    current_position = end_pos

                    if current_position >= len(all_influencers):
                        logger.info("🔄 Reached end of influencer list. Starting over next day.")
                        current_position = 0

                    daily_state["categorization_and_summarization"] = True
                    logger.info(f"✅ Daily categorization and summarization completed. Processed {len(batch_influencers)} influencers.")
                    update_scheduler_state(
                        username, 
                        True,
                        SchedulerStatus.WAITING_FOR_POSTING, 
                        details={
                            "message": "All influencers processed, waiting for posting time",
                            "next_position": current_position,
                            "influencers_processed": len(batch_influencers)
                        }
                    )
                else:
                    logger.warning("⚠️ No influencers loaded. Will try to reload list.")
                    all_influencers = [inf["username"] for inf in get_influencers()][:5]
                    current_position = 0
                    update_scheduler_state(
                        username, 
                        True,
                        SchedulerStatus.IDLE, 
                        details={
                            "message": "No influencers loaded. Reloading list.",
                            "next_check": (datetime.now(ZoneInfo("Europe/Paris")) + timedelta(minutes=check_interval_minutes)).strftime("%Y-%m-%d %H:%M:%S")
                        }
                    )

            except Exception as e:
                logger.error(f"❌ Error during processing for {username}: {e}", exc_info=True)
                update_scheduler_state(
                    username, 
                    True,
                    SchedulerStatus.ERROR, 
                    details={
                        "message": "Error during processing",
                        "error": str(e)
                    }
                )

        # Weekly pipeline
        elif is_weekly_time() and not daily_state["weekly_done"]:
            logger.info("🗓️ It's the scheduled minute — running weekly pipeline.")
            try:
                run_weekly_pipeline(is_active=True, username=username)
                daily_state["weekly_done"] = True
                logger.info("✅ Weekly pipeline run completed.")
                update_scheduler_state(
                    username,
                    True,
                    SchedulerStatus.WEEKLY_REPORT,
                    details={
                        "message": "Weekly pipeline run at scheduled time",
                        "date": daily_state["date"]
                    }
                )
            except Exception as e:
                logger.error(f"❌ Error during weekly pipeline for {username}: {e}", exc_info=True)
                update_scheduler_state(
                    username,
                    True,
                    SchedulerStatus.ERROR,
                    details={
                        "message": "Error during weekly pipeline execution",
                        "error": str(e)
                    }
                )

        # Posting
        elif is_posting_time() and daily_state["categorization_and_summarization"] and not daily_state["posting_done"]:
            logger.info("🕒 It's posting time.")
            try:
                logger.info("🐦 Posting daily summaries to X...")
                # post_category_summaries(batch=1, is_active=True, username=username)

                daily_state["posting_done"] = True

                logger.info("✅ Daily posting completed. All tasks done for today.")
                update_scheduler_state(
                    username, 
                    True,
                    SchedulerStatus.DAY_COMPLETED, 
                    details={
                        "message": "Completed all processing for today",
                        "date": daily_state["date"],
                        "next_position": current_position
                    }
                )
            except Exception as e:
                logger.error(f"❌ Error during posting for {username}: {e}", exc_info=True)
                update_scheduler_state(
                    username, 
                    True,
                    SchedulerStatus.ERROR, 
                    details={
                        "message": "Error during posting execution",
                        "error": str(e)
                    }
                )

            try:
                logger.info('Sending daily report to web')
                daily_report_pipeline(batch=1, is_active=True, username=username)
                logger.info('Sent daily report to web')
            except Exception as e:
                logger.error(f'Error in sending the report {e}')

        else:
            if not is_processing_time() and not daily_state["categorization_and_summarization"]:
                logger.info("⏳ Outside processing window. Waiting for processing time.")
            elif not is_posting_time() and daily_state["categorization_and_summarization"] and not daily_state["posting_done"]:
                logger.info("⏳ Processing done. Waiting for posting time.")
            elif daily_state["posting_done"]:
                logger.info("✅ All processing completed for today. Waiting for tomorrow's processing window.")
            else:
                logger.info("⏳ Waiting for next scheduled activity.")

            update_scheduler_state(
                username, 
                True,
                SchedulerStatus.IDLE, 
                details={
                    "message": "Waiting for next time window",
                    "next_check": (datetime.now(ZoneInfo("Europe/Paris")) + timedelta(minutes=check_interval_minutes)).strftime("%Y-%m-%d %H:%M:%S")
                }
            )

        logger.info(f"⏸ Checking schedule again in {check_interval_minutes} minute(s)...")
        time_module.sleep(check_interval_minutes * 60)

    logger.info(f"🚫 Scheduler turned off for user {username}. Exiting.")
    update_scheduler_state(
        username,
        False, 
        SchedulerStatus.IDLE, 
        details={
            "message": "Scheduler turned off"
        }
    )
