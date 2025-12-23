# Backend Dockerfile for TARA Report Generator API
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# === 1. 彻底清理所有现有 APT 源 ===
RUN rm -f /etc/apt/sources.list && \
    rm -rf /etc/apt/sources.list.d/*

# === 2. 使用 bookworm（Debian 12）的阿里云源 ===
RUN echo "deb https://mirrors.aliyun.com/debian/ bookworm main non-free non-free-firmware contrib" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ bookworm-updates main non-free non-free-firmware contrib" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main non-free non-free-firmware contrib" >> /etc/apt/sources.list

# === 3. 配置 pip 使用阿里云镜像 ===
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY tara_api/ ./tara_api/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Create directories for uploads and reports
RUN mkdir -p /app/uploads/images /app/reports

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "tara_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
