#!/bin/bash

# Lite Kanban - 后台启动脚本
# 服务将在后台运行，使用 stop.sh 停止

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
PID_FILE="$SCRIPT_DIR/kanban.pid"
LOG_FILE="$SCRIPT_DIR/kanban.log"

cd "$BACKEND_DIR"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "❌ Lite Kanban 已经在运行 (PID: $PID)"
        echo "   访问: http://localhost:5001"
        echo "   停止服务请运行: ./stop.sh"
        exit 1
    else
        # PID 文件存在但进程不存在，删除旧的 PID 文件
        rm -f "$PID_FILE"
    fi
fi

echo "===================================================="
echo "🚀 启动 Lite Kanban (后台模式)"
echo "===================================================="

# 启动服务
if [ -n "$VIRTUAL_ENV" ]; then
    nohup python app.py > "$LOG_FILE" 2>&1 &
else
    if [ -f "$HOME/.venv/bin/activate" ]; then
        nohup bash -c "source $HOME/.venv/bin/activate && python app.py" > "$LOG_FILE" 2>&1 &
    else
        nohup python3 app.py > "$LOG_FILE" 2>&1 &
    fi
fi

PID=$!
echo $PID > "$PID_FILE"

# 等待服务启动
sleep 2

# 检查服务是否成功启动
if ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ 服务已启动"
    echo "   PID: $PID"
    echo "   访问: http://localhost:5001"
    echo "   日志: $LOG_FILE"
    echo "   停止服务: ./stop.sh"
    echo "===================================================="
else
    echo "❌ 服务启动失败，请查看日志: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
