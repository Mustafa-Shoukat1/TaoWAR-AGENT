#!/usr/bin/env python3
"""
Standalone script to get summaries that are ready to be posted to X today.
Shows all unposted summaries for the current date that would be used by the 
post_daily_summary_to_x script.
"""

import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict

# Add the project root to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules
from database.connection import get_connection
from services.categorized_summary_service import fetch_unposted_summaries, get_paris_date
from utils.logger import logger

# Constants
TODAY_DATE = "2025-09-16"
CET = ZoneInfo("Europe/Paris")

def get_all_unposted_summaries_for_date(target_date: str = None) -> List[Dict]:
    """Get all unposted summaries for a specific date (regardless of batch)"""
    if target_date is None:
        target_date = get_paris_date()
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, category, summary, batch_no, influencer_usernames
            FROM category_summaries
            WHERE date = ? AND posted_flag = 0
            ORDER BY batch_no ASC, id ASC
        """, (target_date,))
        
        rows = cursor.fetchall()
        summaries = []
        
        for row in rows:
            summaries.append({
                "id": row[0],
                "category": row[1], 
                "summary": row[2],
                "batch_no": row[3],
                "influencer_usernames": row[4].split(',') if row[4] else []
            })
            
        logger.info(f"📊 Found {len(summaries)} unposted summaries for {target_date}")
        return summaries
        
    except Exception as e:
        logger.error(f"❌ Error fetching unposted summaries: {e}")
        return []
    finally:
        conn.close()

def get_batch_statistics(summaries: List[Dict]) -> Dict:
    """Get statistics about batches in the summaries"""
    if not summaries:
        return {}
    
    batch_stats = {}
    for summary in summaries:
        batch_no = summary["batch_no"]
        if batch_no not in batch_stats:
            batch_stats[batch_no] = {
                "count": 0,
                "categories": [],
                "ids": []
            }
        
        batch_stats[batch_no]["count"] += 1
        batch_stats[batch_no]["categories"].append(summary["category"])
        batch_stats[batch_no]["ids"].append(summary["id"])
    
    return batch_stats

def display_summary_preview(summary: Dict, index: int, total: int) -> None:
    """Display a formatted preview of a summary"""
    print(f"\n📝 Summary {index}/{total}")
    print(f"   🆔 ID: {summary['id']}")
    print(f"   📂 Category: {summary['category']}")
    print(f"   🔢 Batch: {summary['batch_no']}")
    print(f"   👥 Influencers: {', '.join(summary['influencer_usernames'])}")
    print(f"   📄 Content Preview:")
    
    # Show first 200 characters of summary
    content = summary['summary']
    if len(content) > 200:
        preview = content
    else:
        preview = content
    
    # Indent the content
    for line in preview.split('\n'):
        print(f"      {line}")

def show_posting_ready_summaries():
    """Main function to show summaries ready for posting"""
    
    logger.info("🚀 Getting summaries ready for posting to X")
    logger.info(f"📅 Date: {TODAY_DATE}")
    
    # Get all unposted summaries for today
    summaries = get_all_unposted_summaries_for_date(TODAY_DATE)
    
    if not summaries:
        logger.info(f"❌ No unposted summaries found for {TODAY_DATE}")
        print(f"\n❌ No summaries ready to be posted for {TODAY_DATE}")
        print("   This could mean:")
        print("   • No summaries have been generated yet")
        print("   • All summaries have already been posted (posted_flag = 1)")
        print("   • Summaries exist for different dates")
        return
    
    # Get batch statistics
    batch_stats = get_batch_statistics(summaries)
    
    # Display overview
    print(f"\n🎯 SUMMARIES READY FOR POSTING")
    print(f"📅 Date: {TODAY_DATE}")
    print(f"📊 Total unposted summaries: {len(summaries)}")
    print(f"📦 Batches involved: {len(batch_stats)}")
    
    # Display batch breakdown
    print(f"\n📦 Batch Statistics:")
    for batch_no, stats in batch_stats.items():
        print(f"   Batch {batch_no}: {stats['count']} summaries")
        print(f"      Categories: {', '.join(stats['categories'])}")
        print(f"      IDs: {stats['ids']}")
    
    # Ask user if they want to see detailed previews
    print(f"\n❓ Would you like to see detailed previews of all summaries?")
    show_details = input("   Enter 'y' for yes, anything else for no: ").lower().strip()
    
    if show_details == 'y':
        print(f"\n📋 DETAILED SUMMARY PREVIEWS:")
        print("=" * 80)
        
        for idx, summary in enumerate(summaries, 1):
            display_summary_preview(summary, idx, len(summaries))
            
            # Pause after every 3 summaries (except the last)
            if idx % 3 == 0 and idx < len(summaries):
                input(f"\n⏸️  Press Enter to continue viewing summaries...")
    
    # Show what the posting script would do
    print(f"\n🤖 POSTING SCRIPT BEHAVIOR:")
    print(f"   The 'post_daily_summary_to_x.py' script would:")
    print(f"   1. 📝 Post a header tweet")
    print(f"   2. 🧵 Create {len(summaries)} reply tweets (one per summary)")
    print(f"   3. 🎯 Post a final mega-summary tweet")
    print(f"   4. ✅ Mark all {len(summaries)} summaries as posted (posted_flag = 1)")
    
    # Show batch information for posting
    if len(batch_stats) == 1:
        batch_no = list(batch_stats.keys())[0]
        print(f"   📦 Will process batch {batch_no}")
        print(f"   💡 Use: fetch_unposted_summaries({batch_no}) to get these summaries")
    else:
        print(f"   ⚠️  Multiple batches detected: {list(batch_stats.keys())}")
        print(f"   💡 The posting script typically processes one batch at a time")
    
    logger.info("✅ Summary review completed")

def main():
    """Entry point"""
    print("=" * 80)
    print("📊 TAOWAR X-Agent: Daily Summaries Ready for Posting")
    print("=" * 80)
    
    try:
        show_posting_ready_summaries()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Process interrupted by user")
        print("\n🛑 Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("🏁 Process completed")
    print("=" * 80)

if __name__ == "__main__":
    main()
