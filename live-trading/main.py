"""
Entry point — chạy toàn bộ hệ thống live trading.
Khởi động 3 component song song:
  1. TikTok listener (nhận comment)
  2. Flask overlay server (localhost:5000)
  3. Main loop (mỗi 30s chuyển mã trên TradingView)
"""

import sys
import time
import logging
import threading
import signal

from config import OVERLAY_PORT, LOG_FILE
from queue_manager import QueueManager
from tiktok_listener import TikTokListener
from auto_typer import AutoTyper
from overlay.server import set_queue_manager, set_listener, run_server, get_interval

# ── Logging setup ─────────────────────────────────────────────────────────────
def setup_logging():
    # Force UTF-8 cho stdout trên Windows (tránh UnicodeEncodeError với tiếng Việt)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    fmt = "[%(asctime)s] %(levelname)-7s %(message)s"
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.stream = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1, closefd=False)

    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        datefmt="%H:%M:%S",
        handlers=[
            console_handler,
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )

setup_logging()
logger = logging.getLogger(__name__)

# ── Khởi tạo các component ────────────────────────────────────────────────────
queue = QueueManager()
listener = TikTokListener(queue)

# dry_run=True nếu chạy với flag --dry-run (không cần TradingView mở)
DRY_RUN = "--dry-run" in sys.argv
typer = AutoTyper(dry_run=DRY_RUN)

# ── Graceful shutdown ─────────────────────────────────────────────────────────
_shutdown_event = threading.Event()

def _signal_handler(sig, frame):
    logger.info("\n[MAIN] Nhận tín hiệu dừng (Ctrl+C). Đang tắt hệ thống...")
    _shutdown_event.set()

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# ── Thread 1: TikTok Listener ─────────────────────────────────────────────────
def start_listener():
    listener.start()

# ── Thread 2: Flask Overlay ───────────────────────────────────────────────────
def start_overlay():
    set_queue_manager(queue)
    set_listener(listener)
    run_server(port=OVERLAY_PORT)

# ── Main loop: chuyển mã theo interval động ───────────────────────────────────
def main_loop():
    logger.info("[MAIN] Main loop khởi động — interval: %ds", get_interval())
    while not _shutdown_event.is_set():
        item = queue.next()
        if item:
            symbol = item["symbol"]
            votes = item["votes"]
            logger.info(
                "[MAIN] ═══ Chuyển sang: %s (%d votes) ═══  [queue còn: %d]",
                symbol, votes, len(queue.queue),
            )
            typer.switch_to_symbol(symbol)
        else:
            logger.info("[MAIN] Queue rỗng — đợi mã tiếp theo...")

        # Chờ theo interval hiện tại (đọc lại mỗi giây để nhận thay đổi realtime)
        elapsed = 0
        while not _shutdown_event.is_set():
            if elapsed >= get_interval():
                break
            time.sleep(1)
            elapsed += 1

    logger.info("[MAIN] Main loop đã dừng")


def main():
    logger.info("=" * 60)
    logger.info(" DucTrading Live — Hệ thống phân tích cổ phiếu TikTok Live")
    logger.info("=" * 60)
    if DRY_RUN:
        logger.info("[MAIN] Chế độ DRY RUN — không gõ phím thật")
    logger.info("[MAIN] Overlay: http://localhost:%d", OVERLAY_PORT)
    logger.info("[MAIN] Log: %s", LOG_FILE)
    logger.info("[MAIN] Nhấn Ctrl+C để dừng")
    logger.info("-" * 60)

    # Khởi động các thread
    threads = [
        threading.Thread(target=start_listener, name="ListenerThread", daemon=True),
        threading.Thread(target=start_overlay,  name="OverlayThread",  daemon=True),
        threading.Thread(target=main_loop,       name="MainLoopThread", daemon=False),
    ]
    for t in threads:
        t.start()

    # Chờ cho đến khi có tín hiệu dừng
    _shutdown_event.wait()

    # Cleanup
    listener.stop()
    logger.info("[MAIN] Hệ thống đã dừng hoàn toàn. Tạm biệt!")
    sys.exit(0)


if __name__ == "__main__":
    main()
