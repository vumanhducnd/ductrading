/**
 * TikTok Live → Python bridge (tiktok-live-connector v2.x)
 *
 * Theo dõi live của bất kỳ tài khoản TikTok nào (public).
 * Mỗi comment ghi ra stdout dạng JSON line:
 *   {"user":"username","comment":"nội dung"}
 *
 * Biến môi trường:
 *   TIKTOK_USERNAME   - @username của người đang live (bắt buộc)
 *   TIKTOK_SESSION_ID - sessionid cookie từ tài khoản của bạn (nên có)
 *
 * Chạy: node bridge.js @username
 */

const { WebcastPushConnection } = require('tiktok-live-connector');

const username = process.env.TIKTOK_USERNAME || process.argv[2];

if (!username) {
    process.stderr.write('[BRIDGE] Lỗi: Thiếu username.\n');
    process.stderr.write('[BRIDGE] Dùng: node bridge.js @username\n');
    process.exit(1);
}

let connection = null;
let reconnectTimeout = null;

function connect() {
    const sessionId = process.env.TIKTOK_SESSION_ID || '';

    const options = {
        enableExtendedGiftInfo: false,
        enableWebsocketUpgrade: true,
        requestPollingIntervalMs: 2000,
        ...(sessionId && { sessionId }),
    };

    connection = new WebcastPushConnection(username, options);

    connection.connect()
        .then(state => {
            process.stderr.write(`[BRIDGE] Đã kết nối: ${username} (roomId: ${state.roomId})\n`);
        })
        .catch(err => {
            process.stderr.write(`[BRIDGE] Kết nối thất bại: ${err.message}\n`);
            if (!sessionId) {
                process.stderr.write('[BRIDGE] Gợi ý: Thêm TIKTOK_SESSION_ID vào .env để giảm bị chặn\n');
            }
            scheduleReconnect();
        });

    const sendComment = (data) => {
        const payload = JSON.stringify({
            user: data.nickname || data.uniqueId || 'unknown',  // tên hiển thị ưu tiên
            comment: data.comment || '',
        });
        process.stdout.write(payload + '\n');
    };

    // Tương thích v1.x ('comment') và v2.x ('chat')
    connection.on('chat',    sendComment);
    connection.on('comment', sendComment);

    connection.on('disconnected', () => {
        process.stderr.write('[BRIDGE] Mất kết nối, thử lại sau 10 giây...\n');
        scheduleReconnect();
    });

    connection.on('error', err => {
        process.stderr.write(`[BRIDGE] Lỗi: ${err.message || err}\n`);
    });
}

function scheduleReconnect() {
    if (reconnectTimeout) return;
    reconnectTimeout = setTimeout(() => {
        reconnectTimeout = null;
        process.stderr.write('[BRIDGE] Đang kết nối lại...\n');
        connect();
    }, 10_000);
}

process.on('SIGTERM', () => {
    if (reconnectTimeout) clearTimeout(reconnectTimeout);
    if (connection) connection.disconnect();
    process.exit(0);
});

process.on('SIGINT', () => {
    if (reconnectTimeout) clearTimeout(reconnectTimeout);
    if (connection) connection.disconnect();
    process.exit(0);
});

connect();
