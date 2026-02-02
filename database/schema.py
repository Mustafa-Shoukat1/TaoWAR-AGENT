from database.connection import get_connection
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        # Influencers Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS influencers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
CREATE TABLE IF NOT EXISTS user_metrics (
    id BIGINT PRIMARY KEY,                -- Twitter user ID (unique)
    username VARCHAR(64) NOT NULL,        -- Twitter username
    name VARCHAR(128),                    -- Display name
    bio TEXT,                             -- Bio/description
    location VARCHAR(255),                -- Location (nullable)
    created_at TIMESTAMP,                 -- When account was created
    profile_image_url TEXT,               -- Avatar URL

    followers_count INTEGER DEFAULT 0,    -- Follower count
    following_count INTEGER DEFAULT 0,    -- Following count
    tweet_count INTEGER DEFAULT 0,        -- Total tweet count
    listed_count INTEGER DEFAULT 0,       -- Listed count

    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
        ''')

        # Posts Tables
        for table in ["posts", "selected", "garbage_posts"]:
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    text TEXT NOT NULL,
                    link TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    retweet_count INTEGER DEFAULT NULL,
                    like_count INTEGER DEFAULT NULL,
                    reply_count INTEGER DEFAULT NULL,
                    quote_count INTEGER DEFAULT NULL,
                    hashtags TEXT DEFAULT NULL,
                    context_annotations TEXT DEFAULT NULL
                )
            ''')
        
        columns = [
            ("retweet_count", "INTEGER DEFAULT NULL"),
            ("like_count", "INTEGER DEFAULT NULL"),
            ("reply_count", "INTEGER DEFAULT NULL"),
            ("quote_count", "INTEGER DEFAULT NULL"),
            ("hashtags", "TEXT DEFAULT NULL"),
            ("context_annotations", "TEXT DEFAULT NULL"),
        ]
        for table in ["posts", "selected", "garbage_posts"]:
            for col, coltype in columns:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype};")
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"⚠️ Error adding {col} to {table}: {e}")



        # Keywords Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Categories Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # API Usage Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                count INTEGER DEFAULT 0
            )
        ''')

        # Scheduling State Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduling_state (
                id INTEGER PRIMARY KEY,
                batch_no INTEGER NOT NULL,
                last_switch TIMESTAMP NOT NULL
            )
        ''')
        
        # 🆕 Categorized Posts Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorized_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                influencer TEXT NOT NULL,
                tweet_id TEXT NOT NULL,
                categories TEXT NOT NULL, -- comma-separated category names
                batch_no INTEGER NOT NULL,
                date DATE DEFAULT CURRENT_DATE
            )
        ''')

        # 🆕 Individual Category Summary Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS category_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                influencer_usernames TEXT NOT NULL, -- comma-separated
                summary TEXT NOT NULL,
                batch_no INTEGER NOT NULL,
                posted_flag INTEGER DEFAULT 0, -- 0 for not posted, 1 for posted
                weekly_post_flag INTEGER DEFAULT 0, -- 0 for not posted, 1 for posted
                date DATE DEFAULT CURRENT_DATE
            )
        ''')

        # 🆕 Global Daily Summary Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS all_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_no INTEGER NOT NULL,
                date DATE DEFAULT CURRENT_DATE,
                summary TEXT NOT NULL
            )
        ''')
        
        # 🆕 X Posting Logs Table (Updated with batch_no)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS x_post_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary TEXT NOT NULL,
                tweet_ids TEXT NOT NULL, -- comma-separated
                batch_no INTEGER NOT NULL,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
    #     cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS scheduler_state (
    #         username TEXT PRIMARY KEY,
    #         is_active INTEGER DEFAULT 0,
    #         last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     )
    # ''')
    
        # Create scheduler_state table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduler_state (
                username TEXT PRIMARY KEY,
                is_active BOOL DEFAULT False,
                status TEXT,
                batch INTEGER,
                current_influencer TEXT,
                progress REAL,
                last_updated TEXT,
                details TEXT
            )
        ''')
        
        # Create history table for tracking state changes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduler_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            is_active BOOL DEFAULT False,
            username TEXT,
            status TEXT,
            batch INTEGER,
            timestamp TEXT,
            details TEXT
        )
        ''')
        
        # Create daily scheduler state table for persistent daily states
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_scheduler_state (
            username TEXT,
            date TEXT,
            categorization_and_summarization BOOLEAN DEFAULT FALSE,
            posting_done BOOLEAN DEFAULT FALSE,
            weekly_done BOOLEAN DEFAULT FALSE,
            current_position INTEGER DEFAULT 0,
            weekly_img_rotator INTEGER DEFAULT 1,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (username, date)
        )
        ''')
        
        # Daily Reports Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_no INTEGER NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                report_md TEXT NOT NULL,
                sent_daily_report INTEGER DEFAULT 0,
                used_in_weekly_report INTEGER DEFAULT 0
            )
        ''')

        # ALTER TABLE to add columns if they don't exist (for existing DBs)
        try:
            cursor.execute("ALTER TABLE daily_reports ADD COLUMN sent_daily_report INTEGER DEFAULT 0")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                print(f"⚠️ Error adding sent_daily_report column: {e}")

        try:
            cursor.execute("ALTER TABLE daily_reports ADD COLUMN used_in_weekly_report INTEGER DEFAULT 0")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                print(f"⚠️ Error adding used_in_weekly_report column: {e}")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_report_category_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                category_name TEXT NOT NULL,
                category_summary TEXT NOT NULL,
                influencers TEXT,
                FOREIGN KEY(report_id) REFERENCES daily_reports(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            week_end DATE NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            report_md TEXT NOT NULL,
            sent_weekly_report INTEGER DEFAULT 0
        )
        ''')




        # Insert default scheduling row
        cursor.execute("SELECT COUNT(*) FROM scheduling_state WHERE id=1")
        if cursor.fetchone()[0] == 0:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            cursor.execute("INSERT INTO scheduling_state (id, batch_no, last_switch) VALUES (1, 0, ?)", (datetime.now(ZoneInfo("Europe/Paris")),))

        conn.commit()
    except Exception as e:
        print(f"⚠️ Error initializing schema: {e}")
    finally:
        conn.close()

