# TARA Report Generator API

威胁分析和风险评估(TARA)报告生成后端服务。

## 功能特性

- 🚀 基于FastAPI的高性能API服务
- 📊 生成专业的TARA分析Excel报告
- 📄 生成专业的TARA分析PDF报告（支持中文）
- 🖼️ 支持图片上传（项目边界图、架构图等）
- 📁 报告管理（列表、预览、下载、删除）
- 🔄 支持JSON文件和JSON字符串两种输入方式
- 🗄️ MySQL数据库存储报告数据
- 📦 MinIO对象存储管理图片和报告文件

## 中文字体配置

PDF报告需要中文字体支持。系统会自动查找以下字体：

### Linux
```bash
# Ubuntu/Debian
sudo apt-get install fonts-wqy-zenhei fonts-wqy-microhei

# CentOS/RHEL/Fedora
sudo yum install wqy-zenhei-fonts wqy-microhei-fonts

# 或安装 Noto CJK 字体
sudo apt-get install fonts-noto-cjk
```

### Windows
系统自带的微软雅黑、宋体、黑体等字体会自动被识别。

### macOS
系统自带的苹方、华文黑体等字体会自动被识别。

### 手动安装字体
如果系统字体不可用，可以将中文字体文件（.ttf/.ttc）放到以下目录：
```
backend/app/generators/fonts/
```

推荐的开源中文字体：
- [文泉驿正黑](http://wenq.org/wqy2/index.cgi?ZenHei)
- [思源黑体](https://github.com/adobe-fonts/source-han-sans)
- [Noto Sans CJK](https://github.com/googlefonts/noto-cjk)

## 快速开始

### 安装依赖

```bash
# 使用pip安装
pip install -e .

# 或者使用pip安装依赖
pip install fastapi uvicorn openpyxl pillow python-multipart pydantic aiofiles sqlalchemy pymysql minio reportlab
```

### 启动服务

```bash
# 方式1: 使用命令行工具
tara-api

# 方式2: 使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式3: 直接运行
python -m app.main
```

### API文档

启动服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

所有API端点使用 `/api/v1` 前缀。

### 图片上传
```
POST /api/v1/images/upload
```
上传图片，支持类型：
- `item_boundary`: 项目边界图
- `system_architecture`: 系统架构图
- `software_architecture`: 软件架构图
- `dataflow`: 数据流图
- `attack_tree`: 攻击树图

### 批量上传生成报告
```
POST /api/v1/upload/batch
```
一键上传JSON数据和图片，生成报告。

### 上传报告数据
```
POST /api/v1/reports/upload
```
参数：
- `json_file`: JSON数据文件（可选）
- `json_data`: JSON数据字符串（可选）
- `item_boundary_image`: 项目边界图
- `system_architecture_image`: 系统架构图
- `software_architecture_image`: 软件架构图
- `dataflow_image`: 数据流图
- `attack_tree_images`: 攻击树图片列表

### 获取报告列表
```
GET /api/v1/reports
```

### 获取报告详情
```
GET /api/v1/reports/{report_id}
```

### 生成报告文件
```
POST /api/v1/reports/{report_id}/generate?format=xlsx|pdf
```

### 下载报告
```
GET /api/v1/reports/{report_id}/download?format=xlsx|pdf
GET /api/v1/reports/{report_id}/download/{format}
```

### 删除报告
```
DELETE /api/v1/reports/{report_id}
```

### 健康检查
```
GET /api/v1/health
```

## Docker部署

使用Docker Compose部署完整服务：

```bash
docker-compose up -d
```

服务将在以下端口运行：
- 前端: http://localhost:30031
- 后端API: http://localhost:8000
- MySQL: localhost:3306
- MinIO Console: http://localhost:9001

## 输入数据格式

详细的JSON输入格式请参考 `docs/API_SPECIFICATION.md`。

## 目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 主应用入口
│   ├── config.py               # 配置入口（兼容性）
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # API v1 路由器
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py   # 健康检查端点
│   │           ├── images.py   # 图片管理端点
│   │           ├── reports.py  # 报告管理端点
│   │           └── upload.py   # 批量上传端点
│   ├── common/
│   │   ├── __init__.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py     # 应用配置
│   │   ├── constants/
│   │   │   ├── __init__.py
│   │   │   └── enums.py        # 枚举常量
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── mysql.py        # MySQL连接
│   │   │   └── minio.py        # MinIO客户端
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── report.py       # 数据库模型
│   │   └── schemas/
│   │       └── __init__.py
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── excel_generator.py  # Excel报告生成器
│   │   └── pdf_generator.py    # PDF报告生成器
│   ├── repositories/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
├── Dockerfile
├── pyproject.toml
└── README.md
```

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| MYSQL_HOST | mysql | MySQL主机 |
| MYSQL_PORT | 3306 | MySQL端口 |
| MYSQL_USER | tara | MySQL用户名 |
| MYSQL_PASSWORD | tara123456 | MySQL密码 |
| MYSQL_DATABASE | tara_db | MySQL数据库名 |
| MINIO_ENDPOINT | minio:9000 | MinIO端点 |
| MINIO_ACCESS_KEY | minioadmin | MinIO访问密钥 |
| MINIO_SECRET_KEY | minioadmin123 | MinIO密钥 |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black app/
```

## License

MIT License
