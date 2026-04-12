# 单阶段构建 — 前端已预构建，直接复制 static 目录
FROM python:3.11-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy pre-built frontend (已提交到仓库的构建产物)
COPY backend/static ./static

# Create data directories
RUN mkdir -p /app/data/images /app/data/barcodes

# Expose port
EXPOSE 8000

# Environment variables
ENV RESET_DB=false
ENV CORS_ORIGINS=*
ENV DEBUG=false

# 用 entrypoint.sh 读取 Zeabur 注入的 WEB_PORT
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
