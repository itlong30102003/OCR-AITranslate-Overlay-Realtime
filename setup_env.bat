@echo off
REM ============================================
REM Environment Variables Setup Script
REM ============================================
REM
REM This script helps set environment variables for development
REM
REM Usage:
REM   1. Edit the values below with your real API keys
REM   2. Run: setup_env.bat
REM   3. Restart your terminal/IDE
REM
REM ============================================

echo Setting up environment variables...
echo.

REM ============================================
REM EDIT THESE VALUES WITH YOUR REAL API KEYS
REM ============================================

set GEMINI_API_KEY=your_gemini_api_key_here
set FIREBASE_API_KEY=your_firebase_api_key_here
set FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
set FIREBASE_DATABASE_URL=
set FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app

REM ============================================
REM Optional Settings (can keep defaults)
REM ============================================

set NLLB_MODEL_SIZE=600M
set M2M_MODEL_SIZE=418M
set DEFAULT_TARGET_LANG=vi
set MIN_CONFIDENCE=0.7
set MAX_TEXT_LENGTH=1000
set USE_GPU=true
set CACHE_TRANSLATIONS=true
set CACHE_SIZE=1000
set LOG_LEVEL=INFO
set LOG_TRANSLATIONS=false
set CAPTURE_MODE=window
set OVERLAY_DISPLAY=positioned
set POSITIONED_FONT_SIZE=12
set POSITIONED_SHOW_BBOX=true
set POSITIONED_OPACITY=0.85
set SUBTITLE_POSITION=bottom
set SCAN_MODE=snapshot

REM ============================================
REM Set as User Environment Variables (Permanent)
REM ============================================

echo Setting permanent environment variables...
echo.

setx GEMINI_API_KEY "%GEMINI_API_KEY%"
setx FIREBASE_API_KEY "%FIREBASE_API_KEY%"
setx FIREBASE_AUTH_DOMAIN "%FIREBASE_AUTH_DOMAIN%"
setx FIREBASE_DATABASE_URL "%FIREBASE_DATABASE_URL%"
setx FIREBASE_STORAGE_BUCKET "%FIREBASE_STORAGE_BUCKET%"

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Environment variables have been set.
echo Please RESTART your terminal/IDE for changes to take effect.
echo.
echo To verify, run: echo %GEMINI_API_KEY%
echo.
pause
