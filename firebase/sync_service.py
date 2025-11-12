"""Sync Service - Batch sync local SQLite history to Firestore"""

import threading
import time
import os
from datetime import datetime, timezone
from firebase.firebase_manager import FirebaseManager
from firebase_admin import firestore
from .local_history_service import LocalHistoryService


class SyncService:
    """Service for syncing local history to Firestore in batches"""

    def __init__(self, user_id: str, sync_interval: int = 300, batch_size: int = 20):  # 5 minutes default
        """
        Initialize Sync Service

        Args:
            user_id: User ID for syncing
            sync_interval: Sync interval in seconds
            batch_size: Number of records to batch before syncing
        """
        self.user_id = user_id
        self.sync_interval = sync_interval
        self.last_sync_file = "last_sync.txt"
        self.local_history = LocalHistoryService(batch_size=batch_size)
        self.firestore_db = FirebaseManager().get_firestore()
        # Note: We use subcollections under users/{user_id}/translationHistory
        # So we don't need a global collection reference

        self._running = False
        self._thread = None

        print(f"[Sync Service] Initialized for user {user_id}, interval: {sync_interval}s, batch_size: {batch_size}")

    def start(self):
        """Start the sync service in background thread"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
        print("[Sync Service] Started background sync")

    def stop(self):
        """Stop the sync service"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[Sync Service] Stopped")

    def _sync_loop(self):
        """Main sync loop with smart batching"""
        while self._running:
            try:
                # Check if batch sync should be triggered for this user
                if self.local_history.should_trigger_batch_sync(self.user_id):
                    print(f"[Sync Service] Batch sync triggered for user {self.user_id}")
                    self.sync_to_firestore()
                else:
                    batch_status = self.local_history.get_batch_status(self.user_id)
                    print(f"[Sync Service] Batch not ready for user {self.user_id} (pending: {batch_status['pending_count']}/{batch_status['batch_size']})")
            except Exception as e:
                print(f"[Sync Service] Sync error: {e}")

            # Wait for next check
            time.sleep(self.sync_interval)

    def sync_to_firestore(self):
        """Sync unsynced records and deletions to Firestore"""
        try:
            # Get last sync time
            last_sync_time = self._get_last_sync_time()

            # Get unsynced records
            unsynced_records = self.local_history.get_unsynced_records(last_sync_time)

            # Get deleted records
            deleted_records = self.local_history.get_deleted_records(last_sync_time)

            total_operations = len(unsynced_records) + len(deleted_records)

            if total_operations == 0:
                print("[Sync Service] No new records or deletions to sync")
                return

            print(f"[Sync Service] Syncing {len(unsynced_records)} records and {len(deleted_records)} deletions to Firestore")

            # Batch write to Firestore
            batch = self.firestore_db.batch()
            batch_size = 0
            max_batch_size = 500  # Firestore batch limit

            latest_timestamp = last_sync_time
            if isinstance(latest_timestamp, str):
                latest_timestamp = datetime.fromisoformat(latest_timestamp)

            # Sync new/updated records
            for record in unsynced_records:
                # Prepare Firestore document (subcollection under users/{user_id}/translationHistory)
                doc_data = {
                    'sourceText': record['sourceText'],
                    'translatedText': record['translatedText'],
                    'sourceLang': record.get('sourceLang'),
                    'targetLang': record.get('targetLang'),
                    'modelUsed': record.get('modelUsed'),
                    'confidence': record.get('confidence', 0.0),
                    'timestamp': firestore.SERVER_TIMESTAMP,  # Use server timestamp for consistency
                    'favorite': record.get('favorite', False)
                }

                # Use subcollection: users/{user_id}/translationHistory/{record_id}
                user_collection = self.firestore_db.collection('users').document(record['user_id']).collection('translationHistory')
                doc_ref = user_collection.document(record['id'])

                batch.set(doc_ref, doc_data)
                batch_size += 1

                # Update latest timestamp
                record_time = datetime.fromisoformat(record['timestamp'])
                if record_time > latest_timestamp:
                    latest_timestamp = record_time

                # Commit batch if full
                if batch_size >= max_batch_size:
                    batch.commit()
                    batch = self.firestore_db.batch()
                    batch_size = 0

            # Sync deletions
            for deleted_record in deleted_records:
                # Delete from Firestore subcollection
                user_collection = self.firestore_db.collection('users').document(deleted_record['user_id']).collection('translationHistory')
                doc_ref = user_collection.document(deleted_record['id'])

                batch.delete(doc_ref)
                batch_size += 1

                # Update latest timestamp
                deleted_time = datetime.fromisoformat(deleted_record['deleted_at'])
                if deleted_time > latest_timestamp:
                    latest_timestamp = deleted_time

                # Commit batch if full
                if batch_size >= max_batch_size:
                    batch.commit()
                    batch = self.firestore_db.batch()
                    batch_size = 0

            # Commit remaining batch
            if batch_size > 0:
                batch.commit()

            # Update last sync time
            self._set_last_sync_time(latest_timestamp.isoformat())

            # Reset batch tracking after successful sync
            self.local_history.reset_batch_tracking(self.user_id)

            print(f"[Sync Service] Successfully synced {len(unsynced_records)} records and {len(deleted_records)} deletions")

        except Exception as e:
            print(f"[Sync Service] Failed to sync: {e}")

    def _get_last_sync_time(self) -> str:
        """Get last sync timestamp from file"""
        try:
            if os.path.exists(self.last_sync_file):
                with open(self.last_sync_file, 'r') as f:
                    timestamp_str = f.read().strip()
                    if timestamp_str:
                        return timestamp_str
            # Return epoch time if no sync file exists or empty
            return datetime(1970, 1, 1, tzinfo=timezone.utc).isoformat()
        except Exception as e:
            print(f"[Sync Service] Failed to read last sync time: {e}")
            return datetime(1970, 1, 1, tzinfo=timezone.utc).isoformat()

    def _set_last_sync_time(self, timestamp: str):
        """Save last sync timestamp to file"""
        try:
            with open(self.last_sync_file, 'w') as f:
                f.write(timestamp)
        except Exception as e:
            print(f"[Sync Service] Failed to save last sync time: {e}")

    def force_sync_now(self):
        """Force immediate sync"""
        threading.Thread(target=self.sync_to_firestore, daemon=True).start()

    def get_sync_status(self) -> dict:
        """Get sync status information"""
        last_sync = self._get_last_sync_time()
        unsynced_count = len(self.local_history.get_unsynced_records(last_sync))
        batch_status = self.local_history.get_batch_status()

        return {
            'last_sync': last_sync,
            'unsynced_count': unsynced_count,
            'sync_interval': self.sync_interval,
            'running': self._running,
            'batch_status': batch_status
        }

    def sync_from_firestore(self):
        """Sync from Firestore to local SQLite (for login)"""
        try:
            # Get all records from Firestore subcollection
            user_collection = self.firestore_db.collection('users').document(self.user_id).collection('translationHistory')
            docs = user_collection.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()

            synced_count = 0
            for doc in docs:
                doc_data = doc.to_dict()
                doc_id = doc.id

                # Check if record already exists in local SQLite (avoid duplicates)
                # We can check by ID or by content, but ID is more reliable
                existing_record = None
                try:
                    # Quick check if ID exists in local DB
                    import sqlite3
                    with self.local_history._lock:
                        with sqlite3.connect(self.local_history.db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute('SELECT id FROM translation_history WHERE id = ?', (doc_id,))
                            existing_record = cursor.fetchone()
                except:
                    pass

                if not existing_record:
                    # Add to local SQLite
                    self.local_history.save_translation(
                        user_id=self.user_id,
                        source_text=doc_data.get('sourceText', ''),
                        translated_text=doc_data.get('translatedText', ''),
                        source_lang=doc_data.get('sourceLang'),
                        target_lang=doc_data.get('targetLang'),
                        model_used=doc_data.get('modelUsed'),
                        confidence=doc_data.get('confidence', 0.0)
                    )
                    synced_count += 1

            print(f"[Sync Service] Synced {synced_count} records from Firestore to local")
            return synced_count

        except Exception as e:
            print(f"[Sync Service] Failed to sync from Firestore: {e}")
            return 0
