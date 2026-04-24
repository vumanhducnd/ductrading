"""
Quản lý hàng đợi mã cổ phiếu từ TikTok Live.
Hỗ trợ deduplication, vote counting và giới hạn kích thước queue.
"""

import threading
import logging
from datetime import datetime, timedelta
from config import MAX_QUEUE_SIZE

logger = logging.getLogger(__name__)


class QueueManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.max_size: int = MAX_QUEUE_SIZE

        # Danh sách mã đang chờ: [{symbol, votes, requester, timestamp}]
        self.queue: list[dict] = []

        # Mã đang được hiển thị trên TradingView
        self.current: dict | None = None

        # Tổng lượt request mỗi mã từ đầu session {symbol: count}
        self.stats: dict[str, int] = {}

        # Thời điểm bắt đầu hiển thị mã hiện tại (dùng cho countdown overlay)
        self.current_started_at: datetime | None = None
        self._pause_started_at: datetime | None = None
        self._paused_duration: timedelta = timedelta(0)

    # ── Thêm mã vào queue ────────────────────────────────────────────────────

    def add(self, symbol: str, username: str) -> str:
        """
        Thêm mã vào queue hoặc tăng votes nếu đã tồn tại.
        Trả về 'added', 'voted', 'current', hoặc 'full'.
        """
        symbol = symbol.upper().strip()
        with self._lock:
            # Cập nhật thống kê tổng
            self.stats[symbol] = self.stats.get(symbol, 0) + 1

            # Bỏ qua nếu đang là mã hiện tại
            if self.current and self.current["symbol"] == symbol:
                logger.debug("[QUEUE] %s đang được hiển thị, bỏ qua vote từ %s", symbol, username)
                return "current"

            # Nếu mã đã có trong queue → tăng votes
            for item in self.queue:
                if item["symbol"] == symbol:
                    item["votes"] += 1
                    logger.info("[QUEUE] %s +1 vote → %d votes (từ %s)", symbol, item["votes"], username)
                    return "voted"

            # Queue đã đầy
            if len(self.queue) >= self.max_size:
                logger.warning("[QUEUE] Queue đầy (%d/%d), bỏ qua %s", len(self.queue), self.max_size, symbol)
                return "full"

            # Thêm mã mới
            self.queue.append({
                "symbol": symbol,
                "votes": 1,
                "requester": username,
                "timestamp": datetime.now().isoformat(),
            })
            logger.info("[QUEUE] %s thêm bởi %s (queue: %d mã)", symbol, username, len(self.queue))
            return "added"

    # ── Chuyển sang mã tiếp theo ─────────────────────────────────────────────

    def next(self) -> dict | None:
        """
        Lấy mã đầu tiên trong queue, đặt làm current.
        Trả về dict mã hoặc None nếu queue rỗng.
        """
        with self._lock:
            if not self.queue:
                self.current = None
                self.current_started_at = None
                self._pause_started_at = None
                self._paused_duration = timedelta(0)
                return None
            # Sắp xếp theo votes giảm dần trước khi lấy
            self.queue.sort(key=lambda x: x["votes"], reverse=True)
            self.current = self.queue.pop(0)
            self.current_started_at = datetime.now()
            self._pause_started_at = None
            self._paused_duration = timedelta(0)
            logger.info("[QUEUE] → Chuyển sang %s (%d votes)", self.current["symbol"], self.current["votes"])
            return self.current

    # ── Bỏ qua mã hiện tại ──────────────────────────────────────────────────

    def skip(self) -> dict | None:
        """Bỏ qua mã đang hiển thị, chuyển sang mã tiếp theo."""
        logger.info("[QUEUE] Skip mã hiện tại: %s", self.current["symbol"] if self.current else "None")
        return self.next()

    # ── Xóa queue ────────────────────────────────────────────────────────────

    def clear(self):
        """Xóa toàn bộ queue (giữ nguyên current và stats)."""
        with self._lock:
            self.queue.clear()
            logger.info("[QUEUE] Đã xóa toàn bộ queue")
    def pause_current(self):
        """Pause thời gian đếm ngược cho current item."""
        with self._lock:
            if self.current and self._pause_started_at is None:
                self._pause_started_at = datetime.now()
                logger.info("[QUEUE] Current paused")

    def resume_current(self):
        """Resume thời gian đếm ngược cho current item."""
        with self._lock:
            if self.current and self._pause_started_at is not None:
                self._paused_duration += datetime.now() - self._pause_started_at
                self._pause_started_at = None
                logger.info("[QUEUE] Current resumed")

    def is_paused(self) -> bool:
        return self._pause_started_at is not None
    # ── Lấy trạng thái cho overlay ───────────────────────────────────────────

    def get_state(self) -> dict:
        """Trả về JSON state đầy đủ để overlay hiển thị."""
        with self._lock:
            # Tính thời gian đã trôi qua kể từ khi hiển thị mã hiện tại
            elapsed = 0
            if self.current_started_at:
                elapsed = (datetime.now() - self.current_started_at).total_seconds()
                elapsed -= self._paused_duration.total_seconds()
                if self._pause_started_at is not None:
                    elapsed -= (datetime.now() - self._pause_started_at).total_seconds()
                elapsed = max(0, elapsed)

            return {
                "current": self.current,
                "queue": list(self.queue[:8]),          # Overlay chỉ hiện 8 mã
                "queue_full": list(self.queue),         # Full list cho API
                "stats": dict(self.stats),
                "total_requests": sum(self.stats.values()),
                "elapsed_seconds": round(elapsed, 1),
            }

    # ── Thống kê ─────────────────────────────────────────────────────────────

    def get_top_symbols(self, n: int = 10) -> list[tuple[str, int]]:
        """Trả về top N mã được request nhiều nhất."""
        with self._lock:
            return sorted(self.stats.items(), key=lambda x: x[1], reverse=True)[:n]
