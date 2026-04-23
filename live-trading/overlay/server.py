"""
Flask server cung cấp overlay web cho OBS Browser Source.
GET  /                  → HTML overlay
GET  /api/state         → JSON state của queue (poll mỗi 2 giây)
POST /api/skip          → Bỏ qua mã hiện tại
POST /api/clear         → Xóa toàn bộ queue
GET  /api/settings      → Lấy cài đặt hiện tại
POST /api/settings      → Cập nhật cài đặt
POST /api/reconnect     → Đổi username và kết nối lại TikTok
"""

import logging
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from config import INTERVAL_SECONDS as _DEFAULT_INTERVAL, TIKTOK_USERNAME, MAX_QUEUE_SIZE

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

_queue_manager = None
_listener      = None

# Settings động — đổi được qua API không cần restart app
_settings = {
    "interval_seconds": _DEFAULT_INTERVAL,
    "tiktok_username":  TIKTOK_USERNAME,
    "max_queue_size":   MAX_QUEUE_SIZE,
}


def get_interval() -> int:
    return _settings["interval_seconds"]


def set_queue_manager(qm):
    global _queue_manager
    _queue_manager = qm


def set_listener(l):
    global _listener
    _listener = l


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state")
def api_state():
    if _queue_manager is None:
        return jsonify({"error": "queue_manager chưa được khởi tạo"}), 500
    state = _queue_manager.get_state()
    state["interval_seconds"] = _settings["interval_seconds"]
    return jsonify(state)


@app.route("/api/skip", methods=["POST"])
def api_skip():
    if _queue_manager is None:
        return jsonify({"error": "queue_manager chưa được khởi tạo"}), 500
    nxt = _queue_manager.skip()
    logger.info("[OVERLAY] Skip → %s", nxt["symbol"] if nxt else "None")
    return jsonify({"skipped": True, "next": nxt})


@app.route("/api/clear", methods=["POST"])
def api_clear():
    if _queue_manager is None:
        return jsonify({"error": "queue_manager chưa được khởi tạo"}), 500
    _queue_manager.clear()
    return jsonify({"cleared": True})


@app.route("/api/settings", methods=["GET"])
def api_settings_get():
    return jsonify(_settings)


@app.route("/api/settings", methods=["POST"])
def api_settings_post():
    data = request.get_json(force=True, silent=True) or {}

    if "interval_seconds" in data:
        val = max(5, min(300, int(data["interval_seconds"])))
        _settings["interval_seconds"] = val
        logger.info("[OVERLAY] Interval đổi thành %ds", val)

    if "max_queue_size" in data:
        val = max(1, min(100, int(data["max_queue_size"])))
        _settings["max_queue_size"] = val
        if _queue_manager:
            _queue_manager.max_size = val
        logger.info("[OVERLAY] Max queue size đổi thành %d", val)

    return jsonify(_settings)


@app.route("/api/reconnect", methods=["POST"])
def api_reconnect():
    """Đổi TikTok username và kết nối lại listener."""
    if _listener is None:
        return jsonify({"error": "listener chưa được khởi tạo"}), 500

    data = request.get_json(force=True, silent=True) or {}
    new_username = data.get("username", "").strip()
    if not new_username:
        return jsonify({"error": "Thiếu username"}), 400

    _settings["tiktok_username"] = new_username
    logger.info("[OVERLAY] Reconnect → %s", new_username)

    import threading
    threading.Thread(
        target=_listener.restart,
        args=(new_username,),
        daemon=True,
        name="RestartThread",
    ).start()

    return jsonify({"ok": True, "username": new_username})


def run_server(host: str = "0.0.0.0", port: int = 5000):
    logger.info("[OVERLAY] Server khởi động tại http://localhost:%d", port)
    app.run(host=host, port=port, debug=False, use_reloader=False)
