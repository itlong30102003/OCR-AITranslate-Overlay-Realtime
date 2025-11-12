"""Firebase History Service - Save and retrieve translation history"""

from .firebase_manager import FirebaseManager
from firebase_admin import firestore
from datetime import datetime
from typing import List, Optional


class FirebaseHistoryService:
    """Handle translation history storage in Firestore"""

    def __init__(self, user_id: str = None):
        self.db = FirebaseManager().get_firestore()
        if user_id:
            self.collection = self.db.collection('users').document(user_id).collection('translationHistory')
        else:
            # Fallback for backward compatibility
            self.collection = self.db.collection('translationHistory')

    def save_translation(self,
                         user_id: str,
                         source_text: str,
                         translated_text: str,
                         source_lang: str,
                         target_lang: str,
                         model_used: str,
                         confidence: float):
        """
        Save a translation to history

        Args:
            user_id: User ID
            source_text: Original text
            translated_text: Translated text
            source_lang: Source language code
            target_lang: Target language code
            model_used: Translation model name
            confidence: Translation confidence score (0-1)

        Returns:
            str: Document ID of saved translation
        """
        try:
            # Use subcollection under users/{user_id}/translationHistory
            user_collection = self.db.collection('users').document(user_id).collection('translationHistory')
            doc_ref = user_collection.document()
            doc_ref.set({
                'sourceText': source_text,
                'translatedText': translated_text,
                'sourceLang': source_lang,
                'targetLang': target_lang,
                'modelUsed': model_used,
                'confidence': confidence,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'favorite': False
            })

            print(f"[History] Saved: {source_text[:30]}... -> {translated_text[:30]}...")
            return doc_ref.id

        except Exception as e:
            print(f"[History] Failed to save: {e}")
            return None

    def get_user_history(self,
                         user_id: str,
                         limit: int = 50,
                         offset: int = 0) -> List[dict]:
        """
        Get translation history for a user

        Args:
            user_id: User ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List[dict]: List of translation records
        """
        try:
            # Use subcollection under users/{user_id}/translationHistory
            user_collection = self.db.collection('users').document(user_id).collection('translationHistory')
            query = (user_collection
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)
                    .limit(limit)
                    .offset(offset))

            docs = query.stream()

            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id

                # Convert Firestore timestamp to datetime
                if 'timestamp' in data and data['timestamp']:
                    data['timestamp'] = data['timestamp']
                else:
                    data['timestamp'] = datetime.now()

                results.append(data)

            print(f"[History] Retrieved {len(results)} records for user")
            return results

        except Exception as e:
            print(f"[History] Failed to retrieve: {e}")
            return []

    def search_history(self, user_id: str, search_text: str) -> List[dict]:
        """
        Search in user's translation history

        Note: Firestore doesn't support full-text search natively,
        so we fetch all and filter client-side for MVP

        Args:
            user_id: User ID
            search_text: Text to search for

        Returns:
            List[dict]: Matching translation records
        """
        all_history = self.get_user_history(user_id, limit=1000)

        search_lower = search_text.lower()
        return [
            item for item in all_history
            if search_lower in item.get('sourceText', '').lower()
            or search_lower in item.get('translatedText', '').lower()
        ]

    def toggle_favorite(self, user_id: str, history_id: str):
        """
        Toggle favorite status of a translation

        Args:
            user_id: User ID
            history_id: Document ID
        """
        try:
            user_collection = self.db.collection('users').document(user_id).collection('translationHistory')
            doc_ref = user_collection.document(history_id)
            doc = doc_ref.get()

            if doc.exists:
                current = doc.to_dict().get('favorite', False)
                doc_ref.update({'favorite': not current})
                print(f"[History] Toggled favorite: {history_id}")

        except Exception as e:
            print(f"[History] Failed to toggle favorite: {e}")

    def delete_history(self, user_id: str, history_id: str):
        """
        Delete a translation record

        Args:
            user_id: User ID
            history_id: Document ID
        """
        try:
            user_collection = self.db.collection('users').document(user_id).collection('translationHistory')
            user_collection.document(history_id).delete()
            print(f"[History] Deleted: {history_id}")

        except Exception as e:
            print(f"[History] Failed to delete: {e}")

    def clear_user_history(self, user_id: str):
        """
        Delete all history for a user

        Args:
            user_id: User ID
        """
        try:
            user_collection = self.db.collection('users').document(user_id).collection('translationHistory')
            docs = user_collection.stream()

            batch = self.db.batch()
            count = 0

            for doc in docs:
                batch.delete(doc.reference)
                count += 1

                # Firestore batch limit: 500 operations
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()

            batch.commit()
            print(f"[History] Cleared {count} records for user")

        except Exception as e:
            print(f"[History] Failed to clear history: {e}")

    def get_statistics(self, user_id: str) -> dict:
        """
        Get basic statistics for user

        Args:
            user_id: User ID

        Returns:
            dict: Statistics (total translations, languages used, etc.)
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
            print(f"[History] Failed to get statistics: {e}")
            return {'total_translations': 0, 'languages': {}, 'models': {}, 'avg_confidence': 0}
