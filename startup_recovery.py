"""
Application startup script that recovers scheduler state after service restart
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.scheduler_health_service import get_real_scheduler_status, recover_stale_scheduler, start_health_monitor
from database.connection import get_connection
from utils.logger import logger

def recover_schedulers_on_startup():
    """
    Check for stale schedulers on service startup and recover them
    This should be called when the service starts
    """
    try:
        logger.info("🔄 Checking for stale schedulers on startup...")
        
        # Get all users who should have active schedulers
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM scheduler_state WHERE is_active = 1")
        active_users = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        recovered_count = 0
        
        for username in active_users:
            status = get_real_scheduler_status(username)
            
            if status['needs_recovery']:
                logger.warning(f"Found stale scheduler for {username}, recovering...")
                if recover_stale_scheduler(username):
                    logger.info(f"✅ Successfully recovered scheduler for {username}")
                    recovered_count += 1
                else:
                    logger.error(f"❌ Failed to recover scheduler for {username}")
            else:
                logger.info(f"✅ Scheduler for {username} is healthy")
        
        if recovered_count > 0:
            logger.info(f"🎯 Recovered {recovered_count} stale schedulers on startup")
        else:
            logger.info("✅ No stale schedulers found on startup")
            
    except Exception as e:
        logger.error(f"Error during scheduler recovery on startup: {e}")

def initialize_service():
    """
    Initialize the service with proper scheduler recovery
    """
    logger.info("🚀 Initializing TaoWAR service...")
    
    # Start health monitor
    start_health_monitor()
    
    # Recover any stale schedulers
    recover_schedulers_on_startup()
    
    logger.info("✅ Service initialization complete")

if __name__ == "__main__":
    initialize_service()
