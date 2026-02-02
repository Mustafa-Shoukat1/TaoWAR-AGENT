import time as time_module 
import random
from services.scheduler_state_service import get_scheduler_state
from services.scheduler_state_service import update_scheduler_state, SchedulerStatus
from services.influencer_service import get_influencers
from services.daily_state_service import get_daily_state, save_daily_state, reset_daily_state_for_new_day, update_daily_state_field
from services.duplication_prevention_service import (
    is_influencer_processed_today, 
    mark_influencer_processing_start, 
    mark_influencer_processing_complete,
    get_daily_x_posts_count,
    is_x_post_already_sent,
    is_report_already_sent_today,
    mark_report_sent,
    get_processing_summary_for_date,
    is_summary_already_generated,
    mark_summary_generated,
    get_daily_summary_count,
    is_categorization_pipeline_complete
)
from scripts.post_categorization_and_summarization import run_pipeline as categorize_and_summarize
from scripts.post_daily_summary_to_x import post_category_summaries
from scripts.post_daily_report import run_pipeline as daily_report_pipeline
from scripts.post_weekly_report import run_weekly_pipeline
from utils.logger import logger
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo  # Standard library in Python 3.9+
from services.scheduler_mutex_service import ensure_single_scheduler, SchedulerMutex

def is_processing_time():
    """
    Determine if current time is in the processing window (2:00 AM to 12:00 PM CET)
    
    Returns:
        bool: True if in processing window, False otherwise
    """
    # CET: 'Europe/Paris' or 'Europe/Berlin'
    now = datetime.now(ZoneInfo("Europe/Paris"))

    return time(2, 0) <= now.time() < time(9, 0)

def is_weekly_time():
    now = datetime.now(ZoneInfo("Europe/Paris"))
    return now.hour >= 9 and now.hour < 11



def is_posting_time():
    """
    Determine if current time is in the posting window (after 15:00 CET)
    
    Returns:
        bool: True if in posting window, False otherwise
    """
    # CET: 'Europe/Paris' or 'Europe/Berlin'
    now = datetime.now(ZoneInfo("Europe/Paris"))

    return now.time() >= time(15, 0)


def run_user_scheduler(username: str, check_interval_minutes: int = 15):
    """
    Run the user-specific scheduler:
    - Processes up to 48 influencers per day in one batch
    - Runs processing during 2am-12pm CET
    - Posts summary at 15:00 CET or later
    - Checks schedule every `check_interval_minutes` (default 15 min)
    - Uses mutex to ensure only one scheduler runs per user
    """
    # Ensure only one scheduler thread runs for this user
    try:
        with ensure_single_scheduler(username):
            logger.info(f"🔒 Acquired exclusive scheduler lock for {username}")
            _run_scheduler_main_loop(username, check_interval_minutes)
    except RuntimeError as e:
        logger.error(f"❌ Cannot start scheduler for {username}: {e}")
        return
    except Exception as e:
        logger.error(f"❌ Unexpected error in scheduler for {username}: {e}")
        return
    finally:
        logger.info(f"🔓 Scheduler for {username} has stopped")


def _run_scheduler_main_loop(username: str, check_interval_minutes: int = 15):
    """
    Main scheduler loop (protected by mutex)
    """
    # Initialize scheduler state
    try:
        is_active = get_scheduler_state(username)

        logger.info(f"Starting Main Summary Scheduler..{username}")
        logger.info(f"Started scheduler thread for {username}")
        
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
        
        # Fetch all influencers once when scheduler starts
        all_influencers = [inf["username"] for inf in get_influencers()]
        random.shuffle(all_influencers)
        logger.info(f"📋 Loaded {len(all_influencers)} influencers")
        
        # Get current date in CET
        today = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d")
        
        # Load daily state from database (persistent across restarts)
        daily_state = get_daily_state(username, today)
        logger.info(f"📅 Loaded daily state for {today}: {daily_state}")
        
        # Get persistent counters
        current_position = daily_state.get("current_position", 0)
        weekly_img_rotator = daily_state.get("weekly_img_rotator", 1)
        
        while get_scheduler_state(username):
            today = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d")
            
            # Check if it's a new day and reset daily state if needed
            if today != daily_state["date"]:
                logger.info(f"🗓️ New day detected: {today}. Resetting daily processing state.")
                
                # Log daily processing summary for yesterday
                yesterday_summary = get_processing_summary_for_date(daily_state["date"])
                if yesterday_summary:
                    logger.info(f"📊 Yesterday's processing summary: {yesterday_summary}")
                
                daily_state = reset_daily_state_for_new_day(username, today)
                # Reset counters for new day (optional - you can preserve them if needed)
                current_position = daily_state.get("current_position", 0)
                weekly_img_rotator = daily_state.get("weekly_img_rotator", 1)
                        
            # Processing time (2:00 AM - 12:00 PM CET)
            check = is_processing_time()
            print(f"Current time: {datetime.now(ZoneInfo('Europe/Paris')).strftime('%Y-%m-%d %H:%M:%S %Z')}, Processing time: {check}")
            if is_processing_time() and not daily_state["categorization_and_summarization"]:
                
                # ✅ CRITICAL: Enhanced duplicate detection for categorization 
                categorization_already_done = is_categorization_pipeline_complete(today, 1)
                
                # Also check if any summaries were generated today (additional safety check)
                summary_count = get_daily_summary_count(today, 1)
                
                if categorization_already_done or summary_count > 0:
                    logger.warning(f"⚠️ Categorization/Summary pipeline already processed today - found {summary_count} summaries - marking as done to prevent duplicate")
                    daily_state["categorization_and_summarization"] = True
                    save_daily_state(username, daily_state)
                    
                    update_scheduler_state(
                        username, 
                        True,
                        SchedulerStatus.WAITING_FOR_POSTING, 
                        details={
                            "message": f"Categorization already completed today - preventing duplicate execution (found {summary_count} existing summaries)",
                            "prevention": "duplicate_categorization_detected",
                            "existing_summaries": summary_count
                        }
                    )
                    
                    time_module.sleep(check_interval_minutes * 60)
                    continue
                
                logger.info(f"🏁 Starting daily processing for {today}.")
                
                # Mark categorization pipeline start with batch info
                mark_influencer_processing_start('CATEGORIZATION_PIPELINE', 'categorization_pipeline', batch_number=1)
                
                try:
                    # Calculate batch size and end position (up to 48 influencers)
                    start_pos = current_position
                    batch_size = min(48, len(all_influencers) - current_position)
                    end_pos = start_pos + batch_size
                    
                    batch_influencers = all_influencers[start_pos:end_pos]
                    
                    if batch_influencers:
                        logger.info(f"📦 Processing {len(batch_influencers)} influencers (positions {start_pos} to {end_pos-1}).")
                        
                        # Update state before processing
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
                        
                        # Process the batch
                        logger.info(f"Starting categorization and summarization pipeline")

                        categorize_and_summarize(batch=1, is_active=True, influencers=batch_influencers, username=username)
                        
                        # Mark categorization pipeline complete with batch info
                        mark_influencer_processing_complete('CATEGORIZATION_PIPELINE', 'categorization_pipeline')
                        
                        # Update position for next day
                        current_position = end_pos
                        
                        # If we've reached the end of the list, start over
                        if current_position >= len(all_influencers):
                            logger.info("🔄 Reached end of influencer list. Starting over from the beginning next day.")
                            current_position = 0
                        
                        # Mark processing as done and save to database
                        daily_state["categorization_and_summarization"] = True
                        daily_state["current_position"] = current_position
                        save_daily_state(username, daily_state)
                        
                        logger.info(f"✅ Daily categorization and summarization completed. Processed {len(batch_influencers)} influencers.")
                        update_scheduler_state(
                            username, 
                            True,
                            SchedulerStatus.WAITING_FOR_POSTING, 
                            details={
                                "message": "All influencers processed, waiting for posting time (15:00 CET)",
                                "next_position": current_position,
                                "influencers_processed": len(batch_influencers)
                            }
                        )
                    else:
                        logger.warning("⚠️ No influencers loaded. Will try to reload list.")
                        all_influencers = [inf["username"] for inf in get_influencers()]
                        current_position = 0
                        
                        update_scheduler_state(
                            username, 
                            True,
                            SchedulerStatus.IDLE, 
                            details={
                                "message": "No influencers loaded. Reloading list.",
                                "next_check": (datetime.now(ZoneInfo("Europe/Paris")) + timedelta(minutes=check_interval_minutes)).strftime("%Y-%m-%d %H:%M:%S %Z")
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
                    
            elif is_weekly_time() and not daily_state["weekly_done"]:
                logger.info("🗓️ It's 10:00 CET — running weekly pipeline.")
                
                # ✅ CRITICAL: Check if weekly report already sent today  
                if is_report_already_sent_today('weekly'):
                    logger.warning("⚠️ Weekly report already sent today - marking as done to prevent duplicate")
                    daily_state["weekly_done"] = True
                    save_daily_state(username, daily_state)
                    
                    time_module.sleep(check_interval_minutes * 60)
                    continue
                
                try:
                    weekly_ran = run_weekly_pipeline(is_active=True, username=username, weekly_img_rotator = weekly_img_rotator)
                    daily_state["weekly_done"] = True
                    
                    if weekly_ran:
                        weekly_img_rotator += 1
                        if weekly_img_rotator > 3:
                            weekly_img_rotator = 1
                        mark_report_sent('weekly')
                    
                    # Save updated state to database
                    daily_state["weekly_img_rotator"] = weekly_img_rotator
                    save_daily_state(username, daily_state)
                    
                    logger.info("✅ Weekly pipeline run completed.")
                    update_scheduler_state(
                        username,
                        True,
                        SchedulerStatus.WEEKLY_REPORT,
                        details={
                            "message": "Weekly pipeline run at 10:00 CET",
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
            
            # Posting time (after 15:00 CET)
            elif is_posting_time() and daily_state["categorization_and_summarization"] and not daily_state["posting_done"]:
                
                # ✅ CRITICAL: Check if posting already done today
                daily_x_posts = get_daily_x_posts_count('daily_summary')
                if daily_x_posts > 0:
                    logger.warning(f"⚠️ Daily X posts already sent today ({daily_x_posts} posts) - marking as done to prevent duplicates")
                    daily_state["posting_done"] = True
                    save_daily_state(username, daily_state)
                    
                    time_module.sleep(check_interval_minutes * 60)
                    continue
                
                logger.info("🕒 It's posting time (after 15:00 CET).")
                try:
                    # Set posting_done IMMEDIATELY to prevent duplicate posting sessions
                    daily_state["posting_done"] = True
                    daily_state["current_position"] = current_position
                    save_daily_state(username, daily_state)
                    
                    logger.info("🐦 Posting daily summaries to X...")
                    post_category_summaries(batch=1, is_active=True, username=username)
                    
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
                    
                    # ✅ CRITICAL: Check if daily report already sent today
                    if is_report_already_sent_today('daily'):
                        logger.warning("⚠️ Daily report already sent today - skipping to prevent duplicate")
                    else:
                        daily_report_pipeline(batch=1, is_active=True, username=username)
                        mark_report_sent('daily')
                        logger.info('✅ Sent daily report to web')
                        
                except Exception as e:
                    logger.error(f'❌ Error in sending the report {e}')

            
            # Outside of any active time windows or waiting for next step
            else:

                if not is_processing_time() and not daily_state["categorization_and_summarization"]:
                    logger.info("⏳ Outside categorization_and_summarization window (2:00-09:00 CET). Waiting for processing time.")
                    status = SchedulerStatus.IDLE
                    message = "Waiting for daily processing window"
                elif (
                    daily_state["categorization_and_summarization"]
                    and not daily_state["posting_done"]
                    and not is_posting_time()
                ):
                    logger.info("⏳ Daily processing done. Waiting for posting window (after 15:00 CET).")
                    status = SchedulerStatus.WAITING_FOR_POSTING
                    message = "Waiting for posting window (after 15:00 CET)"
                elif (
                    daily_state["categorization_and_summarization"]
                    and daily_state["posting_done"]
                    and not is_weekly_time()
                    and not daily_state["weekly_done"]
                ):
                    logger.info("⏳ Posting done. Waiting for weekly processing window (after 09:00 CET).")
                    status = SchedulerStatus.WAITING_FOR_POSTING
                    message = "Posting done. Waiting for weekly processing window (after 09:00 CET)"
                elif daily_state["posting_done"] and daily_state["weekly_done"]:
                    logger.info("✅ All processing completed for today. Waiting for tomorrow's processing window.")
                    status = SchedulerStatus.DAY_COMPLETED
                    message = "All processing done for today, waiting for tomorrow."
                else:
                    logger.info("⏳ Waiting for next scheduled activity.")
                    status = SchedulerStatus.IDLE
                    message = "Waiting for next scheduled activity."
                
                update_scheduler_state(
                    username,
                    True,
                    status,
                    details={
                        "message": message,
                        "next_check": (datetime.now(ZoneInfo("Europe/Paris")) + timedelta(minutes=check_interval_minutes)).strftime("%Y-%m-%d %H:%M:%S %Z")
                    }
                )

            # Check again after the specified interval, but with shorter intervals to detect stop signals
            logger.info(f"⏸ Checking schedule again in {check_interval_minutes} minutes...")
            
            # Sleep in smaller chunks to respond quickly to stop signals
            total_sleep_seconds = check_interval_minutes * 60
            chunk_sleep = min(30, total_sleep_seconds)  # Sleep max 30 seconds at a time
            elapsed = 0
            
            while elapsed < total_sleep_seconds and get_scheduler_state(username):
                time_module.sleep(chunk_sleep)
                elapsed += chunk_sleep
                
                # If scheduler was turned off, break early
                if not get_scheduler_state(username):
                    logger.info(f"🚫 Scheduler stop signal detected during sleep. Exiting early.")
                    break
        
        logger.info(f"🚫 Scheduler turned off for user {username}. Exiting.")
        update_scheduler_state(
            username,
            False, 
            SchedulerStatus.IDLE, 
            details={
                "message": "Scheduler turned off"
            }
        )
    except Exception as e:
        logger.error(f"Got error in main scheduler function: {e}")
        


        