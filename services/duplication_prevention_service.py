import sqlite3
from datetime import datetime, date
from zoneinfo import ZoneInfo
from database.connection import get_connection
from utils.logger import logger

CET = ZoneInfo("Europe/Paris")

def create_daily_processing_log_table():
    """Create table to track daily processing operations"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                influencer TEXT,
                batch_number INTEGER,
                status TEXT DEFAULT 'in_progress',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                details TEXT,
                UNIQUE(date, operation_type, influencer, batch_number)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_daily_processing_date_operation 
            ON daily_processing_log(date, operation_type)
        ''')
        
        # Enhanced X post tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS x_post_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                post_type TEXT NOT NULL,
                category_name TEXT,
                summary_hash TEXT,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tweet_id TEXT,
                UNIQUE(date, post_type, category_name, summary_hash)
            )
        ''')
        
        # Enhanced report tracking  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                report_type TEXT NOT NULL,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                UNIQUE(date, report_type)
            )
        ''')
        
        # NEW: Summary generation tracking to prevent duplicate summaries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summary_generation_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                batch_number INTEGER NOT NULL,
                category TEXT NOT NULL,
                summary_hash TEXT NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                UNIQUE(date, batch_number, category, summary_hash)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_summary_generation_date_batch 
            ON summary_generation_tracking(date, batch_number)
        ''')
        
        conn.commit()
        logger.info("✅ Daily processing tracking tables created/verified")
        
    except Exception as e:
        logger.error(f"❌ Error creating daily processing log tables: {e}")
    finally:
        conn.close()

def is_influencer_processed_today(influencer: str, operation_type: str = 'fetch_posts') -> bool:
    """Check if an influencer has already been processed today"""
    today = datetime.now(CET).date().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM daily_processing_log 
            WHERE date = ? AND operation_type = ? AND influencer = ? AND status = 'completed'
        ''', (today, operation_type, influencer))
        
        count = cursor.fetchone()[0]
        return count > 0
        
    except Exception as e:
        logger.error(f"❌ Error checking if influencer {influencer} processed: {e}")
        return False
    finally:
        conn.close()

def mark_influencer_processing_start(influencer: str, operation_type: str = 'fetch_posts', batch_number: int = 1):
    """Mark that influencer processing has started"""
    today = datetime.now(CET).date().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO daily_processing_log 
            (date, operation_type, influencer, batch_number, status, started_at) 
            VALUES (?, ?, ?, ?, 'in_progress', ?)
        ''', (today, operation_type, influencer, batch_number, datetime.now(CET).isoformat()))
        
        conn.commit()
        logger.info(f"📝 Marked {operation_type} start for {influencer} on {today}")
        
    except Exception as e:
        logger.error(f"❌ Error marking processing start for {influencer}: {e}")
    finally:
        conn.close()

def mark_influencer_processing_complete(influencer: str, operation_type: str = 'fetch_posts'):
    """Mark that influencer processing has completed"""
    today = datetime.now(CET).date().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE daily_processing_log 
            SET status = 'completed', completed_at = ?
            WHERE date = ? AND operation_type = ? AND influencer = ? AND status = 'in_progress'
        ''', (datetime.now(CET).isoformat(), today, operation_type, influencer))
        
        conn.commit()
        logger.info(f"✅ Marked {operation_type} complete for {influencer} on {today}")
        
    except Exception as e:
        logger.error(f"❌ Error marking processing complete for {influencer}: {e}")
    finally:
        conn.close()

def is_x_post_already_sent(category_name: str, summary_hash: str, post_type: str = 'daily_summary') -> bool:
    """Check if a summary has already been posted to X today"""
    today = datetime.now(CET).date().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM x_post_tracking 
            WHERE date = ? AND post_type = ? AND category_name = ? AND summary_hash = ?
        ''', (today, post_type, category_name, summary_hash))
        
        count = cursor.fetchone()[0]
        return count > 0
        
    except Exception as e:
        logger.error(f"❌ Error checking if X post sent for {category_name}: {e}")
        return False
    finally:
        conn.close()

def get_daily_x_posts_count(post_type: str = 'daily_summary') -> int:
    """Get count of X posts already sent today"""
    today = datetime.now(CET).date().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM x_post_tracking 
            WHERE date = ? AND post_type = ?
        ''', (today, post_type))
        
        count = cursor.fetchone()[0]
        return count
        
    except Exception as e:
        logger.error(f"❌ Error getting daily X posts count: {e}")
        return 0
    finally:
        conn.close()

def mark_x_post_sent(category_name: str, summary_hash: str, tweet_id: str = None, post_type: str = 'daily_summary'):
    """Mark that a summary has been posted to X"""
    today = datetime.now(CET).date().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO x_post_tracking 
            (date, post_type, category_name, summary_hash, tweet_id, posted_at) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (today, post_type, category_name, summary_hash, tweet_id, datetime.now(CET).isoformat()))
        
        conn.commit()
        logger.info(f"📝 Marked X post sent for {category_name} on {today}")
        
    except Exception as e:
        logger.error(f"❌ Error marking X post sent for {category_name}: {e}")
    finally:
        conn.close()

def is_report_already_sent_today(report_type: str = 'daily') -> bool:
    """Check if daily/weekly report has already been sent today"""
    today = datetime.now(CET).date().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM report_tracking 
            WHERE date = ? AND report_type = ? AND sent_at IS NOT NULL
        ''', (today, report_type))
        
        count = cursor.fetchone()[0]
        return count > 0
        
    except Exception as e:
        logger.error(f"❌ Error checking if {report_type} report sent: {e}")
        return False
    finally:
        conn.close()

def mark_report_sent(report_type: str, report_id: int = None):
    """Mark that a report has been sent"""
    today = datetime.now(CET).date().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO report_tracking 
            (date, report_type, report_id, sent_at) 
            VALUES (?, ?, ?, ?)
        ''', (today, report_type, report_id, datetime.now(CET).isoformat()))
        
        conn.commit()
        logger.info(f"✅ Marked {report_type} report sent on {today}")
        
    except Exception as e:
        logger.error(f"❌ Error marking {report_type} report sent: {e}")
    finally:
        conn.close()

def get_processing_summary_for_date(date_str: str = None):
    """Get processing summary for a specific date"""
    if date_str is None:
        date_str = datetime.now(CET).date().isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Get influencer processing stats
        cursor.execute('''
            SELECT operation_type, COUNT(*) as count, 
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM daily_processing_log 
            WHERE date = ?
            GROUP BY operation_type
        ''', (date_str,))
        
        processing_stats = cursor.fetchall()
        
        # Get X posting stats
        cursor.execute('''
            SELECT post_type, COUNT(*) as count
            FROM x_post_tracking 
            WHERE date = ?
            GROUP BY post_type
        ''', (date_str,))
        
        x_post_stats = cursor.fetchall()
        
        # Get report stats
        cursor.execute('''
            SELECT report_type, COUNT(*) as count,
                   SUM(CASE WHEN sent_at IS NOT NULL THEN 1 ELSE 0 END) as sent
            FROM report_tracking 
            WHERE date = ?
            GROUP BY report_type
        ''', (date_str,))
        
        report_stats = cursor.fetchall()
        
        # Convert processing stats (operation_type, count, completed)
        processing_dict = {}
        for operation_type, count, completed in processing_stats:
            processing_dict[operation_type] = {'total': count, 'completed': completed}
        
        # Convert report stats (report_type, count, sent)
        reports_dict = {}
        for report_type, count, sent in report_stats:
            reports_dict[report_type] = {'total': count, 'sent': sent}
        
        return {
            'date': date_str,
            'processing': processing_dict,
            'x_posts': dict(x_post_stats),  # This one is fine (2 columns)
            'reports': reports_dict
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting processing summary: {e}")
        return None
    finally:
        conn.close()


def is_summary_already_generated(date_str: str, batch_number: int, category: str, summary_hash: str) -> bool:
    """Check if a summary has already been generated for this date, batch, category and content hash"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM summary_generation_tracking 
            WHERE date = ? AND batch_number = ? AND category = ? AND summary_hash = ?
        ''', (date_str, batch_number, category, summary_hash))
        
        count = cursor.fetchone()[0]
        return count > 0
        
    except Exception as e:
        logger.error(f"❌ Error checking if summary generated for {category}: {e}")
        return False
    finally:
        conn.close()


def mark_summary_generated(date_str: str, batch_number: int, category: str, summary_hash: str, details: str = None):
    """Mark that a summary has been generated for this category to prevent duplicates"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO summary_generation_tracking 
            (date, batch_number, category, summary_hash, details) 
            VALUES (?, ?, ?, ?, ?)
        ''', (date_str, batch_number, category, summary_hash, details))
        
        conn.commit()
        logger.info(f"📝 Marked summary generated for {category} on {date_str} batch {batch_number}")
        
    except Exception as e:
        logger.error(f"❌ Error marking summary generated for {category}: {e}")
    finally:
        conn.close()


def get_daily_summary_count(date_str: str, batch_number: int) -> int:
    """Get count of summaries generated for a specific date and batch"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT COUNT(DISTINCT category) FROM summary_generation_tracking 
            WHERE date = ? AND batch_number = ?
        ''', (date_str, batch_number))
        
        count = cursor.fetchone()[0]
        return count
        
    except Exception as e:
        logger.error(f"❌ Error getting summary count for {date_str} batch {batch_number}: {e}")
        return 0
    finally:
        conn.close()


def is_categorization_pipeline_complete(date_str: str, batch_number: int) -> bool:
    """Check if categorization pipeline has been completed for this date and batch"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM daily_processing_log 
            WHERE date = ? AND operation_type = 'categorization_pipeline' 
            AND batch_number = ? AND status = 'completed'
        ''', (date_str, batch_number))
        
        count = cursor.fetchone()[0]
        return count > 0
        
    except Exception as e:
        logger.error(f"❌ Error checking categorization completion: {e}")
        return False
    finally:
        conn.close()


# Initialize tables on import
create_daily_processing_log_table()
