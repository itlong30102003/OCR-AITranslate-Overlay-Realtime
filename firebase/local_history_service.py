"""Local History Service - SQLite-based translation history with fast access"""

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional
import os
import threading


class LocalHistoryService:
    """Handle translation history storage in local SQLite database"""

    def __init__(self, db_path: str = "translation_history.db", batch_size: int = 20, current_user_id: str = None):
        """
        Initialize Local History Service

        Args:
            db_path: Path to SQLite database file
            batch_size: Number of records to batch before triggering sync
            current_user_id: Current user ID for user-specific operations
        """
        self.db_path = db_path
        self.batch_size = batch_size
        self.current_user_id = current_user_id
        self._init_db()
        self._lock = threading.Lock()  # Thread-safe operations

        # In-memory cache for fast access (per user)
        self._cache: Dict[str, List[Dict]] = {}
        self._cache_size = 100  # Max records per user in cache
        self._load_cache()

        # Batch sync tracking (per user)
        self._pending_sync_count: Dict[str, int] = {}
        self._last_batch_time: Dict[str, datetime] = {}
        self._batch_timeout = 600  # 10 minutes timeout for batch sync

        print(f"[Local History] Initialized with database: {db_path}, batch_size: {batch_size}, user: {current_user_id}")

    def _init_db(self):
        """Initialize SQLite database and create tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create translation_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS translation_history (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    source_lang TEXT,
                    target_lang TEXT,
                    model_used TEXT,
                    confidence REAL,
                    timestamp TEXT NOT NULL,
                    favorite INTEGER DEFAULT 0
                )
            ''')

            # Create indexes for fast queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_timestamp ON translation_history(user_id, timestamp DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON translation_history(timestamp DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON translation_history(user_id)')

            # Create deleted records table for sync tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deleted_records (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    deleted_at TEXT NOT NULL
                )
            ''')

            conn.commit()

    def _load_cache(self):
        """Load recent records into memory cache for fast access"""
        try:
            with self._lock:
                # Load last 100 records per user
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT DISTINCT user_id FROM translation_history
                    ''')

                    user_ids = [row[0] for row in cursor.fetchall()]

                    for user_id in user_ids:
                        cursor.execute('''
                            SELECT id, user_id, source_text, translated_text, source_lang,
                                   target_lang, model_used, confidence, timestamp, favorite
                            FROM translation_history
                            WHERE user_id = ?
                            ORDER BY timestamp DESC
                            LIMIT ?
                        ''', (user_id, self._cache_size))

                        records = []
                        for row in cursor.fetchall():
                            records.append({
                                'id': row[0],
                                'user_id': row[1],
                                'sourceText': row[2],
                                'translatedText': row[3],
                                'sourceLang': row[4],
                                'targetLang': row[5],
                                'modelUsed': row[6],
                                'confidence': row[7],
                                'timestamp': datetime.fromisoformat(row[8]),
                                'favorite': bool(row[9])
                            })

                        self._cache[user_id] = records

            print(f"[Local History] Cache loaded for {len(self._cache)} users")

        except Exception as e:
            print(f"[Local History] Failed to load cache: {e}")

    def _update_cache(self, user_id: str, record: Dict):
        """Update in-memory cache with new record"""
        with self._lock:
            if user_id not in self._cache:
                self._cache[user_id] = []

            # Add to beginning (most recent)
            self._cache[user_id].insert(0, record)

            # Keep only recent records
            if len(self._cache[user_id]) > self._cache_size:
                self._cache[user_id] = self._cache[user_id][:self._cache_size]

    def save_translation(self,
                         user_id: str,
                         source_text: str,
                         translated_text: str,
                         source_lang: str = None,
                         target_lang: str = None,
                         model_used: str = None,
                         confidence: float = 0.0) -> str:
        """
        Save a translation to local SQLite database

        Args:
            user_id: User ID
            source_text: Original text
            translated_text: Translated text
            source_lang: Source language code
            target_lang: Target language code
            model_used: Translation model name
            confidence: Translation confidence score (0-1)

        Returns:
            str: Record ID
        """
        record_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO translation_history
                        (id, user_id, source_text, translated_text, source_lang, target_lang, model_used, confidence, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, user_id, source_text, translated_text, source_lang, target_lang, model_used, confidence, timestamp))

                    conn.commit()

                # Update batch sync tracking for this user
                if user_id not in self._pending_sync_count:
                    self._pending_sync_count[user_id] = 0
                    self._last_batch_time[user_id] = datetime.now(timezone.utc)

                self._pending_sync_count[user_id] += 1
                self._last_batch_time[user_id] = datetime.now(timezone.utc)

            # Update cache
            record = {
                'id': record_id,
                'user_id': user_id,
                'sourceText': source_text,
                'translatedText': translated_text,
                'sourceLang': source_lang,
                'targetLang': target_lang,
                'modelUsed': model_used,
                'confidence': confidence,
                'timestamp': datetime.fromisoformat(timestamp),
                'favorite': False
            }
            self._update_cache(user_id, record)

            print(f"[Local History] Saved: {source_text[:30]}... -> {translated_text[:30]}... (pending sync: {self._pending_sync_count})")
            return record_id

        except Exception as e:
            print(f"[Local History] Failed to save: {e}")
            return None

    def get_user_history(self,
                         user_id: str,
                         limit: int = 50,
                         offset: int = 0,
                         search_text: str = None) -> List[Dict]:
        """
        Get translation history for a user

        Args:
            user_id: User ID
            limit: Maximum number of records to return
            offset: Number of records to skip
            search_text: Optional search filter

        Returns:
            List[Dict]: List of translation records
        """
        try:
            # Try cache first for recent records
            if user_id in self._cache and offset == 0 and not search_text:
                cached_records = self._cache[user_id]
                if len(cached_records) >= limit:
                    return cached_records[:limit]

            # Query database
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    if search_text:
                        # Search in source or translated text
                        search_pattern = f"%{search_text}%"
                        cursor.execute('''
                            SELECT id, user_id, source_text, translated_text, source_lang,
                                   target_lang, model_used, confidence, timestamp, favorite
                            FROM translation_history
                            WHERE user_id = ? AND (source_text LIKE ? OR translated_text LIKE ?)
                            ORDER BY timestamp DESC
                            LIMIT ? OFFSET ?
                        ''', (user_id, search_pattern, search_pattern, limit, offset))
                    else:
                        cursor.execute('''
                            SELECT id, user_id, source_text, translated_text, source_lang,
                                   target_lang, model_used, confidence, timestamp, favorite
                            FROM translation_history
                            WHERE user_id = ?
                            ORDER BY timestamp DESC
                            LIMIT ? OFFSET ?
                        ''', (user_id, limit, offset))

                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            'id': row[0],
                            'user_id': row[1],
                            'sourceText': row[2],
                            'translatedText': row[3],
                            'sourceLang': row[4],
                            'targetLang': row[5],
                            'modelUsed': row[6],
                            'confidence': row[7],
                            'timestamp': datetime.fromisoformat(row[8]),
                            'favorite': bool(row[9])
                        })

            print(f"[Local History] Retrieved {len(results)} records for user {user_id}")
            return results

        except Exception as e:
            print(f"[Local History] Failed to retrieve: {e}")
            return []

    def get_unsynced_records(self, last_sync_time: str) -> List[Dict]:
        """
        Get records that haven't been synced to Firestore yet

        Args:
            last_sync_time: ISO timestamp string

        Returns:
            List[Dict]: Unsynced records
        """
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT id, user_id, source_text, translated_text, source_lang,
                               target_lang, model_used, confidence, timestamp, favorite
                        FROM translation_history
                        WHERE timestamp > ?
                        ORDER BY timestamp ASC
                    ''', (last_sync_time,))

                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            'id': row[0],
                            'user_id': row[1],
                            'sourceText': row[2],
                            'translatedText': row[3],
                            'sourceLang': row[4],
                            'targetLang': row[5],
                            'modelUsed': row[6],
                            'confidence': row[7],
                            'timestamp': row[8],
                            'favorite': bool(row[9])
                        })

            print(f"[Local History] Found {len(results)} unsynced records")
            return results

        except Exception as e:
            print(f"[Local History] Failed to get unsynced records: {e}")
            return []

    def toggle_favorite(self, record_id: str) -> bool:
        """
        Toggle favorite status of a translation

        Args:
            record_id: Record ID

        Returns:
            bool: Success status
        """
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Get current favorite status
                    cursor.execute('SELECT favorite FROM translation_history WHERE id = ?', (record_id,))
                    row = cursor.fetchone()
                    if not row:
                        return False

                    current = bool(row[0])
                    new_status = 1 if not current else 0

                    cursor.execute('UPDATE translation_history SET favorite = ? WHERE id = ?', (new_status, record_id))
                    conn.commit()

                    # Update cache if exists
                    for user_records in self._cache.values():
                        for record in user_records:
                            if record['id'] == record_id:
                                record['favorite'] = bool(new_status)
                                break

            print(f"[Local History] Toggled favorite: {record_id}")
            return True

        except Exception as e:
            print(f"[Local History] Failed to toggle favorite: {e}")
            return False

    def delete_record(self, record_id: str, user_id: str = None) -> bool:
        """
        Delete a translation record and track deletion for sync

        Args:
            record_id: Record ID
            user_id: User ID (optional, for tracking deletions)

        Returns:
            bool: Success status
        """
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # First, get the user_id if not provided
                    if not user_id:
                        cursor.execute('SELECT user_id FROM translation_history WHERE id = ?', (record_id,))
                        row = cursor.fetchone()
                        if row:
                            user_id = row[0]

                    # Delete from main table
                    cursor.execute('DELETE FROM translation_history WHERE id = ?', (record_id,))

                    # Track deletion for sync
                    if user_id:
                        deleted_at = datetime.now(timezone.utc).isoformat()
                        cursor.execute('''
                            INSERT OR REPLACE INTO deleted_records (id, user_id, deleted_at)
                            VALUES (?, ?, ?)
                        ''', (record_id, user_id, deleted_at))

                    conn.commit()

                    # Remove from cache
                    for uid, records in self._cache.items():
                        self._cache[uid] = [r for r in records if r['id'] != record_id]

                # Update batch sync tracking for deletions too
                if user_id not in self._pending_sync_count:
                    self._pending_sync_count[user_id] = 0
                    self._last_batch_time[user_id] = datetime.now(timezone.utc)

                self._pending_sync_count[user_id] += 1
                self._last_batch_time[user_id] = datetime.now(timezone.utc)

            print(f"[Local History] Deleted: {record_id} (pending sync: {self._pending_sync_count})")
            return True

        except Exception as e:
            print(f"[Local History] Failed to delete: {e}")
            return False

    def clear_user_history(self, user_id: str) -> bool:
        """
        Delete all history for a user and track deletions for sync

        Args:
            user_id: User ID

        Returns:
            bool: Success status
        """
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Get all record IDs before deleting
                    cursor.execute('SELECT id FROM translation_history WHERE user_id = ?', (user_id,))
                    record_ids = [row[0] for row in cursor.fetchall()]

                    # Delete from main table
                    cursor.execute('DELETE FROM translation_history WHERE user_id = ?', (user_id,))
                    deleted_count = cursor.rowcount

                    # Also delete from deleted_records table to clean up
                    cursor.execute('DELETE FROM deleted_records WHERE user_id = ?', (user_id,))

                    conn.commit()

                    # Clear cache for user
                    if user_id in self._cache:
                        del self._cache[user_id]

                    # Clear batch tracking for user
                    if user_id in self._pending_sync_count:
                        del self._pending_sync_count[user_id]
                    if user_id in self._last_batch_time:
                        del self._last_batch_time[user_id]

            print(f"[Local History] Cleared {deleted_count} records for user {user_id}")
            return True

        except Exception as e:
            print(f"[Local History] Failed to clear history: {e}")
            return False

    def get_deleted_records(self, since_timestamp: str) -> List[Dict]:
        """
        Get deleted records since a timestamp for sync

        Args:
            since_timestamp: ISO timestamp string

        Returns:
            List[Dict]: Deleted records
        """
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT id, user_id, deleted_at
                        FROM deleted_records
                        WHERE deleted_at > ?
                        ORDER BY deleted_at ASC
                    ''', (since_timestamp,))

                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            'id': row[0],
                            'user_id': row[1],
                            'deleted_at': row[2]
                        })

            print(f"[Local History] Found {len(results)} deleted records to sync")
            return results

        except Exception as e:
            print(f"[Local History] Failed to get deleted records: {e}")
            return []

    def should_trigger_batch_sync(self, user_id: str = None) -> bool:
        """
        Check if batch sync should be triggered based on count or timeout

        Args:
            user_id: User ID to check (uses current_user_id if None)

        Returns:
            bool: True if sync should be triggered
        """
        target_user = user_id or self.current_user_id
        if not target_user:
            return False

        if target_user not in self._pending_sync_count:
            return False

        if self._pending_sync_count[target_user] >= self.batch_size:
            return True

        # Check timeout (10 minutes)
        time_since_last_batch = datetime.now(timezone.utc) - self._last_batch_time[target_user]
        if time_since_last_batch.total_seconds() >= self._batch_timeout:
            return True

        return False

    def reset_batch_tracking(self, user_id: str = None):
        """Reset batch sync tracking after successful sync"""
        with self._lock:
            target_user = user_id or self.current_user_id
            if target_user:
                self._pending_sync_count[target_user] = 0
                self._last_batch_time[target_user] = datetime.now(timezone.utc)

    def get_batch_status(self, user_id: str = None) -> Dict:
        """
        Get current batch sync status

        Args:
            user_id: User ID to check (uses current_user_id if None)

        Returns:
            Dict: Batch status information
        """
        target_user = user_id or self.current_user_id

        if not target_user or target_user not in self._pending_sync_count:
            return {
                'pending_count': 0,
                'batch_size': self.batch_size,
                'time_since_last_batch': 0,
                'timeout_seconds': self._batch_timeout,
                'should_sync': False
            }

        time_since_last_batch = datetime.now(timezone.utc) - self._last_batch_time[target_user]
        return {
            'pending_count': self._pending_sync_count[target_user],
            'batch_size': self.batch_size,
            'time_since_last_batch': time_since_last_batch.total_seconds(),
            'timeout_seconds': self._batch_timeout,
            'should_sync': self.should_trigger_batch_sync(target_user)
        }

    def get_statistics(self, user_id: str) -> Dict:
        """
        Get basic statistics for user

        Args:
            user_id: User ID

        Returns:
            Dict: Statistics
        """
        try:
            history = self.get_user_history(user_id, limit=1000)

            stats = {
                'total_translations': len(history),
                'languages': {},
                'models': {},
                'avg_confidence': 0
            }

            if not history:
                return stats

            # Count language pairs
            for item in history:
                lang_pair = f"{item.get('sourceLang', 'unknown')} → {item.get('targetLang', 'unknown')}"
                stats['languages'][lang_pair] = stats['languages'].get(lang_pair, 0) + 1

                # Count models
                model = item.get('modelUsed', 'unknown')
                stats['models'][model] = stats['models'].get(model, 0) + 1

            # Average confidence
            confidences = [item.get('confidence', 0) for item in history]
            stats['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0

            return stats

        except Exception as e:
            print(f"[Local History] Failed to get statistics: {e}")
            return {'total_translations': 0, 'languages': {}, 'models': {}, 'avg_confidence': 0}
