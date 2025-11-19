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

            # Refresh response doesn't have localId, so add it from saved session
            if 'localId' not in user and 'userId' in session:
                user['localId'] = session['userId']

            # Add email from session if missing in refresh response
            if 'email' not in user:
                user['email'] = session.get('email', '')

            # Validate essential fields
            if not user.get('email') or not user.get('localId'):
                self._clear_session()
                return None

            self._save_session(user)
            print(f"[Auth] Session restored for: {user.get('email', 'unknown')}")
            return user
        except:
            # Token expired or invalid
            self._clear_session()
            return None

    def _save_session(self, user):
        """Save user session to file"""
        try:
            # Handle both login response (has localId) and refresh response (has userId)
            user_id = user.get('localId') or user.get('userId') or user.get('user_id')

            session_data = {
                'userId': user_id,
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

    def send_password_reset_email(self, email):
        """
        Send password reset email to user

        Args:
            email: User email address

        Returns:
            dict: Success response

        Raises:
            Exception: If email sending fails
        """
        try:
            # Firebase REST API automatically sends password reset email
            self.auth_client.send_password_reset_email(email)
            print(f"[Auth] Password reset email sent to: {email}")
            return {"success": True, "message": "Password reset email sent"}

        except Exception as e:
            error_msg = str(e)
            if "EMAIL_NOT_FOUND" in error_msg:
                raise Exception("Email không tồn tại trong hệ thống")
            elif "INVALID_EMAIL" in error_msg:
                raise Exception("Email không hợp lệ")
            else:
                raise Exception(f"Không thể gửi email: {error_msg}")
