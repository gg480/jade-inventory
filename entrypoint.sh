#!/bin/bash
# Zeabur 注入 WEB_PORT 环境变量，回退到 8000
PORT=${WEB_PORT:-${PORT:-8000}}
echo "Starting uvicorn on port $PORT"
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
