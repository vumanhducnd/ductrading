"""
Tìm toạ độ cần click để mở symbol search trên TradingView.
Chạy: python find_click_pos.py
Rồi di chuột đến vị trí tên mã trên TradingView, đứng yên 3 giây.
Script sẽ in ra offset X, Y để điền vào .env
"""
import sys, time
sys.stdout.reconfigure(encoding="utf-8")

import pyautogui
import pygetwindow as gw
from dotenv import load_dotenv
import os

load_dotenv()
keyword = os.getenv("TRADINGVIEW_WINDOW_TITLE", "tradingview").lower()

# Tìm cửa sổ TradingView
win = None
for w in gw.getAllWindows():
    if w.title and keyword in w.title.lower():
        win = w
        break

if not win:
    print(f"Không tìm thấy cửa sổ TradingView (keyword: '{keyword}')")
    print("Hãy mở TradingView app trước.")
    sys.exit(1)

print(f"Tìm thấy: {win.title!r}")
print(f"Vị trí cửa sổ: left={win.left}, top={win.top}")
print()
print("Di chuột đến VỊ TRÍ TÊN MÃ trên TradingView rồi đứng yên...")

for i in range(5, 0, -1):
    x, y = pyautogui.position()
    print(f"  {i}s — chuột tại: ({x}, {y})  →  offset từ cửa sổ: ({x - win.left}, {y - win.top})", end="\r")
    time.sleep(1)

x, y = pyautogui.position()
offset_x = x - win.left
offset_y = y - win.top

print(f"\n\nKết quả:")
print(f"  TV_SYMBOL_CLICK_X={offset_x}")
print(f"  TV_SYMBOL_CLICK_Y={offset_y}")
print(f"\nThêm 2 dòng này vào file .env")
