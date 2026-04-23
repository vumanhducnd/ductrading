"""
Cấu hình trung tâm cho toàn bộ hệ thống live trading.
Đọc từ file .env nếu có, fallback về giá trị mặc định.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── TikTok ──────────────────────────────────────────────────────────────────
TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME", "@your_username")

# ── Timing ──────────────────────────────────────────────────────────────────
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "30"))

# ── Overlay ─────────────────────────────────────────────────────────────────
OVERLAY_PORT = int(os.getenv("OVERLAY_PORT", "5000"))

# ── TradingView ──────────────────────────────────────────────────────────────
# Keyword tìm cửa sổ TradingView app (partial match trong window title)
# TradingView app title: "VNM ▼ 70,000 -1.2% / YourUsername" → đặt = username
TRADINGVIEW_WINDOW_TITLE = os.getenv("TRADINGVIEW_WINDOW_TITLE", "TradingView")

# Offset click vào vùng tên mã trên toolbar TradingView (tính từ góc trên trái cửa sổ).
# Chạy 'python find_click_pos.py' để hiệu chỉnh nếu click sai chỗ.
TV_SYMBOL_CLICK_X = int(os.getenv("TV_SYMBOL_CLICK_X", "120"))
TV_SYMBOL_CLICK_Y = int(os.getenv("TV_SYMBOL_CLICK_Y", "20"))

# ── Queue ───────────────────────────────────────────────────────────────────
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "20"))

# ── Demo mode ────────────────────────────────────────────────────────────────
# Bật demo mode khi không có TikTok live để test overlay + auto typer
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
DEMO_INTERVAL_SECONDS = int(os.getenv("DEMO_INTERVAL_SECONDS", "5"))

# ── Node.js bridge ────────────────────────────────────────────────────────────
# Dùng Node.js bridge (tiktok-live-connector) thay vì TikTokLive Python.
# Không cần API key, kết nối trực tiếp vào TikTok Live.
# Cài trước: cd live-trading/tiktok_bridge && npm install
USE_NODEJS_BRIDGE = os.getenv("USE_NODEJS_BRIDGE", "false").lower() == "true"

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_FILE = os.getenv("LOG_FILE", "trading.log")
