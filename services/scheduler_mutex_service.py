"""
Scheduler Mutex Service - Ensures only one scheduler thread runs per user
Uses database-based locking with file-based fallback for cross-process synchronization
"""
import os
import time
import sys
import threading
import uuid
from typing import Optional
from utils.logger import logger
from database.connection import get_connection

# Windows-compatible file locking
if sys.platform == "win32":
    import msvcrt
    
    def lock_file(file_handle, exclusive=True, blocking=True):
        """Windows file locking using msvcrt"""
        flags = 0
        if not blocking:
            flags |= msvcrt.LK_NBLCK
        if exclusive:
            flags |= msvcrt.LK_LOCK
        
        try:
            msvcrt.locking(file_handle.fileno(), flags, 1)
            return True
        except IOError:
            return False
    
    def unlock_file(file_handle):
        """Windows file unlocking"""
        try:
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
        except IOError:
            pass
else:
    import fcntl
    
    def lock_file(file_handle, exclusive=True, blocking=True):
        """Unix file locking using fcntl"""
        flags = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        if not blocking:
            flags |= fcntl.LOCK_NB
        
        try:
            fcntl.flock(file_handle.fileno(), flags)
            return True
        except IOError:
            return False
    
    def unlock_file(file_handle):
        """Unix file unlocking"""
        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        except IOError:
            pass

class SchedulerMutex:
    """
    Database-based mutex to ensure only one scheduler thread runs per user
    With file-based fallback for additional safety
    """
    
    def __init__(self, username: str, lock_dir: str = "locks"):
        self.username = username
        self.lock_dir = lock_dir
        self.lock_file_path = os.path.join(lock_dir, f"scheduler_{username}.lock")
        self.lock_file_handle: Optional[object] = None
        self.instance_id = str(uuid.uuid4())
        self.process_id = os.getpid()
        
        # Create lock directory if it doesn't exist
        os.makedirs(lock_dir, exist_ok=True)
        
        # Initialize database table for locks
        self._init_lock_table()
    
    def _init_lock_table(self):
        """Initialize the scheduler locks table"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scheduler_locks (
                        username TEXT PRIMARY KEY,
                        instance_id TEXT NOT NULL,
                        process_id INTEGER NOT NULL,
                        locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        details TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize scheduler locks table: {e}")
    
    def _update_heartbeat(self):
        """Update heartbeat to show this lock is still active"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE scheduler_locks 
                    SET last_heartbeat = CURRENT_TIMESTAMP 
                    WHERE username = ? AND instance_id = ?
                """, (self.username, self.instance_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update heartbeat for {self.username}: {e}")
    
    def _is_lock_stale(self, last_heartbeat_str: str, max_age_minutes: int = 30) -> bool:
        """Check if a database lock is stale based on heartbeat"""
        try:
            from datetime import datetime, timedelta
            last_heartbeat = datetime.fromisoformat(last_heartbeat_str.replace('Z', '+00:00'))
            now = datetime.now(last_heartbeat.tzinfo) if last_heartbeat.tzinfo else datetime.now()
            return (now - last_heartbeat) > timedelta(minutes=max_age_minutes)
        except Exception:
            return True  # If we can't parse, consider it stale
    
    def acquire_lock(self, timeout: int = 5) -> bool:
        """
        Try to acquire the scheduler lock for this user using database + file
        
        Args:
            timeout: Maximum time to wait for lock acquisition
            
        Returns:
            bool: True if lock acquired, False otherwise
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # First try database lock
                if self._acquire_database_lock():
                    # Then try file lock as additional safety
                    if self._acquire_file_lock():
                        logger.info(f"🔒 Acquired scheduler lock for {self.username} (Instance: {self.instance_id})")
                        return True
                    else:
                        # Release database lock if file lock fails
                        self._release_database_lock()
                
                # Wait before retry
                time.sleep(0.5)
            
            logger.warning(f"⏰ Failed to acquire scheduler lock for {self.username} within {timeout}s")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error acquiring scheduler lock for {self.username}: {e}")
            return False
    
    def _acquire_database_lock(self) -> bool:
        """Try to acquire database lock"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if there's an existing lock
                cursor.execute("""
                    SELECT instance_id, process_id, last_heartbeat, details
                    FROM scheduler_locks 
                    WHERE username = ?
                """, (self.username,))
                
                existing_lock = cursor.fetchone()
                
                if existing_lock:
                    instance_id, process_id, last_heartbeat, details = existing_lock
                    
                    # Check if lock is stale
                    if self._is_lock_stale(last_heartbeat):
                        logger.info(f"🧹 Removing stale lock for {self.username} (Instance: {instance_id})")
                        cursor.execute("DELETE FROM scheduler_locks WHERE username = ?", (self.username,))
                    else:
                        logger.warning(f"❌ Lock already held by another instance: {instance_id} (PID: {process_id})")
                        return False
                
                # Try to create new lock
                cursor.execute("""
                    INSERT INTO scheduler_locks (username, instance_id, process_id, details)
                    VALUES (?, ?, ?, ?)
                """, (
                    self.username, 
                    self.instance_id, 
                    self.process_id,
                    f"Scheduler lock acquired at {time.strftime('%Y-%m-%d %H:%M:%S')}"
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Database lock acquisition failed for {self.username}: {e}")
            return False
    
    def _acquire_file_lock(self) -> bool:
        """Try to acquire file lock as additional safety"""
        try:
            self.lock_file_handle = open(self.lock_file_path, 'w')
            
            if lock_file(self.lock_file_handle, exclusive=True, blocking=False):
                # Write process info to lock file
                self.lock_file_handle.write(f"PID: {self.process_id}\n")
                self.lock_file_handle.write(f"User: {self.username}\n")
                self.lock_file_handle.write(f"Instance: {self.instance_id}\n")
                self.lock_file_handle.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.lock_file_handle.flush()
                return True
            else:
                self._cleanup_file_handle()
                return False
                
        except Exception as e:
            logger.error(f"File lock acquisition failed for {self.username}: {e}")
            self._cleanup_file_handle()
            return False
    
    def release_lock(self):
        """
        Release both database and file locks
        """
        try:
            # Release database lock
            self._release_database_lock()
            
            # Release file lock
            if self.lock_file_handle:
                unlock_file(self.lock_file_handle)
                self._cleanup_file_handle()
                
                # Remove lock file
                if os.path.exists(self.lock_file_path):
                    os.remove(self.lock_file_path)
                
            logger.info(f"🔓 Released scheduler lock for {self.username} (Instance: {self.instance_id})")
                
        except Exception as e:
            logger.error(f"❌ Error releasing scheduler lock for {self.username}: {e}")
            self._cleanup_file_handle()
    
    def _release_database_lock(self):
        """Release the database lock"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM scheduler_locks 
                    WHERE username = ? AND instance_id = ?
                """, (self.username, self.instance_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Database lock release failed for {self.username}: {e}")
    
    def _cleanup_file_handle(self):
        """Clean up file handle"""
        try:
            if self.lock_file_handle:
                self.lock_file_handle.close()
                self.lock_file_handle = None
        except Exception as e:
            logger.error(f"Error cleaning up lock file handle: {e}")
    
    def is_lock_held_by_other(self) -> bool:
        """
        Check if lock is currently held by another process
        
        Returns:
            bool: True if lock is held by another process
        """
        try:
            # Check database lock first
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT instance_id, last_heartbeat 
                    FROM scheduler_locks 
                    WHERE username = ? AND instance_id != ?
                """, (self.username, self.instance_id))
                
                lock_info = cursor.fetchone()
                if lock_info:
                    instance_id, last_heartbeat = lock_info
                    # If lock exists and is not stale, it's held by another process
                    if not self._is_lock_stale(last_heartbeat):
                        return True
                        
            # Also check file lock for additional verification
            if not os.path.exists(self.lock_file_path):
                return False
            
            # Try to open and lock the file briefly
            with open(self.lock_file_path, 'r') as f:
                if lock_file(f, exclusive=True, blocking=False):
                    unlock_file(f)
                    return False  # No lock held
                else:
                    return True  # Lock is held by another process
                    
        except Exception as e:
            logger.error(f"Error checking lock status: {e}")
            return False
    
    def get_lock_info(self) -> Optional[dict]:
        """
        Get information about who holds the lock
        
        Returns:
            dict: Lock holder information or None if no lock
        """
        try:
            if not os.path.exists(self.lock_file_path):
                return None
            
            # On Windows, we can't read the file while it's locked
            # So we'll try to read it, and if it fails, we'll return basic info
            try:
                with open(self.lock_file_path, 'r') as f:
                    content = f.read().strip()
                    
                # Parse lock file content
                info = {}
                for line in content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
                
                return info
            except (IOError, PermissionError):
                # File is locked, return basic info
                return {
                    "Status": "Locked",
                    "Platform": "Windows",
                    "Note": "File is actively locked"
                }
                
        except Exception as e:
            logger.error(f"Error reading lock info: {e}")
            return None
    
    def __enter__(self):
        """Context manager entry"""
        if self.acquire_lock():
            return self
        else:
            raise RuntimeError(f"Failed to acquire scheduler lock for {self.username}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release_lock()


def ensure_single_scheduler(username: str) -> SchedulerMutex:
    """
    Ensure only one scheduler thread runs for a user
    
    Args:
        username: Username to create mutex for
        
    Returns:
        SchedulerMutex: Mutex object (use as context manager)
        
    Raises:
        RuntimeError: If another scheduler is already running
    """
    mutex = SchedulerMutex(username)
    
    if mutex.is_lock_held_by_other():
        lock_info = mutex.get_lock_info()
        if lock_info:
            logger.error(f"❌ Another scheduler is already running for {username}: {lock_info}")
        else:
            logger.error(f"❌ Another scheduler is already running for {username}")
        
        raise RuntimeError(f"Another scheduler is already running for {username}")
    
    return mutex


def check_scheduler_locks() -> dict:
    """
    Check all active scheduler locks
    
    Returns:
        dict: Mapping of username to lock info
    """
    lock_dir = "locks"
    active_locks = {}
    
    if not os.path.exists(lock_dir):
        return active_locks
    
    for filename in os.listdir(lock_dir):
        if filename.startswith("scheduler_") and filename.endswith(".lock"):
            # Extract username from filename
            username = filename[10:-5]  # Remove "scheduler_" prefix and ".lock" suffix
            
            mutex = SchedulerMutex(username)
            if mutex.is_lock_held_by_other():
                lock_info = mutex.get_lock_info()
                active_locks[username] = lock_info
    
    return active_locks


def cleanup_stale_locks(max_age_hours: int = 24):
    """
    Clean up stale lock files
    
    Args:
        max_age_hours: Maximum age of lock files before considering them stale
    """
    lock_dir = "locks"
    
    if not os.path.exists(lock_dir):
        return
    
    current_time = time.time()
    cleaned_count = 0
    
    for filename in os.listdir(lock_dir):
        if filename.startswith("scheduler_") and filename.endswith(".lock"):
            lock_path = os.path.join(lock_dir, filename)
            
            try:
                # Check file age
                file_age_hours = (current_time - os.path.getmtime(lock_path)) / 3600
                
                if file_age_hours > max_age_hours:
                    # Try to remove if not actively locked
                    try:
                        with open(lock_path, 'w') as f:
                            if lock_file(f, exclusive=True, blocking=False):
                                # If we can lock it, it's stale
                                unlock_file(f)
                                # File handle will close automatically with 'with' statement
                        
                        os.remove(lock_path)
                        cleaned_count += 1
                        logger.info(f"🧹 Cleaned up stale lock file: {filename}")
                        
                    except IOError:
                        # File is actively locked, skip
                        logger.info(f"⏭️ Skipping active lock file: {filename}")
                        pass
                        
            except Exception as e:
                logger.error(f"Error processing lock file {filename}: {e}")
    
    if cleaned_count > 0:
        logger.info(f"🧹 Cleaned up {cleaned_count} stale lock files")
