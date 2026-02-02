from database.connection import get_connection
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from utils.logger import logger

def initiate_weekly_report(week_start: str, week_end: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cet_now = datetime.now(ZoneInfo("Europe/Paris")).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO weekly_reports (week_start, week_end, generated_at, report_md) VALUES (?, ?, ?, ?)",
            (week_start, week_end, cet_now, "PENDING")
        )
        report_id = cursor.lastrowid
        conn.commit()
        logger.info(f"✅ Weekly report initiated for {week_start} - {week_end} with id {report_id}")
        return report_id
    except Exception as e:
        logger.error(f"⚠️ Error initiating weekly report: {e}")
        return None
    finally:
        conn.close()

def update_weekly_report_md(report_id: int, full_report: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE weekly_reports SET report_md = ? WHERE id = ?",
            (full_report, report_id)
        )
        conn.commit()
        logger.info(f"✅ Weekly report markdown updated for report id {report_id}")
        return True
    except Exception as e:
        logger.error(f"⚠️ Error updating weekly report markdown: {e}")
        return False
    finally:
        conn.close()

def mark_weekly_report_sent(report_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE weekly_reports SET sent_weekly_report = 1 WHERE id = ?",
            (report_id,)
        )
        conn.commit()
        logger.info(f"✅ Marked weekly report {report_id} as sent.")
    except Exception as e:
        logger.error(f"⚠️ Error updating sent_weekly_report: {e}")
    finally:
        conn.close()


# def get_report_ids_last_7_days():
#     """
#     Returns a list of (id, generated_at) tuples for reports from the last 7 days (including today), newest first.
#     """
#     conn = get_connection()
#     cursor = conn.cursor()
#     try:
#         cet_now = datetime.now(ZoneInfo("Europe/Paris"))
#         start_date = (cet_now - timedelta(days=6)).strftime('%Y-%m-%d 00:00:00')  # include today
#         cursor.execute("""
#             SELECT id, generated_at
#             FROM daily_reports
#             WHERE generated_at >= ?
#             ORDER BY generated_at DESC
#         """, (start_date,))
#         results = cursor.fetchall()
#         return results  # list of (id, generated_at)
#     except Exception as e:
#         print(f"⚠️ Error fetching report ids: {e}")
#         return []
#     finally:
#         conn.close()
        
def get_report_ids_last_7_days():
    """
    Returns a list of (id, generated_at) tuples for reports from the previous 7 days (NOT including today), newest first.
    Example: If today is July 24, returns for July 17–23 (inclusive).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cet_now = datetime.now(ZoneInfo("Europe/Paris"))
        end_date = (cet_now - timedelta(days=1)).strftime('%Y-%m-%d 23:59:59')      # yesterday end
        start_date = (cet_now - timedelta(days=7)).strftime('%Y-%m-%d 00:00:00')    # 7 days before yesterday start

        cursor.execute("""
            SELECT id, generated_at
            FROM daily_reports
            WHERE generated_at >= ? AND generated_at <= ?
            ORDER BY generated_at DESC
        """, (start_date, end_date))
        results = cursor.fetchall()
        return results  # list of (id, generated_at)
    except Exception as e:
        print(f"⚠️ Error fetching report ids: {e}")
        return []
    finally:
        conn.close()


import json

def get_category_summaries_for_reports(report_ids):
    """
    For a list of report ids, returns a dict:
    {
        report_id: [
            (category_name, category_summary, influencers_list),
            ...
        ],
        ...
    }
    """
    if not report_ids:
        return {}
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Prepare placeholders (?, ?, ?, ...)
        placeholders = ','.join(['?'] * len(report_ids))
        cursor.execute(f"""
            SELECT report_id, category_name, category_summary, influencers
            FROM daily_report_category_summaries
            WHERE report_id IN ({placeholders})
        """, report_ids)
        rows = cursor.fetchall()
        data = {}
        for report_id, category_name, category_summary, influencers_json in rows:
            influencers_list = json.loads(influencers_json) if influencers_json else []
            data.setdefault(report_id, []).append(
                (category_name, category_summary, influencers_list)
            )
        return data
    except Exception as e:
        print(f"⚠️ Error fetching category summaries: {e}")
        return {}
    finally:
        conn.close()


def build_report_category_summary_dict():
    """
    Returns a dict of:
    {
      report_id: {
        "generated_at": ...,
        "categories": {
            category_name: (summary, influencers_list),
            ...
        }
      },
      ...
    }
    """
    # Step 1: Get reports from last 7 days
    reports = get_report_ids_last_7_days()
    if not reports:
        return {}
    id_to_date = {report_id: generated_at for report_id, generated_at in reports}
    report_ids = list(id_to_date.keys())

    # Step 2: Get all category summaries for those reports
    cat_summaries = get_category_summaries_for_reports(report_ids)

    # Step 3: Build dict
    result = {}
    for report_id in report_ids:
        result[report_id] = {
            "generated_at": id_to_date[report_id],
            "categories": {}
        }
        for tup in cat_summaries.get(report_id, []):
            category_name, summary, influencers_list = tup
            result[report_id]["categories"][category_name] = (summary, influencers_list)
    return result


# data = build_report_category_summary_dict()
# for report_id, report_info in data.items():
#     print(f"Report ID: {report_id}, Date: {report_info['generated_at']}")
#     for cat, (summary, influencers) in report_info["categories"].items():
#         print(f"  Category: {cat}")
#         print(f"    Summary: {summary}")
#         print(f"    Influencers: {influencers}")
