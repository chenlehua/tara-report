# Report Service Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# === 配置 pip 使用阿里云镜像 ===
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

# Install system dependencies (including Chinese fonts for PDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules
COPY shared/ ./shared/

# Copy service files
COPY report-service/pyproject.toml ./
COPY report-service/main.py ./
COPY report-service/__init__.py ./
COPY report-service/tara_excel_generator.py ./
COPY report-service/tara_pdf_generator.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 8002

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
