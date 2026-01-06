# Frontend Dockerfile for TARA Report Generator
# Multi-stage build for production

# Stage 1: Build
FROM node:20-alpine AS builder

# === 1. 配置 Alpine 使用阿里云镜像 ===
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# === 2. 配置 npm 使用淘宝镜像 ===
RUN npm config set registry https://registry.npmmirror.com

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* pnpm-lock.yaml* ./

# Install dependencies (prefer pnpm if lock file exists)
RUN if [ -f pnpm-lock.yaml ]; then \
        npm install -g pnpm && pnpm config set registry https://registry.npmmirror.com && pnpm install --frozen-lockfile; \
    elif [ -f package-lock.json ]; then \
        npm ci; \
    else \
        npm install; \
    fi

# Copy source files
COPY . .

# Build the application
RUN npm run build

# Stage 2: Production with Nginx
FROM nginx:alpine

# === 配置 Alpine 使用阿里云镜像 ===
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 30031

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
