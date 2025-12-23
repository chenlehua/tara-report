# TARA Backend Services

TARA (Threat Analysis and Risk Assessment) 后端服务，用于生成威胁分析和风险评估报告。

## 目录结构

```
backend/
├── tara-data-service/          # 数据服务 - 数据上传、解析和存储
│   ├── app/
│   │   ├── api/                # API 路由
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── common/             # 公共模块
│   │   │   ├── __init__.py
│   │   │   ├── database.py     # 数据库配置
│   │   │   ├── minio_client.py # MinIO 客户端
│   │   │   └── models.py       # 数据库模型
│   │   ├── config.py           # 配置模块
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI 入口
│   │   ├── repositories/       # 数据仓库层
│   │   │   ├── __init__.py
│   │   │   └── report.py
│   │   └── services/           # 业务逻辑层
│   │       ├── __init__.py
│   │       └── data.py
│   ├── Dockerfile
│   └── pyproject.toml
│
├── tara-report-service/        # 报告服务 - 报告生成和下载
│   ├── app/
│   │   ├── api/                # API 路由
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── common/             # 公共模块
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── minio_client.py
│   │   │   └── models.py
│   │   ├── config.py           # 配置模块
│   │   ├── generators/         # 报告生成器
│   │   │   ├── __init__.py
│   │   │   ├── excel.py        # Excel 报告生成器
│   │   │   └── pdf.py          # PDF 报告生成器
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI 入口
│   │   ├── repositories/       # 数据仓库层
│   │   │   ├── __init__.py
│   │   │   └── report.py
│   │   └── services/           # 业务逻辑层
│   │       ├── __init__.py
│   │       └── report.py
│   ├── Dockerfile
│   └── pyproject.toml
│
└── README.md
```

## 服务说明

### tara-data-service (数据服务)

负责数据的上传、解析和存储。

**主要功能：**
- 上传 JSON 数据和图片
- 解析并存储到 MySQL 数据库
- 图片存储到 MinIO
- 提供报告数据查询 API

**端口：** 8001

**主要 API：**
- `POST /api/upload/batch` - 批量上传 JSON 和图片
- `GET /api/reports` - 获取报告列表
- `GET /api/reports/{report_id}` - 获取报告详情
- `GET /api/reports/{report_id}/cover` - 获取封面信息
- `GET /api/reports/{report_id}/definitions` - 获取相关定义
- `GET /api/reports/{report_id}/assets` - 获取资产列表
- `GET /api/reports/{report_id}/attack-trees` - 获取攻击树
- `GET /api/reports/{report_id}/tara-results` - 获取 TARA 分析结果
- `DELETE /api/reports/{report_id}` - 删除报告

### tara-report-service (报告服务)

负责报告的生成和下载。

**主要功能：**
- 生成 Excel 报告
- 生成 PDF 报告
- 提供报告下载

**端口：** 8002

**主要 API：**
- `POST /api/reports/{report_id}/generate` - 生成报告 (支持 xlsx/pdf 格式)
- `GET /api/reports/{report_id}/download` - 下载报告
- `GET /api/reports/{report_id}/preview` - 获取报告预览数据
- `GET /api/reports/{report_id}/status` - 获取报告状态

## 运行方式

### 使用 Docker Compose（推荐）

```bash
# 在项目根目录下
docker-compose up -d
```

### 本地开发

```bash
# 数据服务
cd tara-data-service
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 报告服务
cd tara-report-service
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## 环境变量

### 通用配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| MYSQL_HOST | MySQL 主机 | mysql |
| MYSQL_PORT | MySQL 端口 | 3306 |
| MYSQL_USER | MySQL 用户名 | tara |
| MYSQL_PASSWORD | MySQL 密码 | tara123456 |
| MYSQL_DATABASE | MySQL 数据库名 | tara_db |
| MINIO_ENDPOINT | MinIO 端点 | minio:9000 |
| MINIO_ACCESS_KEY | MinIO 访问密钥 | minioadmin |
| MINIO_SECRET_KEY | MinIO 秘密密钥 | minioadmin123 |
| MINIO_SECURE | 是否使用 HTTPS | false |

### 数据服务配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| REPORT_SERVICE_URL | 报告服务地址 | http://report-service:8002 |

### 报告服务配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATA_SERVICE_URL | 数据服务地址 | http://data-service:8001 |

## 技术栈

- **Web 框架**: FastAPI
- **ORM**: SQLAlchemy
- **数据库**: MySQL 8.0
- **对象存储**: MinIO
- **报告生成**: openpyxl (Excel), reportlab (PDF)
