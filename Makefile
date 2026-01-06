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
	@echo "服务管理:"
	@echo "  make logs-data     - 查看数据服务日志"
	@echo "  make logs-report   - 查看报告服务日志"
	@echo "  make logs-mysql    - 查看MySQL日志"
	@echo "  make logs-minio    - 查看MinIO日志"
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
	@echo "   前端: http://localhost:30031"
	@echo "   数据服务API: http://localhost:8001"
	@echo "   数据服务文档: http://localhost:8001/docs"
	@echo "   报告服务API: http://localhost:8002"
	@echo "   报告服务文档: http://localhost:8002/docs"
	@echo "   MinIO控制台: http://localhost:9001 (minioadmin/minioadmin123)"
	@echo "   phpMyAdmin: http://localhost:8080 (root/root123456)"

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

# ==================== 服务日志 ====================

# 数据服务日志
logs-data:
	docker compose logs data-service

logs-data-f:
	docker compose logs -f data-service

# 报告服务日志
logs-report:
	docker compose logs report-service

logs-report-f:
	docker compose logs -f report-service

# MySQL日志
logs-mysql:
	docker compose logs mysql

# MinIO日志
logs-minio:
	docker compose logs minio

# 前端日志
logs-frontend:
	docker compose logs frontend

# phpMyAdmin日志
logs-phpmyadmin:
	docker compose logs phpmyadmin

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

# ==================== 单独服务命令 ====================

# 只构建数据服务
build-data:
	docker compose build data-service

# 只构建报告服务
build-report:
	docker compose build report-service

# 只构建前端
build-frontend:
	docker compose build frontend

# 只启动基础设施(MySQL + MinIO)
up-infra:
	docker compose up -d mysql minio

# 只启动数据服务
up-data:
	docker compose up -d data-service

# 只启动报告服务
up-report:
	docker compose up -d report-service

# 只启动前端
up-frontend:
	docker compose up -d frontend

# 进入数据服务容器
shell-data:
	docker compose exec data-service /bin/bash

# 进入报告服务容器
shell-report:
	docker compose exec report-service /bin/bash

# 进入MySQL容器
shell-mysql:
	docker compose exec mysql mysql -u tara -ptara123456 tara_db

# ==================== 开发命令 ====================

# 启动开发环境
dev:
	@echo "🔧 启动开发环境..."
	@echo "1. 首先启动基础设施:"
	@echo "   make up-infra"
	@echo ""
	@echo "2. 然后在各终端分别运行:"
	@echo "   终端1 (数据服务): cd backend/data-service && pip install -e . && uvicorn main:app --reload --port 8001"
	@echo "   终端2 (报告服务): cd backend/report-service && pip install -e . && uvicorn main:app --reload --port 8002"
	@echo "   终端3 (前端): cd frontend && npm install && npm run dev"
