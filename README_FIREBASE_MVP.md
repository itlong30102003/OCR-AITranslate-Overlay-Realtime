# 🚀 OCR Translator with Firebase - MVP Setup Guide

## 📋 Prerequisites

- Python 3.10 or higher
- Tesseract OCR installed
- Google account for Firebase

---

## 🔥 Step 1: Firebase Setup (15 minutes)

### 1.1. Create Firebase Project

1. Go to https://console.firebase.google.com
2. Click "Add project" or "Create a project"
3. Enter project name: `OCRTranslatorPro` (or your choice)
4. Disable Google Analytics (optional for MVP)
5. Click "Create Project"

### 1.2. Enable Authentication

1. In Firebase Console, go to **Build** → **Authentication**
2. Click "Get Started"
3. Click "Sign-in method" tab
4. Enable **Email/Password**:
   - Click on "Email/Password"
   - Toggle "Enable" to ON
   - Click "Save"

### 1.3. Enable Firestore Database

1. In Firebase Console, go to **Build** → **Firestore Database**
2. Click "Create database"
3. Choose **Start in test mode** (for MVP - allows read/write for 30 days)
4. Select your preferred location (e.g., `asia-southeast1`)
5. Click "Enable"

### 1.4. Download Service Account Key

1. Go to **Project Settings** (gear icon) → **Service accounts** tab
2. Click "Generate new private key"
3. Click "Generate key" in the popup
4. Save the downloaded JSON file as `serviceAccountKey.json`
5. **IMPORTANT:** Move this file to your project root directory
6. **NEVER commit this file to Git!**

### 1.5. Get Web API Key

1. Go to **Project Settings** → **General** tab
2. Scroll down to "Your apps" section
3. Click the **Web** icon `</>`
4. Register app (name: "OCR Translator Web")
5. Copy the `apiKey` value from the config object

---

## 📦 Step 2: Project Setup

### 2.1. Install Dependencies

```bash
# Navigate to project directory
cd OCR-AITranslate-Overlay-Realtime

# Install Python packages
pip install -r requirements.txt
```

### 2.2. Configure Environment Variables

1. Open `config.env` file
2. Add Firebase configuration at the end:

```ini
# ========== Firebase Configuration ==========
FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX
FIREBASE_AUTH_DOMAIN=ocrtranslatorpro.firebaseapp.com
FIREBASE_DATABASE_URL=
FIREBASE_STORAGE_BUCKET=ocrtranslatorpro.appspot.com

# Replace with your actual values:
# - FIREBASE_API_KEY: From Project Settings → General → Web API Key
# - FIREBASE_AUTH_DOMAIN: your-project-id.firebaseapp.com
# - FIREBASE_STORAGE_BUCKET: your-project-id.appspot.com
```

**Example:**
```ini
FIREBASE_API_KEY=AIzaSyDEMOKEY123456789
FIREBASE_AUTH_DOMAIN=ocrtranslatorpro.firebaseapp.com
FIREBASE_DATABASE_URL=
FIREBASE_STORAGE_BUCKET=ocrtranslatorpro.appspot.com
```

### 2.3. Verify Firebase Setup

```bash
# Test Firebase connection
python -c "from firebase.firebase_manager import FirebaseManager; print('✅ Firebase OK' if FirebaseManager.is_available() else '❌ Firebase Error')"
```

---

## 🎮 Step 3: Run the Application

### 3.1. Start the App

```bash
python main_with_ui.py
```

### 3.2. First Time Usage

1. **Registration:**
   - Click "Create Account"
   - Enter email and password (min 6 characters)
   - Click "Register"
   - Account will be created in Firebase

2. **Login:**
   - Enter your email and password
   - Click "Login"
   - Session will be saved (auto-login next time)

3. **Start OCR:**
   - Click "🚀 Bắt đầu OCR & Translation"
   - Select screen region to translate
   - Translations will be saved to Firebase automatically

4. **View History:**
   - Click "📜 Lịch sử" tab
   - See all your saved translations
   - Export to CSV, search, or delete items

---

## 📂 Project Structure

```
OCR-AITranslate-Overlay-Realtime/
├── main_with_ui.py              ✨ NEW - Main entry with UI
├── config.env                   ✨ UPDATED - Add Firebase config
├── serviceAccountKey.json       ⚠️ SECRET - Don't commit!
├── .session                     ⚠️ AUTO-GENERATED - User session
│
├── firebase/                    ✨ NEW
│   ├── firebase_manager.py      - Firebase connection
│   ├── auth_service.py          - Login/Register
│   └── history_service.py       - Save/Load history
│
├── ui/                          ✨ NEW
│   ├── login_window.py          - Login/Register UI
│   ├── main_window.py           - Main app window
│   └── tabs/
│       └── history_tab.py       - History display
│
├── services/
│   └── async_processing_service.py  ✨ UPDATED - History integration
│
└── (existing folders unchanged)
```

---

## 🔒 Security Notes

### Files to NEVER commit to Git:

```gitignore
# Add to .gitignore
serviceAccountKey.json
.session
config.env
*.pyc
__pycache__/
```

### Firebase Security Rules (Test Mode)

**Current (Test Mode - Expires in 30 days):**
```javascript
// Allows all read/write for 30 days
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.time < timestamp.date(2025, 12, 7);
    }
  }
}
```

**Production Rules (TODO - After MVP):**
```javascript
// Only allow users to access their own data
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth.uid == userId;
    }
    match /translationHistory/{docId} {
      allow create: if request.auth != null;
      allow read, delete: if request.auth.uid == resource.data.userId;
    }
  }
}
```

---

## 🧪 Testing the Integration

### Test 1: Authentication
```bash
python main_with_ui.py
# Should show login window
# Register a new account
# Login should work
```

### Test 2: OCR + History
1. Login to app
2. Click "Bắt đầu OCR"
3. Select screen region with text
4. Wait for translation
5. Go to "Lịch sử" tab
6. **Verify:** Translation appears in history

### Test 3: History Features
1. Search for text in history
2. Export history to CSV
3. Delete a single item
4. Logout and login again
5. **Verify:** History persists

---

## 🐛 Troubleshooting

### Error: "Firebase not available"
- Check `serviceAccountKey.json` is in project root
- Verify `config.env` has correct Firebase config
- Run: `pip install firebase-admin Pyrebase4 python-dotenv`

### Error: "EMAIL_EXISTS"
- Email already registered
- Try different email or use "Forgot Password"

### Error: "INVALID_PASSWORD"
- Wrong password
- Password must be at least 6 characters

### Error: "Permission denied" (Firestore)
- Check Firestore security rules
- Ensure "Test mode" is enabled
- Verify expiration date hasn't passed

### History not saving
- Check console for errors
- Verify user is logged in (check `.session` file exists)
- Check Firebase Console → Firestore Database for data

---

## 📊 Firebase Console - Verify Data

### Check Users
1. Go to Firebase Console
2. **Authentication** → **Users** tab
3. Should see registered users

### Check History
1. Go to Firebase Console
2. **Firestore Database** → **Data** tab
3. Click `translationHistory` collection
4. Should see translation documents

---

## 🎯 What Works in MVP

✅ User registration and login
✅ Session persistence (auto-login)
✅ OCR + Translation (existing functionality)
✅ Automatic history saving to Firebase
✅ View history in UI
✅ Search history
✅ Export history to CSV
✅ Delete history items

## 🚧 TODO for Production

❌ Firebase security rules (production mode)
❌ Email verification
❌ Password reset
❌ User profile editing
❌ Settings sync to Firebase
❌ Screenshot storage (Cloud Storage)
❌ Pagination for large history
❌ PyInstaller executable
❌ Auto-update mechanism

---

## 💡 Next Steps

After MVP works, you can:

1. **Update Firebase Rules:** Set production security rules
2. **Add Features:** Settings sync, profile editing
3. **Package App:** Use PyInstaller to create `.exe`
4. **Deploy:** Create installer with Inno Setup

---

## 📞 Support

Issues? Check:
- Firebase Console for errors
- Console output for Python errors
- Firestore security rules
- Network connection

**Happy Translating! 🚀**
