import threading
import random
import time
import datetime
import traceback
from zoneinfo import ZoneInfo

from core import scraper
from core.responder import generate_response, post_reply
from services.keyword_service import get_keywords
from services.post_service import save_relevant_posts, save_garbage_posts, get_all_saved_tweet_ids
from services.influencer_service import get_influencers
from services.scheduler_service import get_scheduling_state, update_scheduling_state
from database.api_usage import log_api_call, get_api_usage_count
from config import (
    MAX_INFLUENCERS,
    TWEETS_PER_SCRAPE,
    DAILY_SCRAPES_PER_INFLUENCER,
    SKIP_SCRAPE_PERCENTAGE,
    API_LIMIT,
    BATCH_SWITCH_INTERVAL_DAYS
)


# Global state
_scheduling_active = False
_scheduling_thread = None
_current_influencer_batch = 0  # Track current batch index
x = 0
y = 0

def _schedule_loop_runner():
    """
    Wraps _schedule_loop() so it restarts if there's a fatal error,
    up to max_retries times.
    """
    max_retries = 5
    attempt = 0

    while attempt < max_retries:
        try:
            _schedule_loop()
            break  # If successful, exit retry loop
        except Exception as e:
            attempt += 1
            print(f"❌ Fatal error in scheduling. Restarting attempt {attempt}/{max_retries}.")
            traceback.print_exc()
            time.sleep(60)

    print("🚨 Maximum retry attempts reached. Manual restart required.")

def start_scheduling():
    """
    Starts a background thread for scheduled scraping, if not already running.
    """
    global _scheduling_active, _scheduling_thread
    if _scheduling_active:
        print("⚠️ Scheduler is already running.")
        return

    _scheduling_active = True
    _scheduling_thread = threading.Thread(target=_schedule_loop_runner, daemon=True)
    _scheduling_thread.start()
    print("✅ Scheduling started...")

def stop_scheduling():
    """
    Stops the scheduling thread by setting the global flag to False.
    """
    global _scheduling_active
    if not _scheduling_active:
        print("⚠️ Scheduler is not running.")
        return
    _scheduling_active = False
    print("🛑 Scheduling stopped.")


def _schedule_loop():
    """
    Main scraping loop with:
      - Uniformly assigned morning scrapes (6–12)
      - Uniformly assigned evening scrapes (18–24)
      - 10% skip chance for each influencer for either morning or evening
      - Skips entire morning/evening window if we're already past it
      - No "rollover" to the next day for missed windows—just skip them
      - Waits until next day after each full cycle
    """
        # 1) Load scheduling state from DB
    db_batch_no, db_last_switch_str = get_scheduling_state()
    try:
        last_batch_switch = datetime.datetime.fromisoformat(db_last_switch_str)
    except Exception:
        # fallback if parse fails
        last_batch_switch = datetime.datetime.now(ZoneInfo("Europe/Paris"))

    _current_influencer_batch = db_batch_no
    print(f"🔄 Loaded scheduling state from DB: batch={_current_influencer_batch}, last_switch={last_batch_switch}")


    while _scheduling_active:
        try:
            now = datetime.datetime.now(ZoneInfo("Europe/Paris"))

            influencers = get_influencers()

            if not influencers:
                print("⚠️ No influencers found. Waiting for influencers to be added...")
                time.sleep(60)
                continue

            total_influencers = len(influencers)
            print(f"🔄 Starting daily scraping cycle for {total_influencers} influencers at {now}")

            # If fewer than MAX_INFLUENCERS, use total_influencers as batch_size
            batch_size = min(MAX_INFLUENCERS, total_influencers)

            # Switch influencer batch every BATCH_SWITCH_INTERVAL_DAYS (default 30 days)
            if (now - last_batch_switch).days >= BATCH_SWITCH_INTERVAL_DAYS:
                _current_influencer_batch += 1
                last_batch_switch = now
                print(f"🔄 Switching to new influencer batch: {_current_influencer_batch}")
                # Persist change to DB
                update_scheduling_state(_current_influencer_batch, last_batch_switch)


            # Determine which influencers go in this batch
            start_index = _current_influencer_batch * batch_size
            end_index = start_index + batch_size
            batch_influencers = influencers[start_index:end_index]

            print(f"🔄 Scraping influencers {start_index} to {end_index}")
            print(f"🔄 Total influencers: {total_influencers}")
            print(f"🔄 Batch size: {batch_influencers}")

            # If the current batch is empty, reset to first batch
            if not batch_influencers:
                print(f"⚠️ No influencers available in batch {_current_influencer_batch}. "
                      "Resetting to first batch.")
                _current_influencer_batch = 0
                update_scheduling_state(_current_influencer_batch, last_batch_switch)
                continue

            # Separate influencers for morning & evening
            # Apply skip logic (10% chance to skip morning or evening)
            morning_influencers = []
            evening_influencers = []

            for influencer in batch_influencers:
                username = influencer.get("username")
                if not username:
                    print("⚠️ Skipping invalid influencer entry:", influencer)
                    continue
                SKIP_SCRAPE_PERCENTAGE = 0 #testing
                # Randomly skip morning or evening 10% of the time
                # This ensures we skip exactly one of them, not both
                # You can decide if it's possible to skip both, but the original code
                # random.choice(["morning", "evening"]) picks only one to skip.
                if random.randint(1, 100) <= SKIP_SCRAPE_PERCENTAGE:
                    if random.choice(["morning", "evening"]) == "morning":
                        # skip morning
                        evening_influencers.append(username)
                    else:
                        # skip evening
                        morning_influencers.append(username)
                else:
                    # skip neither
                    morning_influencers.append(username)
                    evening_influencers.append(username)

            # Assign uniform random times in the morning window (6–12)
            random.shuffle(morning_influencers)
            random.shuffle(evening_influencers)
            #Testing
            # morning_schedule = _assign_uniform_times(morning_influencers, 13, 14)
            # # Assign uniform random times in the evening window (18–24)
            # evening_schedule = _assign_uniform_times(evening_influencers, 14, 15)
            
            morning_schedule = _assign_uniform_times(morning_influencers, 4, 12)
            # Assign uniform random times in the evening window (18–24)
            evening_schedule = _assign_uniform_times(evening_influencers, 16, 24)

            print(f"\n\n🔄 Morning schedule: {morning_schedule}")
            print(f"\n\n🔄 Evening schedule: {evening_schedule}\n\n")

            # Process morning scrapes
            print("🌅 Processing all morning scrapes...")

            for username, target_time in morning_schedule:
                now = datetime.datetime.now(ZoneInfo("Europe/Paris"))
                # If the random assigned time is in the past, skip
                if target_time < now:
                    print(f"⏭️ Skipping {username}'s morning scrape at {target_time}, as it's in the past.")
                    continue

                if _sleep_until(target_time):
                    print(f'\nsleep finished, scraping\n')
                    _do_daily_scrape(username, "Morning")
                    # Short delay after each scrape to avoid burst requests
                    time.sleep(random.randint(30, 60))
                    

            # Process evening scrapes
            print("🌆 Processing all evening scrapes...")
            for username, target_time in evening_schedule:
                now = datetime.datetime.now(ZoneInfo("Europe/Paris"))
                # If the random assigned time is in the past, skip
                if target_time < now:
                    print(f"⏭️ Skipping {username}'s evening scrape at {target_time}, as it's in the past.")
                    continue

                if _sleep_until(target_time):
                    _do_daily_scrape(username, "Evening")
                    # Short delay after each scrape
                    time.sleep(random.randint(30, 60))

            print("🔄 Daily scraping cycle completed. Waiting for the next day...")
            
            # Persist current state in DB, so we don't lose batch progress on crash
            update_scheduling_state(_current_influencer_batch, last_batch_switch)
            
            # Wait until next midnight
            _sleep_until(
                datetime.datetime.now(ZoneInfo("Europe/Paris")).replace(hour=0, minute=0, second=0, microsecond=0)
                + datetime.timedelta(days=1)
            )

        except Exception as e:
            print(f"❌ Fatal error in scheduling loop: {e}")
            traceback.print_exc()


def _assign_uniform_times(influencers_list, start_hour, end_hour):
    """
    Distributes 'len(influencers_list)' uniformly over the time window [start_hour, end_hour).
    Returns a list of (username, assigned_datetime).

    If the *entire* window is already in the past for the current day (e.g., now.hour >= end_hour),
    we simply skip by returning an empty list—no rollover to the next day.
    """
    results = []
    now = datetime.datetime.now(ZoneInfo("Europe/Paris"))

    # If the entire window is already in the past, skip
    if now.hour >= end_hour:
        print(f"⏭️ Entire window {start_hour}–{end_hour} is in the past for today. Skipping these scrapes.")
        return results

    total_influencers = len(influencers_list)
    if total_influencers == 0:
        return results

    # Calculate total minutes in the window
    total_minutes = (end_hour - start_hour) * 60
    # Each influencer gets a sub-interval of length chunk_size
    chunk_size = total_minutes // total_influencers  if total_influencers else 1

    for i, username in enumerate(influencers_list):
        # Start & end (in "minutes from start_hour")
        chunk_start = i * chunk_size
        # Last chunk can be bigger if not evenly divisible
        # but for simplicity we assume each chunk is chunk_size
        chunk_end = chunk_start + chunk_size
        # If chunk_end goes beyond total_minutes, clamp it
        if chunk_end > total_minutes:
            chunk_end = total_minutes

        # Pick a random minute within [chunk_start, chunk_end)
        if chunk_end > chunk_start:
            chosen_offset = random.randint(chunk_start, chunk_end - 1)
        else:
            chosen_offset = chunk_start

        # Convert to absolute hour/minute within [start_hour, end_hour)
        # chunk_start + chosen_offset is minutes from start_hour
        absolute_minutes = start_hour * 60 + chosen_offset
        assigned_hour = absolute_minutes // 60
        assigned_minute = absolute_minutes % 60
        assigned_second = random.randint(0, 59)

        assigned_time = now.replace(
            hour=assigned_hour,
            minute=assigned_minute,
            second=assigned_second,
            microsecond=0
        )
        results.append((username, assigned_time))

    return results


def _sleep_until(target_time):
    """
    Sleeps incrementally until target_time, returning True when reached,
    or False if _scheduling_active is turned off.

    Adds a random delay (5–15 min) to the assigned 'target_time'
    so the scheduler doesn't appear too robotic.
    """
    try:
        print(f'\nsleep till : {target_time}\n')
        if not target_time:
            return False

        # Random delay: 5-15 minutes
        # delay = random.randint(300, 900)
        # target_time += datetime.timedelta(seconds=delay)

        while _scheduling_active:
            now = datetime.datetime.now(ZoneInfo("Europe/Paris"))
            if now >= target_time:
                return True
            # Sleep in smaller chunks to respond quickly to stop_scheduling()
            time.sleep(min(60, max(1, (target_time - now).total_seconds())))

        return False

    except Exception as e:
        print(f"⚠️ Error in sleep function: {e}")
        return False


def _do_daily_scrape(username, label):
    """
    Scrape tweets for a given user, automatically reply to relevant tweets,
    with limited retries if rate-limited.
    """
    max_retries = 3
    attempt = 0
    while attempt < max_retries:
        try:
            print(f"💡 {label} scrape started for {username} at {datetime.datetime.now(ZoneInfo('Europe/Paris'))}")

            # If near monthly API limit, reduce scraping intensity
            if _approaching_api_limit():
                global DAILY_SCRAPES_PER_INFLUENCER, TWEETS_PER_SCRAPE
                DAILY_SCRAPES_PER_INFLUENCER = max(1, DAILY_SCRAPES_PER_INFLUENCER - 1)
                TWEETS_PER_SCRAPE = max(5, TWEETS_PER_SCRAPE - 2)

            # Perform the scraping
            relevant_tweets, _ = scraper.scrape_influencers(username, TWEETS_PER_SCRAPE)
            log_api_call(TWEETS_PER_SCRAPE)

            if relevant_tweets:
                print(f"✅ {len(relevant_tweets)} relevant tweet(s) found for {username}. Auto-replying...")
                for tweet in relevant_tweets:
                    reply_text = generate_response(tweet['text'], tone=None)
                    post_reply(tweet['id'], reply_text)
                    print(f"✅ Replied to {username}'s tweet: {reply_text}")

            print(f"💡 {label} scrape ended for {username} at {datetime.datetime.now(ZoneInfo('Europe/Paris'))}")
            # if label == 'morning': #testing
            #     global x
            #     x +=1 
            #     z = x
            # else:
            #     global y
            #     y += 1
            #     z = y
            # print(f'Count {label} {z}')
            break  # success -> stop retrying

        except scraper.TwitterRateLimitError:
            attempt += 1
            wait_time = 60 * attempt  # e.g. 60s -> 120s -> 180s
            print(f"⚠️ Rate limit error for {username}, attempt {attempt}/{max_retries}. Waiting {wait_time}s...")
            time.sleep(wait_time)

        except Exception as e:
            # Other exceptions: log and stop retrying
            print(f"⚠️ Error during {label} scrape for {username}: {e}")
            traceback.print_exc()
            break


def _approaching_api_limit():
    """
    Checks if API usage is at or above 90% of the monthly limit (8,000 by default).
    If so, the script reduces future scraping intensity in _do_daily_scrape().
    """
    try:
        api_usage = get_api_usage_count()
        return api_usage >= API_LIMIT * 0.9
    except Exception as e:
        print(f"⚠️ Error checking API limit: {e}")
        return False
