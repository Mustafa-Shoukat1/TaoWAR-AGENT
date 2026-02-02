import sqlite3
DB = "TaoWar-X.db"

def get_connection():
    return sqlite3.connect(DB)

import csv
import datetime

def export_todays_category_summaries_csv(filename="category_summaries_today.csv"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        today = datetime.date.today().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT * FROM category_summaries WHERE date = ?
        ''', (today,))
        rows = cursor.fetchall()
        # Get column names
        colnames = [desc[0] for desc in cursor.description]

        with open(filename, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(colnames)
            writer.writerows(rows)
        print(f"✅ Exported {len(rows)} rows to {filename}")
    finally:
        conn.close()

if __name__ == "__main__":
    export_todays_category_summaries_csv("category_summaries_today.csv")

