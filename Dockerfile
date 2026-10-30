# ============================================================================
# Stage 1: Build & Dependencies
# ============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Tạo virtual environment độc lập
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Production Runtime
# ============================================================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Cài đặt curl phục vụ container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Sao chép virtual environment từ builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Tạo người dùng không đặc quyền (non-root) để bảo mật container
RUN useradd -m -u 1001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

# Sao chép mã nguồn ứng dụng
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser pytest.ini ./
COPY --chown=appuser:appuser main.py ./

# Chuyển sang quyền appuser
USER appuser

# Khai báo port của FastAPI và Web Dashboard
EXPOSE 8000

# Thiết lập Healthcheck kiểm tra định kỳ endpoint /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Khởi chạy Uvicorn server
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
