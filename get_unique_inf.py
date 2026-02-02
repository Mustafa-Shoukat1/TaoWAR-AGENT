import sqlite3
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DB_PATH = "TaoWar-X.db"
OUTPUT_FILE = "unique_influencers_grouped_by_category.json"

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_report_ids_last_7_days():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cet_now = datetime.now(ZoneInfo("Europe/Paris"))
        start_date = "2025-07-23 00:00:00"
        end_date   = "2025-07-29 23:59:59"
        print(f"Start: {start_date}, End: {end_date}")
        cursor.execute("""
            SELECT id, generated_at
            FROM daily_reports
            WHERE generated_at >= ? AND generated_at <= ?
            ORDER BY generated_at DESC
        """, (start_date, end_date))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"⚠️ Error fetching report ids: {e}")
        return []
    finally:
        conn.close()

def get_category_summaries_for_reports(report_ids):
    if not report_ids:
        return {}
    conn = get_connection()
    cursor = conn.cursor()
    try:
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
    reports = get_report_ids_last_7_days()
    if not reports:
        return {}
    id_to_date = {report_id: generated_at for report_id, generated_at in reports}
    report_ids = list(id_to_date.keys())
    cat_summaries = get_category_summaries_for_reports(report_ids)
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

def get_unique_influencers_and_groups(weekly_data):
    unique_influencers = set()
    grouped_data = []
    for report_id, report in weekly_data.items():
        report_date = report["generated_at"]
        for category, (summary, influencers) in report["categories"].items():
            unique_influencers.update(influencers)
            grouped_data.append({
                "report_id": report_id,
                "report_date": report_date,
                "category": category,
                "influencers": influencers
            })
    return sorted(unique_influencers), grouped_data

if __name__ == "__main__":
    weekly_data = build_report_category_summary_dict()
    unique_influencers, grouped_data = get_unique_influencers_and_groups(weekly_data)

    # Save to JSON
    output = {
        "unique_influencer_count": len(unique_influencers),
        "unique_influencer_names": unique_influencers,
        "groups": grouped_data
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Saved influencer grouping (by report and category) to {OUTPUT_FILE}")
