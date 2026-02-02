#!/usr/bin/env python3
"""
Standalone script to generate summaries for posts categorized yesterday (2025-09-15) 
and save them with today's date (2025-09-16).

This script:
1. Gets all posts categorized on 2025-09-15
2. Groups them by category  
3. Generates AI summaries for each category
4. Saves summaries with today's date (2025-09-16)
"""

import sys
import os
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Dict, List
import json

# Add the project root to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules
from database.connection import get_connection
from services.category_service import get_all_categories
from services.post_service import fetch_post_text
from ai_pipelines.summarize import generate_category_summary
from services.daily_state_service import save_daily_state, get_daily_state
from utils.logger import logger

# Constants
YESTERDAY_DATE = "2025-09-15"
TODAY_DATE = "2025-09-16"
CET = ZoneInfo("Europe/Paris")


def get_categorized_posts_for_date(target_date: str) -> List[Dict]:
    """Get all categorized posts for a specific date"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT influencer, tweet_id, categories, batch_no
            FROM categorized_posts
            WHERE date = ?
            ORDER BY batch_no, influencer
        ''', (target_date,))
        
        rows = cursor.fetchall()
        posts = []
        
        for row in rows:
            influencer, tweet_id, categories_str, batch_no = row
            categories = [cat.strip() for cat in categories_str.split(",")]
            
            # Get the actual post text
            post_text = fetch_post_text(tweet_id)
            if not post_text:
                logger.warning(f"⚠️ No text found for tweet_id: {tweet_id}")
                continue
                
            posts.append({
                "influencer": influencer,
                "tweet_id": tweet_id,
                "text": post_text,
                "categories": categories,
                "batch_no": batch_no
            })
            
        logger.info(f"📊 Found {len(posts)} categorized posts for {target_date}")
        return posts
        
    except Exception as e:
        logger.error(f"❌ Error fetching categorized posts: {e}")
        return []
    finally:
        conn.close()

def group_posts_by_category(posts: List[Dict]) -> Dict[str, List[Dict]]:
    """Group posts by their categories"""
    grouped = {}
    
    for post in posts:
        for category in post["categories"]:
            if category not in grouped:
                grouped[category] = []
            
            grouped[category].append({
                "influencer": post["influencer"],
                "tweet_id": post["tweet_id"],
                "text": post["text"],
                "batch_no": post["batch_no"]
            })
    
    logger.info(f"📋 Grouped posts into {len(grouped)} categories: {list(grouped.keys())}")
    return grouped

def get_category_description(category_name: str) -> str:
    """Get category description from database"""
    categories = get_all_categories()
    for cat in categories:
        if cat["name"] == category_name:
            return cat["description"] or "No description available"
    return "No description available"

def save_category_summary_with_date(category: str, influencer_usernames: List[str], 
                                  summary: str, batch_no: int, target_date: str) -> int:
    """Save category summary with specific date"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO category_summaries (category, influencer_usernames, summary, batch_no, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            category,
            ','.join(influencer_usernames),
            summary,
            batch_no,
            target_date
        ))
        summary_id = cursor.lastrowid
        conn.commit()
        logger.info(f"✅ Saved summary for category '{category}' with ID {summary_id}")
        return summary_id
        
    except Exception as e:
        logger.error(f"❌ Error saving category summary: {e}")
        return 0
    finally:
        conn.close()

def check_existing_summaries(target_date: str) -> List[str]:
    """Check if summaries already exist for the target date"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT DISTINCT category 
            FROM category_summaries 
            WHERE date = ?
        ''', (target_date,))
        
        existing_categories = [row[0] for row in cursor.fetchall()]
        if existing_categories:
            logger.warning(f"⚠️  Found existing summaries for {target_date}: {existing_categories}")
        return existing_categories
        
    except Exception as e:
        logger.error(f"❌ Error checking existing summaries: {e}")
        return []
    finally:
        conn.close()

def update_daily_progress(date: str, username: str = "admin"):
    """Update daily progress to mark categorization_and_summarization and weekly_done as True"""
    try:
        # Get current daily state
        current_state = get_daily_state(username, date)
        
        # Update the flags
        current_state["categorization_and_summarization"] = True
        current_state["weekly_done"] = True
        current_state["date"] = date
        
        # Save updated state
        save_daily_state(username, current_state)
        
        logger.info(f"✅ Updated daily progress for {username} on {date}")
        logger.info(f"   - categorization_and_summarization: True")
        logger.info(f"   - weekly_done: True")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating daily progress: {e}")
        return False

def generate_summaries_for_yesterday():
    """Main function to generate summaries for yesterday's categorized posts"""
    
    logger.info("🚀 Starting summary generation for yesterday's posts")
    logger.info(f"📅 Source date (yesterday): {YESTERDAY_DATE}")
    logger.info(f"📅 Target date (today): {TODAY_DATE}")
    
    # Check if summaries already exist for today
    existing_summaries = check_existing_summaries(TODAY_DATE)
    if existing_summaries:
        response = input(f"❓ Summaries already exist for {TODAY_DATE}. Continue anyway? (y/N): ")
        if response.lower() != 'y':
            logger.info("🛑 Aborted by user")
            return
    
    # Get categorized posts from yesterday
    posts = get_categorized_posts_for_date(YESTERDAY_DATE)
    if not posts:
        logger.error(f"❌ No categorized posts found for {YESTERDAY_DATE}")
        return
    
    # Group posts by category
    grouped_posts = group_posts_by_category(posts)
    
    if not grouped_posts:
        logger.error("❌ No posts to process")
        return
    
    # Generate summaries for each category
    total_categories = len(grouped_posts)
    processed_categories = 0
    generated_summaries = []
    
    logger.info(f"🔄 Processing {total_categories} categories...")
    
    for category, category_posts in grouped_posts.items():
        try:
            logger.info(f"\n📝 Processing category: {category}")
            logger.info(f"   📊 Posts count: {len(category_posts)}")
            
            # Get category description
            category_description = get_category_description(category)
            
            # Get unique influencers for this category
            influencers = list(set(post["influencer"] for post in category_posts))
            logger.info(f"   👥 Influencers: {', '.join(influencers)}")
            
            # Determine batch number (use the most common batch_no from posts)
            batch_numbers = [post["batch_no"] for post in category_posts]
            batch_no = max(set(batch_numbers), key=batch_numbers.count)
            
            # Generate thread number (simple counter)
            thread_no = f"🧵{processed_categories + 1}/{total_categories}"
            
            # Prepare posts for AI summary
            posts_for_ai = [
                {
                    "influencer": post["influencer"],
                    "text": post["text"]
                }
                for post in category_posts
            ]
            
            # Generate AI summary
            logger.info(f"   🤖 Generating AI summary...")
            summary = generate_category_summary(
                category=category,
                category_desp=category_description,
                posts=posts_for_ai,
                thread_no=thread_no
            )
            
            if summary:
                # Save summary with today's date
                summary_id = save_category_summary_with_date(
                    category=category,
                    influencer_usernames=influencers,
                    summary=summary,
                    batch_no=batch_no,
                    target_date=TODAY_DATE
                )
                
                if summary_id > 0:
                    generated_summaries.append({
                        "id": summary_id,
                        "category": category,
                        "influencers": influencers,
                        "posts_count": len(category_posts),
                        "batch_no": batch_no
                    })
                    logger.info(f"   ✅ Summary generated successfully (ID: {summary_id})")
                else:
                    logger.error(f"   ❌ Failed to save summary for {category}")
            else:
                logger.error(f"   ❌ Failed to generate summary for {category}")
                
        except Exception as e:
            logger.error(f"❌ Error processing category {category}: {e}")
        
        processed_categories += 1
    
    # Final report
    logger.info(f"\n🎉 Summary Generation Complete!")
    logger.info(f"📊 Total categories processed: {processed_categories}")
    logger.info(f"✅ Summaries generated: {len(generated_summaries)}")
    logger.info(f"📅 Summaries saved with date: {TODAY_DATE}")
    
    if generated_summaries:
        logger.info("\n📋 Generated Summaries:")
        for summary in generated_summaries:
            logger.info(f"   • {summary['category']} (ID: {summary['id']}, Posts: {summary['posts_count']}, Batch: {summary['batch_no']})")
        
        # Update daily progress if summaries were successfully generated
        logger.info("\n📝 Updating daily progress...")
        if update_daily_progress(TODAY_DATE):
            logger.info("✅ Daily progress updated successfully")
        else:
            logger.error("❌ Failed to update daily progress")
    
    logger.info("\n🔍 You can check the summaries in the 'category_summaries' table")

def main():
    """Entry point"""
    print("="*60)
    print("🤖 TAOWAR X-Agent: Yesterday's Posts Summary Generator")
    print("="*60)
    
    try:
        generate_summaries_for_yesterday()
    except KeyboardInterrupt:
        logger.info("\n🛑 Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("🏁 Process completed")
    print("="*60)

if __name__ == "__main__":
    main()
