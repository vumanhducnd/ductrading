"""
Tiện ích liệt kê cửa sổ đang mở và kiểm tra config TRADINGVIEW_WINDOW_TITLE.
Chạy: python find_windows.py
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")

import pygetwindow as gw

# Đọc keyword từ .env nếu có
keyword = "tradingview"
try:
    from dotenv import load_dotenv
    load_dotenv()
    keyword = os.getenv("TRADINGVIEW_WINDOW_TITLE", "tradingview").lower()
except Exception:
    pass

windows = [w for w in gw.getAllWindows() if w.title.strip()]
windows.sort(key=lambda w: w.title.lower())

print(f"Keyword đang dùng: '{keyword}'\n")
print(f"{'TITLE':<60}  SIZE")
print("-" * 75)
for w in windows:
    mark = "  ◄ MATCH" if keyword in w.title.lower() else ""
    print(f"{w.title:<60}  {w.width}x{w.height}{mark}")

print(f"\nTổng: {len(windows)} cửa sổ")

matches = [w for w in windows if keyword in w.title.lower()]
print(f"\n--- Cửa sổ khớp keyword '{keyword}': {len(matches)} ---")
for w in matches:
    print(f"  >> {w.title!r}  ({w.width}x{w.height})")

if not matches:
    print("  (Không tìm thấy!)")
    print("  → Hãy mở TradingView app trước")
    print("  → Cập nhật TRADINGVIEW_WINDOW_TITLE trong .env cho đúng với title ở trên")
