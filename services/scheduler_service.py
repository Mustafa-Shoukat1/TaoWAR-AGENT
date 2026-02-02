from database.connection import get_connection
import datetime
from zoneinfo import ZoneInfo

def get_scheduling_state():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT batch_no, last_switch FROM scheduling_state WHERE id=1")
    row = cursor.fetchone()
    conn.close()
    return (row[0], row[1]) if row else (0, datetime.datetime.now(ZoneInfo("Europe/Paris")))

def update_scheduling_state(batch_no, last_switch):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE scheduling_state SET batch_no = ?, last_switch = ? WHERE id = 1", (batch_no, last_switch))
    conn.commit()
    conn.close()
