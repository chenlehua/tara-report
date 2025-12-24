# Data Service API 规范

数据服务 - TARA报告数据管理服务

## 服务信息

- **服务名称**: TARA Data Service
- **版本**: 1.0.0
- **端口**: 8001
- **描述**: 负责上传JSON和图片、生成报告ID、保存数据到MySQL和MinIO

## 基础信息

### 基础URL

```
http://data-service:8001
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

**响应示例:**
```json
{
  "name": "TARA Data Service",
  "version": "1.0.0",
  "status": "running"
}
```

---

#### GET /api/health

健康检查，返回服务和依赖状态。

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

#### POST /api/images/upload

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
  "image_url": "/api/images/IMG-abc123def456",
  "image_type": "item_boundary"
}
```

---

#### GET /api/images/{image_id}

获取图片。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| image_id | string | 图片ID |

**响应:** 图片文件流

---

### 3. 报告数据管理

#### POST /api/reports/upload

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

#### POST /api/upload/batch

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
  "report_info": {
    "id": "RPT-20250115-ABC12345",
    "name": "威胁分析和风险评估报告",
    "project_name": "项目名称",
    "version": "1.0",
    "created_at": "2025-01-15T10:30:00.000000",
    "file_path": "",
    "file_size": 0,
    "statistics": {
      "assets_count": 10,
      "attack_trees_count": 3,
      "tara_results_count": 25,
      "images_count": 5
    }
  },
  "download_url": "/api/reports/RPT-20250115-ABC12345/download",
  "preview_url": "/api/reports/RPT-20250115-ABC12345/preview"
}
```

---

#### GET /api/reports

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
      "file_path": "",
      "statistics": {
        "assets_count": 10,
        "threats_count": 25,
        "high_risk_count": 5,
        "measures_count": 25,
        "attack_trees_count": 3
      }
    }
  ]
}
```

---

#### GET /api/reports/{report_id}

获取报告完整信息（用于预览）。

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
  "updated_at": null,
  "file_path": "",
  "statistics": {
    "assets_count": 10,
    "threats_count": 25,
    "high_risk_count": 5,
    "measures_count": 25,
    "attack_trees_count": 3
  },
  "cover": {
    "report_title": "威胁分析和风险评估报告",
    "report_title_en": "Threat Analysis And Risk Assessment Report",
    "project_name": "项目名称",
    "data_level": "秘密",
    "document_number": "DOC-001",
    "version": "V1.0",
    "author_date": "2025.01",
    "review_date": "2025.01",
    "sign_date": "",
    "approve_date": ""
  },
  "definitions": {
    "title": "相关定义",
    "functional_description": "功能描述...",
    "item_boundary_image": "/api/reports/RPT-20250115-ABC12345/image-by-path?path=...",
    "system_architecture_image": "/api/reports/RPT-20250115-ABC12345/image-by-path?path=...",
    "software_architecture_image": "/api/reports/RPT-20250115-ABC12345/image-by-path?path=...",
    "assumptions": [],
    "terminology": []
  },
  "assets": {
    "title": "资产列表",
    "assets": [],
    "dataflow_image": null
  },
  "attack_trees": {
    "title": "攻击树分析",
    "attack_trees": []
  },
  "tara_results": {
    "title": "TARA分析结果",
    "results": []
  }
}
```

---

#### GET /api/reports/{report_id}/cover

获取报告封面信息。

**响应示例:**
```json
{
  "report_title": "威胁分析和风险评估报告",
  "report_title_en": "Threat Analysis And Risk Assessment Report",
  "project_name": "项目名称",
  "data_level": "秘密",
  "document_number": "DOC-001",
  "version": "V1.0",
  "author_date": "2025.01",
  "review_date": "2025.01",
  "sign_date": "",
  "approve_date": ""
}
```

---

#### GET /api/reports/{report_id}/definitions

获取报告相关定义。

**响应示例:**
```json
{
  "title": "相关定义",
  "functional_description": "功能描述...",
  "item_boundary_image": "path/to/image",
  "system_architecture_image": "path/to/image",
  "software_architecture_image": "path/to/image",
  "dataflow_image": "path/to/image",
  "assumptions": [
    {"id": "ASM-01", "description": "假设描述"}
  ],
  "terminology": [
    {"abbreviation": "IVI", "english": "In-Vehicle Infotainment", "chinese": "车载信息娱乐系统"}
  ]
}
```

---

#### GET /api/reports/{report_id}/assets

获取报告资产列表。

**响应示例:**
```json
{
  "title": "项目名称 - 资产列表 Asset List",
  "dataflow_image": "path/to/image",
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
}
```

---

#### GET /api/reports/{report_id}/attack-trees

获取报告攻击树。

**响应示例:**
```json
{
  "title": "攻击树分析 Attack Tree Analysis",
  "attack_trees": [
    {
      "asset_id": "P001",
      "asset_name": "SOC",
      "title": "攻击树1",
      "image": "path/to/image"
    }
  ]
}
```

---

#### GET /api/reports/{report_id}/tara-results

获取TARA分析结果。

**响应示例:**
```json
{
  "title": "TARA分析结果 TARA Analysis Results",
  "results": [
    {
      "asset_id": "P001",
      "asset_name": "资产名称",
      "subdomain1": "",
      "subdomain2": "",
      "subdomain3": "",
      "category": "内部实体",
      "security_attribute": "Authenticity",
      "stride_model": "S欺骗",
      "threat_scenario": "威胁场景描述",
      "attack_path": "攻击路径描述",
      "wp29_mapping": "",
      "attack_vector": "本地",
      "attack_complexity": "低",
      "privileges_required": "低",
      "user_interaction": "不需要",
      "safety_impact": "中等的",
      "financial_impact": "中等的",
      "operational_impact": "重大的",
      "privacy_impact": "可忽略不计的",
      "security_goal": "",
      "security_requirement": "安全需求描述"
    }
  ]
}
```

---

#### GET /api/reports/{report_id}/images/{image_id}

获取报告关联的图片。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |
| image_id | string | 图片ID |

**响应:** 图片文件流

---

#### GET /api/reports/{report_id}/image-by-path

根据MinIO路径获取图片。

**查询参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| path | string | MinIO对象路径 |

**响应:** 图片文件流

---

#### DELETE /api/reports/{report_id}

删除报告及其关联的所有资源。

**响应示例:**
```json
{
  "success": true,
  "message": "报告已删除"
}
```

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
    "review_date": "2025.01",
    "sign_date": "",
    "approve_date": ""
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
      {
        "asset_id": "P001",
        "asset_name": "SOC",
        "title": "攻击树1",
        "image": ""
      }
    ]
  },
  "tara_results": {
    "title": "TARA分析结果",
    "results": [
      {
        "asset_id": "P001",
        "asset_name": "资产名称",
        "subdomain1": "",
        "subdomain2": "",
        "subdomain3": "",
        "category": "内部实体",
        "security_attribute": "Authenticity",
        "stride_model": "S欺骗",
        "threat_scenario": "威胁场景描述",
        "attack_path": "攻击路径描述",
        "wp29_mapping": "",
        "attack_vector": "本地",
        "attack_complexity": "低",
        "privileges_required": "低",
        "user_interaction": "不需要",
        "safety_impact": "中等的",
        "financial_impact": "中等的",
        "operational_impact": "重大的",
        "privacy_impact": "可忽略不计的",
        "security_goal": "",
        "security_requirement": "安全需求描述"
      }
    ]
  }
}
```

---

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| REPORT_SERVICE_URL | http://report-service:8002 | 报告服务地址 |
| MYSQL_HOST | mysql | MySQL主机 |
| MYSQL_PORT | 3306 | MySQL端口 |
| MYSQL_USER | root | MySQL用户名 |
| MYSQL_PASSWORD | password | MySQL密码 |
| MYSQL_DATABASE | tara | MySQL数据库名 |
| MINIO_ENDPOINT | minio:9000 | MinIO端点 |
| MINIO_ACCESS_KEY | minioadmin | MinIO访问密钥 |
| MINIO_SECRET_KEY | minioadmin | MinIO密钥 |

---

## 错误码

| HTTP状态码 | 说明 |
|------------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
