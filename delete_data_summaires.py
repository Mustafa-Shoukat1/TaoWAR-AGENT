import sqlite3
DB = "TaoWar-X.db"

def get_connection():
    return sqlite3.connect(DB)

from datetime import datetime, date

def delete_category_summaries_before_time(cutoff_time_str="07:06:33"):
    """
    Deletes rows from category_summaries where date is today and the current time is before cutoff_time_str.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Today's date
        today = date.today().strftime('%Y-%m-%d')
        # Delete where date is today and time(current_timestamp) < cutoff_time_str
        cursor.execute(f"""
            DELETE FROM category_summaries
            WHERE date = ? AND time('now', 'localtime') < ?
        """, (today, cutoff_time_str))
        deleted = cursor.rowcount
        conn.commit()
        print(f"✅ Deleted {deleted} rows from category_summaries for today before {cutoff_time_str}")
    except Exception as e:
        print(f"⚠️ Error deleting rows: {e}")
    finally:
        conn.close()

# Usage
if __name__ == "__main__":
    delete_category_summaries_before_time("10:06:33")

