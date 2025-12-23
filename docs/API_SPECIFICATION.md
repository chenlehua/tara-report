# TARA 后端服务 API 接口规范

## 概述

TARA (Threat Analysis and Risk Assessment) 后端服务提供威胁分析和风险评估报告的生成功能。

### 基础信息

| 项目 | 说明 |
|------|------|
| API 版本 | v1 |
| 基础路径 | `/api/v1` |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |

### 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| tara-data-service | 8001 | 数据服务 - 数据上传、存储和查询 |
| tara-report-service | 8002 | 报告服务 - 报告生成和下载 |

### 通用响应格式

**成功响应**
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

**错误响应**
```json
{
  "detail": "错误信息描述"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 一、数据服务 API (tara-data-service)

### 1.1 健康检查

#### GET /api/v1/health

检查数据服务及其依赖组件的健康状态。

**请求参数**

无

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 整体状态：`healthy` / `degraded` |
| timestamp | string | 检查时间 (ISO 8601 格式) |
| services | object | 各服务状态 |
| services.database | string | 数据库状态 |
| services.minio | string | MinIO 存储状态 |

**请求示例**

```bash
curl -X GET "http://localhost:8001/api/v1/health"
```

**响应示例**

```json
{
  "status": "healthy",
  "timestamp": "2024-12-23T10:30:00.123456",
  "services": {
    "database": "healthy",
    "minio": "healthy"
  }
}
```

---

### 1.2 图片管理

#### POST /api/v1/images/upload

上传图片到临时存储。

**请求参数 (multipart/form-data)**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件 |
| image_type | string | 是 | 图片类型 |

**image_type 可选值**

| 值 | 说明 |
|----|------|
| item_boundary | 项目边界图 |
| system_architecture | 系统架构图 |
| software_architecture | 软件架构图 |
| dataflow | 数据流图 |
| attack_tree | 攻击树图 |

**支持的图片格式**

`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.svg`

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| message | string | 提示信息 |
| image_id | string | 图片唯一标识 |
| image_url | string | 图片访问路径 |
| image_type | string | 图片类型 |

**请求示例**

```bash
curl -X POST "http://localhost:8001/api/v1/images/upload" \
  -F "file=@/path/to/image.png" \
  -F "image_type=system_architecture"
```

**响应示例**

```json
{
  "success": true,
  "message": "图片上传成功",
  "image_id": "IMG-a1b2c3d4e5f6",
  "image_url": "/api/v1/images/IMG-a1b2c3d4e5f6",
  "image_type": "system_architecture"
}
```

**错误响应示例**

```json
{
  "detail": "不支持的文件格式。支持的格式: .png, .jpg, .jpeg, .gif, .bmp, .svg"
}
```

---

#### GET /api/v1/images/{image_id}

获取图片内容。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| image_id | string | 图片唯一标识 |

**响应**

返回图片二进制数据，Content-Type 为对应的图片 MIME 类型。

**请求示例**

```bash
curl -X GET "http://localhost:8001/api/v1/images/IMG-a1b2c3d4e5f6" \
  --output image.png
```

---

### 1.3 报告数据上传

#### POST /api/v1/reports/upload

上传报告 JSON 数据和图片，创建报告记录。

**请求参数 (multipart/form-data)**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| json_file | File | 否* | JSON 数据文件 |
| json_data | string | 否* | JSON 数据字符串 |
| item_boundary_image | File | 否 | 项目边界图 |
| system_architecture_image | File | 否 | 系统架构图 |
| software_architecture_image | File | 否 | 软件架构图 |
| dataflow_image | File | 否 | 数据流图 |
| attack_tree_images | File[] | 否 | 攻击树图片列表 |

> *注：`json_file` 和 `json_data` 二选一，必须提供其中之一。

**JSON 数据结构**

```json
{
  "cover": {
    "report_title": "威胁分析与风险评估报告",
    "report_title_en": "Threat Analysis and Risk Assessment Report",
    "project_name": "智能网联汽车",
    "data_level": "机密",
    "document_number": "DOC-2024-001",
    "version": "1.0",
    "author_date": "2024-01-01",
    "review_date": "2024-01-05",
    "sign_date": "2024-01-08",
    "approve_date": "2024-01-10"
  },
  "definitions": {
    "title": "相关定义",
    "functional_description": "本系统实现智能网联汽车的核心功能...",
    "assumptions": [
      {"id": "A001", "content": "假设网络环境安全"},
      {"id": "A002", "content": "假设用户身份已验证"}
    ],
    "terminology": [
      {"term": "TARA", "definition": "威胁分析与风险评估"},
      {"term": "ECU", "definition": "电子控制单元"}
    ]
  },
  "assets": {
    "title": "资产列表",
    "assets": [
      {
        "id": "AS001",
        "name": "车载通信模块",
        "category": "硬件",
        "remarks": "负责车辆与外部通信",
        "authenticity": "高",
        "integrity": "高",
        "non_repudiation": "中",
        "confidentiality": "高",
        "availability": "高",
        "authorization": "高"
      }
    ]
  },
  "attack_trees": {
    "title": "攻击树分析",
    "attack_trees": [
      {
        "asset_id": "AS001",
        "asset_name": "车载通信模块",
        "title": "通信模块攻击树"
      }
    ]
  },
  "tara_results": {
    "title": "TARA分析结果",
    "results": [
      {
        "asset_id": "AS001",
        "asset_name": "车载通信模块",
        "subdomain1": "通信安全",
        "subdomain2": "数据传输",
        "subdomain3": "加密",
        "category": "网络攻击",
        "security_attribute": "机密性",
        "stride_model": "信息泄露",
        "threat_scenario": "攻击者窃听车载通信数据",
        "attack_path": "通过中间人攻击截获通信",
        "wp29_mapping": "7.2.1",
        "attack_vector": "网络",
        "attack_complexity": "低",
        "privileges_required": "无",
        "user_interaction": "无",
        "safety_impact": "中等的",
        "financial_impact": "中等的",
        "operational_impact": "中等的",
        "privacy_impact": "重大的",
        "security_goal": "确保通信数据机密性",
        "security_requirement": "实施端到端加密"
      }
    ]
  }
}
```

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| message | string | 提示信息 |
| report_id | string | 报告唯一标识 |
| statistics | object | 统计信息 |
| statistics.assets_count | number | 资产数量 |
| statistics.attack_trees_count | number | 攻击树数量 |
| statistics.tara_results_count | number | TARA 结果数量 |
| statistics.images_count | number | 图片数量 |

**请求示例**

```bash
curl -X POST "http://localhost:8001/api/v1/reports/upload" \
  -F "json_file=@/path/to/report.json" \
  -F "item_boundary_image=@/path/to/boundary.png" \
  -F "system_architecture_image=@/path/to/architecture.png"
```

**响应示例**

```json
{
  "success": true,
  "message": "数据上传成功",
  "report_id": "RPT-20241223-A1B2C3D4",
  "statistics": {
    "assets_count": 5,
    "attack_trees_count": 3,
    "tara_results_count": 15,
    "images_count": 4
  }
}
```

---

#### POST /api/v1/upload/batch

批量上传 JSON 和图片，一键生成报告（自动触发 Excel 和 PDF 生成）。

**请求参数 (multipart/form-data)**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| json_file | File | 是 | JSON 数据文件 |
| item_boundary_image | File | 否 | 项目边界图 |
| system_architecture_image | File | 否 | 系统架构图 |
| software_architecture_image | File | 否 | 软件架构图 |
| dataflow_image | File | 否 | 数据流图 |
| attack_tree_images | File[] | 否 | 攻击树图片列表 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| message | string | 提示信息 |
| report_id | string | 报告唯一标识 |
| report_info | object | 报告信息 |
| download_url | string | 下载链接 |
| preview_url | string | 预览链接 |

**请求示例**

```bash
curl -X POST "http://localhost:8001/api/v1/upload/batch" \
  -F "json_file=@/path/to/report.json" \
  -F "item_boundary_image=@/path/to/boundary.png" \
  -F "system_architecture_image=@/path/to/architecture.png" \
  -F "attack_tree_images=@/path/to/attack_tree1.png" \
  -F "attack_tree_images=@/path/to/attack_tree2.png"
```

**响应示例**

```json
{
  "success": true,
  "message": "报告生成成功",
  "report_id": "RPT-20241223-A1B2C3D4",
  "report_info": {
    "id": "RPT-20241223-A1B2C3D4",
    "name": "威胁分析与风险评估报告",
    "project_name": "智能网联汽车",
    "version": "1.0",
    "created_at": "2024-12-23T10:30:00.123456",
    "file_path": "",
    "file_size": 0,
    "statistics": {
      "assets_count": 5,
      "attack_trees_count": 3,
      "tara_results_count": 15,
      "images_count": 4
    }
  },
  "download_url": "/api/v1/reports/RPT-20241223-A1B2C3D4/download",
  "preview_url": "/api/v1/reports/RPT-20241223-A1B2C3D4/preview"
}
```

---

### 1.4 报告查询

#### GET /api/v1/reports

获取报告列表。

**查询参数**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | number | 否 | 1 | 页码 |
| page_size | number | 否 | 20 | 每页数量 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| total | number | 总数量 |
| page | number | 当前页码 |
| page_size | number | 每页数量 |
| reports | array | 报告列表 |

**报告对象字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 报告 ID |
| report_id | string | 报告 ID（兼容字段） |
| name | string | 报告名称 |
| project_name | string | 项目名称 |
| report_title | string | 报告标题 |
| status | string | 状态：`pending` / `completed` |
| created_at | string | 创建时间 |
| file_path | string | 文件路径 |
| statistics | object | 统计信息 |

**请求示例**

```bash
curl -X GET "http://localhost:8001/api/v1/reports?page=1&page_size=10"
```

**响应示例**

```json
{
  "success": true,
  "total": 25,
  "page": 1,
  "page_size": 10,
  "reports": [
    {
      "id": "RPT-20241223-A1B2C3D4",
      "report_id": "RPT-20241223-A1B2C3D4",
      "name": "威胁分析与风险评估报告",
      "project_name": "智能网联汽车",
      "report_title": "威胁分析与风险评估报告",
      "status": "completed",
      "created_at": "2024-12-23T10:30:00.123456",
      "file_path": "",
      "statistics": {
        "assets_count": 5,
        "threats_count": 15,
        "high_risk_count": 3,
        "measures_count": 15,
        "attack_trees_count": 3
      }
    }
  ]
}
```

---

#### GET /api/v1/reports/{report_id}

获取报告完整信息。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 报告 ID |
| report_id | string | 报告 ID |
| name | string | 报告名称 |
| project_name | string | 项目名称 |
| status | string | 状态 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| statistics | object | 统计信息 |
| cover | object | 封面信息 |
| definitions | object | 相关定义 |
| assets | object | 资产列表 |
| attack_trees | object | 攻击树 |
| tara_results | object | TARA 分析结果 |

**请求示例**

```bash
curl -X GET "http://localhost:8001/api/v1/reports/RPT-20241223-A1B2C3D4"
```

**响应示例**

```json
{
  "id": "RPT-20241223-A1B2C3D4",
  "report_id": "RPT-20241223-A1B2C3D4",
  "name": "威胁分析与风险评估报告",
  "project_name": "智能网联汽车",
  "status": "completed",
  "created_at": "2024-12-23T10:30:00.123456",
  "updated_at": "2024-12-23T10:35:00.123456",
  "statistics": {
    "assets_count": 5,
    "threats_count": 15,
    "high_risk_count": 3,
    "measures_count": 15,
    "attack_trees_count": 3
  },
  "cover": {
    "report_title": "威胁分析与风险评估报告",
    "report_title_en": "Threat Analysis and Risk Assessment Report",
    "project_name": "智能网联汽车",
    "data_level": "机密",
    "document_number": "DOC-2024-001",
    "version": "1.0",
    "author_date": "2024-01-01",
    "review_date": "2024-01-05",
    "sign_date": "2024-01-08",
    "approve_date": "2024-01-10"
  },
  "definitions": {
    "title": "相关定义",
    "functional_description": "本系统实现智能网联汽车的核心功能...",
    "item_boundary_image": "/api/v1/reports/RPT-20241223-A1B2C3D4/image-by-path?path=...",
    "system_architecture_image": "/api/v1/reports/RPT-20241223-A1B2C3D4/image-by-path?path=...",
    "software_architecture_image": null,
    "assumptions": [
      {"id": "A001", "content": "假设网络环境安全"}
    ],
    "terminology": [
      {"term": "TARA", "definition": "威胁分析与风险评估"}
    ]
  },
  "assets": {
    "title": "资产列表",
    "assets": [
      {
        "id": "AS001",
        "name": "车载通信模块",
        "category": "硬件",
        "remarks": "负责车辆与外部通信",
        "authenticity": "高",
        "integrity": "高",
        "non_repudiation": "中",
        "confidentiality": "高",
        "availability": "高",
        "authorization": "高"
      }
    ],
    "dataflow_image": "/api/v1/reports/RPT-20241223-A1B2C3D4/image-by-path?path=..."
  },
  "attack_trees": {
    "title": "攻击树分析",
    "attack_trees": [
      {
        "asset_id": "AS001",
        "asset_name": "车载通信模块",
        "title": "通信模块攻击树",
        "image": "...",
        "image_url": "/api/v1/reports/RPT-20241223-A1B2C3D4/image-by-path?path=..."
      }
    ]
  },
  "tara_results": {
    "title": "TARA分析结果",
    "results": [
      {
        "asset_id": "AS001",
        "asset_name": "车载通信模块",
        "subdomain1": "通信安全",
        "subdomain2": "数据传输",
        "subdomain3": "加密",
        "category": "网络攻击",
        "security_attribute": "机密性",
        "stride_model": "信息泄露",
        "threat_scenario": "攻击者窃听车载通信数据",
        "attack_path": "通过中间人攻击截获通信",
        "wp29_mapping": "7.2.1",
        "attack_vector": "网络",
        "attack_complexity": "低",
        "privileges_required": "无",
        "user_interaction": "无",
        "safety_impact": "中等的",
        "financial_impact": "中等的",
        "operational_impact": "中等的",
        "privacy_impact": "重大的",
        "security_goal": "确保通信数据机密性",
        "security_requirement": "实施端到端加密"
      }
    ]
  }
}
```

---

#### GET /api/v1/reports/{report_id}/cover

获取报告封面信息。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_title | string | 报告标题 |
| report_title_en | string | 报告英文标题 |
| project_name | string | 项目名称 |
| data_level | string | 数据等级 |
| document_number | string | 文档编号 |
| version | string | 版本号 |
| author_date | string | 编写日期 |
| review_date | string | 审核日期 |
| sign_date | string | 会签日期 |
| approve_date | string | 批准日期 |

**请求示例**

```bash
curl -X GET "http://localhost:8001/api/v1/reports/RPT-20241223-A1B2C3D4/cover"
```

**响应示例**

```json
{
  "report_title": "威胁分析与风险评估报告",
  "report_title_en": "Threat Analysis and Risk Assessment Report",
  "project_name": "智能网联汽车",
  "data_level": "机密",
  "document_number": "DOC-2024-001",
  "version": "1.0",
  "author_date": "2024-01-01",
  "review_date": "2024-01-05",
  "sign_date": "2024-01-08",
  "approve_date": "2024-01-10"
}
```

---

#### GET /api/v1/reports/{report_id}/definitions

获取报告相关定义。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 标题 |
| functional_description | string | 功能描述 |
| item_boundary_image | string | 项目边界图路径 |
| system_architecture_image | string | 系统架构图路径 |
| software_architecture_image | string | 软件架构图路径 |
| dataflow_image | string | 数据流图路径 |
| assumptions | array | 假设列表 |
| terminology | array | 术语列表 |

**请求示例**

```bash
curl -X GET "http://localhost:8001/api/v1/reports/RPT-20241223-A1B2C3D4/definitions"
```

**响应示例**

```json
{
  "title": "相关定义",
  "functional_description": "本系统实现智能网联汽车的核心功能...",
  "item_boundary_image": "RPT-20241223-A1B2C3D4/item_boundary/IMG-xxx.png",
  "system_architecture_image": "RPT-20241223-A1B2C3D4/system_architecture/IMG-xxx.png",
  "software_architecture_image": null,
  "dataflow_image": "RPT-20241223-A1B2C3D4/dataflow/IMG-xxx.png",
  "assumptions": [
    {"id": "A001", "content": "假设网络环境安全"},
    {"id": "A002", "content": "假设用户身份已验证"}
  ],
  "terminology": [
    {"term": "TARA", "definition": "威胁分析与风险评估"},
    {"term": "ECU", "definition": "电子控制单元"}
  ]
}
```

---

#### GET /api/v1/reports/{report_id}/assets

获取报告资产列表。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 标题 |
| dataflow_image | string | 数据流图路径 |
| assets | array | 资产列表 |

**资产对象字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 资产 ID |
| name | string | 资产名称 |
| category | string | 资产类别 |
| remarks | string | 备注 |
| authenticity | string | 真实性 |
| integrity | string | 完整性 |
| non_repudiation | string | 不可否认性 |
| confidentiality | string | 机密性 |
| availability | string | 可用性 |
| authorization | string | 授权性 |

**请求示例**

```bash
curl -X GET "http://localhost:8001/api/v1/reports/RPT-20241223-A1B2C3D4/assets"
```

**响应示例**

```json
{
  "title": "智能网联汽车 - 资产列表 Asset List",
  "dataflow_image": "RPT-20241223-A1B2C3D4/dataflow/IMG-xxx.png",
  "assets": [
    {
      "id": "AS001",
      "name": "车载通信模块",
      "category": "硬件",
      "remarks": "负责车辆与外部通信",
      "authenticity": "高",
      "integrity": "高",
      "non_repudiation": "中",
      "confidentiality": "高",
      "availability": "高",
      "authorization": "高"
    },
    {
      "id": "AS002",
      "name": "车载操作系统",
      "category": "软件",
      "remarks": "车辆核心控制系统",
      "authenticity": "高",
      "integrity": "高",
      "non_repudiation": "高",
      "confidentiality": "高",
      "availability": "高",
      "authorization": "高"
    }
  ]
}
```

---

#### GET /api/v1/reports/{report_id}/attack-trees

获取报告攻击树列表。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 标题 |
| attack_trees | array | 攻击树列表 |

**攻击树对象字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| asset_id | string | 关联资产 ID |
| asset_name | string | 关联资产名称 |
| title | string | 攻击树标题 |
| image | string | 攻击树图片路径 |

**请求示例**

```bash
curl -X GET "http://localhost:8001/api/v1/reports/RPT-20241223-A1B2C3D4/attack-trees"
```

**响应示例**

```json
{
  "title": "攻击树分析 Attack Tree Analysis",
  "attack_trees": [
    {
      "asset_id": "AS001",
      "asset_name": "车载通信模块",
      "title": "通信模块攻击树",
      "image": "RPT-20241223-A1B2C3D4/attack_tree_0/IMG-xxx.png"
    },
    {
      "asset_id": "AS002",
      "asset_name": "车载操作系统",
      "title": "操作系统攻击树",
      "image": "RPT-20241223-A1B2C3D4/attack_tree_1/IMG-xxx.png"
    }
  ]
}
```

---

#### GET /api/v1/reports/{report_id}/tara-results

获取 TARA 分析结果。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 标题 |
| results | array | TARA 结果列表 |

**TARA 结果对象字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| asset_id | string | 资产 ID |
| asset_name | string | 资产名称 |
| subdomain1 | string | 子域 1 |
| subdomain2 | string | 子域 2 |
| subdomain3 | string | 子域 3 |
| category | string | 类别 |
| security_attribute | string | 安全属性 |
| stride_model | string | STRIDE 模型 |
| threat_scenario | string | 威胁场景 |
| attack_path | string | 攻击路径 |
| wp29_mapping | string | WP29 映射 |
| attack_vector | string | 攻击向量 |
| attack_complexity | string | 攻击复杂度 |
| privileges_required | string | 所需权限 |
| user_interaction | string | 用户交互 |
| safety_impact | string | 安全影响 |
| financial_impact | string | 财务影响 |
| operational_impact | string | 运营影响 |
| privacy_impact | string | 隐私影响 |
| security_goal | string | 安全目标 |
| security_requirement | string | 安全需求 |

**请求示例**

```bash
curl -X GET "http://localhost:8001/api/v1/reports/RPT-20241223-A1B2C3D4/tara-results"
```

**响应示例**

```json
{
  "title": "TARA分析结果 TARA Analysis Results",
  "results": [
    {
      "asset_id": "AS001",
      "asset_name": "车载通信模块",
      "subdomain1": "通信安全",
      "subdomain2": "数据传输",
      "subdomain3": "加密",
      "category": "网络攻击",
      "security_attribute": "机密性",
      "stride_model": "信息泄露",
      "threat_scenario": "攻击者窃听车载通信数据",
      "attack_path": "通过中间人攻击截获通信",
      "wp29_mapping": "7.2.1",
      "attack_vector": "网络",
      "attack_complexity": "低",
      "privileges_required": "无",
      "user_interaction": "无",
      "safety_impact": "中等的",
      "financial_impact": "中等的",
      "operational_impact": "中等的",
      "privacy_impact": "重大的",
      "security_goal": "确保通信数据机密性",
      "security_requirement": "实施端到端加密"
    }
  ]
}
```

---

#### GET /api/v1/reports/{report_id}/images/{image_id}

获取报告关联图片。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |
| image_id | string | 图片唯一标识 |

**响应**

返回图片二进制数据。

**请求示例**

```bash
curl -X GET "http://localhost:8001/api/v1/reports/RPT-20241223-A1B2C3D4/images/IMG-a1b2c3d4" \
  --output image.png
```

---

#### GET /api/v1/reports/{report_id}/image-by-path

根据 MinIO 路径获取图片。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**查询参数**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| path | string | 是 | MinIO 存储路径 |

**响应**

返回图片二进制数据。

**请求示例**

```bash
curl -X GET "http://localhost:8001/api/v1/reports/RPT-20241223-A1B2C3D4/image-by-path?path=RPT-20241223-A1B2C3D4/item_boundary/IMG-xxx.png" \
  --output image.png
```

---

### 1.5 报告删除

#### DELETE /api/v1/reports/{report_id}

删除报告及其关联数据。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| message | string | 提示信息 |

**请求示例**

```bash
curl -X DELETE "http://localhost:8001/api/v1/reports/RPT-20241223-A1B2C3D4"
```

**响应示例**

```json
{
  "success": true,
  "message": "报告已删除"
}
```

---

## 二、报告服务 API (tara-report-service)

### 2.1 健康检查

#### GET /api/v1/health

检查报告服务及其依赖组件的健康状态。

**请求参数**

无

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 整体状态：`healthy` / `degraded` |
| timestamp | string | 检查时间 (ISO 8601 格式) |
| services | object | 各服务状态 |
| services.database | string | 数据库状态 |
| services.minio | string | MinIO 存储状态 |
| services.data_service | string | 数据服务状态 |

**请求示例**

```bash
curl -X GET "http://localhost:8002/api/v1/health"
```

**响应示例**

```json
{
  "status": "healthy",
  "timestamp": "2024-12-23T10:30:00.123456",
  "services": {
    "database": "healthy",
    "minio": "healthy",
    "data_service": "healthy"
  }
}
```

---

### 2.2 报告生成

#### POST /api/v1/reports/{report_id}/generate

生成报告文件（Excel 或 PDF 格式）。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**查询参数**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| format | string | 否 | xlsx | 报告格式：`xlsx` / `pdf` |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| message | string | 提示信息 |
| report_id | string | 报告 ID |
| format | string | 生成的格式 |
| file_size | number | 文件大小（字节） |
| download_url | string | 下载链接 |
| file_name | string | 文件名 |

**请求示例**

```bash
# 生成 Excel 报告
curl -X POST "http://localhost:8002/api/v1/reports/RPT-20241223-A1B2C3D4/generate?format=xlsx"

# 生成 PDF 报告
curl -X POST "http://localhost:8002/api/v1/reports/RPT-20241223-A1B2C3D4/generate?format=pdf"
```

**响应示例**

```json
{
  "success": true,
  "message": "报告生成成功",
  "report_id": "RPT-20241223-A1B2C3D4",
  "format": "xlsx",
  "file_size": 125840,
  "download_url": "/api/v1/reports/RPT-20241223-A1B2C3D4/download?format=xlsx",
  "file_name": "智能网联汽车_RPT-20241223-A1B2C3D4.xlsx"
}
```

---

### 2.3 报告下载

#### GET /api/v1/reports/{report_id}/download

下载报告文件（格式作为查询参数）。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**查询参数**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| format | string | 否 | xlsx | 报告格式：`xlsx` / `pdf` |

**响应**

返回文件二进制数据，响应头包含：
- `Content-Type`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (xlsx) 或 `application/pdf` (pdf)
- `Content-Disposition`: `attachment; filename*=UTF-8''<encoded_filename>`

**请求示例**

```bash
# 下载 Excel
curl -X GET "http://localhost:8002/api/v1/reports/RPT-20241223-A1B2C3D4/download?format=xlsx" \
  --output report.xlsx

# 下载 PDF
curl -X GET "http://localhost:8002/api/v1/reports/RPT-20241223-A1B2C3D4/download?format=pdf" \
  --output report.pdf
```

---

#### GET /api/v1/reports/{report_id}/download/{format}

下载报告文件（格式作为路径参数）。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |
| format | string | 报告格式：`xlsx` / `pdf` |

**响应**

同上。

**请求示例**

```bash
# 下载 Excel
curl -X GET "http://localhost:8002/api/v1/reports/RPT-20241223-A1B2C3D4/download/xlsx" \
  --output report.xlsx

# 下载 PDF
curl -X GET "http://localhost:8002/api/v1/reports/RPT-20241223-A1B2C3D4/download/pdf" \
  --output report.pdf
```

---

### 2.4 报告预览

#### GET /api/v1/reports/{report_id}/preview

获取报告预览数据。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 报告 ID |
| report_id | string | 报告 ID |
| name | string | 报告名称 |
| project_name | string | 项目名称 |
| status | string | 状态 |
| created_at | string | 创建时间 |
| statistics | object | 统计信息 |
| cover | object | 封面信息 |
| definitions | object | 相关定义（含图片 URL） |
| assets | object | 资产列表（含数据流图 URL） |
| attack_trees | object | 攻击树（含图片 URL） |
| tara_results | object | TARA 分析结果 |
| downloads | object | 下载信息 |

**请求示例**

```bash
curl -X GET "http://localhost:8002/api/v1/reports/RPT-20241223-A1B2C3D4/preview"
```

**响应示例**

```json
{
  "id": "RPT-20241223-A1B2C3D4",
  "report_id": "RPT-20241223-A1B2C3D4",
  "name": "威胁分析与风险评估报告",
  "project_name": "智能网联汽车",
  "status": "completed",
  "created_at": "2024-12-23T10:30:00.123456",
  "statistics": {
    "assets_count": 5,
    "threats_count": 15,
    "high_risk_count": 3,
    "measures_count": 15,
    "attack_trees_count": 3
  },
  "cover": {
    "report_title": "威胁分析与风险评估报告",
    "project_name": "智能网联汽车"
  },
  "definitions": {
    "title": "相关定义",
    "functional_description": "...",
    "item_boundary_image": "/api/v1/reports/RPT-20241223-A1B2C3D4/image-by-path?path=...",
    "system_architecture_image": "/api/v1/reports/RPT-20241223-A1B2C3D4/image-by-path?path=...",
    "software_architecture_image": null
  },
  "assets": {
    "title": "资产列表",
    "assets": [...],
    "dataflow_image": "/api/v1/reports/RPT-20241223-A1B2C3D4/image-by-path?path=..."
  },
  "attack_trees": {
    "title": "攻击树分析",
    "attack_trees": [
      {
        "asset_id": "AS001",
        "asset_name": "车载通信模块",
        "title": "通信模块攻击树",
        "image": "...",
        "image_url": "/api/v1/reports/RPT-20241223-A1B2C3D4/image-by-path?path=..."
      }
    ]
  },
  "tara_results": {
    "title": "TARA分析结果",
    "results": [...]
  },
  "downloads": {
    "xlsx": {
      "url": "/api/v1/reports/RPT-20241223-A1B2C3D4/download?format=xlsx",
      "file_size": 125840,
      "generated_at": "2024-12-23T10:35:00.123456"
    },
    "pdf": {
      "url": "/api/v1/reports/RPT-20241223-A1B2C3D4/download?format=pdf",
      "file_size": 256000,
      "generated_at": "2024-12-23T10:36:00.123456"
    }
  }
}
```

---

### 2.5 报告状态

#### GET /api/v1/reports/{report_id}/status

获取报告生成状态。

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告唯一标识 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告 ID |
| status | string | 状态：`pending` / `completed` |
| created_at | string | 创建时间 |
| generated_files | array | 已生成的文件列表 |

**已生成文件对象字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 文件类型：`xlsx` / `pdf` |
| size | number | 文件大小（字节） |
| generated_at | string | 生成时间 |

**请求示例**

```bash
curl -X GET "http://localhost:8002/api/v1/reports/RPT-20241223-A1B2C3D4/status"
```

**响应示例**

```json
{
  "report_id": "RPT-20241223-A1B2C3D4",
  "status": "completed",
  "created_at": "2024-12-23T10:30:00.123456",
  "generated_files": [
    {
      "type": "xlsx",
      "size": 125840,
      "generated_at": "2024-12-23T10:35:00.123456"
    },
    {
      "type": "pdf",
      "size": 256000,
      "generated_at": "2024-12-23T10:36:00.123456"
    }
  ]
}
```

---

## 三、错误码说明

| HTTP 状态码 | 错误类型 | 说明 |
|-------------|----------|------|
| 400 | Bad Request | 请求参数错误，如 JSON 格式错误、缺少必填参数 |
| 404 | Not Found | 资源不存在，如报告 ID 不存在、图片不存在 |
| 500 | Internal Server Error | 服务器内部错误，如数据库连接失败、文件生成失败 |

**错误响应格式**

```json
{
  "detail": "具体错误信息描述"
}
```

---

## 四、数据模型

### 4.1 报告 ID 格式

```
RPT-YYYYMMDD-XXXXXXXX
```

- `RPT`: 固定前缀
- `YYYYMMDD`: 创建日期
- `XXXXXXXX`: 8 位随机十六进制字符串（大写）

示例：`RPT-20241223-A1B2C3D4`

### 4.2 图片 ID 格式

```
IMG-XXXXXXXXXXXX
```

- `IMG`: 固定前缀
- `XXXXXXXXXXXX`: 12 位随机十六进制字符串

示例：`IMG-a1b2c3d4e5f6`

### 4.3 安全属性等级

| 值 | 说明 |
|----|------|
| 高 | 高安全要求 |
| 中 | 中等安全要求 |
| 低 | 低安全要求 |

### 4.4 影响等级

| 值 | 说明 |
|----|------|
| 严重的 | 最高影响等级 |
| 重大的 | 重大影响 |
| 中等的 | 中等影响 |
| 可忽略的 | 可忽略影响 |

---

## 五、使用流程

### 5.1 完整报告生成流程

```
1. 准备 JSON 数据文件和相关图片
2. 调用 POST /api/v1/upload/batch 上传数据并自动生成报告
3. 使用返回的 report_id 访问报告
4. 调用 GET /api/v1/reports/{report_id}/download 下载报告
```

### 5.2 分步骤操作流程

```
1. 调用 POST /api/v1/reports/upload 上传数据（不自动生成报告）
2. 调用 POST /api/v1/reports/{report_id}/generate?format=xlsx 生成 Excel
3. 调用 POST /api/v1/reports/{report_id}/generate?format=pdf 生成 PDF
4. 调用 GET /api/v1/reports/{report_id}/download 下载报告
```

### 5.3 图片单独上传流程

```
1. 调用 POST /api/v1/images/upload 上传图片
2. 保存返回的 image_id
3. 在 JSON 数据中引用 image_id
4. 调用 POST /api/v1/upload/batch 上传完整数据
```

---

## 六、版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2024-12-23 | 初始版本，包含完整的数据上传、报告生成和下载功能 |
