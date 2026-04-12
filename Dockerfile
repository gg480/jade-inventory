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

# 复制后端代码
COPY backend/ .

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./static

# 数据目录
RUN mkdir -p /app/data/images

EXPOSE 8000

# 环境变量
ENV DB_PATH=/app/data/jade.db
ENV IMAGE_DIR=/app/data/images
ENV CORS_ORIGINS=*
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
