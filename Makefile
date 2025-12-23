# TARA Report Generator - Makefile
# 一键部署和管理命令

.PHONY: help build up down restart logs clean dev install

# 默认目标：显示帮助信息
help:
	@echo "TARA Report Generator - 可用命令"
	@echo "=================================="
	@echo ""
	@echo "Docker Compose 部署命令:"
	@echo "  make build      - 构建所有Docker镜像"
	@echo "  make up         - 启动所有服务(后台运行)"
	@echo "  make down       - 停止并移除所有服务"
	@echo "  make restart    - 重启所有服务"
	@echo "  make logs       - 查看所有服务日志"
	@echo "  make logs-f     - 实时查看日志(follow模式)"
	@echo ""
	@echo "快捷命令:"
	@echo "  make deploy     - 一键部署(build + up)"
	@echo "  make rebuild    - 强制重新构建并启动"
	@echo ""
	@echo "开发命令:"
	@echo "  make dev        - 启动开发环境"
	@echo "  make install    - 安装所有依赖"
	@echo ""
	@echo "清理命令:"
	@echo "  make clean      - 清理Docker资源"
	@echo "  make clean-all  - 深度清理(包括volumes)"
	@echo ""
	@echo "状态命令:"
	@echo "  make status     - 查看服务状态"
	@echo "  make ps         - 查看容器状态"

# ==================== Docker Compose 命令 ====================

# 构建Docker镜像
build:
	@echo "🔨 正在构建Docker镜像..."
	docker compose build
	@echo "✅ 构建完成!"

# 启动服务(后台运行)
up:
	@echo "🚀 正在启动服务..."
	docker compose up -d
	@echo "✅ 服务已启动!"
	@echo ""
	@echo "📝 访问地址:"
	@echo "   前端: http://localhost"
	@echo "   后端API: http://localhost:8000"
	@echo "   API文档: http://localhost:8000/docs"

# 停止服务
down:
	@echo "🛑 正在停止服务..."
	docker compose down
	@echo "✅ 服务已停止!"

# 重启服务
restart:
	@echo "🔄 正在重启服务..."
	docker compose restart
	@echo "✅ 服务已重启!"

# 查看日志
logs:
	docker compose logs

# 实时查看日志
logs-f:
	docker compose logs -f

# ==================== 快捷命令 ====================

# 一键部署
deploy: build up
	@echo ""
	@echo "🎉 部署完成!"

# 强制重新构建并启动
rebuild:
	@echo "🔨 强制重新构建..."
	docker compose build --no-cache
	docker compose up -d --force-recreate
	@echo "✅ 重新构建并启动完成!"

# ==================== 开发命令 ====================

# 启动开发环境
dev:
	@echo "🔧 启动开发环境..."
	@echo "请在两个终端分别运行:"
	@echo "  终端1 (后端): cd backend && pip install -e . && uvicorn tara_api.main:app --reload"
	@echo "  终端2 (前端): cd frontend && npm install && npm run dev"

# 安装依赖
install:
	@echo "📦 安装后端依赖..."
	cd backend && pip install -e .
	@echo "📦 安装前端依赖..."
	cd frontend && npm install
	@echo "✅ 依赖安装完成!"

# ==================== 清理命令 ====================

# 清理Docker资源
clean:
	@echo "🧹 清理Docker资源..."
	docker compose down --rmi local
	@echo "✅ 清理完成!"

# 深度清理(包括volumes)
clean-all:
	@echo "🧹 深度清理Docker资源..."
	docker compose down --rmi local -v
	docker system prune -f
	@echo "✅ 深度清理完成!"

# ==================== 状态命令 ====================

# 查看服务状态
status:
	@echo "📊 服务状态:"
	docker compose ps

# 查看容器状态(别名)
ps: status

# 查看后端日志
logs-backend:
	docker compose logs backend

# 查看前端日志
logs-frontend:
	docker compose logs frontend

# ==================== 单独服务命令 ====================

# 只构建后端
build-backend:
	docker compose build backend

# 只构建前端
build-frontend:
	docker compose build frontend

# 只启动后端
up-backend:
	docker compose up -d backend

# 只启动前端
up-frontend:
	docker compose up -d frontend

# 进入后端容器
shell-backend:
	docker compose exec backend /bin/bash

# 进入前端容器
shell-frontend:
	docker compose exec frontend /bin/sh
