# ── Stage 1: 前端构建 ──
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: 最终镜像 ──
FROM python:3.11-slim
WORKDIR /app

# 安装后端依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码到临时目录，再选择性复制，避免 backend/config/ 覆盖 /app/config 挂载点
COPY backend/ /tmp/backend-src/

# 复制后端代码（排除 config 子目录，因为它会和 volume 挂载点冲突）
RUN cp -r /tmp/backend-src/* /app/ && \
    cp -r /tmp/backend-src/.??* /app/ 2>/dev/null || true && \
    rm -rf /tmp/backend-src /app/config

# 把配置模板放到不会被 volume 覆盖的安全路径
RUN mkdir -p /app/templates
COPY backend/config/env.template /app/templates/env.template

# 持久化挂载点：data/ 和 config/
# 首次启动时 main.py 从 /app/templates/env.template → /app/config/.env
RUN mkdir -p /app/data/images /app/data/barcodes /app/config

EXPOSE 8000

# 环境变量
ENV DB_PATH=/app/data/jade.db
ENV IMAGE_DIR=/app/data/images
ENV CORS_ORIGINS=*
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
