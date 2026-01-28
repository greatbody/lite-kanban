#!/bin/bash

# Lite Kanban - 前台启动脚本
# 使用 Ctrl+C 可以终止服务

cd "$(dirname "$0")/backend"

echo "===================================================="
echo "🚀 启动 Lite Kanban (前台模式)"
echo "===================================================="
echo "访问: http://localhost:5001"
echo "按 Ctrl+C 停止服务"
echo "===================================================="
echo ""

# 检查是否在虚拟环境中
if [ -n "$VIRTUAL_ENV" ]; then
    python app.py
else
    # 尝试激活虚拟环境
    if [ -f "$HOME/.venv/bin/activate" ]; then
        source "$HOME/.venv/bin/activate"
        python app.py
    else
        # 直接使用系统 Python
        python3 app.py
    fi
fi
