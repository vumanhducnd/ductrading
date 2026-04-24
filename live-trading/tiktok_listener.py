"""
Kết nối TikTok Live và lắng nghe comment realtime.
Hỗ trợ 3 chế độ:
  - DEMO_MODE=true        : thêm mã ngẫu nhiên, không cần TikTok live
  - USE_NODEJS_BRIDGE=true: dùng Node.js bridge (miễn phí, không cần API key)
  - mặc định              : dùng TikTokLive Python (cần EulerStream API key)
"""

import asyncio
import json
import logging
import os
import random
import subprocess
import threading

from config import TIKTOK_USERNAME, DEMO_MODE, DEMO_INTERVAL_SECONDS, USE_NODEJS_BRIDGE
from validator import extract_tickers
from queue_manager import QueueManager

logger = logging.getLogger(__name__)

_DEMO_TICKERS = [
    "VNM", "HPG", "FPT", "VIC", "VHM", "TCB", "VCB", "BID", "CTG", "MBB",
    "ACB", "STB", "HDB", "TPB", "VPB", "MSN", "MWG", "PNJ", "REE", "SAB",
    "SSI", "VND", "HCM", "SHS", "DXG", "NVL", "PDR", "KDH", "VRE", "VJC",
    "HVN", "ACV", "GMD", "PVT", "GAS", "PLX", "POW", "NT2", "DCM", "DPM",
]

_DEMO_USERS = [
    "tiktok_user_01", "trader_vn", "codon_vnm", "dautu2024", "stockmaster",
    "phanich_viet", "lamdautu", "fxviet", "chungkhoan_pro", "nguoichoi99",
]


def _run_demo_mode(queue: QueueManager, stop_event: threading.Event):
    """Chế độ demo: tự động thêm mã ngẫu nhiên vào queue."""
    logger.info("[DEMO] Bắt đầu demo mode — thêm mã ngẫu nhiên mỗi %ds", DEMO_INTERVAL_SECONDS)
    while not stop_event.is_set():
        ticker = random.choice(_DEMO_TICKERS)
        user = random.choice(_DEMO_USERS)
        comment = f"cho xem {ticker} với ạ"
        result = queue.add(ticker, user)
        logger.info("[DEMO] %s: '%s' → %s %s", user, comment, ticker, result)
        stop_event.wait(DEMO_INTERVAL_SECONDS)


class TikTokListener:
    def __init__(self, queue: QueueManager, username: str = TIKTOK_USERNAME):
        self.queue = queue
        self.username = username
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._node_proc: subprocess.Popen | None = None

    def _handle_comment(self, username: str, text: str):
        """Xử lý một comment: tìm mã hợp lệ và thêm vào queue."""
        tickers = extract_tickers(text)
        if not tickers:
            return
        for ticker in tickers:
            result = self.queue.add(ticker, username)
            logger.info("[COMMENT] %s: \"%s\" → %s %s", username, text, ticker, result)

    # ── Node.js bridge ────────────────────────────────────────────────────────

    def _run_nodejs_bridge(self):
        """Chạy Node.js bridge, đọc comment từ stdout dạng JSON line."""
        bridge_js = os.path.join(os.path.dirname(__file__), "tiktok_bridge", "bridge.js")

        if not os.path.exists(bridge_js):
            logger.error(
                "[BRIDGE] Không tìm thấy %s\n"
                "        → Chạy: cd live-trading/tiktok_bridge && npm install",
                bridge_js,
            )
            return

        while not self._stop_event.is_set():
            logger.info("[BRIDGE] Khởi động Node.js bridge cho %s...", self.username)
            try:
                proc = subprocess.Popen(
                    ["node", bridge_js, self.username],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    env={**os.environ, "TIKTOK_USERNAME": self.username},
                )
                self._node_proc = proc

                def _log_stderr():
                    for line in proc.stderr:
                        line = line.strip()
                        if line:
                            logger.info("[BRIDGE] %s", line)

                threading.Thread(target=_log_stderr, daemon=True, name="BridgeStderr").start()

                for line in proc.stdout:
                    if self._stop_event.is_set():
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        self._handle_comment(data.get("user", "unknown"), data.get("comment", ""))
                    except json.JSONDecodeError:
                        logger.warning("[BRIDGE] Không parse được dòng: %s", line)

                proc.wait()
                if not self._stop_event.is_set():
                    logger.warning("[BRIDGE] Bridge thoát (code %d), thử lại sau 10s...", proc.returncode)
                    self._stop_event.wait(10)

            except FileNotFoundError:
                logger.error("[BRIDGE] Không tìm thấy lệnh 'node'. Cài Node.js tại https://nodejs.org")
                break
            except Exception as e:
                logger.error("[BRIDGE] Lỗi không mong đợi: %s", e)
                if not self._stop_event.is_set():
                    self._stop_event.wait(10)

    # ── TikTokLive Python ─────────────────────────────────────────────────────

    def _run_live(self):
        """Chạy TikTok Live listener dùng thư viện TikTokLive Python."""
        try:
            from TikTokLive import TikTokLiveClient
            from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent
        except ImportError:
            logger.error("[TIKTOK] Thư viện TikTokLive chưa được cài. Chạy: pip install TikTokLive")
            return

        async def _async_run():
            while not self._stop_event.is_set():
                client = TikTokLiveClient(unique_id=self.username)

                @client.on(ConnectEvent)
                async def on_connect(event: ConnectEvent):
                    logger.info("[TIKTOK] Đã kết nối vào live của %s", self.username)

                @client.on(CommentEvent)
                async def on_comment(event: CommentEvent):
                    uname = event.user.unique_id if event.user else "unknown"
                    text = event.comment or ""
                    self._handle_comment(uname, text)

                @client.on(DisconnectEvent)
                async def on_disconnect(event: DisconnectEvent):
                    logger.warning("[TIKTOK] Mất kết nối, thử lại sau 10 giây...")

                try:
                    await client.start()
                except Exception as e:
                    logger.error("[TIKTOK] Lỗi kết nối: %s", e)

                if not self._stop_event.is_set():
                    await asyncio.sleep(10)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_async_run())
        finally:
            loop.close()

    # ── Khởi động / Dừng / Restart ────────────────────────────────────────────

    def start(self):
        """Khởi động listener trong background thread."""
        if self._thread and self._thread.is_alive():
            logger.info("[TIKTOK] Listener đã chạy, không khởi động lại")
            return

        self._stop_event.clear()
        if DEMO_MODE:
            logger.info("[TIKTOK] Chạy ở chế độ DEMO")
            target = lambda: _run_demo_mode(self.queue, self._stop_event)
            name = "DemoThread"
        elif USE_NODEJS_BRIDGE:
            logger.info("[TIKTOK] Dùng Node.js bridge → %s", self.username)
            target = self._run_nodejs_bridge
            name = "NodeBridgeThread"
        else:
            logger.info("[TIKTOK] Dùng TikTokLive Python → %s", self.username)
            target = self._run_live
            name = "TikTokThread"

        self._thread = threading.Thread(target=target, daemon=True, name=name)
        self._thread.start()
        logger.info("[TIKTOK] Listener đã khởi động (thread: %s)", name)

    def stop(self):
        """Dừng listener."""
        self._stop_event.set()
        if self._node_proc and self._node_proc.poll() is None:
            self._node_proc.terminate()
            try:
                self._node_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._node_proc.kill()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[TIKTOK] Listener đã dừng")

    def restart(self, new_username: str | None = None):
        """Dừng và khởi động lại listener, có thể đổi username."""
        logger.info("[TIKTOK] Đang restart listener...")
        self.stop()
        if new_username:
            self.username = new_username
            logger.info("[TIKTOK] Username đổi thành: %s", self.username)
        self.start()
