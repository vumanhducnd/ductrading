"""
Tự động chuyển mã cổ phiếu trên TradingView desktop app.

Cách hoạt động: click vào vùng tên mã ở toolbar trên cùng của TradingView,
rồi paste mã từ clipboard và Enter — tránh dùng phím / vì nó mở indicator search.
"""

import time
import logging
from config import TRADINGVIEW_WINDOW_TITLE, TV_SYMBOL_CLICK_X, TV_SYMBOL_CLICK_Y
from validator import get_exchange

logger = logging.getLogger(__name__)


class AutoTyper:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        if not dry_run:
            try:
                import pyautogui
                import pygetwindow as gw
                import pyperclip
                pyautogui.FAILSAFE = True
                pyautogui.PAUSE = 0.05
                self._pyautogui = pyautogui
                self._gw = gw
                self._pyperclip = pyperclip
            except ImportError as e:
                logger.error("[TYPER] Thiếu thư viện: %s", e)
                raise

    def _format_symbol(self, symbol: str) -> str:
        exchange = get_exchange(symbol)
        return f"{exchange}:{symbol}" if exchange else f"HOSE:{symbol}"

    def _find_tradingview_window(self):
        """
        Tìm cửa sổ TradingView bằng keyword trong title.
        TradingView app title dạng: 'VNM ▼ 70,000 -1.2% / VuManhDuc'
        → đặt TRADINGVIEW_WINDOW_TITLE = username TradingView.
        """
        keyword = TRADINGVIEW_WINDOW_TITLE.lower()
        matches = [w for w in self._gw.getAllWindows()
                   if w.title and keyword in w.title.lower()]
        if not matches:
            return None
        return max(matches, key=lambda w: w.width * w.height)

    def switch_to_symbol(self, symbol: str) -> bool:
        """
        Chuyển TradingView sang mã chỉ định.
        Click vào vùng symbol trên toolbar → paste mã → Enter.
        """
        formatted = self._format_symbol(symbol)
        logger.info("[TYPER] Chuyển sang %s", formatted)

        if self.dry_run:
            logger.info("[TYPER][DRY RUN] Sẽ click và paste: %s", formatted)
            return True

        win = self._find_tradingview_window()
        if win is None:
            logger.error(
                "[TYPER] Không tìm thấy cửa sổ TradingView! (keyword: '%s')\n"
                "        → Mở TradingView app trước\n"
                "        → Chạy 'python find_windows.py' để kiểm tra title\n"
                "        → Cập nhật TRADINGVIEW_WINDOW_TITLE trong .env",
                TRADINGVIEW_WINDOW_TITLE,
            )
            return False

        logger.debug("[TYPER] Window: %r  pos=(%d,%d)  size=%dx%d",
                     win.title, win.left, win.top, win.width, win.height)

        try:
            pyautogui = self._pyautogui

            if win.isMinimized:
                win.restore()
                time.sleep(0.3)
            win.activate()
            time.sleep(0.4)

            # Tính toạ độ tuyệt đối của vùng symbol trên toolbar TradingView.
            # TV_SYMBOL_CLICK_X/Y là offset so với góc trên trái cửa sổ.
            click_x = win.left + TV_SYMBOL_CLICK_X
            click_y = win.top  + TV_SYMBOL_CLICK_Y
            logger.debug("[TYPER] Click symbol area tại (%d, %d)", click_x, click_y)

            # Click vào vùng tên mã để mở symbol search
            pyautogui.click(click_x, click_y)
            time.sleep(0.5)     # Chờ popup search mở ra

            # Đặt mã vào clipboard (tránh bàn phím tiếng Việt làm sai ký tự)
            self._pyperclip.copy(formatted)

            # Xoá nội dung cũ trong ô tìm kiếm, paste mã mới
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)     # Chờ autocomplete hiện kết quả

            # Chọn kết quả đầu tiên
            pyautogui.press('enter')
            time.sleep(0.5)

            logger.info("[TYPER] Đã chuyển sang %s", formatted)
            return True

        except Exception as e:
            logger.error("[TYPER] Lỗi: %s", e)
            return False
