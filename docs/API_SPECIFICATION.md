# TARA Report Generator API 规范

威胁分析和风险评估报告生成服务 - 统一API接口

## 服务信息

- **服务名称**: TARA Report Generator API
- **版本**: 1.0.0
- **端口**: 8000
- **API前缀**: `/api/v1`
- **描述**: 统一的TARA报告数据管理、生成和下载服务

## 基础信息

### 基础URL

```
http://backend:8000/api/v1
```

### 通用响应格式

成功响应:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

错误响应:
```json
{
  "detail": "错误信息"
}
```

---

## API 端点

### 1. 服务状态

#### GET /

获取服务状态信息。

**时序图:**
```
┌────────┐          ┌─────────┐
│ Client │          │ Backend │
└───┬────┘          └────┬────┘
    │                    │
    │  GET /             │
    │───────────────────>│
    │                    │
    │  { name, version,  │
    │    status }        │
    │<───────────────────│
    │                    │
```

**响应示例:**
```json
{
  "name": "TARA Report Generator API",
  "version": "1.0.0",
  "status": "running"
}
```

---

#### GET /api/v1/health

健康检查，返回服务和依赖状态。

**时序图:**
```
┌────────┐          ┌─────────┐          ┌───────┐          ┌───────┐
│ Client │          │ Backend │          │ MySQL │          │ MinIO │
└───┬────┘          └────┬────┘          └───┬───┘          └───┬───┘
    │                    │                   │                  │
    │  GET /api/v1/health│                   │                  │
    │───────────────────>│                   │                  │
    │                    │                   │                  │
    │                    │  SELECT 1         │                  │
    │                    │──────────────────>│                  │
    │                    │                   │                  │
    │                    │  Check connection │                  │
    │                    │─────────────────────────────────────>│
    │                    │                   │                  │
    │  { status, services }                  │                  │
    │<───────────────────│                   │                  │
    │                    │                   │                  │
```

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000000",
  "services": {
    "database": "healthy",
    "minio": "healthy"
  }
}
```

---

### 2. 图片管理

#### POST /api/v1/images/upload

上传图片（临时存储）。

**请求参数 (multipart/form-data):**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件 |
| image_type | string | 是 | 图片类型 |

**图片类型:**
- `item_boundary`: 项目边界图
- `system_architecture`: 系统架构图
- `software_architecture`: 软件架构图
- `dataflow`: 数据流图
- `attack_tree`: 攻击树图

**支持的文件格式:** `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.svg`

**响应示例:**
```json
{
  "success": true,
  "message": "图片上传成功",
  "image_id": "IMG-abc123def456",
  "image_url": "/api/v1/images/IMG-abc123def456",
  "image_type": "item_boundary"
}
```

---

#### GET /api/v1/images/{image_id}

获取图片。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| image_id | string | 图片ID |

**响应:** 图片文件流

---

### 3. 报告数据上传

#### POST /api/v1/reports/upload

上传JSON参数和图片，生成报告ID并保存数据到数据库。

**请求参数 (multipart/form-data):**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| json_file | File | 否* | JSON数据文件 |
| json_data | string | 否* | JSON数据字符串 |
| item_boundary_image | File | 否 | 项目边界图 |
| system_architecture_image | File | 否 | 系统架构图 |
| software_architecture_image | File | 否 | 软件架构图 |
| dataflow_image | File | 否 | 数据流图 |
| attack_tree_images | File[] | 否 | 攻击树图片列表 |

*注: `json_file` 和 `json_data` 二选一必填

**响应示例:**
```json
{
  "success": true,
  "message": "数据上传成功",
  "report_id": "RPT-20250115-ABC12345",
  "statistics": {
    "assets_count": 10,
    "attack_trees_count": 3,
    "tara_results_count": 25,
    "images_count": 5
  }
}
```

---

#### POST /api/v1/upload/batch

批量上传JSON和图片文件，一键生成报告。

**请求参数 (multipart/form-data):**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| json_file | File | 是 | JSON数据文件 |
| item_boundary_image | File | 否 | 项目边界图 |
| system_architecture_image | File | 否 | 系统架构图 |
| software_architecture_image | File | 否 | 软件架构图 |
| dataflow_image | File | 否 | 数据流图 |
| attack_tree_images | File[] | 否 | 攻击树图片列表 |

**响应示例:**
```json
{
  "success": true,
  "message": "报告生成成功",
  "report_id": "RPT-20250115-ABC12345",
  "report_info": {...},
  "download_url": "/api/v1/reports/RPT-20250115-ABC12345/download",
  "preview_url": "/api/v1/reports/RPT-20250115-ABC12345/preview"
}
```

---

### 4. 报告列表

#### GET /api/v1/reports

获取报告列表。

**查询参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |

**响应示例:**
```json
{
  "success": true,
  "total": 50,
  "page": 1,
  "page_size": 20,
  "reports": [
    {
      "id": "RPT-20250115-ABC12345",
      "report_id": "RPT-20250115-ABC12345",
      "name": "威胁分析和风险评估报告",
      "project_name": "项目名称",
      "report_title": "威胁分析和风险评估报告",
      "status": "completed",
      "created_at": "2025-01-15T10:30:00.000000",
      "statistics": {
        "assets_count": 10,
        "threats_count": 25,
        "high_risk_count": 5,
        "measures_count": 25,
        "attack_trees_count": 3
      },
      "downloads": {
        "xlsx": {
          "url": "/api/v1/reports/RPT-xxx/download?format=xlsx",
          "file_size": 125840,
          "generated_at": "2025-01-15T10:35:00"
        }
      }
    }
  ]
}
```

---

### 5. 报告详情

#### GET /api/v1/reports/{report_id}

获取报告完整信息。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |

**响应示例:**
```json
{
  "id": "RPT-20250115-ABC12345",
  "report_id": "RPT-20250115-ABC12345",
  "name": "威胁分析和风险评估报告",
  "project_name": "项目名称",
  "status": "completed",
  "created_at": "2025-01-15T10:30:00.000000",
  "statistics": {...},
  "downloads": {...},
  "cover": {...},
  "definitions": {...},
  "assets": {...},
  "attack_trees": {...},
  "tara_results": {...}
}
```

---

#### GET /api/v1/reports/{report_id}/cover

获取报告封面信息。

#### GET /api/v1/reports/{report_id}/definitions

获取报告相关定义。

#### GET /api/v1/reports/{report_id}/assets

获取报告资产列表。

#### GET /api/v1/reports/{report_id}/attack-trees

获取报告攻击树。

#### GET /api/v1/reports/{report_id}/tara-results

获取TARA分析结果。

---

### 6. 删除报告

#### DELETE /api/v1/reports/{report_id}

删除报告及其所有关联资源。

**响应示例:**
```json
{
  "success": true,
  "message": "报告已删除"
}
```

**注意事项:**
- 此操作不可逆，将永久删除报告及其所有关联资源
- 删除的内容包括：
  - 数据库中的报告记录
  - MinIO中存储的所有图片文件
  - MinIO中存储的生成报告文件（Excel、PDF）

---

### 7. 报告生成

#### POST /api/v1/reports/{report_id}/generate

生成报告文件（Excel或PDF）。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |

**查询参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| format | string | xlsx | 报告格式: `xlsx` 或 `pdf` |

**响应示例:**
```json
{
  "success": true,
  "message": "报告生成成功",
  "report_id": "RPT-20250115-ABC12345",
  "format": "xlsx",
  "file_size": 125840,
  "download_url": "/api/v1/reports/RPT-20250115-ABC12345/download?format=xlsx",
  "file_name": "项目名称_RPT-20250115-ABC12345.xlsx"
}
```

---

### 8. 报告下载

#### GET /api/v1/reports/{report_id}/download

下载报告文件（格式作为查询参数）。

**查询参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| format | string | xlsx | 报告格式: `xlsx` 或 `pdf` |

#### GET /api/v1/reports/{report_id}/download/{format}

下载报告文件（格式作为路径参数）。

**响应:** 
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (xlsx)
- Content-Type: `application/pdf` (pdf)

---

### 9. 报告预览

#### GET /api/v1/reports/{report_id}/preview

获取报告预览数据。

---

### 10. 报告状态

#### GET /api/v1/reports/{report_id}/status

获取报告状态信息。

**响应示例:**
```json
{
  "report_id": "RPT-20250115-ABC12345",
  "status": "completed",
  "created_at": "2025-01-15T10:30:00.000000",
  "generated_files": [
    {
      "type": "xlsx",
      "size": 125840,
      "generated_at": "2025-01-15T10:35:00.000000"
    }
  ]
}
```

---

### 11. 图片访问

#### GET /api/v1/reports/{report_id}/images/{image_id}

获取报告关联的图片。

#### GET /api/v1/reports/{report_id}/image-by-path

根据MinIO路径获取图片。

**查询参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| path | string | MinIO对象路径 |

---

## 数据模型

### JSON输入数据格式

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
    "title": "相关定义标题",
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
        "integrity": false,
        "non_repudiation": false,
        "confidentiality": false,
        "availability": true,
        "authorization": false
      }
    ]
  },
  "attack_trees": {
    "title": "攻击树分析",
    "attack_trees": [
      {"asset_id": "P001", "asset_name": "SOC", "title": "攻击树1"}
    ]
  },
  "tara_results": {
    "title": "TARA分析结果",
    "results": [
      {
        "asset_id": "P001",
        "asset_name": "资产名称",
        "subdomain1": "子领域一",
        "subdomain2": "子领域二",
        "subdomain3": "子领域三",
        "category": "分类",
        "security_attribute": "真实性",
        "stride_model": "S欺骗",
        "threat_scenario": "威胁场景描述",
        "attack_path": "攻击路径",
        "wp29_mapping": "4.1",
        "attack_vector": "本地",
        "attack_complexity": "低",
        "privileges_required": "低",
        "user_interaction": "不需要",
        "safety_impact": "中等的",
        "financial_impact": "中等的",
        "operational_impact": "重大的",
        "privacy_impact": "可忽略不计的",
        "security_goal": "安全目标",
        "security_requirement": "安全需求"
      }
    ]
  }
}
```

---

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
| MINIO_SECURE | false | MinIO是否使用HTTPS |

---

## MinIO存储桶

| 存储桶名称 | 说明 |
|------------|------|
| tara-reports | 存储生成的报告文件 |
| tara-images | 存储图片文件 |

---

## 错误码

| HTTP状态码 | 说明 |
|------------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 使用示例

### 批量上传生成报告

```bash
curl -X POST "http://backend:8000/api/v1/upload/batch" \
  -F "json_file=@report_data.json" \
  -F "item_boundary_image=@boundary.png" \
  -F "system_architecture_image=@system_arch.png"
```

### 获取报告列表

```bash
curl "http://backend:8000/api/v1/reports?page=1&page_size=20"
```

### 生成Excel报告

```bash
curl -X POST "http://backend:8000/api/v1/reports/RPT-20250115-ABC12345/generate?format=xlsx"
```

### 下载报告

```bash
curl -O "http://backend:8000/api/v1/reports/RPT-20250115-ABC12345/download?format=xlsx"
```

### 删除报告

```bash
curl -X DELETE "http://backend:8000/api/v1/reports/RPT-20250115-ABC12345"
```

---

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

---

## 注意事项

1. **PDF中文支持**: 系统需要安装中文字体才能正确显示PDF中的中文内容

2. **大文件处理**: 对于包含大量图片的报告，生成时间可能较长

3. **删除操作**: 删除报告是不可逆操作，会永久删除所有相关资源

4. **并发限制**: 建议对报告生成接口进行并发限制

5. **API版本**: 所有API端点使用 `/api/v1` 前缀，旧的 `/api` 路径会自动重定向到 `/api/v1`
