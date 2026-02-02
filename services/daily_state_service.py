from database.connection import get_connection
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from utils.logger import logger

def get_current_date_cet():
    """Get current date in CET/Paris timezone"""
    return datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d")

def save_daily_state(username, daily_state):
    """
    Save daily state to database
    
    Args:
        username (str): Username
        daily_state (dict): Daily state dictionary with keys:
            - date
            - categorization_and_summarization
            - posting_done
            - weekly_done
            - current_position (optional)
            - weekly_img_rotator (optional)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO daily_scheduler_state 
            (username, date, categorization_and_summarization, posting_done, weekly_done, 
             current_position, weekly_img_rotator, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            daily_state.get("date", get_current_date_cet()),
            daily_state.get("categorization_and_summarization", False),
            daily_state.get("posting_done", False),
            daily_state.get("weekly_done", False),
            daily_state.get("current_position", 0),
            daily_state.get("weekly_img_rotator", 1),
            datetime.now(ZoneInfo("Europe/Paris"))
        ))
        
        conn.commit()
        logger.info(f"Saved daily state for {username}: {daily_state}")
        
    except Exception as e:
        logger.error(f"Error saving daily state for {username}: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_daily_state(username, date=None):
    """
    Get daily state from database
    
    Args:
        username (str): Username
        date (str, optional): Date in YYYY-MM-DD format. If None, uses current CET date
        
    Returns:
        dict: Daily state dictionary, or default state if not found
    """
    if date is None:
        date = get_current_date_cet()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT date, categorization_and_summarization, posting_done, weekly_done,
                   current_position, weekly_img_rotator
            FROM daily_scheduler_state 
            WHERE username = ? AND date = ?
        """, (username, date))
        
        row = cursor.fetchone()
        
        if row:
            daily_state = {
                "date": row[0],
                "categorization_and_summarization": bool(row[1]),
                "posting_done": bool(row[2]),
                "weekly_done": bool(row[3]),
                "current_position": row[4] or 0,
                "weekly_img_rotator": row[5] or 1
            }
            logger.info(f"Retrieved daily state for {username} on {date}: {daily_state}")
            return daily_state
        else:
            # Return default state if not found
            default_state = {
                "date": date,
                "categorization_and_summarization": False,
                "posting_done": False,
                "weekly_done": False,
                "current_position": 0,
                "weekly_img_rotator": 1
            }
            logger.info(f"No daily state found for {username} on {date}, returning default: {default_state}")
            return default_state
            
    except Exception as e:
        logger.error(f"Error getting daily state for {username} on {date}: {e}")
        # Return default state on error
        return {
            "date": date,
            "categorization_and_summarization": False,
            "posting_done": False,
            "weekly_done": False,
            "current_position": 0,
            "weekly_img_rotator": 1
        }
    finally:
        conn.close()

def reset_daily_state_for_new_day(username, new_date=None):
    """
    Reset daily state for a new day (sets all boolean flags to False)
    
    Args:
        username (str): Username
        new_date (str, optional): Date in YYYY-MM-DD format. If None, uses current CET date
    """
    if new_date is None:
        new_date = get_current_date_cet()
    
    # Get the previous day's state to preserve position and rotator
    previous_date = (datetime.now(ZoneInfo("Europe/Paris")) - timedelta(days=1)).strftime("%Y-%m-%d")
    previous_state = get_daily_state(username, previous_date)
    
    new_state = {
        "date": new_date,
        "categorization_and_summarization": False,
        "posting_done": False,
        "weekly_done": False,
        "current_position": previous_state.get("current_position", 0),  # Preserve position from previous day
        "weekly_img_rotator": previous_state.get("weekly_img_rotator", 1)  # Preserve rotator from previous day
    }
    
    save_daily_state(username, new_state)
    logger.info(f"Reset daily state for {username} on {new_date} (preserved position: {previous_state.get('current_position', 0)}, rotator: {previous_state.get('weekly_img_rotator', 1)})")
    return new_state

def cleanup_old_daily_states(days_to_keep=7):
    """
    Clean up old daily states (older than specified days)
    
    Args:
        days_to_keep (int): Number of days to keep (default: 7)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Calculate cutoff date
        cutoff_date = datetime.now(ZoneInfo("Europe/Paris"))
        cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        cursor.execute("""
            DELETE FROM daily_scheduler_state 
            WHERE date < ?
        """, (cutoff_str,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old daily state records (older than {cutoff_str})")
        
    except Exception as e:
        logger.error(f"Error cleaning up old daily states: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_daily_state_field(username, field_name, value, date=None):
    """
    Update a specific field in daily state
    
    Args:
        username (str): Username
        field_name (str): Field to update (e.g., 'posting_done', 'weekly_done')
        value: New value for the field
        date (str, optional): Date in YYYY-MM-DD format. If None, uses current CET date
    """
    if date is None:
        date = get_current_date_cet()
    
    # Get current state, update the field, and save back
    current_state = get_daily_state(username, date)
    current_state[field_name] = value
    save_daily_state(username, current_state)
    
    logger.info(f"Updated {field_name} = {value} for {username} on {date}")
