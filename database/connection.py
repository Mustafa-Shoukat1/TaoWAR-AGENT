import sqlite3
from config import DB

def get_connection():
    return sqlite3.connect(DB)
