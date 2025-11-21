# 🔐 Environment Variables Setup Guide

This guide shows you how to properly configure API keys and secrets without committing them to git.

---

## 🚨 Security First

**NEVER commit files containing real API keys to git!**

Files that should NEVER be committed:
- ✅ `config.env` (in .gitignore)
- ✅ `serviceAccountKey.json` (in .gitignore)
- ✅ `.session` (in .gitignore)

Files that SHOULD be committed:
- ✅ `config.env.example` (template only)
- ✅ `setup_env.ps1` / `setup_env.bat` (setup scripts)

---

## 📦 Quick Start (Recommended)

### Option 1: Using PowerShell Script (Recommended)

1. **Copy template to config.env:**
   ```powershell
   Copy-Item config.env.example config.env
   ```

2. **Edit config.env with your real API keys:**
   ```powershell
   notepad config.env
   ```

3. **Run setup script:**
   ```powershell
   .\setup_env.ps1
   ```

4. **Restart your terminal/IDE** for changes to take effect

5. **Verify:**
   ```powershell
   echo $env:GEMINI_API_KEY
   ```

### Option 2: Manual Setup (All methods)

Choose ONE of the following methods:

---

## 🛠️ Method 1: Local .env File (Development - Easiest)

**Best for:** Local development, quick testing

**Pros:**
- Easy to setup
- Works immediately (no restart needed)
- Good for multiple projects

**Cons:**
- Only works when app loads config.env
- Must never commit config.env

**Steps:**

1. Copy template:
   ```bash
   copy config.env.example config.env
   ```

2. Edit `config.env` with real values:
   ```env
   GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXX
   FIREBASE_API_KEY=AIzaSyYYYYYYYYYYYYYYYYYYYYYYYY
   FIREBASE_AUTH_DOMAIN=myproject.firebaseapp.com
   FIREBASE_STORAGE_BUCKET=myproject.firebasestorage.app
   ```

3. **Verify it's in .gitignore:**
   ```bash
   git check-ignore config.env
   # Should output: config.env
   ```

4. Run the app - it will automatically load from `config.env`

---

## 🛠️ Method 2: System Environment Variables (Production - Recommended)

**Best for:** Production deployment, shared machines, CI/CD

**Pros:**
- Most secure
- Works system-wide
- No file to manage

**Cons:**
- Requires admin/restart
- More steps to setup

### Windows GUI Method:

1. **Open Environment Variables:**
   - Press `Win + R`
   - Type: `sysdm.cpl` → Enter
   - Click "Advanced" tab
   - Click "Environment Variables"

2. **Add User Variables:**
   - Click "New" under "User variables"
   - Variable name: `GEMINI_API_KEY`
   - Variable value: `your_actual_api_key`
   - Click OK
   - Repeat for all variables

3. **Restart terminal/IDE**

4. **Verify:**
   ```cmd
   echo %GEMINI_API_KEY%
   ```

### Windows Command Line (CMD):

```cmd
setx GEMINI_API_KEY "your_actual_api_key"
setx FIREBASE_API_KEY "your_actual_api_key"
setx FIREBASE_AUTH_DOMAIN "myproject.firebaseapp.com"
setx FIREBASE_STORAGE_BUCKET "myproject.firebasestorage.app"
```

**Note:** Restart terminal after running `setx`

### PowerShell:

```powershell
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your_actual_api_key", "User")
[System.Environment]::SetEnvironmentVariable("FIREBASE_API_KEY", "your_actual_api_key", "User")
[System.Environment]::SetEnvironmentVariable("FIREBASE_AUTH_DOMAIN", "myproject.firebaseapp.com", "User")
[System.Environment]::SetEnvironmentVariable("FIREBASE_STORAGE_BUCKET", "myproject.firebasestorage.app", "User")
```

---

## 🛠️ Method 3: Session Environment Variables (Temporary)

**Best for:** Testing, one-time runs

**Pros:**
- No permanent changes
- Quick testing

**Cons:**
- Only works in current terminal session
- Lost when terminal closes

### CMD:

```cmd
set GEMINI_API_KEY=your_actual_api_key
set FIREBASE_API_KEY=your_actual_api_key
python main_with_ui.py
```

### PowerShell:

```powershell
$env:GEMINI_API_KEY="your_actual_api_key"
$env:FIREBASE_API_KEY="your_actual_api_key"
python main_with_ui.py
```

---

## 🛠️ Method 4: Using python-dotenv (Alternative)

If you want to use `.env` files with python-dotenv (currently using custom parser):

1. **Install python-dotenv** (already in requirements.txt):
   ```bash
   pip install python-dotenv
   ```

2. **Create `.env` file** (not `config.env`):
   ```env
   GEMINI_API_KEY=your_actual_api_key
   FIREBASE_API_KEY=your_actual_api_key
   ```

3. **Code already loads from config.env** via `load_dotenv('config.env')` in [firebase_manager.py:26](c:\Users\ADMIN\MyProject\OCR-AITranslate-Overlay-Realtime\firebase\firebase_manager.py#L26)

---

## 🔍 Verify Setup

Run this Python script to check:

```python
import os
from dotenv import load_dotenv

load_dotenv('config.env')

print("Environment Variables Check:")
print("=" * 50)
print(f"GEMINI_API_KEY: {'✓ Set' if os.getenv('GEMINI_API_KEY') else '✗ Missing'}")
print(f"FIREBASE_API_KEY: {'✓ Set' if os.getenv('FIREBASE_API_KEY') else '✗ Missing'}")
print(f"FIREBASE_AUTH_DOMAIN: {os.getenv('FIREBASE_AUTH_DOMAIN', 'Not set')}")
print(f"FIREBASE_STORAGE_BUCKET: {os.getenv('FIREBASE_STORAGE_BUCKET', 'Not set')}")
print("=" * 50)
```

Or use the provided verification script:

```bash
python verify_env.py
```

---

## 📚 Environment Variables Reference

### Required Variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSyXXXXX...` |
| `FIREBASE_API_KEY` | Firebase Web API key | `AIzaSyYYYYY...` |
| `FIREBASE_AUTH_DOMAIN` | Firebase auth domain | `myapp.firebaseapp.com` |
| `FIREBASE_STORAGE_BUCKET` | Firebase storage bucket | `myapp.firebasestorage.app` |

### Optional Variables (with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `NLLB_MODEL_SIZE` | `600M` | NLLB model size |
| `DEFAULT_TARGET_LANG` | `vi` | Default translation target |
| `MIN_CONFIDENCE` | `0.7` | OCR confidence threshold |
| `USE_GPU` | `true` | Enable GPU acceleration |
| `CACHE_SIZE` | `1000` | Translation cache size |
| `OVERLAY_DISPLAY` | `positioned` | Overlay mode |
| `SCAN_MODE` | `snapshot` | Scan mode |

---

## 🔒 Getting API Keys

### Google Gemini API Key:

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Get API Key"
3. Create new project or use existing
4. Copy the API key

### Firebase Configuration:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Click ⚙️ Settings → Project settings
4. Scroll to "Your apps" section
5. Copy:
   - Web API Key → `FIREBASE_API_KEY`
   - Auth Domain → `FIREBASE_AUTH_DOMAIN`
   - Storage Bucket → `FIREBASE_STORAGE_BUCKET`

### Firebase Service Account:

1. Firebase Console → ⚙️ Settings → Service accounts
2. Click "Generate new private key"
3. Save as `serviceAccountKey.json` in project root
4. **Never commit this file!** (already in .gitignore)

---

## 🚫 What NOT to Do

❌ **DON'T** commit config.env with real keys:
```bash
git add config.env  # NEVER DO THIS!
```

❌ **DON'T** hardcode API keys in Python files:
```python
api_key = "AIzaSyXXXXX"  # NEVER DO THIS!
```

❌ **DON'T** share API keys in Slack/Discord/Email

✅ **DO** use environment variables

✅ **DO** commit config.env.example (template only)

✅ **DO** add config.env to .gitignore (already done)

---

## 🔄 Migration from Hardcoded Keys

If you already have hardcoded keys in config.env:

1. **Rotate API keys** (generate new ones):
   - [Gemini API](https://makersuite.google.com/app/apikey) - delete old key, create new
   - [Firebase Console](https://console.firebase.google.com/) → Settings → Regenerate keys

2. **Remove from git history** (if committed):
   ```bash
   # Install git-filter-repo
   pip install git-filter-repo

   # Remove file from history
   git filter-repo --path config.env --invert-paths

   # Force push (CAUTION!)
   git push origin --force --all
   ```

3. **Update config.env with new keys** (locally only)

4. **Set environment variables** using one of the methods above

---

## 🆘 Troubleshooting

### "Firebase not available" error:

**Check:**
1. `serviceAccountKey.json` exists in project root
2. `FIREBASE_API_KEY` is set
3. `FIREBASE_AUTH_DOMAIN` is set
4. No typos in variable names (case-sensitive on Linux/Mac)

**Verify:**
```python
import os
print(os.getenv('FIREBASE_API_KEY'))  # Should print your key
```

### "Translation not available" error:

**Check:**
1. `GEMINI_API_KEY` is set
2. Key is valid (test in Google AI Studio)
3. Billing is enabled (Gemini requires paid account)

### Variables not loading:

**Check:**
1. Restart terminal/IDE after setting variables
2. Run `echo %VARIABLE_NAME%` (CMD) or `echo $env:VARIABLE_NAME` (PowerShell)
3. Check config.env has correct format (no quotes around values)
4. Verify .env parser in [translation/config.py:50-65](c:\Users\ADMIN\MyProject\OCR-AITranslate-Overlay-Realtime\translation\config.py#L50-L65)

---

## 📖 Additional Resources

- [Python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [Firebase Admin SDK Setup](https://firebase.google.com/docs/admin/setup)
- [Google AI Studio](https://makersuite.google.com/)
- [Windows Environment Variables Guide](https://docs.microsoft.com/en-us/windows/win32/procthread/environment-variables)

---

**Security Reminder:** Always treat API keys like passwords. Never share, never commit!
