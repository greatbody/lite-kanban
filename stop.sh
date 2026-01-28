#!/bin/bash

# Lite Kanban - 停止后台服务脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/kanban.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "❌ 未找到运行中的服务"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "❌ 服务未运行 (PID: $PID)"
    rm -f "$PID_FILE"
    exit 1
fi

echo "🛑 停止 Lite Kanban 服务 (PID: $PID)..."
kill "$PID"

# 等待进程结束
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ 服务已停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 如果还没停止，强制终止
if ps -p "$PID" > /dev/null 2>&1; then
    echo "⚠️  强制终止服务..."
    kill -9 "$PID"
    sleep 1
fi

rm -f "$PID_FILE"
echo "✅ 服务已停止"
