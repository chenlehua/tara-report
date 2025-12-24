# TARA Report Generator API

威胁分析和风险评估(TARA)报告生成后端服务。

## 功能特性

- 🚀 基于FastAPI的高性能API服务
- 📊 生成专业的TARA分析Excel报告
- 📄 生成专业的TARA分析PDF报告（支持中文）
- 🖼️ 支持图片上传（项目边界图、架构图等）
- 📁 报告管理（列表、预览、下载、删除）
- 🔄 支持JSON文件和JSON字符串两种输入方式

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
pip install fastapi uvicorn openpyxl pillow python-multipart pydantic aiofiles reportlab
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

所有API端点都使用 `/api/v1` 前缀。

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

### 获取图片
```
GET /api/v1/images/{image_id}
```

### 生成报告
```
POST /api/v1/reports/generate
```
参数：
- `json_file`: JSON数据文件（可选）
- `json_data`: JSON数据字符串（可选）
- `item_boundary_image`: 项目边界图片ID
- `system_architecture_image`: 系统架构图片ID
- `software_architecture_image`: 软件架构图片ID
- `dataflow_image`: 数据流图片ID
- `attack_tree_images`: 攻击树图片ID列表（逗号分隔）

### 批量上传生成
```
POST /api/v1/upload/batch
```
一键上传JSON和图片文件，自动生成报告。

### 获取报告列表
```
GET /api/v1/reports
```

### 获取报告详情
```
GET /api/v1/reports/{report_id}
```

### 获取报告预览
```
GET /api/v1/reports/{report_id}/preview
```

### 下载Excel报告
```
GET /api/v1/reports/{report_id}/download
```

### 下载PDF报告
```
GET /api/v1/reports/{report_id}/download/pdf
```

### 生成PDF
```
POST /api/v1/reports/{report_id}/generate-pdf
```

### 删除报告
```
DELETE /api/v1/reports/{report_id}
```

### 健康检查
```
GET /api/v1/health
```

## 输入数据格式

```json
{
  "cover": {
    "report_title": "威胁分析和风险评估报告",
    "report_title_en": "Threat Analysis And Risk Assessment Report",
    "project_name": "项目名称",
    "data_level": "秘密",
    "document_number": "文档编号",
    "version": "V1.0",
    "author_date": "2025.01",
    "review_date": "2025.01"
  },
  "definitions": {
    "title": "相关定义",
    "functional_description": "功能描述...",
    "assumptions": [
      {"id": "ASM-01", "description": "假设描述"}
    ],
    "terminology": [
      {"abbreviation": "IVI", "english": "In-Vehicle Infotainment", "chinese": "车载信息娱乐系统"}
    ]
  },
  "assets": {
    "title": "资产列表",
    "assets": [
      {
        "id": "P001",
        "name": "SOC",
        "category": "内部实体",
        "remarks": "备注",
        "authenticity": true,
        "availability": true
      }
    ]
  },
  "attack_trees": {
    "title": "攻击树分析",
    "attack_trees": [
      {"title": "攻击树1", "image": ""}
    ]
  },
  "tara_results": {
    "title": "TARA分析结果",
    "results": [
      {
        "asset_id": "P001",
        "asset_name": "资产名称",
        "category": "内部实体",
        "security_attribute": "Authenticity",
        "stride_model": "S欺骗",
        "threat_scenario": "威胁场景描述",
        "attack_path": "攻击路径描述",
        "attack_vector": "本地",
        "attack_complexity": "低",
        "privileges_required": "低",
        "user_interaction": "不需要",
        "safety_impact": "中等的",
        "financial_impact": "中等的",
        "operational_impact": "重大的",
        "privacy_impact": "可忽略不计的",
        "security_requirement": "安全需求描述"
      }
    ]
  }
}
```

## 目录结构

```
backend/
├── pyproject.toml              # 项目配置
├── Dockerfile                  # Docker构建文件
├── README.md                   # 说明文档
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置入口
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # API路由器
│   │       └── endpoints/      # API端点
│   │           ├── images.py   # 图片管理
│   │           ├── reports.py  # 报告管理
│   │           ├── upload.py   # 批量上传
│   │           └── health.py   # 健康检查
│   ├── common/
│   │   ├── __init__.py
│   │   ├── config/
│   │   │   └── settings.py     # 应用配置
│   │   ├── constants/
│   │   │   └── enums.py        # 枚举常量
│   │   ├── database/
│   │   │   ├── mysql.py        # MySQL配置
│   │   │   └── minio.py        # MinIO配置
│   │   ├── models/
│   │   │   └── report.py       # SQLAlchemy ORM模型
│   │   └── schemas/
│   │       └── report.py       # Pydantic数据模型
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── excel_generator.py  # Excel报告生成器
│   │   └── pdf_generator.py    # PDF报告生成器
│   ├── repositories/           # 数据仓库层
│   │   └── __init__.py
│   └── services/               # 业务服务层
│       └── __init__.py
├── uploads/                    # 上传文件目录
│   └── images/                 # 图片存储
└── reports/                    # 生成的报告
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black app/
```

## Docker 部署

```bash
# 使用 docker-compose 启动所有服务
docker-compose up -d

# 仅构建后端服务
docker build -t tara-backend ./backend

# 运行后端容器
docker run -p 8000:8000 tara-backend
```

## License

MIT License
