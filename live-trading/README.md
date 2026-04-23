# DucTrading Live — Phân Tích Cổ Phiếu TikTok Live

Hệ thống tự động đọc mã cổ phiếu từ comment TikTok Live và hiển thị lên TradingView mỗi 30 giây.

---

## Tính năng

- Lắng nghe comment TikTok Live realtime
- Validate mã HOSE / HNX (~500+ mã)
- Queue thông minh: vote counting, deduplication, tự sắp xếp theo lượt vote
- Overlay web đẹp cho OBS (localhost:5000)
- Tự động gõ mã vào TradingView mỗi 30 giây
- Demo mode để test không cần TikTok live

---

## Yêu cầu hệ thống

- Windows 10/11
- Python 3.11+
- TradingView chạy trên Chrome/browser (không phải app desktop)
- OBS Studio (nếu dùng overlay)

---

## Cài đặt

### Bước 1 — Clone / tải code

```bash
cd c:\DucVM\PROJECT\DucTrading\live-trading
```

### Bước 2 — Tạo môi trường ảo

```bash
python -m venv venv
venv\Scripts\activate
```

### Bước 3 — Cài dependencies

```bash
pip install -r requirements.txt
```

### Bước 4 — Cấu hình

```bash
copy .env.example .env
```

Mở `.env` và chỉnh:
```
TIKTOK_USERNAME=@ten_tiktok_cua_ban
INTERVAL_SECONDS=30
```

---

## Chạy hệ thống

### Chạy bình thường (kết nối TikTok Live)

```bash
python main.py
```

### Chạy demo mode (test không cần TikTok live)

```bash
# Trong .env, đặt DEMO_MODE=true
python main.py
```

hoặc:

```bash
set DEMO_MODE=true && python main.py
```

### Chạy dry-run (không gõ phím thật vào TradingView)

```bash
python main.py --dry-run
```

---

## Cài OBS Overlay

1. Mở OBS → Thêm **Browser Source**
2. URL: `http://localhost:5000`
3. Width: `400`, Height: `600`
4. Tick **Refresh browser when scene becomes active**

---

## Cấu trúc thư mục

```
live-trading/
├── main.py              ← Entry point
├── config.py            ← Cấu hình (đọc từ .env)
├── validator.py         ← Validate mã HOSE/HNX
├── queue_manager.py     ← Quản lý queue + vote
├── tiktok_listener.py   ← Kết nối TikTok Live
├── auto_typer.py        ← Gõ mã vào TradingView
├── overlay/
│   ├── server.py        ← Flask server
│   ├── templates/       ← HTML overlay
│   └── static/          ← CSS
├── .env                 ← Cấu hình cá nhân (không commit)
├── .env.example         ← Template cấu hình
├── requirements.txt
└── trading.log          ← Log hoạt động (tự tạo khi chạy)
```

---

## Cách viewer request mã

Viewer chỉ cần gõ tên mã trong comment, ví dụ:

```
cho xem VNM với
HPG đi ơi
xem FPT được không
```

Hệ thống tự nhận diện và thêm vào queue. Mã nào được nhiều người vote sẽ lên đầu queue.

---

## Dừng hệ thống

Nhấn `Ctrl+C` trong terminal. Hệ thống sẽ dừng graceful.

**Failsafe PyAutoGUI:** Di chuột lên góc trên trái màn hình để dừng khẩn cấp nếu auto typer hoạt động sai.

---

## API Overlay

| Endpoint | Method | Mô tả |
|---|---|---|
| `/` | GET | Trang overlay HTML |
| `/api/state` | GET | JSON state queue |
| `/api/skip` | POST | Bỏ qua mã hiện tại |
| `/api/clear` | POST | Xóa toàn bộ queue |

---

## Troubleshooting

**TikTokLive không kết nối được:**
- Kiểm tra username có `@` ở đầu
- Tài khoản phải đang live
- Thử dùng DEMO_MODE=true để test trước

**TradingView không nhận mã:**
- Kiểm tra `TRADINGVIEW_WINDOW_TITLE` trong `.env` khớp với title cửa sổ browser
- Chạy `python main.py --dry-run` để xem log mà không gõ thật
- Đảm bảo cửa sổ TradingView không bị minimize

**Overlay không load trong OBS:**
- Kiểm tra Flask đang chạy: mở `http://localhost:5000` trong browser
- Tắt firewall hoặc thêm exception cho port 5000
