"""Firebase Authentication Service"""

import json
import os
from .firebase_manager import FirebaseManager
from firebase_admin import firestore


class FirebaseAuthService:
    """Handle user authentication with Firebase"""

    def __init__(self):
        self.manager = FirebaseManager()
        self.auth_client = self.manager.get_auth()
        self.db = self.manager.get_firestore()
        self.session_file = '.session'

    def register(self, email, password, display_name=None):
        """
        Register a new user

        Args:
            email: User email
            password: User password
            display_name: Optional display name

        Returns:
            dict: User data with token

        Raises:
            Exception: If registration fails
        """
        try:
            # Create auth user
            user = self.auth_client.create_user_with_email_and_password(email, password)

            # Create user profile in Firestore
            self.db.collection('users').document(user['localId']).set({
                'email': email,
                'displayName': display_name or email.split('@')[0],
                'createdAt': firestore.SERVER_TIMESTAMP,
                'settings': {
                    'defaultTargetLang': 'vi',
                    'overlayMode': 'positioned',
                    'subtitlePosition': 'bottom'
                }
            })

            print(f"[Auth] User registered: {email}")
            return user

        except Exception as e:
            error_msg = str(e)
            if "EMAIL_EXISTS" in error_msg:
                raise Exception("Email already exists")
            elif "WEAK_PASSWORD" in error_msg:
                raise Exception("Password should be at least 6 characters")
            else:
                raise Exception(f"Registration failed: {error_msg}")

    def login(self, email, password):
        """
        Login user

        Args:
            email: User email
            password: User password

        Returns:
            dict: User data with token

        Raises:
            Exception: If login fails
        """
        try:
            user = self.auth_client.sign_in_with_email_and_password(email, password)

            # Save session
            self._save_session(user)

            print(f"[Auth] User logged in: {email}")
            return user

        except Exception as e:
            error_msg = str(e)
            if any(err in error_msg for err in ["INVALID_PASSWORD", "EMAIL_NOT_FOUND", "INVALID_LOGIN_CREDENTIALS"]):
                raise Exception("Invalid email or password")
            else:
                raise Exception(f"Login failed: {error_msg}")

    def logout(self):
        """Logout current user"""
        self._clear_session()
        print("[Auth] User logged out")

    def get_current_user(self):
        """
        Get currently logged in user from session

        Returns:
            dict: User data if logged in, None otherwise
        """
        session = self._load_session()
        if not session:
            return None

        try:
            # Try to refresh token
            user = self.auth_client.refresh(session['refreshToken'])
            self._save_session(user)
            print(f"[Auth] Session restored for: {user['email']}")
            return user
        except:
            # Token expired or invalid
            self._clear_session()
            return None

    def _save_session(self, user):
        """Save user session to file"""
        try:
            session_data = {
                'userId': user['localId'],
                'email': user.get('email', ''),
                'idToken': user['idToken'],
                'refreshToken': user['refreshToken']
            }

            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)

        except Exception as e:
            print(f"[Auth] Failed to save session: {e}")

    def _load_session(self):
        """Load user session from file"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[Auth] Failed to load session: {e}")

        return None

    def _clear_session(self):
        """Clear user session"""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
        except Exception as e:
            print(f"[Auth] Failed to clear session: {e}")

    def is_logged_in(self):
        """Check if user is currently logged in"""
        return self.get_current_user() is not None
