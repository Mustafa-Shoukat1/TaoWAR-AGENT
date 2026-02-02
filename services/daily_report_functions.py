import json
from database.connection import get_connection
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.logger import logger

def insert_category_summary(report_id: int, category_name: str, category_summary: str, influencers: list) -> int:
    """
    Inserts a category summary for a given report into the daily_report_category_summaries table,
    including a JSON list of influencers (with possible duplicates and original order).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cet_now = datetime.now(ZoneInfo("Europe/Paris"))
        cet_now_str = cet_now.strftime('%Y-%m-%d %H:%M:%S')
        influencers_json = json.dumps(influencers)  # NO set(), keep as is
        cursor.execute("""
            INSERT INTO daily_report_category_summaries (report_id, timestamp, category_name, category_summary, influencers)
            VALUES (?, ?, ?, ?, ?)
        """, (report_id, cet_now_str, category_name, category_summary, influencers_json))
        summary_id = cursor.lastrowid
        conn.commit()
        logger.info(f"✅ Category summary inserted for '{category_name}' in report id {report_id} at {cet_now_str} CET with id {summary_id}")
        return summary_id
    except Exception as e:
        logger.error(f"⚠️ Error inserting category summary: {e}")
        return None
    finally:
        conn.close()


def initiate_daily_report(batch_no: int) -> int:
    """
    Inserts a new daily report with placeholder markdown ("PENDING"), returns the inserted report's id.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cet_now = datetime.now(ZoneInfo("Europe/Paris"))
        cet_now_str = cet_now.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO daily_reports (batch_no, generated_at, report_md)
            VALUES (?, ?, ?)
        """, (batch_no, cet_now_str, "PENDING"))
        report_id = cursor.lastrowid
        conn.commit()
        logger.info(f"✅ Daily report INITIATED for batch {batch_no} at {cet_now_str} CET with id {report_id}")
        return report_id
    except Exception as e:
        logger.error(f"⚠️ Error initiating daily report: {e}")
        return None
    finally:
        conn.close()

def update_report_md(report_id: int, full_report: str) -> bool:
    """
    Updates the report_md field of a daily report by id.
    Returns True if successful, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE daily_reports
            SET report_md = ?
            WHERE id = ?
        """, (full_report, report_id))
        conn.commit()
        logger.info(f"✅ Report markdown updated for report id {report_id}")
        return True
    except Exception as e:
        logger.error(f"⚠️ Error updating report markdown: {e}")
        return False
    finally:
        conn.close()

def mark_daily_report_sent(report_id: int):
    """
    Set sent_daily_report = 1 for the given daily report ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            UPDATE daily_reports
            SET sent_daily_report = 1
            WHERE id = ?
            ''',
            (report_id,)
        )
        conn.commit()
        logger.info(f"✅ Marked report {report_id} as sent.")
    except Exception as e:
        logger.error(f"⚠️ Error updating sent_daily_report: {e}")
    finally:
        conn.close()

        
import requests

def send_daily_report(
    title: str,
    content: str,
    generated_by: str = "daily_ai",  # or another slug if needed
    description_summary: str = "",
    api_key: str = "7febb13aee3d64c20ecd7d1d312cd24c7446e144bd594c1f858d465d9a40dfa3"
) -> dict:
    """
    Send the daily report to the TaoWAR backend daily/internal endpoint.
    Returns the response as a dict.
    Raises requests.HTTPError if the API call fails.
    """
    url = "https://tao-war-backend.onrender.com/daily/internal"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "title": title,
        "content": content,
        "generatedBy": generated_by,
        "descriptionSummary": description_summary
    }
    response = requests.post(url, json=payload, headers=headers, timeout=50)
    response.raise_for_status()  # Will raise an error for 4xx/5xx
    return response.json()


def insert_daily_report(batch_no: int, report_md: str) -> int:
    """
    Insert a daily report into the daily_reports table with generated_at as Paris (CET/CEST) time.
    Returns the inserted report's id, or None if insert fails.
    """
    from database.connection import get_connection
    from datetime import datetime
    from zoneinfo import ZoneInfo

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Get current time in Paris
        cet_now = datetime.now(ZoneInfo("Europe/Paris"))
        cet_now_str = cet_now.strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute(
            '''
            INSERT INTO daily_reports (batch_no, generated_at, report_md)
            VALUES (?, ?, ?)
            ''',
            (batch_no, cet_now_str, report_md)
        )
        report_id = cursor.lastrowid  # Get the inserted ID
        conn.commit()
        print(f"✅ Daily report inserted for batch {batch_no} at {cet_now_str} CET with id {report_id}")
        return report_id
    except Exception as e:
        print(f"⚠️ Error inserting daily report: {e}")
        return None
    finally:
        conn.close()