# CHƯƠNG 5: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

Chương cuối cùng này tổng kết lại những kết quả đã đạt được của đề tài, đánh giá trung thực các hạn chế còn tồn tại và đề xuất các hướng phát triển tiếp theo để hoàn thiện sản phẩm.

## 5.1. Kết quả đạt được

Sau quá trình nghiên cứu và thực hiện, đề tài "Xây dựng công cụ dịch thuật thời gian thực bằng AI Overlay" đã hoàn thành các mục tiêu đề ra ban đầu. Cụ thể:

1.  **Xây dựng thành công ứng dụng Desktop hoàn chỉnh:** Ứng dụng hoạt động ổn định trên hệ điều hành Windows, cho phép người dùng chọn cửa sổ mục tiêu và xem bản dịch trực tiếp.
2.  **Tích hợp công nghệ OCR và AI Dịch thuật hiện đại:**
    *   Sử dụng hiệu quả **Tesseract OCR** để trích xuất văn bản từ hình ảnh với độ chính xác khá cao.
    *   Kết nối thành công với **Google Gemini API** để cung cấp bản dịch chất lượng cao, hiểu ngữ cảnh tốt hơn so với các phương pháp dịch từng từ truyền thống.
    *   Triển khai cơ chế dự phòng (Fallback) với mô hình **NLLB/OPUS** để đảm bảo ứng dụng vẫn hoạt động khi mất kết nối Internet.
3.  **Tối ưu hóa hiệu năng thời gian thực:**
    *   Áp dụng kỹ thuật **BitBlt** để chụp màn hình tốc độ cao.
    *   Sử dụng thuật toán **dHash** để phát hiện thay đổi, giảm thiểu việc gọi OCR và API không cần thiết, giúp tiết kiệm tài nguyên hệ thống.
    *   Kiến trúc **Asynchronous (Asyncio)** giúp giao diện luôn mượt mà, không bị treo (not responding) trong quá trình xử lý nặng.
4.  **Quản lý dữ liệu hiệu quả:** Hệ thống lưu trữ lịch sử dịch thuật cục bộ bằng SQLite và đồng bộ hóa lên đám mây thông qua Firebase Firestore, mang lại trải nghiệm liền mạch cho người dùng.

## 5.2. Hạn chế của hệ thống

Bên cạnh những kết quả đạt được, hệ thống vẫn còn một số hạn chế cần khắc phục:

1.  **Phụ thuộc vào nền tảng Windows:** Do sử dụng các thư viện đặc thù như `pywin32` và API `BitBlt`, ứng dụng hiện tại chỉ chạy được trên Windows, chưa hỗ trợ macOS hay Linux.
2.  **Yêu cầu cài đặt Tesseract thủ công:** Người dùng cần phải cài đặt Tesseract OCR riêng biệt và đường dẫn đến file thực thi (`tesseract.exe`) hiện đang được cấu hình cứng (hardcoded) hoặc yêu cầu biến môi trường, gây khó khăn cho việc cài đặt ban đầu.
3.  **Độ trễ mạng:** Mặc dù đã tối ưu, việc phụ thuộc vào API của Google Gemini vẫn có độ trễ nhất định (từ 0.5s - 1.5s) tùy thuộc vào tốc độ mạng, có thể chưa đáp ứng được nhu cầu của các game hành động nhịp độ quá nhanh.
4.  **Giao diện người dùng còn đơn giản:** Các tùy chọn tùy chỉnh giao diện (font chữ, màu sắc, độ trong suốt của Overlay) còn hạn chế, chưa cho phép người dùng cá nhân hóa sâu.

## 5.3. Hướng phát triển trong tương lai

Để nâng cao chất lượng và khả năng ứng dụng thực tế, các hướng phát triển sau được đề xuất:

1.  **Đa nền tảng hóa (Cross-platform):** Nghiên cứu thay thế `pywin32` bằng các thư viện đa nền tảng như `mss` hoặc `PyQt` native screen capture để hỗ trợ macOS và Linux.
2.  **Tích hợp OCR Engine nhúng:** Thay thế Tesseract bằng các mô hình OCR nhẹ hơn và có thể nhúng trực tiếp vào ứng dụng (như **PaddleOCR** hoặc **EasyOCR**), giúp loại bỏ bước cài đặt phức tạp cho người dùng cuối.
3.  **Cải thiện UI/UX:**
    *   Thêm menu cài đặt chi tiết cho phép chỉnh sửa font, cỡ chữ, màu nền Overlay.
    *   Hỗ trợ chế độ "Dịch vùng chọn" (Select Region) thay vì dịch toàn bộ cửa sổ.
4.  **Tối ưu hóa AI:**
    *   Fine-tune (tinh chỉnh) các mô hình dịch nhỏ gọn để chạy offline với chất lượng cao hơn.
    *   Áp dụng kỹ thuật Caching thông minh hơn để không dịch lại các câu đã từng dịch.
5.  **Đóng gói chuyên nghiệp:** Tạo bộ cài đặt (Installer) tự động tải và cấu hình tất cả các thành phần phụ thuộc, giúp việc phân phối ứng dụng dễ dàng hơn.

---
*Kết thúc báo cáo.*
