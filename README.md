# 🚀 TaoWAR-AGENT — AI-Powered Crypto Marketing Automation for X (Twitter)

**TaoWAR-AGENT** is a production-ready, AI-powered marketing automation system built with Python and Streamlit. It monitors cryptocurrency influencers on X (formerly Twitter), scrapes their tweets, uses OpenAI GPT-4o to categorize and summarize the content, and automatically publishes daily and weekly market intelligence reports back to X — all on a fully automated schedule.

---

## Table of Contents

- [System Overview](#system-overview)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
  - [Core Module](#core-module-core)
  - [Database Module](#database-module-database)
  - [Services Module](#services-module-services)
  - [AI Pipelines](#ai-pipelines-ai_pipelines)
  - [AI Prompts](#ai-prompts-ai_prompts)
  - [Scripts (Scheduler)](#scripts-scheduler-scripts)
  - [Engagement Module](#engagement-module-for_engagements)
  - [Utilities](#utilities-utils)
- [Features](#features)
  - [Influencer Management](#influencer-management)
  - [Keyword Management](#keyword-management)
  - [Automated Tweet Scraping](#automated-tweet-scraping)
  - [AI-Powered Categorization](#ai-powered-categorization)
  - [Content Summarization](#content-summarization)
  - [Automated Posting to X](#automated-posting-to-x)
  - [Daily and Weekly Reports](#daily-and-weekly-reports)
  - [Scheduler and Automation](#scheduler-and-automation)
  - [Duplication Prevention](#duplication-prevention)
  - [Multi-User Support](#multi-user-support)
  - [Auto-Recovery](#auto-recovery)
  - [Interactive Dashboard](#interactive-dashboard)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Scraping Constraints](#scraping-constraints)
  - [Time Scheduling](#time-scheduling)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Testing](#testing)
- [License](#license)

---

## System Overview

TaoWAR-AGENT is designed to automate the entire lifecycle of cryptocurrency market intelligence on X:

1. **Scrape** — Collects tweets from up to 120 tracked crypto influencers using the X API (v1.1 and v2 via Tweepy).
2. **Filter** — Uses configurable keywords (Bitcoin, Ethereum, DeFi, Web3, Crypto, Blockchain, NFT, etc.) and AI relevance scoring to separate signal from noise.
3. **Categorize** — Leverages OpenAI GPT-4o to classify each relevant tweet into predefined cryptocurrency categories.
4. **Summarize** — Generates concise, category-level summaries from the day's categorized tweets.
5. **Report** — Builds daily market intelligence reports and weekly trend analysis reports.
6. **Post** — Automatically publishes summaries and reports to X in a branded "Lady Kaede" format, complete with media attachments.
7. **Analyze** — Tracks influencer engagement metrics (followers, tweet count, likes, retweets) over time.

All of these steps run on a **time-based scheduler** with mutex-protected, per-user execution, auto-recovery for crashed processes, and duplication prevention to ensure no content is posted twice.

---

## How It Works

The system follows a daily automated pipeline:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TaoWAR-AGENT Daily Pipeline                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  2:00 AM – 9:00 AM CET (Processing Window)                             │
│  ┌──────────────────────────────────────────────────────┐               │
│  │ 1. Fetch tweets from influencers (up to 48/day)      │               │
│  │ 2. Filter tweets by keywords and AI relevance        │               │
│  │ 3. Categorize tweets using GPT-4o                    │               │
│  │ 4. Generate per-category summaries                   │               │
│  │ 5. Build daily market report                         │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                         │
│  3:00 PM+ CET (Posting Window)                                          │
│  ┌──────────────────────────────────────────────────────┐               │
│  │ 6. Post category summaries to X                      │               │
│  │ 7. Post daily report to X                            │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                         │
│  Wednesday 9:00 – 11:00 AM CET (Weekly Window)                          │
│  ┌──────────────────────────────────────────────────────┐               │
│  │ 8. Generate and post weekly trend report              │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                         │
│  Continuous: Scheduler checks every 15 min, mutex-protected             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture

The codebase is organized into well-defined modules:

### Core Module (`core/`)

| File | Description |
|------|-------------|
| `scraper.py` | Fetches tweets from the X API using Tweepy v2. Retrieves user info, extracts engagement metrics (likes, retweets, replies, quotes), hashtags, and context annotations. |
| `responder.py` | Uses OpenAI GPT-4o to identify the most relevant tweets based on keywords and generates AI-powered responses in configurable tones (Tactical & Strategic, Sharp & Witty, etc.). |
| `database.py` | Legacy database operations (deprecated, mostly commented out). |

### Database Module (`database/`)

| File | Description |
|------|-------------|
| `connection.py` | Manages the SQLite database connection. |
| `schema.py` | Defines and creates all database tables: users, influencers, posts (raw, selected, garbage), keywords, categories, categorized posts, category summaries, API usage, scheduler state, daily state, duplication prevention, and more. |
| `api_usage.py` | Tracks API call counts to stay within the monthly X API limit (12,000 calls/month). |
| `users.py` | User authentication and account management. |

### Services Module (`services/`)

The services layer contains the core business logic of the system (17 files):

| File | Description |
|------|-------------|
| `influencer_service.py` | Add, delete, list, and manage tracked influencers. |
| `keyword_service.py` | Add, remove, and list keywords used for tweet filtering. |
| `post_service.py` | Store and retrieve tweets (relevant, garbage, all). |
| `category_service.py` | Manage tweet categories. |
| `categorized_post_service.py` | Store and retrieve categorized tweets. |
| `categorized_summary_service.py` | Store and retrieve per-category summaries. |
| `scheduler_service.py` | Core scheduling logic. |
| `scheduler_state_service.py` | Tracks scheduler state transitions (IDLE → FETCHING_TWEETS → CATEGORIZING → SUMMARIZING → POSTING). |
| `scheduler_mutex_service.py` | Database + file-based mutex for cross-process and cross-thread scheduler synchronization. Ensures only one scheduler runs per user. |
| `scheduler_health_service.py` | Monitors scheduler health and detects stuck/crashed processes. |
| `daily_state_service.py` | Tracks the daily processing state (which influencers have been processed, current batch progress). |
| `duplication_prevention_service.py` | Prevents duplicate posts and reports from being sent to X. Tracks daily post counts, processed influencers, and sent reports. |
| `daily_report_functions.py` | Logic for generating daily market intelligence reports. |
| `weekly_report_functions.py` | Logic for generating weekly trend analysis reports. |
| `x_post_log_service.py` | Logs every post sent to X for auditing. |
| `websocket_service.py` | WebSocket support for real-time UI updates. |
| `send_weekly_report.py` | Handles weekly report delivery to X. |

### AI Pipelines (`ai_pipelines/`)

These modules handle all AI-powered content generation using OpenAI GPT-4o:

| File | Description |
|------|-------------|
| `categorize.py` | Classifies tweets into predefined crypto categories (Bitcoin, Ethereum, DeFi, Web3, NFT, etc.). |
| `summarize.py` | Generates concise summaries from groups of categorized tweets. |
| `title_generator.py` | Generates engaging titles for reports and posts. |
| `header_generator.py` | Generates section headers for reports. |
| `daily_report_maker.py` | Builds complete daily market intelligence reports from categorized data. |
| `weekly_report_maker.py` | Builds comprehensive weekly trend analysis reports. |
| `lady_kaedes_post.py` | Formats posts in the branded "Lady Kaede" style for publishing to X. |
| `daily_lady_kaede_report.py` | Generates daily Lady Kaede–formatted reports. |
| `rephrase_weekly_post.py` | Rephrases content for variety to avoid repetitive posts. |

### AI Prompts (`ai_prompts/`)

| File | Description |
|------|-------------|
| `prompts_giver.py` | Central prompt manager that provides system prompts for all AI pipeline stages. |
| `daily_report_prompt.py` | Template prompts for daily report generation. |

### Scripts (Scheduler) (`scripts/`)

| File | Description |
|------|-------------|
| `main_scheduler.py` | The main scheduler loop. Processes up to 48 influencers per day, orchestrates the full pipeline (scrape → categorize → summarize → post), uses mutex-based locking, and checks the schedule every 15 minutes. |
| `scheduler.py` | Scheduler helper utilities. |
| `auth.py` | User authentication for scheduled tasks. |
| `post_categorization_and_summarization.py` | Batch categorization and summarization pipeline — processes all fetched tweets through GPT-4o. |
| `post_daily_report.py` | Generates the daily market report. |
| `post_daily_summary_to_x.py` | Posts category summaries to X with media attachments. |
| `post_weekly_report.py` | Generates and posts the weekly trend report. |
| `user_analyzer.py` | Analyzes user influencer data and engagement patterns. |
| `analyze_all_influencers.py` | Runs analysis across all tracked influencers. |

### Engagement Module (`for_engagements/`)

| File | Description |
|------|-------------|
| `influencer_metrics.py` | Fetches and tracks influencer profile metrics (followers, tweet count, listed count). |
| `engagement_analysis.py` | Analyzes engagement patterns across influencers. |
| `twitter_client.py` | Twitter/X client utilities. |
| `main.py` | Main engagement analysis entry point. |
| `logger.py` | Logging for engagement operations. |

### Utilities (`utils/`)

| File | Description |
|------|-------------|
| `logger.py` | Centralized logging configuration used across the system. |
| `get_influcener_list.py` | Retrieves the current list of tracked influencers. |

---

## Features

### Influencer Management
- Add new influencers by their X (Twitter) username.
- View, delete, and manage the influencer list.
- Track up to **120 influencers per month** with automatic batch rotation.
- Store influencer profile metrics (followers, following, tweet count, bio, avatar).

### Keyword Management
- Add and remove keywords used for filtering relevant tweets.
- Default crypto keywords: Bitcoin, Ethereum, DeFi, Web3, Crypto, Blockchain, NFT.
- Keywords are dynamically updatable through the UI.

### Automated Tweet Scraping
- Fetches tweets from tracked influencers using the X API v2 (via Tweepy).
- Extracts full tweet metadata: text, engagement metrics (likes, retweets, replies, quotes), hashtags, and context annotations.
- Processes up to **48 influencers per day** in batches.
- Each influencer is scraped up to **2 times per day** with **10 tweets per scrape**.
- API usage is tracked to stay within the monthly limit of **12,000 API calls**.

### AI-Powered Categorization
- Every scraped tweet is sent to **OpenAI GPT-4o** for relevance scoring and categorization.
- Tweets are classified into predefined categories (e.g., Bitcoin, Ethereum, DeFi, Web3, NFT, Layer 2, Regulation, Market Analysis).
- Irrelevant tweets are stored separately as "garbage" for auditing.

### Content Summarization
- Categorized tweets are grouped and summarized into concise, category-level summaries.
- Summaries are generated by GPT-4o with customizable prompts.
- Each summary captures the key insights and trends from the day's tweets within that category.

### Automated Posting to X
- Summaries and reports are automatically posted to X via the Tweepy v2 client.
- Posts are formatted in the branded **"Lady Kaede"** style with a consistent voice and tone.
- Media attachments (brand image) are uploaded via the X API v1.1 and attached to each post.
- Post logs are maintained for auditing and duplication prevention.

### Daily and Weekly Reports
- **Daily Reports**: Generated each day from categorized tweets, providing a market intelligence overview covering all active categories.
- **Weekly Reports**: Generated every Wednesday, providing trend analysis and market movement summaries for the entire week.
- Reports are auto-posted to X and can also be viewed in the dashboard.

### Scheduler and Automation
- A fully automated scheduler runs the entire pipeline without manual intervention.
- **Processing window**: 2:00 AM – 9:00 AM CET (scraping, categorization, summarization).
- **Posting window**: 3:00 PM+ CET (posting summaries and reports to X).
- **Weekly window**: Wednesday 9:00 – 11:00 AM CET (weekly report generation and posting).
- The scheduler checks for pending work every **15 minutes**.

### Duplication Prevention
- The system tracks every post sent to X and every report generated.
- Before posting, it checks whether the same content has already been published.
- Prevents duplicate summaries, duplicate daily reports, and duplicate weekly reports.
- Tracks per-influencer processing status to avoid re-scraping within the same day.

### Multi-User Support
- Multiple users can run independent schedulers simultaneously.
- Each user has their own scheduler instance with **mutex-based locking** (database + file-based).
- User authentication is built in for access control.

### Auto-Recovery
- The system automatically detects and recovers from crashed or stuck schedulers.
- Health checks monitor scheduler state transitions and restart stalled processes.
- Detailed recovery guides are provided in `AUTO_RECOVERY_GUIDE.md`.

### Interactive Dashboard
- Built with **Streamlit** for a responsive, interactive web UI.
- Dashboard shows key metrics: influencer count, keyword count, scheduler status.
- Card-style UI for influencer selection with hover effects.
- Expandable sections to view raw and filtered tweets.
- Real-time scheduler state display.

---

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# X (Twitter) API Credentials
X_API_BEARER_TOKEN=your_bearer_token
X_CONSUMER_KEY=your_consumer_key
X_CONSUMER_SECRET=your_consumer_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key
```

### Scraping Constraints

These are configured in `config.py`:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `MAX_INFLUENCERS` | 120 | Maximum influencers tracked per month |
| `TWEETS_PER_SCRAPE` | 10 | Number of tweets fetched per influencer per scrape |
| `DAILY_SCRAPES_PER_INFLUENCER` | 2 | How many times each influencer is scraped per day |
| `SKIP_SCRAPE_PERCENTAGE` | 10% | Percentage of influencers with one scrape skipped daily |
| `API_LIMIT` | 12,000 | Monthly X API call limit |
| `BATCH_SWITCH_INTERVAL_DAYS` | 30 | Days before rotating the influencer batch |

### Time Scheduling

| Window | Time (CET) | Activity |
|--------|------------|----------|
| Processing | 2:00 AM – 9:00 AM | Scraping, categorization, summarization |
| Posting | 3:00 PM onwards | Post summaries and reports to X |
| Weekly Report | Wednesday 9:00 – 11:00 AM | Generate and post weekly report |

---

## Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/Mustafa-Shoukat1/TaoWAR-AGENT.git
    cd TaoWAR-AGENT
    ```

2. **Set up a virtual environment** (recommended):

    ```bash
    python3 -m venv venv
    source venv/bin/activate   # For Windows: venv\Scripts\activate
    ```

3. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Create your `.env` file** with the required API keys (see [Configuration](#configuration)).

5. **Initialize the database**:

    ```bash
    python bootstrap.py
    ```

6. **Run the Streamlit app**:

    ```bash
    streamlit run app.py
    ```

7. Open your browser and navigate to the URL shown in the terminal (typically `http://localhost:8501`).

---

## Usage

1. **Dashboard**: View key metrics — number of influencers, active keywords, and scheduler status.

2. **Manage Influencers**:
   - Add a new influencer by entering their X username.
   - Delete existing influencers from the system.
   - View influencer profile metrics and engagement data.

3. **Manage Keywords**:
   - Add new keywords for tweet filtering.
   - Remove keywords that are no longer relevant.

4. **Trigger Scraping**:
   - Select influencers from the interactive card UI.
   - Trigger scraping to gather relevant tweets.
   - View both raw and AI-filtered tweets in expandable sections.

5. **Scheduler**:
   - Start the automated scheduler from the UI.
   - Monitor scheduler state (IDLE, FETCHING_TWEETS, CATEGORIZING, SUMMARIZING, POSTING).
   - The scheduler runs the full pipeline automatically based on configured time windows.

6. **Reports**:
   - View daily and weekly market intelligence reports.
   - Reports are auto-generated and auto-posted to X on schedule.

---

## Project Structure

```
TaoWAR-AGENT/
├── app.py                  # Main Streamlit web application
├── bootstrap.py            # Database initialization
├── config.py               # Configuration and API credentials
├── requirements.txt        # Python dependencies
├── .env                    # API keys (not committed)
│
├── core/                   # Core scraping and AI response logic
├── database/               # Database connection, schema, and queries
├── services/               # Business logic services (17 modules)
├── ai_pipelines/           # AI-powered content generation pipelines
├── ai_prompts/             # System prompts for AI models
├── scripts/                # Scheduler and automated pipeline scripts
├── for_engagements/        # Influencer engagement analysis
├── utils/                  # Logging and utility functions
├── assets/                 # Static assets (brand images)
├── locks/                  # File-based scheduler locks
├── debug_reports/          # Debug output
│
├── test_*.py               # Test files
├── AUTO_RECOVERY_GUIDE.md  # Scheduler recovery documentation
├── ROOT_CAUSE_ANALYSIS.md  # Issue analysis documentation
├── SCHEDULER_FIX_SUMMARY.md # Scheduler fix documentation
└── TESTING_GUIDE.md        # Testing documentation
```

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| **Python** | Primary programming language for the entire system. |
| **Streamlit** | Web application framework for the interactive dashboard. |
| **OpenAI GPT-4o** | AI model for tweet categorization, summarization, report generation, and content formatting. |
| **Tweepy** | Python library for accessing the X (Twitter) API v1.1 and v2. |
| **SQLite** | Lightweight database for storing influencers, tweets, categories, summaries, scheduler state, and more. |
| **python-dotenv** | Loads environment variables from `.env` files. |
| **Matplotlib** | Data visualization in the dashboard. |
| **Requests** | HTTP client for API calls. |

---

## Testing

The project includes test files for key system components:

| Test File | What It Tests |
|-----------|---------------|
| `test_runner.py` | Main test runner for executing all tests. |
| `test_auto_recovery.py` | Scheduler auto-recovery mechanism. |
| `test_scheduler_simulation.py` | Simulates scheduler behavior and state transitions. |
| `test_mutex.py` | Mutex locking and unlocking for concurrent safety. |
| `test_multi_user.py` | Multi-user concurrent scheduler execution. |
| `test_endpoints.py` | API endpoint functionality. |
| `test_x_api_response.py` | X API response handling and parsing. |

Run tests with:

```bash
python test_runner.py
```

See `TESTING_GUIDE.md` for detailed testing instructions.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
