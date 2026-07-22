# Đưa app lên nền tảng web

## Cách dễ nhất: Replit

1. Đăng nhập Replit và chọn **Create Repl / Import from ZIP**.
2. Tải lên toàn bộ file ZIP của dự án.
3. Chờ Replit cài các gói trong `requirements.txt` và `replit.nix`.
4. Bấm **Run** để thử.
5. Chọn **Deployments** → **Autoscale** hoặc **Reserved VM** → **Deploy**.
6. Replit sẽ cấp một đường link web công khai để mở trên điện thoại và máy tính.

> Với xử lý video và Whisper, nên dùng máy có tối thiểu 4 GB RAM. Gói miễn phí có thể thiếu RAM hoặc hết thời gian xử lý.

## Render bằng Docker

1. Đưa thư mục dự án lên GitHub.
2. Trên Render, chọn **New → Blueprint** hoặc **Web Service**.
3. Kết nối repository.
4. Render tự đọc `render.yaml` và `Dockerfile`.
5. Chọn gói có tối thiểu 4 GB RAM rồi deploy.

## Chạy bằng Docker ở VPS

```bash
docker build -t autosub-video-studio .
docker run -p 8080:8080 -e PORT=8080 autosub-video-studio
```

Mở `http://IP-VPS:8080`.

## Lưu ý khi dùng công khai

- File tải lên và file kết quả hiện lưu tạm trên máy chủ.
- Nên bổ sung đăng nhập, hàng đợi xử lý và tự xóa file cũ.
- Không nên cho nhiều người xử lý video dài cùng lúc trên máy cấu hình thấp.
