import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from services.weekly_report_functions import (
    initiate_weekly_report, update_weekly_report_md, mark_weekly_report_sent, build_report_category_summary_dict
)
from ai_pipelines.weekly_report_maker import generate_weekly_summary  # You'll make this
from ai_pipelines.weekly_report_intro_maker import generate_intro
from ai_pipelines.weekly_report_next_maker import generate_watch_next
from ai_pipelines.title_generator import generate_weekly_title_and_subtitle
from scripts.analyze_all_influencers import analyze_all_influencers
from services.send_weekly_report import send_weekly_report
from services.duplication_prevention_service import is_report_already_sent_today
from utils.get_influcener_list import get_unique_influencers
from ai_pipelines.rephrase_weekly_post import rephrase_post
from services.scheduler_state_service import update_scheduler_state, SchedulerStatus
from config import api_key, api_secret, access_token, access_token_secret, bearer_token, client_v2_media, media
from utils.logger import logger

def cleaned_summary(text):
    """
    Removes leading markdown heading symbols (e.g. "# ", "## ") from a string.
    """
    text = text.lstrip("# ").strip()
    text = text.lstrip("## ").strip()
    return text

def get_week_range():
    """
    Returns the previous 7-day range ending yesterday (in Paris timezone).
    Example: If today is July 24, returns July 17 to July 23.
    """
    now = datetime.now(ZoneInfo("Europe/Paris"))
    end = now - timedelta(days=1)  # yesterday
    start = end - timedelta(days=6)
    return start.date().isoformat(), end.date().isoformat()

def is_weekly_run_day():
    today = datetime.now(ZoneInfo("Europe/Paris"))
    is_wednesday = today.weekday() == 2  # Monday=0 ... Wednesday=2
    return is_wednesday 

def run_weekly_pipeline(is_active: bool, username: str, weekly_img_rotator: int)  -> str | bool:
    # ✅ PRECAUTIONARY CHECK: Ensure weekly report hasn't been sent today
    if is_report_already_sent_today('weekly'):
        logger.warning("⚠️ PRECAUTIONARY BLOCK: Weekly report already sent today - aborting to prevent duplicate")
        return False
    
    # Only proceed if today is Wednesday (weekday == 2)
    if not is_weekly_run_day():
        logger.info("⏩ Weekly report pipeline is only executed on Wednesday. Exiting without action.")
        return False

    try:
        week_start, week_end = get_week_range()
        logger.info(f"🚀 Starting weekly report for {week_start} - {week_end}")

        # 1️⃣ Initiate weekly report in DB
        report_id = initiate_weekly_report(week_start, week_end)
        if report_id is None:
            logger.error("❌ Failed to initiate weekly report in DB.")
            return ""

        # 2️⃣ Get all daily summaries in the week, grouped by report & category
        weekly_data = build_report_category_summary_dict()  # {report_id: {...}, ...}

        # 3️⃣ Reorganize data and collect unique influencers
        cat_agg: dict[str, list[dict]] = {}
        for report in weekly_data.values():
            for cat, (summary, influencers) in report["categories"].items():
                cat_agg.setdefault(cat, []).append(
                    {"summary": summary, "influencers": influencers}
                )

        unique_influencers = get_unique_influencers(weekly_data)
        
        count_of_unique_inf = len(unique_influencers)
        
        below_intro = f"Total Curated Influencers: {count_of_unique_inf}"
        
        # 4️⃣ Generate dynamic introduction
        intro_paragraph = generate_intro(count_of_unique_inf, list(unique_influencers))

        # 5️⃣ Generate weekly summaries per category
        all_weekly_summaries = ""
        for idx, (cat, cat_entries) in enumerate(cat_agg.items(), start=1):
            cat_summaries = [entry["summary"] for entry in cat_entries]
            cat_influencers = [i for entry in cat_entries for i in entry["influencers"]]

            weekly_summary = generate_weekly_summary(cat, cat_summaries, cat_influencers)
            cleaned = cleaned_summary(weekly_summary)  # assume this helper exists
            all_weekly_summaries += f"## {cleaned}\n\n"

            logger.info(f"📝 Weekly summary generated for category '{cat}'")
            
        watch_next_section = generate_watch_next(all_weekly_summaries, list(unique_influencers))
        
        # 6️⃣ Assemble full markdown report
        start_dt = datetime.strptime(week_start, "%Y-%m-%d")
        end_dt   = datetime.strptime(week_end,   "%Y-%m-%d")

        # Example → "June 14–20, 2025"
        date_range_str = f"{start_dt.strftime('%B')} {start_dt.day}–{end_dt.day}, {end_dt.year}"

        # Temporary report composition for title generation
        temp_report = (
            f"{all_weekly_summaries}"
            f"## {watch_next_section}\n\n"
        )

        # Generate AI title and description summary based on report content
        title_data = generate_weekly_title_and_subtitle(temp_report)
        title = title_data["title"]
        description_summary = title_data["description_summary"]
        logger.info(f"🎯 Generated AI weekly title: {title}")
        logger.info(f"🎯 Generated AI weekly description summary: {description_summary}")

        # Final report composition
        full_report = (
            f"## Introduction \n\n ### {below_intro} \n{intro_paragraph}\n\n"
            f"{all_weekly_summaries}"
            f"## {watch_next_section}\n\n"
        )

        # 7️⃣ Persist and (optionally) send
        update_weekly_report_md(report_id, full_report)
        logger.info(f"📝 Weekly report markdown updated in DB for report id {report_id}")

        os.makedirs("debug_reports", exist_ok=True)
        file_path = f"debug_reports/weekly_{week_start}_{week_end}_report.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_report)
        logger.info(f"📄 Weekly report saved to {file_path}")
        
        inf_rank_data = analyze_all_influencers()
        
        influencer_stats = [
            {
                "rank": inf.get("rank"),
                "name": inf.get("name"),
                "handle": inf.get("handle"),
                "followers": inf.get("followers"),
                "likes": inf.get("likes"),
                "retweets": inf.get("retweets"),
                "replies": inf.get("replies"),
                "quotes": inf.get("quotes"),
                "engagement_rate": inf.get("engagement_rate"),
            }
            for inf in inf_rank_data
        ]

        # 9️⃣ Send report to TaoWAR weekly endpoint
        
        payload = {
            "title": title,
            "content": full_report,
            "generatedBy": "Lady Kaede",
            "influencerStats": influencer_stats,
            "descriptionSummary": description_summary
        }
        json_path = f"debug_reports/weekly_{week_start}_{week_end}_payload.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Weekly report API payload saved to {json_path}")
        try:
            resp = send_weekly_report(
                title=title,
                content=full_report,
                generated_by="Lady Kaede",
                influencer_stats=influencer_stats,
                description_summary=description_summary
            )
            logger.info(f"✅ Weekly report sent successfully! response: {resp}")
            mark_weekly_report_sent(report_id)
            logger.info(f"🔔 Marked weekly report as sent in database (id={report_id})")
        except Exception as api_err:
            logger.error(f"❌ Error sending weekly report to endpoint: {api_err}")
            
        # Do weekly post on X
        # Get top 5 influencers
                # Do weekly post on X
        # Get top 5 influencers
        top_5_influencers = influencer_stats[:5]

        # Build the mention string
        mentions = []
        for inf in top_5_influencers:
            if inf.get("handle"):
                mentions.append(f"@{inf['handle']}")
        mentions_str = " ".join(mentions[:-1]) + f" and {mentions[-1]}" if len(mentions) > 1 else (mentions[0] if mentions else "")

        # Final post content
        post_content = (
            f"Lord Reyoku Weekly DAMI Report is out with most engagement from {mentions_str}\n\n"
            f"Full report available for $tWAR holders only at https://taowar.ai"
        )

        # Rephrase the post content
        try:
            post_content = rephrase_post(post_content, max_len=280)
            logger.info("✅ Post content rephrased successfully")
        except Exception as e:
            logger.error(f"❌ Error rephrasing post content: {e}")
            return False

        # ---- Select weekly image based on `weekly_img_rotator` ----
        # 0 -> weekly_img_1.jpg, 1 -> weekly_img_2.jpg, 2 -> weekly_img_3.jpg
        img_map = {
            1: "weekly_img_1.jpg",
            2: "weekly_img_2.jpg",
            3: "weekly_img_3.jpg",
        }
        # ensure a safe index (in case a higher int is passed)
        img_name = img_map.get(weekly_img_rotator, "weekly_img_1.jpg")

        # Assets folder is at the same hierarchy as this script's folder
        base_dir = os.path.abspath(os.path.dirname(__file__))
        assets_dir = os.path.abspath(os.path.join(base_dir, "..", "assets"))
        img_path = os.path.join(assets_dir, img_name)

        if not os.path.isfile(img_path):
            logger.error(f"❌ Weekly image not found at: {img_path}")
            return False

        # ---- Upload media (v1.1) and post tweet (v2) as an independent post ----
        try:
            import tweepy  # ensure tweepy is available here

            # OAuth1 for media upload (v1.1)
            auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
            api_v1 = tweepy.API(auth)

            uploaded = api_v1.media_upload(img_path)
            media_id = uploaded.media_id

            # ✅ FINAL PRECAUTIONARY CHECK: Ensure weekly report hasn't been sent today
            if is_report_already_sent_today('weekly'):
                logger.warning("⚠️ FINAL CHECK BLOCK: Weekly report already sent today - aborting tweet to prevent duplicate")
                return False

            # Create independent tweet (NOT a reply)
            response = client_v2_media.create_tweet(
                text=post_content,
                media_ids=[media_id],
            )

            now_cet = datetime.now(ZoneInfo("Europe/Paris")).strftime('%Y-%m-%d %H:%M:%S %Z')
            
            # Extract tweet ID safely with detailed debugging
            tweet_id = "unknown"
            try:
                if hasattr(response, 'data') and response.data:
                    if hasattr(response.data, 'get'):
                        tweet_id = response.data.get('id', 'unknown')
                    elif isinstance(response.data, dict):
                        tweet_id = response.data.get('id', 'unknown')
                    else:
                        tweet_id = response.data['id']
                else:
                    logger.warning(f"⚠️ Unexpected response structure: {type(response)}, has data: {hasattr(response, 'data')}")
            except Exception as id_error:
                logger.error(f"❌ Error extracting tweet ID: {id_error}. Response type: {type(response)}")
                tweet_id = "extraction_failed"
            
            logger.info(f"✅🐦 Posted weekly tweet at {now_cet} (CET). Tweet ID: {tweet_id}")
            logger.info(f"📢 Weekly X post content:\n{post_content}")
            
            return True  # Weekly report posted successfully

        except Exception as e:
            logger.error(f"❌ Error posting weekly tweet: {e}")
            return False
    
    except Exception as e:
        logger.error("❌ Error in weekly report pipeline:", exc_info=True)
        update_scheduler_state(
            username=username,
            is_active=is_active,
            status=SchedulerStatus.ERROR,
            batch=-1,
            details={"message": "Weekly pipeline execution failed", "error": str(e)},
        )
        return ""


