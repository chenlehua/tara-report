# Data Service Dockerfile
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

# === 2. 使用 trixie（Debian 13）的阿里云源 ===
RUN echo "deb https://mirrors.aliyun.com/debian/ trixie main non-free non-free-firmware contrib" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ trixie-updates main non-free non-free-firmware contrib" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security trixie-security main non-free non-free-firmware contrib" >> /etc/apt/sources.list

# === 3. 配置 pip 使用阿里云镜像 ===
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy service files
COPY data-service/pyproject.toml ./
COPY data-service/__init__.py ./
COPY data-service/app ./app

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
