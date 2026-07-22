# AutoSub Video Studio

App web đơn giản để:
- Tạo phụ đề tự động bằng Faster-Whisper.
- Ghim phụ đề trực tiếp vào video và tải file SRT.
- Cắt theo thời gian bắt đầu/kết thúc.
- Đổi tỷ lệ 9:16, 1:1, 16:9.
- Lật ngang, đổi tốc độ, tắt tiếng gốc.
- Thêm nhạc nền và watermark chữ.

## Yêu cầu
1. Python 3.10 hoặc mới hơn.
2. FFmpeg và FFprobe đã được cài, có trong PATH.
3. RAM khuyến nghị từ 8 GB.

## Chạy trên Windows
1. Cài Python.
2. Cài FFmpeg, thêm thư mục `bin` của FFmpeg vào PATH.
3. Nhấp đúp `run_windows.bat`.
4. Mở `http://127.0.0.1:5000`.

## Chạy trên macOS/Linux
```bash
./run_mac_linux.sh
```
Sau đó mở `http://127.0.0.1:5000`.

## Chạy thủ công
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Ghi chú
- Lần tạo phụ đề đầu tiên sẽ tải model Whisper `small`.
- App hiện xử lý một tác vụ tại một thời điểm, phù hợp chạy cá nhân hoặc demo.
- Khi triển khai công khai nên bổ sung hàng đợi tác vụ, đăng nhập, giới hạn dung lượng và tự xóa file cũ.
- Chỉ dùng nội dung mà bạn có quyền chỉnh sửa hoặc đăng lại.

## Triển khai thành website có đường link
Dự án đã kèm cấu hình cho **Replit**, **Render** và **Docker**. Xem hướng dẫn chi tiết trong `DEPLOY_WEB.md`.
