# 🚀 Quick Start Guide - MVP

Hướng dẫn nhanh để chạy app trong 10 phút!

---

## ✅ Bước 1: Cài đặt Dependencies (2 phút)

```bash
pip install firebase-admin Pyrebase4 python-dotenv
```

---

## ✅ Bước 2: Setup Firebase (5 phút)

### 2.1. Tạo Firebase Project
1. Vào https://console.firebase.google.com
2. Tạo project mới (tên: `OCRTranslatorPro`)

### 2.2. Enable Authentication
1. Vào **Authentication** → **Get Started**
2. Enable **Email/Password**

### 2.3. Enable Firestore
1. Vào **Firestore Database** → **Create database**
2. Chọn **Test mode**

### 2.4. Download Service Account Key
1. **Project Settings** → **Service accounts**
2. Click **Generate new private key**
3. Lưu file thành `serviceAccountKey.json` vào thư mục gốc project

### 2.5. Lấy API Key
1. **Project Settings** → **General**
2. Copy `apiKey` từ phần "Your apps"

---

## ✅ Bước 3: Configure (1 phút)

Mở file `config.env`, thêm vào cuối file:

```ini
# Firebase Configuration
FIREBASE_API_KEY=AIzaSy...........................  # Paste your API key here
FIREBASE_AUTH_DOMAIN=ocrtranslatorpro.firebaseapp.com  # Replace with your project ID
FIREBASE_DATABASE_URL=
FIREBASE_STORAGE_BUCKET=ocrtranslatorpro.appspot.com  # Replace with your project ID
```

**Ví dụ:**
```ini
FIREBASE_API_KEY=AIzaSyDEMOKEY123456789ABCDEFGH
FIREBASE_AUTH_DOMAIN=ocrtranslatorpro.firebaseapp.com
FIREBASE_DATABASE_URL=
FIREBASE_STORAGE_BUCKET=ocrtranslatorpro.appspot.com
```

---

## ✅ Bước 4: Run! (30 giây)

```bash
python main_with_ui.py
```

---

## 🎮 Sử dụng

1. **Đăng ký account:**
   - Click "Create Account"
   - Nhập email + password (min 6 ký tự)
   - Click "Register"

2. **Login:**
   - Nhập email + password
   - Click "Login"

3. **Bắt đầu OCR:**
   - Click "🚀 Bắt đầu OCR & Translation"
   - Chọn vùng màn hình
   - Xem bản dịch!

4. **Xem lịch sử:**
   - Click tab "📜 Lịch sử"
   - Tất cả bản dịch đã được lưu tự động!

---

## 🐛 Lỗi thường gặp

### ❌ "Firebase not available"
**Fix:**
```bash
pip install firebase-admin Pyrebase4 python-dotenv
```
Check file `serviceAccountKey.json` đã có trong thư mục chưa.

### ❌ "EMAIL_EXISTS"
**Fix:** Email đã được đăng ký. Dùng email khác hoặc login.

### ❌ "INVALID_PASSWORD"
**Fix:** Sai password hoặc password < 6 ký tự.

---

## 📂 Files quan trọng

```
✅ main_with_ui.py           - File chạy chính (NEW)
✅ config.env                - Cấu hình Firebase
⚠️ serviceAccountKey.json   - Firebase credentials (SECRET!)
⚠️ .session                 - User session (auto-generated)
```

---

## 🎯 Tính năng có trong MVP

✅ Login/Register với Firebase
✅ Lưu lịch sử dịch tự động
✅ Xem, tìm kiếm lịch sử
✅ Export CSV
✅ Xóa lịch sử
✅ Session persistence (auto-login)

---

## 📚 Chi tiết hơn?

Đọc `README_FIREBASE_MVP.md` để biết thêm chi tiết về:
- Cấu trúc project
- Security rules
- Troubleshooting
- Production deployment

---

**Chúc bạn dùng vui! 🎉**
