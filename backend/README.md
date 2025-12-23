# TARA Report Generator API

威胁分析和风险评估(TARA)报告生成后端服务。

## 功能特性

- 🚀 基于FastAPI的高性能API服务
- 📊 生成专业的TARA分析Excel报告
- 🖼️ 支持图片上传（项目边界图、架构图等）
- 📁 报告管理（列表、预览、下载、删除）
- 🔄 支持JSON文件和JSON字符串两种输入方式

## 快速开始

### 安装依赖

```bash
# 使用pip安装
pip install -e .

# 或者使用pip安装依赖
pip install fastapi uvicorn openpyxl pillow python-multipart pydantic aiofiles
```

### 启动服务

```bash
# 方式1: 使用命令行工具
tara-api

# 方式2: 使用uvicorn
uvicorn tara_api.main:app --reload --host 0.0.0.0 --port 8000

# 方式3: 直接运行
python -m tara_api.main
```

### API文档

启动服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

### 图片上传
```
POST /api/images/upload
```
上传图片，支持类型：
- `item_boundary`: 项目边界图
- `system_architecture`: 系统架构图
- `software_architecture`: 软件架构图
- `dataflow`: 数据流图
- `attack_tree`: 攻击树图

### 生成报告
```
POST /api/reports/generate
```
参数：
- `json_file`: JSON数据文件（可选）
- `json_data`: JSON数据字符串（可选）
- `item_boundary_image`: 项目边界图片ID
- `system_architecture_image`: 系统架构图片ID
- `software_architecture_image`: 软件架构图片ID
- `dataflow_image`: 数据流图片ID
- `attack_tree_images`: 攻击树图片ID列表（逗号分隔）

### 获取报告列表
```
GET /api/reports
```

### 获取报告详情
```
GET /api/reports/{report_id}
```

### 下载报告
```
GET /api/reports/{report_id}/download
```

### 删除报告
```
DELETE /api/reports/{report_id}
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
├── pyproject.toml          # 项目配置
├── README.md               # 说明文档
├── tara_api/
│   ├── __init__.py
│   ├── main.py             # FastAPI应用
│   ├── models.py           # Pydantic数据模型
│   └── tara_excel_generator.py  # Excel生成器
├── uploads/                # 上传文件目录
│   └── images/             # 图片存储
└── reports/                # 生成的报告
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black tara_api/
```

## License

MIT License
