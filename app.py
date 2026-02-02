# run python bootstrap.py if you are running the script for the first time
import os
import streamlit as st
import pandas as pd
from services.influencer_service import get_influencers, save_influencer, delete_influencer
from services.keyword_service import get_keywords, update_keywords, delete_keyword
from services.post_service import get_relevant_posts, get_all_posts
from services.category_service import get_all_categories, add_category, delete_category
from services.scheduler_state_service import get_scheduler_state_details, SchedulerStatus
from core.scraper import scrape_influencers
from core.responder import generate_response, post_reply
from scripts.scheduler import start_scheduling, stop_scheduling
from scripts.auth import login_page
import time
import random
import threading
from scripts.main_scheduler import run_user_scheduler
from services.scheduler_state_service import get_scheduler_state, set_scheduler_state
from services.scheduler_mutex_service import check_scheduler_locks, cleanup_stale_locks, SchedulerMutex
from utils.logger import logger
import bootstrap

# ===== MUTEX-BASED SCHEDULER MANAGEMENT =====
# Clean up stale locks on startup
cleanup_stale_locks(max_age_hours=24)

def auto_recover_schedulers():
    """
    Auto-recover schedulers that were running before app restart/crash
    This function checks all users and restarts schedulers that were active
    """
    try:
        # Import here to avoid circular imports
        from database.users import get_all_users
        
        logger.info("🔄 Checking for schedulers that need auto-recovery...")
        
        all_users = get_all_users()
        active_locks = check_scheduler_locks()
        recovery_count = 0
        
        for user in all_users:
            username = user['username']
            db_active = get_scheduler_state(username)
            lock_held = username in active_locks
            
            # If DB says active but no lock exists, this scheduler needs recovery
            if db_active and not lock_held:
                logger.info(f"🚑 Auto-recovering scheduler for {username}")
                try:
                    # Start scheduler thread with mutex protection
                    scheduler_thread = threading.Thread(
                        target=run_user_scheduler, 
                        args=(username,), 
                        daemon=True,
                        name=f"auto-recovery-{username}"
                    )
                    scheduler_thread.start()
                    recovery_count += 1
                    logger.info(f"✅ Auto-recovered scheduler for {username}")
                except Exception as e:
                    logger.error(f"❌ Failed to auto-recover scheduler for {username}: {e}")
                    # Set state to inactive if recovery fails
                    set_scheduler_state(username, False)
        
        if recovery_count > 0:
            logger.info(f"🎯 Auto-recovery completed: {recovery_count} scheduler(s) restarted")
        else:
            logger.info("✅ No schedulers needed recovery")
            
    except Exception as e:
        logger.error(f"❌ Error during auto-recovery: {e}")

# Perform auto-recovery on app startup (only once per session)
if "auto_recovery_done" not in st.session_state:
    auto_recover_schedulers()
    st.session_state.auto_recovery_done = True

def get_scheduler_status_mutex(username: str) -> dict:
    """
    Get scheduler status using mutex-based checking
    """
    try:
        db_active = get_scheduler_state(username)
        active_locks = check_scheduler_locks()
        lock_held = username in active_locks
        
        logger.info(f"Status check for {username}: DB={db_active}, Lock={lock_held}")
        
        if db_active and lock_held:
            actual_status = 'ACTIVE'
            needs_recovery = False
        elif db_active and not lock_held:
            actual_status = 'RECOVERING'  # Changed from STALE to RECOVERING
            needs_recovery = True
        else:
            actual_status = 'INACTIVE'
            needs_recovery = False
        
        result = {
            'db_active': db_active,
            'lock_held': lock_held,
            'actual_status': actual_status,
            'needs_recovery': needs_recovery,
            'lock_info': active_locks.get(username)
        }
        
        logger.info(f"Final status for {username}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error checking scheduler status: {e}")
        return {
            'db_active': False,
            'lock_held': False,
            'actual_status': 'ERROR',
            'needs_recovery': False
        }

def start_scheduler_mutex(username: str) -> bool:
    """Start scheduler using mutex-based management"""
    try:
        # Check if already running
        status = get_scheduler_status_mutex(username)
        if status['actual_status'] == 'ACTIVE':
            logger.info(f"Scheduler for {username} is already running")
            return True
        
        # Update DB state
        set_scheduler_state(username, True)
        
        # Start new thread (the mutex will be acquired inside the scheduler)
        scheduler_thread = threading.Thread(
            target=run_user_scheduler, 
            args=(username,), 
            daemon=True,
            name=f"scheduler-{username}"
        )
        scheduler_thread.start()
        
        logger.info(f"Started scheduler thread for {username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start scheduler for {username}: {e}")
        return False

def stop_scheduler_mutex(username: str) -> bool:
    """Stop scheduler using mutex-based management"""
    try:
        logger.info(f"Attempting to stop scheduler for {username}")
        
        # Update DB state (this will cause the scheduler loop to exit)
        set_scheduler_state(username, False)
        logger.info(f"Set DB state to False for {username}")
        
        # Give the scheduler a moment to detect the state change and exit gracefully
        import time
        time.sleep(2)
        
        # Check if lock is still held after graceful shutdown attempt
        from services.scheduler_mutex_service import SchedulerMutex
        mutex = SchedulerMutex(username)
        
        if mutex.is_lock_held_by_other():
            logger.warning(f"⚠️ Lock still held after stop signal. This may indicate a stale lock.")
            
            # Force cleanup of potentially stale lock (careful approach)
            try:
                cleanup_stale_locks(max_age_hours=0.001)  # Very short age to clean recent locks
                logger.info(f"🧹 Attempted cleanup of stale locks")
            except Exception as e:
                logger.error(f"❌ Error during stale lock cleanup: {e}")
        
        # The scheduler will release its own mutex when it exits
        logger.info(f"Stopped scheduler for {username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to stop scheduler for {username}: {e}")
        return False

# In-memory thread tracking (not persistent, only for active session)
if "summary_scheduler_thread" not in st.session_state:
    st.session_state.summary_scheduler_thread = None


# Streamlit App Title
st.set_page_config(page_title="TaoWar-X Bot", layout="wide")

# Set auto-refresh interval for the dashboard page
AUTO_REFRESH_INTERVAL = 10  # seconds

# Authentication Check
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_page()
    st.stop()  # This stops execution if not authenticated

# Session storage for scraped tweets
if "current_relevant" not in st.session_state:
    st.session_state.current_relevant = []
if "current_non_relevant" not in st.session_state:
    st.session_state.current_non_relevant = []
if "scheduling_on" not in st.session_state:
    st.session_state.scheduling_on = False
if "tone_selection" not in st.session_state:
    st.session_state.tone_selection = {}

TWEETS_TO_SCRAPE = 10

# Sidebar Navigation
st.sidebar.image(os.path.join("assets", "logo.png"), width=200)
# Show username if available in session state
if "username" in st.session_state:
    st.sidebar.write(f"👤 Logged in as: **{st.session_state.username}**")
menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Config", "Trigger Scraping", "Data Visualization"]
)

#################
### DASHBOARD ###
#################
if menu == "Dashboard":
    st.markdown("<h1 style='text-align: left;'>Dashboard</h1>", unsafe_allow_html=True)
    st.empty()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Influencers")
        try:
            influencers = get_influencers()
            st.markdown(f"**Total Influencers: {len(influencers)}**")

            with st.expander("🔽 View Influencers", expanded=False):
                if influencers:
                    # Create a container with fixed height and scrollable content
                    influencer_container = st.container()
                    with influencer_container:
                        # Apply CSS to make the container scrollable
                        st.markdown("""
                        <style>
                            div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
                                max-height: 300px;
                                overflow-y: auto;
                            }
                        </style>
                        """, unsafe_allow_html=True)
                        # List all influencers
                        for inf in influencers:
                            st.markdown(f"🔹 **{inf['username']}**")
                else:
                    st.write(" No influencers found.")
        except Exception as e:
            st.error(f"Error loading influencers: {e}")

    with col2:
        st.subheader("Keywords")
        try:
            keywords = get_keywords()
            st.markdown(f"**Total Keywords: {len(keywords)}**")

            with st.expander("🔽 View Keywords", expanded=False):
                if keywords:
                    # Create a container with fixed height and scrollable content
                    keyword_container = st.container()
                    with keyword_container:
                        # CSS is shared across all expanders
                        for kw in keywords:
                            st.markdown(f" **{kw}**")
                else:
                    st.write(" No keywords found.")
        except Exception as e:
            st.error(f"Error loading keywords: {e}")

    with col3:
        st.subheader("Categories")
        try:
            categories = get_all_categories()
            st.markdown(f"**Total Categories: {len(categories)}**")

            with st.expander("🔽 View Categories", expanded=False):
                if categories:
                    # Create a container with fixed height and scrollable content
                    categories_container = st.container()
                    with categories_container:
                        # CSS is shared across all expanders
                        for cat in categories:
                            st.markdown(f" **{cat['name']}**: _{cat['description']}_")
                else:
                    st.write(" No categories found.")
        except Exception as e:
            st.error(f"Error loading categories: {e}")
        
    # Add Scheduler Progress Tracking Section
    st.markdown("---")
    st.subheader("Scheduler Progress Tracking")
    # Add this code to your Dashboard section, after the scheduler status section
    # ---------------------------------------------------------------------

    # Add this code to your Dashboard section
    # ---------------------------------------------------------------------

    # Simple, transparent refresh button (left-aligned)
    st.markdown("""
        <style>
        /* Target the wrapper div for Streamlit buttons */
        div[data-testid="stButton"] > button[data-testid="baseButton-refresh_dashboard"] {
            background-color: transparent;
            color: #2e6fdf;
            border: 1px solid #2e6fdf;
            border-radius: 4px;
            padding: 5px 15px; /* Increased horizontal padding */
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            outline: none;
            margin-bottom: 15px;
            width: auto; /* Changed from fixed width to auto */
            min-width: 120px; /* Added minimum width */
            white-space: nowrap; /* Prevents text wrapping */
        }
        div[data-testid="stButton"] > button[data-testid="baseButton-refresh_dashboard"]:hover {
            background-color: rgba(46, 111, 223, 0.1);
        }
        div[data-testid="stButton"] > button[data-testid="baseButton-refresh_dashboard"]:active {
            background-color: #2e6fdf;
            color: white;
        }
        </style>
""", unsafe_allow_html=True)

    left_col, _, _ = st.columns([1, 3, 3])
    with left_col:
        if st.button("Refresh", key="refresh_dashboard"):
            st.rerun()

    username = st.session_state.get("username", "system")

    
    # Get scheduler state details
    try:
        scheduler_state = get_scheduler_state_details(username)
        
        # Display current status
        status = scheduler_state.get('status', SchedulerStatus.IDLE)
        status_emoji = {
            SchedulerStatus.IDLE: "⏸",
            SchedulerStatus.FETCHING_TWEETS: "",
            SchedulerStatus.CATEGORIZING_TWEETS: "",
            SchedulerStatus.GENERATING_SUMMARIES: "",
            SchedulerStatus.POSTING_SUMMARIES: "",
            SchedulerStatus.BATCH_COMPLETED: "",
            SchedulerStatus.DAY_COMPLETED: "",
            "error": ""
        }.get(status, "")
        
        # Create a colored status indicator
        status_color = {
            SchedulerStatus.IDLE: "blue",
            SchedulerStatus.FETCHING_TWEETS: "orange",
            SchedulerStatus.CATEGORIZING_TWEETS: "orange",
            SchedulerStatus.GENERATING_SUMMARIES: "orange",
            SchedulerStatus.POSTING_SUMMARIES: "orange",
            SchedulerStatus.BATCH_COMPLETED: "green",
            SchedulerStatus.DAY_COMPLETED: "green",
            "error": "red"
        }.get(status, "gray")
        
        # Show status with emoji and color
        st.markdown(f"<h4 style='color: {status_color};'>{status_emoji} Current Status: {status}</h4>", unsafe_allow_html=True)
        
        # Show batch number if available
        batch = scheduler_state.get('batch')
        if batch:
            st.markdown(f"**🔄 Current Batch:** {batch}")
        
        # Show current influencer if available
        current_influencer = scheduler_state.get('current_influencer')
        if current_influencer:
            st.markdown(f"**👤 Processing Influencer:** {current_influencer}")
        
        # Show progress bar if progress is available
        progress = scheduler_state.get('progress', 0)
        if progress is not None:
            if progress > 0:
                st.progress(progress)
                st.text(f"Progress: {int(progress * 100)}%")
        
        # Show additional details
        details = scheduler_state.get('details', {})
        if details:
            with st.expander("View Additional Details", expanded=False):
                if isinstance(details, dict):
                    for key, value in details.items():
                        st.markdown(f"**{key}:** {value}")
                else:
                    st.markdown(f"**Details:** {details}")
        
        # Show recent history
        history = scheduler_state.get('history', [])
        if history:
            with st.expander("View Recent History", expanded=False):
                for entry in history:
                    timestamp = entry.get('timestamp', '')
                    entry_status = entry.get('status', '')
                    entry_batch = entry.get('batch', '')
                    
                    st.markdown(f"**{timestamp}**: {entry_status} (Batch: {entry_batch})")
        
        # Add timestamp of last update
        last_updated = scheduler_state.get('last_updated')
        if last_updated:
            st.caption(f"Last updated: {last_updated}")
    
    except Exception as e:
        st.error(f"Error loading scheduler state: {e}")

    st.markdown("Main Summary Scheduler")

    # Get the current user from session state
    username = st.session_state.get("username", "guest")
    
    # Debug print (can be removed later)
    logger.info(f"Current logged-in user: {username}")
    print(f"Current logged-in user: {username}")
    
    # Get REAL scheduler status using mutex-based checking
    scheduler_status = get_scheduler_status_mutex(username)
    
    # Add a refresh button specifically for scheduler status
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Status", key="refresh_scheduler_status"):
            # Force cleanup and refresh
            cleanup_stale_locks()
            st.rerun()
    
    # Create a container for the scheduler status
    status_container = st.container()
    
    # Show the current status with health information
    with status_container:
        if scheduler_status['actual_status'] == 'ACTIVE':
            st.success(f"✅ **Scheduler Status: ACTIVE** (Thread Running)")
        elif scheduler_status['actual_status'] == 'RECOVERING':
            st.warning(f"🔄 **Scheduler Status: RECOVERING** (Auto-recovery in progress)")
            st.info("💡 The scheduler was active before restart and is being automatically recovered")
        elif scheduler_status['actual_status'] == 'STALE':
            st.error(f"⚠️ **Scheduler Status: STALE** (DB Active but No Lock)")
            if st.button("🔄 Manually Recover Scheduler"):
                if start_scheduler_mutex(username):
                    st.success("✅ Scheduler recovered successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to recover scheduler")
        elif scheduler_status['actual_status'] == 'ERROR':
            st.error(f"❌ **Scheduler Status: ERROR** (Check logs)")
        else:
            st.info(f"⏹️ **Scheduler Status: INACTIVE**")
        
        # Show detailed status for debugging
        with st.expander("🔍 Detailed Status", expanded=False):
            st.write(f"**DB State:** {'Active' if scheduler_status['db_active'] else 'Inactive'}")
            st.write(f"**Lock Held:** {'Yes' if scheduler_status['lock_held'] else 'No'}")
            st.write(f"**Needs Recovery:** {'Yes' if scheduler_status['needs_recovery'] else 'No'}")
            
            # Show lock info if available
            lock_info = scheduler_status.get('lock_info')
            if lock_info:
                st.write("**Lock Information:**")
                for key, value in lock_info.items():
                    st.write(f"  - **{key}:** {value}")
            
            # Show all active locks
            active_locks = check_scheduler_locks()
            if active_locks:
                st.write("**All Active Scheduler Locks:**")
                for user, info in active_locks.items():
                    if info:
                        st.write(f"  - **{user}:** PID {info.get('PID', 'Unknown')}, Started: {info.get('Started', 'Unknown')}")
                    else:
                        st.write(f"  - **{user}:** Lock exists but no info available")
                        
                if len(active_locks) > 1:
                    if st.button("🧹 Clean Up Other Users' Locks", key="cleanup_other_locks"):
                        cleaned = 0
                        for user in list(active_locks.keys()):
                            if user != username:  # Don't touch current user's lock
                                # Stop the other user's scheduler in DB
                                set_scheduler_state(user, False)
                                cleaned += 1
                                logger.info(f"Cleaned up scheduler for other user: {user}")
                        
                        if cleaned > 0:
                            st.success(f"🧹 Cleaned up {cleaned} other users' schedulers")
                            st.rerun()
                        else:
                            st.info("No other users' schedulers to clean up")
            else:
                st.write("**No active scheduler locks found**")
            
            # Show database state directly
            db_state = get_scheduler_state(username)  # Use actual username
            st.write(f"**Raw DB State:** {db_state}")
    
    # Show correct button based on REAL status (not just DB state)
    if scheduler_status['actual_status'] in ['ACTIVE', 'RECOVERING']:
        if st.button("🛑 Stop Main Summary Scheduler"):
            logger.info(f"Stopping Main Summary Scheduler..{username}")
            if stop_scheduler_mutex(username):
                st.success("✅ Main Summary Scheduler turned OFF.")
                # Force immediate refresh to show updated status
                time.sleep(0.5)  # Give time for cleanup
                st.rerun()
            else:
                st.error("❌ Failed to stop scheduler")
    else:
        if st.button("▶️ Start Main Summary Scheduler"):
            logger.info(f"Starting Main Summary Scheduler..{username}")
            if start_scheduler_mutex(username):
                st.success("✅ Main Summary Scheduler turned ON.")
                # Force immediate refresh to show updated status
                time.sleep(0.5)  # Give time for startup
                st.rerun()
            else:
                st.error("❌ Failed to start scheduler")
    
    # Add periodic health check with manual trigger
    if st.button("🔄 Force Health Check", key="force_health_check"):
        cleanup_stale_locks()  # Clean up stale locks
        st.success("🏥 Health check completed!")
        st.rerun()
    
    # Auto health check every few page loads (simulates periodic monitoring)
    if 'health_check_counter' not in st.session_state:
        st.session_state.health_check_counter = 0
    
    st.session_state.health_check_counter += 1
    
    # Run health check every 10 page loads (approximately every few minutes in active use)
    if st.session_state.health_check_counter % 10 == 0:
        cleanup_stale_locks()  # Clean up stale locks
        logger.info("🔄 Automatic health check completed")

#################
### CONFIG ###
#################
elif menu == "Config":
    st.markdown("<h1 style='text-align: left;'>Configuration</h1>", unsafe_allow_html=True)

    # Add CSS for scrollable expanders
    st.markdown("""
    <style>
        div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Manage Influencers")
        try:
            influencers = get_influencers()
            influencer_names = [inf['username'] for inf in influencers]  # Extract usernames
            
            with st.expander("Current Influencers", expanded=False):
                if influencers:
                    # Container will be scrollable due to the CSS above
                    for inf in influencers:
                        c1, c2 = st.columns([5, 1])
                        with c1:
                            st.markdown(f"{inf['username']}")
                        with c2:
                            if st.button("🗑", key=f"delete_{inf['username']}"):
                                delete_influencer(inf['username'])
                                st.success(f"{inf['username']} deleted!")
                else:
                    st.write("⚠ No influencers added.")
        except Exception as e:
            st.error(f"Error managing influencers: {e}")

        new_influencer = st.text_input("Add New Influencer (Username)").strip()  # Strip spaces

        if st.button("Add Influencer"):
            if new_influencer:
                if new_influencer in influencer_names:  # Check if already exists
                    st.warning(f"⚠ Influencer '{new_influencer}' already exists.")
                else:
                    try:
                        save_influencer(new_influencer)
                        st.success(f"Added {new_influencer}!")
                    except Exception as e:
                        st.error(f"Error adding influencer: {e}")
            else:
                st.warning("⚠ Please enter a valid username.")

    with col2:
        st.subheader("Manage Keywords")
        try:
            keywords = get_keywords()
            with st.expander("Active Keywords", expanded=False):
                if keywords:
                    # Container will be scrollable due to the CSS above
                    for kw in keywords:
                        c1, c2 = st.columns([5, 1])
                        with c1:
                            st.markdown(f"**{kw}**")
                        with c2:
                            if st.button("🗑️", key=f"delete_{kw}"):
                                delete_keyword(kw)
                                st.success(f"{kw} deleted!")
                else:
                    st.write("No keywords found.")
        except Exception as e:
            st.error(f"Error managing keywords: {e}")

        new_keyword = st.text_input("Add New Keyword")
        if st.button("Add Keyword"):
            if new_keyword:
                try:
                    keywords.append(new_keyword)
                    update_keywords(keywords)
                    st.success(f"Added {new_keyword}!")
                except Exception as e:
                    st.error(f"Error adding keyword: {e}")
            else:
                st.warning("Please enter a valid keyword.")

    with col3:
        st.subheader("Manage Categories")
        try:
            categories = get_all_categories()
            with st.expander("Active Categories", expanded=False):
                if categories:
                    # Container will be scrollable due to the CSS above
                    for cat in categories:
                        c1, c2 = st.columns([5, 1])
                        with c1:
                            st.markdown(f"**{cat['name']}**: _{cat['description']}_")
                        with c2:
                            if st.button("🗑️", key=f"delete_cat_{cat['name']}"):
                                print({cat['name']})
                                delete_category(cat['name'])
                                st.success(f" Category '{cat['name']}' deleted!")
                else:
                    st.write(" No categories found.")
        except Exception as e:
            st.error(f"Error managing categories: {e}")

        new_category_name = st.text_input("Add New Category Name").strip()
        new_category_desc = st.text_input("Category Description").strip()

        if st.button("Add Category"):
            if new_category_name and new_category_desc:
                try:
                    add_category(new_category_name, new_category_desc)
                    print(f'New CAt = { new_category_name}')
                    st.success(f"Added category '{new_category_name}'!")
                except Exception as e:
                    st.error(f"Error adding category: {e}")
            else:
                st.warning("Please enter both name and description.")
                
########################
### TRIGGER SCRAPING ###
########################
elif menu == "Trigger Scraping":
    st.markdown("<h1 style='text-align: left;'>Trigger Scraping</h1>", unsafe_allow_html=True)

    try:
        influencers = get_influencers()
    except Exception as e:
        st.error(f"Error fetching influencers: {e}")
        influencers = []

    if not influencers:
        st.warning("⚠️ No influencers found. Please add influencers first.")
    else:
        selected_influencers = st.multiselect("Choose influencers:", [inf["username"] for inf in influencers])

        if st.button("Start Scraping"):
            if not selected_influencers:
                st.warning("⚠️ Please select at least one influencer.")
            else:
                st.session_state.current_relevant.clear()
                st.session_state.current_non_relevant.clear()
                delay_seconds = random.randint(70, 90)  # Random delay between 70-90 sec
                st.markdown(f"⏳ Please wait for **{delay_seconds} seconds** before scraping initializes...")
                
                # Progress bar for countdown
                progress_bar = st.progress(0)
                for i in range(delay_seconds):
                    time.sleep(1)
                    progress_bar.progress((i + 1) / delay_seconds)
                
                st.success("✅ Ready for the Scraping!")
                for index, influencer in enumerate(selected_influencers):
                    relevant, non_relevant = scrape_influencers(influencer, TWEETS_TO_SCRAPE)
                    st.session_state.current_relevant.extend(relevant)
                    st.session_state.current_non_relevant.extend(non_relevant)

                    # Delay between scrapes
                    if index < len(selected_influencers) - 1:  # Skip delay after last influencer
                        delay_seconds = random.randint(70, 90)  # Random delay between 70-90 sec
                        st.markdown(f"⏳ Waiting for **{delay_seconds} seconds** before scraping the next influencer...")
                        
                        # Progress bar for countdown
                        progress_bar = st.progress(0)
                        for i in range(delay_seconds):
                            time.sleep(1)
                            progress_bar.progress((i + 1) / delay_seconds)
                        
                        st.success("✅ Ready for the next influencer!")
                    
                    elif index == len(selected_influencers) - 1:
                        delay_seconds = random.randint(70, 90)  # Random delay between 70-90 sec
                        st.markdown(f"⏳ Please wait for **{delay_seconds} seconds** before you start replying to the relevant posts...")
                        
                        # Progress bar for countdown
                        progress_bar = st.progress(0)
                        for i in range(delay_seconds):
                            time.sleep(1)
                            progress_bar.progress((i + 1) / delay_seconds)
                        
                        st.success("✅ Ready for you to do replies!")
                        

    st.markdown("### Scraping Results")

    #######################
    ### Relevant Tweets ###
    #######################
    with st.expander("✅ Relevant Tweets", expanded=True):
        if st.session_state.current_relevant:
            df_rel = pd.DataFrame(st.session_state.current_relevant)
            tweet_id_col = "tweet_id" if "tweet_id" in df_rel.columns else "id"

            # Display tweets in a table format
            st.dataframe(df_rel[["username", "text", "link"]])

            # Loop through each tweet to add individual controls
            for _, row in df_rel.iterrows():
                tweet_id = row[tweet_id_col]
                
                with st.container():
                    col1, col2 = st.columns([3, 2])  # Adjust width proportions for alignment

                    # Tone selection dropdown
                    with col1:
                        selected_tone = st.selectbox(
                            f"Select Reply Tone for {row['username']}",
                            ["Auto-Detect", "Tactical & Strategic", "Sharp & Witty", "Commanding & Engaging"],
                            key=f"tone_{tweet_id}",
                            index=0  # Default to Auto-Detect
                        )
                        st.session_state.tone_selection[tweet_id] = selected_tone

                    # Reply button (aligned with the dropdown)
                    with col2:
                        if st.button(f"Reply to {row['username']}", key=f"reply_{tweet_id}"):
                            with st.spinner("Generating reply..."):
                                reply_tone = st.session_state.tone_selection[tweet_id]
                                reply_tone = None if reply_tone == "Auto-Detect" else reply_tone
                                reply_text = generate_response(row["text"], reply_tone)
                                post_reply(tweet_id, reply_text)
                                st.success(f"✅ Replied to {row['username']}: {reply_text}")
                                delay_seconds = random.randint(70, 90)  # Random delay between 70-90 sec
                                st.markdown(f"⏳ Please wait for **{delay_seconds} seconds** before next reply.")
                                
                                # Progress bar for countdown
                                progress_bar = st.progress(0)
                                for i in range(delay_seconds):
                                    time.sleep(1)
                                    progress_bar.progress((i + 1) / delay_seconds) 
                                
                                

        else:
            st.write("⚠️ No relevant tweets found.")

    ###########################
    ### Non-Relevant Tweets ###
    ###########################
    with st.expander("🗑️ Non-Relevant Tweets", expanded=False):
        if st.session_state.current_non_relevant:
            df_garb = pd.DataFrame(st.session_state.current_non_relevant)
            st.dataframe(df_garb)
        else:
            st.write("⚠️ No non-relevant tweets found.")


###########################
### DATA VISUALIZATION ###
###########################
elif menu == "Data Visualization":
    st.markdown("<h1 style='text-align: left;'>Data Visualization</h1>", unsafe_allow_html=True)
    st.markdown("### See your data from the Database...")
    col1, col2 = st.columns(2)

    # Button to see all data
    with col1:
        if st.button("See Irrelevant Posts"):
            st.dataframe(pd.DataFrame(get_all_posts()))
            
    with col2:
        if st.button("See Relevant Posts"):
            st.dataframe(pd.DataFrame(get_relevant_posts()))