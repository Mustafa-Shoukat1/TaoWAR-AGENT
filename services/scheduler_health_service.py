import threading
import time
from services.scheduler_state_service import get_scheduler_state, set_scheduler_state, update_scheduler_state, SchedulerStatus
from scripts.main_scheduler import run_user_scheduler
from utils.logger import logger

# Global thread tracking (survives across Streamlit sessions)
_active_scheduler_threads = {}
_health_monitor_thread = None
_health_monitor_active = False

def is_scheduler_thread_alive(username: str) -> bool:
    """Check if scheduler thread is actually running for a user"""
    thread = _active_scheduler_threads.get(username)
    return thread is not None and thread.is_alive()

def get_real_scheduler_status(username: str) -> dict:
    """
    Get the REAL scheduler status by checking both DB state and thread health
    Returns: {
        'db_active': bool,
        'thread_alive': bool, 
        'actual_status': 'ACTIVE' | 'INACTIVE' | 'STALE',
        'needs_recovery': bool
    }
    """
    db_active = get_scheduler_state(username)
    thread_alive = is_scheduler_thread_alive(username)
    
    if db_active and thread_alive:
        actual_status = 'ACTIVE'
        needs_recovery = False
    elif db_active and not thread_alive:
        actual_status = 'STALE'  # DB says active but thread is dead
        needs_recovery = True
    else:
        actual_status = 'INACTIVE'
        needs_recovery = False
    
    return {
        'db_active': db_active,
        'thread_alive': thread_alive,
        'actual_status': actual_status,
        'needs_recovery': needs_recovery
    }

def start_scheduler_with_health_check(username: str) -> bool:
    """
    Start scheduler with proper health tracking
    Returns True if started successfully
    """
    try:
        # Check if already running
        if is_scheduler_thread_alive(username):
            logger.info(f"Scheduler for {username} is already running")
            return True
        
        # Update DB state
        set_scheduler_state(username, True)
        
        # Start new thread
        scheduler_thread = threading.Thread(
            target=run_user_scheduler, 
            args=(username,), 
            daemon=True,
            name=f"scheduler-{username}"
        )
        scheduler_thread.start()
        
        # Track the thread globally
        _active_scheduler_threads[username] = scheduler_thread
        
        logger.info(f"Started scheduler thread for {username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start scheduler for {username}: {e}")
        return False

def stop_scheduler_with_cleanup(username: str) -> bool:
    """
    Stop scheduler and clean up properly
    """
    try:
        # Update DB state
        set_scheduler_state(username, False)
        
        # The thread will stop itself when it checks get_scheduler_state()
        # Clean up our tracking
        if username in _active_scheduler_threads:
            del _active_scheduler_threads[username]
        
        logger.info(f"Stopped scheduler for {username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to stop scheduler for {username}: {e}")
        return False

def recover_stale_scheduler(username: str) -> bool:
    """
    Recover a scheduler that shows as active in DB but has no running thread
    """
    logger.warning(f"Recovering stale scheduler for {username}")
    
    # Clean up dead thread reference
    if username in _active_scheduler_threads:
        del _active_scheduler_threads[username]
    
    # Restart the scheduler
    return start_scheduler_with_health_check(username)

def health_monitor_loop():
    """
    Background thread that monitors scheduler health and auto-recovers
    """
    global _health_monitor_active
    
    while _health_monitor_active:
        try:
            # Get all users who should have active schedulers
            from database.connection import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM scheduler_state WHERE is_active = 1")
            active_users = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Check health of each scheduler
            for username in active_users:
                status = get_real_scheduler_status(username)
                
                if status['needs_recovery']:
                    logger.warning(f"Detected stale scheduler for {username}, attempting recovery...")
                    if recover_stale_scheduler(username):
                        logger.info(f"Successfully recovered scheduler for {username}")
                    else:
                        logger.error(f"Failed to recover scheduler for {username}")
            
            # Sleep for 5 minutes before next check
            time.sleep(300)
            
        except Exception as e:
            logger.error(f"Error in health monitor: {e}")
            time.sleep(60)  # Short sleep on error

def start_health_monitor():
    """Start the health monitoring service"""
    global _health_monitor_thread, _health_monitor_active
    
    if _health_monitor_active:
        return
    
    _health_monitor_active = True
    _health_monitor_thread = threading.Thread(
        target=health_monitor_loop,
        daemon=True,
        name="scheduler-health-monitor"
    )
    _health_monitor_thread.start()
    logger.info("Started scheduler health monitor")

def stop_health_monitor():
    """Stop the health monitoring service"""
    global _health_monitor_active
    _health_monitor_active = False
    logger.info("Stopped scheduler health monitor")

# Auto-start health monitor when service loads
start_health_monitor()
