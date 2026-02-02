#!/usr/bin/env python3
"""
Scheduler Status and Lock Cleanup Utility

This script helps diagnose and fix scheduler lock issues.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import time
from services.scheduler_mutex_service import check_scheduler_locks, cleanup_stale_locks, SchedulerMutex
from services.scheduler_state_service import get_scheduler_state, set_scheduler_state
from database.users import get_all_users
from utils.logger import logger

def main():
    print("=" * 60)
    print("🔧  SCHEDULER STATUS & LOCK CLEANUP UTILITY")
    print("=" * 60)
    
    # Check all users
    try:
        all_users = get_all_users()
        active_locks = check_scheduler_locks()
        
        print(f"📋 Found {len(all_users)} users in database")
        print(f"🔒 Found {len(active_locks)} active locks")
        print()
        
        inconsistencies = []
        
        for user in all_users:
            username = user['username']
            db_active = get_scheduler_state(username)
            lock_held = username in active_locks
            
            status_icon = "✅" if db_active == lock_held else "⚠️"
            print(f"{status_icon} {username:25} | DB: {'Active' if db_active else 'Inactive':8} | Lock: {'Held' if lock_held else 'Free':4}")
            
            # Track inconsistencies
            if db_active != lock_held:
                inconsistencies.append({
                    'username': username,
                    'db_active': db_active,
                    'lock_held': lock_held
                })
        
        if inconsistencies:
            print("\n" + "=" * 60)
            print("⚠️  INCONSISTENCIES DETECTED:")
            print("=" * 60)
            
            for issue in inconsistencies:
                username = issue['username']
                db_active = issue['db_active']
                lock_held = issue['lock_held']
                
                print(f"User: {username}")
                print(f"  Database State: {'ACTIVE' if db_active else 'INACTIVE'}")
                print(f"  Lock State: {'HELD' if lock_held else 'FREE'}")
                
                if db_active and not lock_held:
                    print("  Issue: Database says active but no lock held (needs recovery or DB cleanup)")
                elif not db_active and lock_held:
                    print("  Issue: Database says inactive but lock still held (stale lock)")
                print()
                
                # Offer fixes
                if not db_active and lock_held:
                    response = input(f"Clean stale lock for {username}? (y/n): ").strip().lower()
                    if response == 'y':
                        try:
                            mutex = SchedulerMutex(username)
                            # Try to cleanup this specific lock
                            if os.path.exists(mutex.lock_file_path):
                                os.remove(mutex.lock_file_path)
                                print(f"  ✅ Cleaned stale lock for {username}")
                            else:
                                print(f"  ❌ Lock file not found: {mutex.lock_file_path}")
                        except Exception as e:
                            print(f"  ❌ Error cleaning lock: {e}")
                
                elif db_active and not lock_held:
                    response = input(f"Set database state to inactive for {username}? (y/n): ").strip().lower()
                    if response == 'y':
                        try:
                            set_scheduler_state(username, False)
                            print(f"  ✅ Set database state to inactive for {username}")
                        except Exception as e:
                            print(f"  ❌ Error updating database: {e}")
        else:
            print("\n✅ All scheduler states are consistent!")
        
        # General cleanup option
        print("\n" + "=" * 60)
        response = input("Perform general stale lock cleanup? (y/n): ").strip().lower()
        if response == 'y':
            cleanup_stale_locks(max_age_hours=1)  # Clean locks older than 1 hour
            print("🧹 Stale lock cleanup completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
