"""
Environment Variables Verification Script

This script checks if all required environment variables are properly set.
"""

import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load from config.env if exists
load_dotenv('config.env')

def check_env_var(name, required=True):
    """Check if environment variable is set"""
    value = os.getenv(name)
    if value:
        # Check if it's a placeholder value
        if "your_" in value.lower() or "your-project" in value.lower():
            return "⚠️", "Placeholder value detected"
        # Hide actual value (show first 10 chars only)
        display_value = value[:10] + "..." if len(value) > 10 else value
        return "✓", display_value
    else:
        if required:
            return "✗", "Missing (REQUIRED)"
        else:
            return "○", "Not set (optional)"

def main():
    print("=" * 70)
    print("🔍 Environment Variables Verification")
    print("=" * 70)
    print()

    # Required variables
    required_vars = [
        ("GEMINI_API_KEY", "Google Gemini API key"),
        ("FIREBASE_API_KEY", "Firebase Web API key"),
        ("FIREBASE_AUTH_DOMAIN", "Firebase auth domain"),
        ("FIREBASE_STORAGE_BUCKET", "Firebase storage bucket"),
    ]

    # Optional variables with defaults
    optional_vars = [
        ("NLLB_MODEL_SIZE", "NLLB model size", "600M"),
        ("M2M_MODEL_SIZE", "M2M model size", "418M"),
        ("DEFAULT_TARGET_LANG", "Default translation target", "vi"),
        ("MIN_CONFIDENCE", "OCR confidence threshold", "0.7"),
        ("MAX_TEXT_LENGTH", "Max text length", "1000"),
        ("USE_GPU", "Enable GPU", "true"),
        ("CACHE_TRANSLATIONS", "Cache translations", "true"),
        ("CACHE_SIZE", "Cache size", "1000"),
        ("OVERLAY_DISPLAY", "Overlay mode", "positioned"),
        ("SCAN_MODE", "Scan mode", "snapshot"),
    ]

    print("📋 Required Variables:")
    print("-" * 70)
    all_good = True
    for var_name, description in required_vars:
        status, value = check_env_var(var_name, required=True)
        print(f"{status} {var_name:30} {value:20} # {description}")
        if status == "✗" or status == "⚠️":
            all_good = False
    print()

    print("📋 Optional Variables (with defaults):")
    print("-" * 70)
    for var_name, description, default in optional_vars:
        status, value = check_env_var(var_name, required=False)
        if status == "○":
            value = f"Using default: {default}"
        print(f"{status} {var_name:30} {value:20} # {description}")
    print()

    # Check for serviceAccountKey.json
    print("📋 Firebase Service Account:")
    print("-" * 70)
    if os.path.exists("serviceAccountKey.json"):
        print("✓ serviceAccountKey.json            Found")
    else:
        print("✗ serviceAccountKey.json            Missing (REQUIRED)")
        all_good = False
    print()

    # Check for config.env
    print("📋 Configuration Files:")
    print("-" * 70)
    if os.path.exists("config.env"):
        print("✓ config.env                        Found")
    else:
        print("⚠️ config.env                        Not found (will use env vars only)")

    if os.path.exists("config.env.example"):
        print("✓ config.env.example                Found")
    else:
        print("○ config.env.example                Not found")
    print()

    # Summary
    print("=" * 70)
    if all_good:
        print("✅ All required environment variables are properly set!")
        print()
        print("You can now run the application:")
        print("  python main_with_ui.py")
    else:
        print("❌ Some required variables are missing or invalid!")
        print()
        print("Please follow the setup guide:")
        print("  1. Copy config.env.example to config.env")
        print("  2. Edit config.env with your real API keys")
        print("  3. Or set system environment variables")
        print()
        print("See SETUP_GUIDE.md for detailed instructions")
    print("=" * 70)

if __name__ == "__main__":
    main()
