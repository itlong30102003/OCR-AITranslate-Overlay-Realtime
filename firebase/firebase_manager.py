"""Firebase Manager - Singleton instance for Firebase connection"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase
from dotenv import load_dotenv


class FirebaseManager:
    """Singleton Firebase manager"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Load environment variables
        load_dotenv('config.env')

        try:
            # Initialize Firebase Admin SDK (for Firestore)
            if not firebase_admin._apps:
                cred = credentials.Certificate('serviceAccountKey.json')
                firebase_admin.initialize_app(cred)
                print("[Firebase] Admin SDK initialized")

            # Initialize Pyrebase (for Authentication)
            config = {
                "apiKey": os.getenv("FIREBASE_API_KEY"),
                "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
                "databaseURL": os.getenv("FIREBASE_DATABASE_URL", ""),
                "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")
            }

            self.firebase = pyrebase.initialize_app(config)
            self.auth_client = self.firebase.auth()

            # Firestore client
            self.db = firestore.client()

            self._initialized = True
            print("[Firebase] Manager initialized successfully")

        except Exception as e:
            print(f"[Firebase] Initialization error: {e}")
            raise

    def get_firestore(self):
        """Get Firestore client"""
        return self.db

    def get_auth(self):
        """Get Auth client"""
        return self.auth_client

    @staticmethod
    def is_available():
        """Check if Firebase is properly configured"""
        try:
            manager = FirebaseManager()
            return manager._initialized
        except:
            return False
