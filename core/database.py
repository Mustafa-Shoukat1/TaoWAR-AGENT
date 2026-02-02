# import sqlite3
# import datetime
# import os

# # ✅ Import DB path safely
# DB = os.getenv("DB", "TaoWar-X.db") 

# def init_db():
#     """Initialize the database with all necessary tables."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         # Users Table
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS users (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 username TEXT UNIQUE NOT NULL,
#                 password TEXT NOT NULL
#             )
#         ''')
#         # Influencers Table
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS influencers (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 username TEXT UNIQUE NOT NULL,
#                 added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         # Relevant Tweets Table
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS posts (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 tweet_id TEXT UNIQUE NOT NULL,
#                 username TEXT NOT NULL,
#                 text TEXT NOT NULL,
#                 link TEXT NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         # Relevant Tweets - Copy Table
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS selected (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 tweet_id TEXT UNIQUE NOT NULL,
#                 username TEXT NOT NULL,
#                 text TEXT NOT NULL,
#                 link TEXT NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         # Non-Relevant (Garbage) Tweets Table
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS garbage_posts (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 tweet_id TEXT UNIQUE NOT NULL,
#                 username TEXT NOT NULL,
#                 text TEXT NOT NULL,
#                 link TEXT NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         # Keywords Table
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS keywords (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 keyword TEXT UNIQUE NOT NULL,
#                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         # Categories Table
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS categories (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 name TEXT UNIQUE NOT NULL,
#                 description TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         # API Usage Table
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS api_usage (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 date DATE UNIQUE NOT NULL,
#                 count INTEGER DEFAULT 0
#             )
#         ''')

#         conn.commit()
#     except Exception as e:
#         print(f"⚠️ Database initialization error: {e}")
#     finally:
#         conn.close()
#         init_scheduling_state()

# def log_api_call(count=1):
#     """Log API calls per day."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     today = datetime.date.today().isoformat()
#     try:
#         cursor.execute("INSERT INTO api_usage (date, count) VALUES (?, ?) ON CONFLICT(date) DO UPDATE SET count = count + ?", 
#                        (today, count, count))
#         conn.commit()
#     finally:
#         conn.close()

# def get_api_usage_count():
#     """Returns the number of tweets scraped in the current month."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("SELECT SUM(count) FROM api_usage WHERE date >= date('now', 'start of month')")
#         count = cursor.fetchone()[0] or 0
#     finally:
#         conn.close()
#     return count

# def add_default_user():
#     """Adds default users to the users table if they do not already exist."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()

#     # List of users to add
#     default_users = [
#         ("admin", "password123"),
#         ("Mikedoyle@invluencer.com", "Dude3288*TW01!"),
#         ("Kiddoyles@gmail.com", "Dude3288*TW02!"),
#         ("Drpatrickdoyle@gmail.com", "Dude3288*TW03!"),
#         ("marcperkinsism@gmail.com", "Dude3288*TW04!"),
#         ("paul@keyko.io", "Dude3288*TW05!"),
#     ]

#     try:
#         for username, password in default_users:
#             try:
#                 cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
#                 print(f"✅ Added user: {username}")
#             except sqlite3.IntegrityError:
#                 print(f"⚠️ User '{username}' already exists, skipping.")

#         conn.commit()
#     except Exception as e:
#         print(f"⚠️ Error adding default users: {e}")
#     finally:
#         conn.close()


# def check_user_credentials(username, password):
#     """Verify username and password from the database."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
#     user = cursor.fetchone()
#     conn.close()
#     return user is not None

# def get_all_saved_tweet_ids():
#     """Returns a set of tweet IDs stored in either the posts or garbage_posts tables."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     saved_tweet_ids = set()
#     try:
#         cursor.execute("SELECT tweet_id FROM posts")
#         saved_tweet_ids.update(row[0] for row in cursor.fetchall())
#         cursor.execute("SELECT tweet_id FROM garbage_posts")
#         saved_tweet_ids.update(row[0] for row in cursor.fetchall())
#         cursor.execute("SELECT tweet_id FROM selected")
#         saved_tweet_ids.update(row[0] for row in cursor.fetchall())
#     except Exception as e:
#         print(f"⚠️ Error fetching all saved tweet IDs: {e}")
#     finally:
#         conn.close()
#     return saved_tweet_ids

# def save_garbage_posts(posts):
#     """Stores posts that are not the most relevant in the garbage_posts table."""
#     if not posts:
#         print("⚠️ No garbage posts to save.")
#         return
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         for post in posts:
#             cursor.execute('''
#                 INSERT INTO garbage_posts (tweet_id, username, text, link, created_at)
#                 VALUES (?, ?, ?, ?, ?)
#             ''', (post["id"], post["username"], post["text"], post["link"], post["created_at"]))
#         conn.commit()
#     except sqlite3.IntegrityError:
#         print(f"⚠️ Some garbage posts already exist in the database.")
#     except Exception as e:
#         print(f"⚠️ Error saving garbage posts: {e}")
#     finally:
#         conn.close()

# def get_garbage_posts():
#     """Fetches non-relevant (garbage) posts from the database."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     garbage_posts = []
#     try:
#         cursor.execute("SELECT tweet_id, username, text, link, created_at FROM garbage_posts ORDER BY created_at DESC")
#         garbage_posts = [{"tweet_id": row[0], "username": row[1], "text": row[2], "link": row[3], "created_at": row[4]} 
#                          for row in cursor.fetchall()]
#     except Exception as e:
#         print(f"⚠️ Error fetching garbage posts: {e}")
#     finally:
#         conn.close()
#     return garbage_posts

# def save_relevant_posts(posts, table):
#     """Saves relevant tweets into the posts table."""
#     if not posts:
#         return
#     saved_tweet_ids = get_all_saved_tweet_ids()
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         for post in posts:
#             if post["id"] not in saved_tweet_ids:
#                 cursor.execute(f'''
#                     INSERT INTO {table} (tweet_id, username, text, link, created_at)
#                     VALUES (?, ?, ?, ?, ?)
#                 ''', (post["id"], post["username"], post["text"], post["link"], post["created_at"]))
#         conn.commit()
#     except Exception as e:
#         print(f"⚠️ Error saving relevant posts: {e}")
#     finally:
#         conn.close()

# def get_relevant_posts():
#     """Fetches relevant posts from the database."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     posts = []
#     try:
#         cursor.execute("SELECT tweet_id, username, text, link, created_at FROM selected ORDER BY created_at DESC")
#         posts = [{"tweet_id": row[0], "username": row[1], "text": row[2], "link": row[3], "created_at": row[4]} 
#                  for row in cursor.fetchall()]
#     except Exception as e:
#         print(f"⚠️ Error fetching posts: {e}")
#     finally:
#         conn.close()
#     return posts

# def get_all_posts():
#     """Fetches relevant posts from the database."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     posts = []
#     try:
#         cursor.execute("SELECT tweet_id, username, text, link, created_at FROM garbage_posts ORDER BY created_at DESC")
#         posts = [{"tweet_id": row[0], "username": row[1], "text": row[2], "link": row[3], "created_at": row[4]} 
#                  for row in cursor.fetchall()]
#     except Exception as e:
#         print(f"⚠️ Error fetching posts: {e}")
#     finally:
#         conn.close()
#     return posts

# def get_influencers():
#     """Returns a list of influencers."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("SELECT username FROM influencers")
#         influencers = [{"username": row[0]} for row in cursor.fetchall()]
#     finally:
#         conn.close()
#     return influencers

# def save_influencer(username):
#     """Adds a new influencer to the database."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("INSERT INTO influencers (username) VALUES (?)", (username,))
#         conn.commit()
#     except sqlite3.IntegrityError:
#         print(f"⚠️ Influencer '{username}' already exists.")
#     finally:
#         conn.close()

# def delete_influencer(username):
#     """Deletes an influencer from the database."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("DELETE FROM influencers WHERE username = ?", (username,))
#         conn.commit()
#     finally:
#         conn.close()

# def delete_keyword(keyword):
#     """Deletes a keyword from the database."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("DELETE FROM keywords WHERE keyword = ?", (keyword,))
#         conn.commit()
#     finally:
#         conn.close()

# def get_keywords():
#     """Returns a list of keywords."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("SELECT keyword FROM keywords")
#         keywords = [row[0] for row in cursor.fetchall()]
#     finally:
#         conn.close()
#     return keywords

# def update_keywords(new_keywords):
#     """Updates the keywords list in the database."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("DELETE FROM keywords")
#         for keyword in new_keywords:
#             cursor.execute("INSERT INTO keywords (keyword, updated_at) VALUES (?, ?)", 
#                            (keyword, datetime.datetime.utcnow()))
#         conn.commit()
#     finally:
#         conn.close()

# def delete_post(tweet_id):
#     """Deletes a tweet from the posts table after replying."""
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("DELETE FROM posts WHERE tweet_id = ?", (tweet_id,))
#         conn.commit()
#         print(f"🗑 Post {tweet_id} successfully deleted from posts table.")
#     except Exception as e:
#         print(f"⚠️ Error deleting post {tweet_id}: {e}")
#     finally:
#         conn.close()


# # Initialize database and default user

# def init_scheduling_state():
#     """
#     Ensures there is a scheduling_state table
#     and that we have exactly one row for the scheduler state.
#     """
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         # Create the table if it doesn't exist
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS scheduling_state (
#                 id INTEGER PRIMARY KEY,
#                 batch_no INTEGER NOT NULL,
#                 last_switch TIMESTAMP NOT NULL
#             )
#         ''')
#         # Check if row with id=1 already exists
#         cursor.execute("SELECT COUNT(*) FROM scheduling_state WHERE id=1")
#         count = cursor.fetchone()[0]
#         if count == 0:
#             # If not, insert a default row: batch_no=0, last_switch=NOW
#             cursor.execute('''
#                 INSERT INTO scheduling_state (id, batch_no, last_switch)
#                 VALUES (1, 0, ?)
#             ''', (datetime.datetime.now(),))
#             conn.commit()
#     except Exception as e:
#         print(f"⚠️ Error initializing scheduling_state: {e}")
#     finally:
#         conn.close()

# def get_scheduling_state():
#     """
#     Returns (batch_no, last_switch) from scheduling_state,
#     or (0, now) if the row is missing for any reason.
#     """
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("SELECT batch_no, last_switch FROM scheduling_state WHERE id=1")
#         row = cursor.fetchone()
#         if row:
#             # row = (batch_no, last_switch)
#             return row[0], row[1]  # batch_no, last_switch
#         else:
#             # fallback if something is off
#             return 0, datetime.datetime.now()
#     except Exception as e:
#         print(f"⚠️ Error retrieving scheduling_state: {e}")
#         return 0, datetime.datetime.now()
#     finally:
#         conn.close()

# def update_scheduling_state(batch_no, last_switch):
#     """
#     Updates the single row in scheduling_state with the new batch_no and last_switch time.
#     """
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute('''
#             UPDATE scheduling_state
#             SET batch_no = ?, last_switch = ?
#             WHERE id = 1
#         ''', (batch_no, last_switch))
#         conn.commit()
#     except Exception as e:
#         print(f"⚠️ Error updating scheduling_state: {e}")
#     finally:
#         conn.close()

# # def clear_tables():
# #     """Clear contents of posts, selected, and garbage_posts tables."""
# #     conn = sqlite3.connect(DB)
# #     cursor = conn.cursor()
# #     try:
# #         cursor.execute("DELETE FROM posts")
# #         cursor.execute("DELETE FROM selected")
# #         cursor.execute("DELETE FROM garbage_posts")
# #         conn.commit()
# #         print("✅ Tables cleared successfully.")
# #     except Exception as e:
# #         print(f"⚠️ Error clearing tables: {e}")
# #     finally:
# #         conn.close()

# # # Call the function to clear tables
# # clear_tables()


# def add_category(name, description):
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("""
#             INSERT INTO categories (name, description)
#             VALUES (?, ?)
#         """, (name, description))
#         conn.commit()
#     except sqlite3.IntegrityError:
#         print(f"⚠️ Category '{name}' already exists.")
#     finally:
#         conn.close()

# def get_all_categories():
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("SELECT id, name, description, created_at, updated_at FROM categories")
#         rows = cursor.fetchall()
#         return [
#             {"id": row[0], "name": row[1], "description": row[2], "created_at": row[3], "updated_at": row[4]}
#             for row in rows
#         ]
#     finally:
#         conn.close()

# def delete_category(category_id):
#     conn = sqlite3.connect(DB)
#     cursor = conn.cursor()
#     try:
#         cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
#         conn.commit()
#     finally:
#         conn.close()

# init_db()
# add_default_user()