# TARA Report Generator - Makefile
# 一键部署和管理命令

.PHONY: help build up down restart logs clean dev install list

# 服务名称定义
SERVICES := mysql minio data-service report-service frontend phpmyadmin

# 默认目标：显示帮助信息
help:
	@echo "TARA Report Generator - 可用命令"
	@echo "=================================="
	@echo ""
	@echo "Docker Compose 部署命令:"
	@echo "  make build           - 构建所有Docker镜像"
	@echo "  make up              - 启动所有服务(后台运行)"
	@echo "  make down            - 停止并移除所有服务"
	@echo "  make restart         - 重启所有服务"
	@echo "  make logs            - 查看所有服务日志"
	@echo "  make logs-f          - 实时查看日志(follow模式)"
	@echo ""
	@echo "快捷命令:"
	@echo "  make deploy          - 一键部署(build + up)"
	@echo "  make rebuild         - 强制重新构建并启动所有服务"
	@echo ""
	@echo "状态查看:"
	@echo "  make list            - 查看所有服务运行状态和健康检查"
	@echo "  make status          - 查看服务状态"
	@echo "  make ps              - 查看容器状态"
	@echo ""
	@echo "单个服务操作 (SERVICE=服务名):"
	@echo "  make build-one SERVICE=xxx    - 构建单个服务"
	@echo "  make up-one SERVICE=xxx       - 启动单个服务"
	@echo "  make rebuild-one SERVICE=xxx  - 重建单个服务"
	@echo "  make restart-one SERVICE=xxx  - 重启单个服务"
	@echo "  make stop-one SERVICE=xxx     - 停止单个服务"
	@echo "  make logs-one SERVICE=xxx     - 查看单个服务日志"
	@echo ""
	@echo "  可用服务名: mysql, minio, data-service, report-service, frontend, phpmyadmin"
	@echo ""
	@echo "服务快捷命令:"
	@echo "  make build-data      - 构建数据服务"
	@echo "  make build-report    - 构建报告服务"
	@echo "  make build-frontend  - 构建前端"
	@echo "  make up-data         - 启动数据服务"
	@echo "  make up-report       - 启动报告服务"
	@echo "  make up-frontend     - 启动前端"
	@echo "  make up-infra        - 启动基础设施(MySQL+MinIO)"
	@echo "  make rebuild-data    - 重建数据服务"
	@echo "  make rebuild-report  - 重建报告服务"
	@echo "  make rebuild-frontend- 重建前端"
	@echo ""
	@echo "服务日志:"
	@echo "  make logs-data       - 查看数据服务日志"
	@echo "  make logs-report     - 查看报告服务日志"
	@echo "  make logs-mysql      - 查看MySQL日志"
	@echo "  make logs-minio      - 查看MinIO日志"
	@echo ""
	@echo "清理命令:"
	@echo "  make clean           - 清理Docker资源"
	@echo "  make clean-all       - 深度清理(包括volumes)"

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
	@echo "   报告服务API: http://localhost:8006"
	@echo "   报告服务文档: http://localhost:8006/docs"
	@echo "   MinIO控制台: http://localhost:30034 (minioadmin/minioadmin123)"
	@echo "   phpMyAdmin: http://localhost:30033 (root/root123456)"

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

# 查看所有服务运行状态和健康检查
list:
	@echo "╔════════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                        TARA Report Generator - 服务状态                        ║"
	@echo "╠════════════════════════════════════════════════════════════════════════════════╣"
	@echo ""
	@echo "📋 容器运行状态:"
	@echo "────────────────────────────────────────────────────────────────────────────────"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker compose ps
	@echo ""
	@echo "🏥 健康检查状态:"
	@echo "────────────────────────────────────────────────────────────────────────────────"
	@for service in mysql minio data-service report-service frontend; do \
		container=$$(docker compose ps -q $$service 2>/dev/null); \
		if [ -n "$$container" ]; then \
			status=$$(docker inspect --format='{{.State.Status}}' $$container 2>/dev/null); \
			health=$$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}' $$container 2>/dev/null); \
			if [ "$$status" = "running" ]; then \
				if [ "$$health" = "healthy" ]; then \
					printf "  ✅ %-20s 运行中    健康\n" "$$service"; \
				elif [ "$$health" = "unhealthy" ]; then \
					printf "  ❌ %-20s 运行中    不健康\n" "$$service"; \
				elif [ "$$health" = "starting" ]; then \
					printf "  ⏳ %-20s 运行中    启动中\n" "$$service"; \
				else \
					printf "  ✅ %-20s 运行中    -\n" "$$service"; \
				fi; \
			else \
				printf "  ⭕ %-20s 未运行\n" "$$service"; \
			fi; \
		else \
			printf "  ⭕ %-20s 未启动\n" "$$service"; \
		fi; \
	done
	@echo ""
	@echo "🔗 服务访问地址:"
	@echo "────────────────────────────────────────────────────────────────────────────────"
	@echo "  前端界面:        http://localhost:30031"
	@echo "  数据服务API:     http://localhost:8001/docs"
	@echo "  报告服务API:     http://localhost:8006/docs"
	@echo "  MinIO控制台:     http://localhost:30034 (minioadmin/minioadmin123)"
	@echo "  phpMyAdmin:      http://localhost:30033 (root/root123456)"
	@echo ""
	@echo "╚════════════════════════════════════════════════════════════════════════════════╝"

# ==================== 单独服务命令 ====================

# 通用单服务命令 (使用 SERVICE 变量)
# 用法: make build-one SERVICE=data-service

# 构建单个服务
build-one:
ifndef SERVICE
	@echo "❌ 请指定服务名: make build-one SERVICE=服务名"
	@echo "   可用服务: mysql, minio, data-service, report-service, frontend, phpmyadmin"
	@exit 1
endif
	@echo "🔨 正在构建服务: $(SERVICE)..."
	docker compose build $(SERVICE)
	@echo "✅ $(SERVICE) 构建完成!"

# 启动单个服务
up-one:
ifndef SERVICE
	@echo "❌ 请指定服务名: make up-one SERVICE=服务名"
	@echo "   可用服务: mysql, minio, data-service, report-service, frontend, phpmyadmin"
	@exit 1
endif
	@echo "🚀 正在启动服务: $(SERVICE)..."
	docker compose up -d $(SERVICE)
	@echo "✅ $(SERVICE) 已启动!"

# 重建单个服务 (无缓存构建并重新创建)
rebuild-one:
ifndef SERVICE
	@echo "❌ 请指定服务名: make rebuild-one SERVICE=服务名"
	@echo "   可用服务: mysql, minio, data-service, report-service, frontend, phpmyadmin"
	@exit 1
endif
	@echo "🔨 正在重建服务: $(SERVICE)..."
	docker compose build --no-cache $(SERVICE)
	docker compose up -d --force-recreate $(SERVICE)
	@echo "✅ $(SERVICE) 重建并启动完成!"

# 重启单个服务
restart-one:
ifndef SERVICE
	@echo "❌ 请指定服务名: make restart-one SERVICE=服务名"
	@echo "   可用服务: mysql, minio, data-service, report-service, frontend, phpmyadmin"
	@exit 1
endif
	@echo "🔄 正在重启服务: $(SERVICE)..."
	docker compose restart $(SERVICE)
	@echo "✅ $(SERVICE) 已重启!"

# 停止单个服务
stop-one:
ifndef SERVICE
	@echo "❌ 请指定服务名: make stop-one SERVICE=服务名"
	@echo "   可用服务: mysql, minio, data-service, report-service, frontend, phpmyadmin"
	@exit 1
endif
	@echo "🛑 正在停止服务: $(SERVICE)..."
	docker compose stop $(SERVICE)
	@echo "✅ $(SERVICE) 已停止!"

# 查看单个服务日志
logs-one:
ifndef SERVICE
	@echo "❌ 请指定服务名: make logs-one SERVICE=服务名"
	@echo "   可用服务: mysql, minio, data-service, report-service, frontend, phpmyadmin"
	@exit 1
endif
	docker compose logs $(SERVICE)

# 实时查看单个服务日志
logs-one-f:
ifndef SERVICE
	@echo "❌ 请指定服务名: make logs-one-f SERVICE=服务名"
	@echo "   可用服务: mysql, minio, data-service, report-service, frontend, phpmyadmin"
	@exit 1
endif
	docker compose logs -f $(SERVICE)

# ==================== 服务快捷命令 ====================

# 只构建数据服务
build-data:
	@echo "🔨 正在构建数据服务..."
	docker compose build data-service
	@echo "✅ 数据服务构建完成!"

# 只构建报告服务
build-report:
	@echo "🔨 正在构建报告服务..."
	docker compose build report-service
	@echo "✅ 报告服务构建完成!"

# 只构建前端
build-frontend:
	@echo "🔨 正在构建前端..."
	docker compose build frontend
	@echo "✅ 前端构建完成!"

# 只启动基础设施(MySQL + MinIO)
up-infra:
	@echo "🚀 正在启动基础设施..."
	docker compose up -d mysql minio
	@echo "✅ MySQL 和 MinIO 已启动!"

# 只启动数据服务
up-data:
	@echo "🚀 正在启动数据服务..."
	docker compose up -d data-service
	@echo "✅ 数据服务已启动! 访问: http://localhost:8001/docs"

# 只启动报告服务
up-report:
	@echo "🚀 正在启动报告服务..."
	docker compose up -d report-service
	@echo "✅ 报告服务已启动! 访问: http://localhost:8006/docs"

# 只启动前端
up-frontend:
	@echo "🚀 正在启动前端..."
	docker compose up -d frontend
	@echo "✅ 前端已启动! 访问: http://localhost:30031"

# 重建数据服务
rebuild-data:
	@echo "🔨 正在重建数据服务..."
	docker compose build --no-cache data-service
	docker compose up -d --force-recreate data-service
	@echo "✅ 数据服务重建并启动完成!"

# 重建报告服务
rebuild-report:
	@echo "🔨 正在重建报告服务..."
	docker compose build --no-cache report-service
	docker compose up -d --force-recreate report-service
	@echo "✅ 报告服务重建并启动完成!"

# 重建前端
rebuild-frontend:
	@echo "🔨 正在重建前端..."
	docker compose build --no-cache frontend
	docker compose up -d --force-recreate frontend
	@echo "✅ 前端重建并启动完成!"

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
