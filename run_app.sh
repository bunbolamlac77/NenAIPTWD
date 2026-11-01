#!/bin/bash
# ==============================================================================
# Script Khởi Chạy NenAI - Studio Wedding Background & Relighting AI
# Chạy 100% Local AI trên MacBook Pro M1
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PYTHON_BIN="/Users/phuthanh/LLMLocalAI/.venv/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "❌ Không tìm thấy Python tại $PYTHON_BIN"
    exit 1
fi

echo "=================================================================="
echo "🚀 KHỞI ĐỘNG NENAI STUDIO - BẢN 1: LUXURY GOLD & TITANIUM"
echo "📂 Thư mục dự án: $DIR"
echo "🎨 Photoshop UXP Panel: $DIR/ps-panel"
echo "🧠 AI Engine: Apple Silicon M1 (MPS Metal Accelerated)"
echo "💾 Kho Mẫu (Studio Vault): $DIR/presets"
echo "🌐 API Server: http://127.0.0.1:8989"
echo "=================================================================="

# Tự động mở trình duyệt sau khi server khởi động
(sleep 1 && open "http://127.0.0.1:8989") &

# Khởi chạy server FastAPI
exec "$PYTHON_BIN" -m uvicorn app:app --host 127.0.0.1 --port 8989
