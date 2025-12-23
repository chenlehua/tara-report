# TARA Report System

威胁分析和风险评估(TARA)报告生成系统 - 完整的前后端解决方案。

## 📋 项目概述

本系统提供车载信息安全的威胁分析和风险评估(TARA)报告自动生成功能，支持：

- 📤 上传JSON格式的分析数据
- 🖼️ 上传项目边界图、系统架构图等图片
- 📊 自动生成符合ISO/SAE 21434标准的Excel报告
- 👁️ 在线预览报告内容和图片
- ⬇️ 下载生成的Excel报告

## 🏗️ 系统架构

```
tara-report-system/
├── backend/                 # 后端项目 (FastAPI + Python)
│   ├── pyproject.toml       # Python项目配置
│   ├── tara_api/            # API模块
│   │   ├── main.py          # FastAPI应用
│   │   ├── models.py        # 数据模型
│   │   └── tara_excel_generator.py  # Excel生成器
│   └── README.md
│
├── frontend/                # 前端项目 (Vue 3)
│   ├── package.json         # Node项目配置
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── components/      # 可复用组件
│   │   └── api/             # API服务
│   └── README.md
│
└── README.md                # 本文件
```

## 🚀 快速开始

### 方式一：分别启动

#### 1. 启动后端服务

```bash
cd backend

# 安装依赖
pip install -e .

# 启动服务
uvicorn tara_api.main:app --reload --host 0.0.0.0 --port 8000
```

后端API将在 http://localhost:8000 运行。

#### 2. 启动前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:3000 运行。

### 方式二：使用Docker Compose

```bash
docker-compose up -d
```

## 📖 使用指南

### 1. 一键生成报告

1. 访问 http://localhost:3000/generator
2. 上传JSON数据文件（参考 `sample_input_data.json`）
3. 可选：上传架构图片
4. 点击"一键生成TARA报告"
5. 预览并下载报告

### 2. 报告中心

1. 访问 http://localhost:3000/reports
2. 查看所有已生成的报告
3. 点击"预览"查看报告详情
4. 点击"下载"获取Excel文件

## 📝 输入数据格式

JSON数据文件应包含以下结构：

```json
{
  "cover": {
    "report_title": "威胁分析和风险评估报告",
    "project_name": "项目名称",
    "document_number": "文档编号",
    "version": "V1.0"
  },
  "definitions": {
    "functional_description": "功能描述...",
    "assumptions": [...],
    "terminology": [...]
  },
  "assets": {
    "assets": [
      {
        "id": "P001",
        "name": "SOC",
        "category": "内部实体",
        "authenticity": true,
        "availability": true
      }
    ]
  },
  "attack_trees": {
    "attack_trees": [...]
  },
  "tara_results": {
    "results": [
      {
        "asset_id": "P001",
        "asset_name": "资产名称",
        "stride_model": "S欺骗",
        "threat_scenario": "威胁场景",
        "attack_vector": "本地",
        "safety_impact": "中等的",
        ...
      }
    ]
  }
}
```

详细格式请参考 `sample_input_data.json`。

## 🔌 API端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/images/upload | 上传图片 |
| GET | /api/images/{id} | 获取图片 |
| POST | /api/reports/generate | 生成报告 |
| GET | /api/reports | 获取报告列表 |
| GET | /api/reports/{id} | 获取报告详情 |
| GET | /api/reports/{id}/download | 下载报告 |
| DELETE | /api/reports/{id} | 删除报告 |

API文档：http://localhost:8000/docs

## 🛠️ 技术栈

### 后端
- Python 3.9+
- FastAPI
- openpyxl (Excel生成)
- Pillow (图片处理)
- Pydantic (数据验证)

### 前端
- Vue 3
- Vue Router 4
- Pinia
- Vite 5
- Tailwind CSS
- Axios

## 📄 许可证

MIT License
