#!/bin/sh
# Railway 启动脚本
# Railway 会注入 PORT 环境变量,默认 8000
PORT="${PORT:-8000}"
echo "Starting uvicorn on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
