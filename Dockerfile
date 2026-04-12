# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production
FROM python:3.11-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./static

# Create data directories
RUN mkdir -p /app/data/images /app/data/barcodes

# Expose port (Zeabur uses PORT env var)
EXPOSE 8000

# Environment variables
ENV RESET_DB=false
ENV CORS_ORIGINS=*
ENV DEBUG=false
ENV PORT=8000

# Use shell form to support $PORT variable substitution
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
