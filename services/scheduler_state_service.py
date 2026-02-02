from database.connection import get_connection
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import sqlite3

CET = ZoneInfo("Europe/Paris")

def set_scheduler_state(username: str, is_active: bool):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO scheduler_state (username, is_active, last_updated)
            VALUES (?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                is_active = excluded.is_active,
                last_updated = excluded.last_updated
        """, (username, int(is_active), datetime.now(CET)))
        conn.commit()
    finally:
        conn.close()


def get_scheduler_state(username: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM scheduler_state WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return bool(row[0]) if row else False

class SchedulerStatus:
    IDLE = "idle"
    WEEKLY_REPORT = "Generating weekly_report"
    FETCHING_TWEETS = "fetching_tweets"
    CATEGORIZING_TWEETS = "categorizing_tweets"
    GENERATING_SUMMARIES = "generating_summaries"
    POSTING_SUMMARIES = "posting_summaries"
    BATCH_COMPLETED = "batch_completed"
    DAY_COMPLETED = "day_completed"
    WAITING_FOR_POSTING = "WAITING_FOR_POSTING"
    ERROR = "ERROR"


def update_scheduler_state(username, is_active, status, batch=None, current_influencer=None, progress=0, details=None):
    """
    Update the scheduler state for a specific user
    
    Args:
        username (str): Username identifier
        status (str): Current status (use SchedulerStatus constants)
        batch (int, optional): Current batch number
        current_influencer (str, optional): Current influencer being processed
        progress (float, optional): Progress value between 0 and 1
        details (dict, optional): Additional details to store as JSON
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current timestamp
    timestamp = datetime.now(CET).isoformat()
    
    # Serialize details if present
    details_json = json.dumps(details) if details else None
    
    # Check if state exists for this user
    cursor.execute("SELECT * FROM scheduler_state WHERE username = ?", (username,))
    exists = cursor.fetchone()
    
    if exists:
        # Update existing state
        cursor.execute('''
            UPDATE scheduler_state
            SET
                status             = ?,
                is_active          = ?,
                batch              = ?,
                current_influencer = ?,
                progress           = ?,
                last_updated       = ?,
                details            = ?
            WHERE username = ?
        ''', (
            status,
            is_active,
            batch,
            current_influencer,
            progress,
            timestamp,
            details_json,
            username,
        ))

    else:
        # Insert new state
        cursor.execute('''
        INSERT INTO scheduler_state (username, is_active, status, batch, current_influencer, progress, last_updated, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username,is_active, status, batch, current_influencer, progress, timestamp, details_json))
    
    # Add to history
    cursor.execute('''
    INSERT INTO scheduler_history (username, is_active, status, batch, timestamp, details)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, is_active, status, batch, timestamp, details_json))
    
    conn.commit()
    conn.close()
    

def get_scheduler_state_details(username):
    """
    Get detailed scheduler state for a specific user
    
    Args:
        username (str): Username identifier
        
    Returns:
        dict: The current scheduler state with details
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM scheduler_state 
    WHERE username = ?
    ''', (username,))
    
    row = cursor.fetchone()
    
    if row:
        state = dict(row)
        # Parse JSON details
        if state['details']:
            state['details'] = json.loads(state['details'])
        
        # Get recent history
        cursor.execute('''
        SELECT * FROM scheduler_history 
        WHERE username = ? 
        ORDER BY timestamp DESC
        LIMIT 10
        ''', (username,))
        
        history = [dict(h) for h in cursor.fetchall()]
        for h in history:
            if h['details']:
                h['details'] = json.loads(h['details'])
        
        state['history'] = history
        conn.close()
        return state
    
    conn.close()
    return {
        'status': SchedulerStatus.IDLE,
        'is_active': 0,
        'batch': None,
        'current_influencer': None,
        'progress': 0,
        'last_updated': None,
        'details': None,
        'history': []
    }

def get_recent_scheduler_history(username, limit=10):
    """
    Get recent scheduler state history for a specific user
    
    Args:
        username (str): Username identifier
        limit (int): Maximum number of history entries to return
        
    Returns:
        list: Recent history entries
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM scheduler_history 
    WHERE username = ? 
    ORDER BY timestamp DESC
    LIMIT ?
    ''', (username, limit))
    
    rows = cursor.fetchall()
    
    history = []
    for row in rows:
        entry = dict(row)
        if entry['details']:
            entry['details'] = json.loads(entry['details'])
        history.append(entry)
    
    conn.close()
    return history

# from database.connection import get_connection
# from datetime import datetime
# import json
# import sqlite3
# from services.websocket_service import broadcast_status_update

# def set_scheduler_state(username: str, is_active: bool):
#     conn = get_connection()
#     cursor = conn.cursor()
#     try:
#         cursor.execute("""
#             INSERT INTO scheduler_state (username, is_active, last_updated)
#             VALUES (?, ?, ?)
#             ON CONFLICT(username) DO UPDATE SET
#                 is_active = excluded.is_active,
#                 last_updated = excluded.last_updated
#         """, (username, int(is_active), datetime.now()))
#         conn.commit()
#     finally:
#         conn.close()
        
#     # Add WebSocket broadcast
#     broadcast_status_update(username, {
#         "status": "ACTIVE" if is_active else "INACTIVE",
#         "details": {"message": f"Scheduler turned {'ON' if is_active else 'OFF'}"}
#     })

# def get_scheduler_state(username: str) -> bool:
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT is_active FROM scheduler_state WHERE username = ?", (username,))
#     row = cursor.fetchone()
#     conn.close()
#     return bool(row[0]) if row else False

# class SchedulerStatus:
#     IDLE = "idle"
#     FETCHING_TWEETS = "fetching_tweets"
#     CATEGORIZING_TWEETS = "categorizing_tweets"
#     GENERATING_SUMMARIES = "generating_summaries"
#     POSTING_SUMMARIES = "posting_summaries"
#     BATCH_COMPLETED = "batch_completed"
#     DAY_COMPLETED = "day_completed"


# def update_scheduler_state(username, is_active, status, batch=None, current_influencer=None, progress=0, details=None):
#     """
#     Update the scheduler state for a specific user
    
#     Args:
#         username (str): Username identifier
#         status (str): Current status (use SchedulerStatus constants)
#         batch (int, optional): Current batch number
#         current_influencer (str, optional): Current influencer being processed
#         progress (float, optional): Progress value between 0 and 1
#         details (dict, optional): Additional details to store as JSON
#     """
#     conn = get_connection()
#     cursor = conn.cursor()
    
#     # Get current timestamp
#     timestamp = datetime.now().isoformat()
    
#     # Serialize details if present
#     details_json = json.dumps(details) if details else None
    
#     # Check if state exists for this user
#     cursor.execute("SELECT * FROM scheduler_state WHERE username = ?", (username,))
#     exists = cursor.fetchone()
    
#     if exists:
#         # Update existing state
#         cursor.execute('''
#             UPDATE scheduler_state
#             SET
#                 status             = ?,
#                 is_active          = ?,
#                 batch              = ?,
#                 current_influencer = ?,
#                 progress           = ?,
#                 last_updated       = ?,
#                 details            = ?
#             WHERE username = ?
#         ''', (
#             status,
#             is_active,
#             batch,
#             current_influencer,
#             progress,
#             timestamp,
#             details_json,
#             username,
#         ))

#     else:
#         # Insert new state
#         cursor.execute('''
#         INSERT INTO scheduler_state (username, is_active, status, batch, current_influencer, progress, last_updated, details)
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (username, is_active, status, batch, current_influencer, progress, timestamp, details_json))
    
#     # Add to history
#     cursor.execute('''
#     INSERT INTO scheduler_history (username, is_active, status, batch, timestamp, details)
#     VALUES (?, ?, ?, ?, ?, ?)
#     ''', (username, is_active, status, batch, timestamp, details_json))
    
#     conn.commit()
#     conn.close()
    
#     # Add WebSocket broadcast for state updates
#     update_data = {
#         "status": status,
#         "is_active": is_active,
#         "batch": batch,
#         "current_influencer": current_influencer,
#         "progress": progress,
#         "last_updated": timestamp
#     }
    
#     if details:
#         update_data["details"] = details
        
#     broadcast_status_update(username, update_data)

# def get_scheduler_state_details(username):
#     """
#     Get detailed scheduler state for a specific user
    
#     Args:
#         username (str): Username identifier
        
#     Returns:
#         dict: The current scheduler state with details
#     """
#     conn = get_connection()
#     conn.row_factory = sqlite3.Row  # Return rows as dictionaries
#     cursor = conn.cursor()
    
#     cursor.execute('''
#     SELECT * FROM scheduler_state 
#     WHERE username = ?
#     ''', (username,))
    
#     row = cursor.fetchone()
    
#     if row:
#         state = dict(row)
#         # Parse JSON details
#         if state['details']:
#             state['details'] = json.loads(state['details'])
        
#         # Get recent history
#         cursor.execute('''
#         SELECT * FROM scheduler_history 
#         WHERE username = ? 
#         ORDER BY timestamp DESC
#         LIMIT 10
#         ''', (username,))
        
#         history = [dict(h) for h in cursor.fetchall()]
#         for h in history:
#             if h['details']:
#                 h['details'] = json.loads(h['details'])
        
#         state['history'] = history
#         conn.close()
#         return state
    
#     conn.close()
#     return {
#         'status': SchedulerStatus.IDLE,
#         'is_active': 0,
#         'batch': None,
#         'current_influencer': None,
#         'progress': 0,
#         'last_updated': None,
#         'details': None,
#         'history': []
#     }

# def get_recent_scheduler_history(username, limit=10):
#     """
#     Get recent scheduler state history for a specific user
    
#     Args:
#         username (str): Username identifier
#         limit (int): Maximum number of history entries to return
        
#     Returns:
#         list: Recent history entries
#     """
#     conn = get_connection()
#     conn.row_factory = sqlite3.Row  # Return rows as dictionaries
#     cursor = conn.cursor()
    
#     cursor.execute('''
#     SELECT * FROM scheduler_history 
#     WHERE username = ? 
#     ORDER BY timestamp DESC
#     LIMIT ?
#     ''', (username, limit))
    
#     rows = cursor.fetchall()
    
#     history = []
#     for row in rows:
#         entry = dict(row)
#         if entry['details']:
#             entry['details'] = json.loads(entry['details'])
#         history.append(entry)
    
#     conn.close()
#     return history