import sqlite3
DB = "TaoWar-X.db"

def get_connection():
    return sqlite3.connect(DB)



def delete_category_summaries_by_id_range(start_id=511, end_id=522):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM category_summaries
            WHERE id BETWEEN ? AND ?
        """, (start_id, end_id))
        deleted = cursor.rowcount
        conn.commit()
        print(f"✅ Deleted {deleted} rows with IDs from {start_id} to {end_id}")
    except Exception as e:
        print(f"⚠️ Error deleting rows: {e}")
    finally:
        conn.close()

# Run
if __name__ == "__main__":
    delete_category_summaries_by_id_range(511, 522)

