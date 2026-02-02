import os
from services.category_service import get_all_categories
from services.categorized_post_service import fetch_grouped_by_category
from services.scheduler_state_service import update_scheduler_state, SchedulerStatus
from services.post_service import fetch_post_text
from ai_pipelines.daily_report_maker import generate_report
from ai_pipelines.daily_lady_kaede_report import generate_mega_summary
from ai_pipelines.title_generator import generate_daily_title_and_subtitle
from datetime import datetime
from utils.logger import logger
from zoneinfo import ZoneInfo  # for CET timezone
from services.daily_report_functions import (
    insert_category_summary, initiate_daily_report, update_report_md,
    mark_daily_report_sent, send_daily_report
)
from services.duplication_prevention_service import is_report_already_sent_today
import time as time_module

CET = ZoneInfo("Europe/Paris")

def strip_leading_hash(text):
    """
    Removes leading markdown heading symbols (e.g. "# ", "## ") from a string.
    """
    text = text.lstrip("# ").strip()
    text = text.lstrip("## ").strip()
    return text

def make_tweet_link(influencer: str, tweet_id: str) -> str:
    return f"https://x.com/{influencer}/status/{tweet_id}"


def run_pipeline(batch: int, is_active: bool, username: str) -> str:
    # ✅ PRECAUTIONARY CHECK: Ensure daily report hasn't been sent today
    if is_report_already_sent_today('daily'):
        logger.warning("⚠️ PRECAUTIONARY BLOCK: Daily report already sent today - aborting to prevent duplicate")
        return "Daily report already sent today"
    
    try:
        categories_raw = get_all_categories()
        logger.info(f"📦 Fetched {len(categories_raw)} categories for batch {batch}")
        categories_dict = {cat["name"]: cat["description"] for cat in categories_raw}

        categorized = fetch_grouped_by_category(batch)
        total_categories = len(categorized)
        logger.info(f"📊 Found {total_categories} total categories for batch {batch} at {datetime.now(CET).strftime('%Y-%m-%d %H:%M:%S %Z')}")

        # Filter to recognized categories only (preserving order)
        categories_to_process = [cat for cat in categorized if cat in categories_dict]
        logger.info(f"✅ {len(categories_to_process)} categories are recognized and will be summarized")

        full_report = ""

        summaries_text = ""
        all_summaries_section = ""

        # 1️⃣ Initiate the report in DB, get the report_id
        report_id = initiate_daily_report(batch)
        logger.info(f"🆕 Initiated new daily report in DB with id {report_id}")

        for report_index, category in enumerate(categories_to_process, start=1):
            
            posts = categorized[category]
            logger.info(f"🔍 Processing category '{category}' ({report_index}/{len(categories_to_process)})")

            for post in posts:
                post["text"] = fetch_post_text(post["tweet_id"])
                post["link"] = make_tweet_link(post["influencer"], post["tweet_id"])

            update_scheduler_state(
                username=username,
                is_active=is_active,
                status=SchedulerStatus.GENERATING_SUMMARIES,
                batch=batch,
                current_influencer=None,
                progress=0.8 + (report_index / len(categories_to_process)) * 0.2,
                details={
                    "message": f"Generating summary for {category}",
                    "category_index": report_index,
                    "total_categories": len(categories_to_process),
                    "post_count": len(posts),
                }
            )

            category_desc = categories_dict[category]
            time_module.sleep(4)
            summary = generate_report(category, category_desc, posts)
            summary = strip_leading_hash(summary)
            summaries_text += summary + "\n\n"
            all_summaries_section += f"## {summary}\n\n"
            # all_summaries_section += f"## {report_index}. {summary}\n\n"
            logger.info(f"📝 Summary generated for category '{category}'")

            # 2️⃣ Save each category summary immediately
            influencers = [post["influencer"] for post in posts]
            insert_category_summary(
                report_id=report_id,
                category_name=category,
                category_summary=summary,
                influencers=influencers
            )

            logger.info(f"💾 Category summary for '{category}' saved in DB.")

        # Generate Lady Kaede's Take
        lady_kaede_take = generate_mega_summary(summaries_text)
        lady_kaede_section = f"\n{lady_kaede_take}\n\n"

        # Temporary report composition for title generation
        temp_report = (
            f"{lady_kaede_section}"
            f"{all_summaries_section}"
        )

        # Generate AI title and description summary based on report content
        title_data = generate_daily_title_and_subtitle(temp_report)
        title = title_data["title"]
        description_summary = title_data["description_summary"]
        logger.info(f"🎯 Generated AI title: {title}")
        logger.info(f"🎯 Generated AI description summary: {description_summary}")

        # Final report composition
        full_report = (
            f"{lady_kaede_section}"
            f"{all_summaries_section}"
        )

        # 3️⃣ Update the full report markdown in DB
        update_report_md(report_id, full_report)
        logger.info(f"📝 Full report markdown updated in DB for report id {report_id}")

        # Save markdown for debugging (optional)
        os.makedirs("debug_reports", exist_ok=True)
        file_path = f"debug_reports/batch_{batch}_report_4o.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_report)
        logger.info(f"📄 Full report saved to {file_path}")

        # Send report, mark as sent, etc. (as before)
        try:
            # ✅ FINAL PRECAUTIONARY CHECK: Ensure daily report hasn't been sent today
            if is_report_already_sent_today('daily'):
                logger.warning("⚠️ FINAL CHECK BLOCK: Daily report already sent today - aborting send to prevent duplicate")
                return "Daily report already sent - blocked at send stage"
            
            resp = send_daily_report(
                title=title,
                content=full_report,
                generated_by="Lady Kaede",
                description_summary=description_summary
            )
            logger.info(f"✅ Report sent successfully, API response id: {resp}")
            mark_daily_report_sent(report_id)
            logger.info(f"🔔 Marked report as sent in database (id={report_id})")
        except Exception as api_err:
            logger.error(f"❌ Error sending report to endpoint: {api_err}")

        logger.info(f"🏁 Completed report generation at {datetime.now(CET).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        return full_report

    except Exception as e:
        logger.error(f"❌ Error in report pipeline: {e}", exc_info=True)
        update_scheduler_state(
            username=username,
            is_active=is_active,
            status=SchedulerStatus.ERROR,
            batch=batch,
            details={"message": "Pipeline execution failed", "error": str(e)}
        )
        return ""
