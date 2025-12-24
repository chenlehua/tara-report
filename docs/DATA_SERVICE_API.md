# Data Service API 规范

数据服务 - TARA报告数据管理服务

## 服务信息

- **服务名称**: TARA Data Service
- **版本**: 1.0.0
- **端口**: 8001
- **描述**: 负责上传JSON和图片、解析数据并保存到MySQL和MinIO

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

**时序图:**
```
┌────────┐          ┌──────────────┐
│ Client │          │ Data Service │
└───┬────┘          └──────┬───────┘
    │                      │
    │  GET /               │
    │─────────────────────>│
    │                      │
    │  { name, version,    │
    │    status }          │
    │<─────────────────────│
    │                      │
```

**响应示例:**
```json
{
  "name": "TARA Data Service",
  "version": "1.0.0",
  "status": "running"
}
```

---

#### GET /api/v1/health

健康检查，返回服务和依赖状态。

**时序图:**
```
┌────────┐          ┌──────────────┐          ┌───────┐          ┌───────┐
│ Client │          │ Data Service │          │ MySQL │          │ MinIO │
└───┬────┘          └──────┬───────┘          └───┬───┘          └───┬───┘
    │                      │                      │                  │
    │  GET /api/v1/health     │                      │                  │
    │─────────────────────>│                      │                  │
    │                      │                      │                  │
    │                      │  SELECT 1            │                  │
    │                      │─────────────────────>│                  │
    │                      │                      │                  │
    │                      │  OK                  │                  │
    │                      │<─────────────────────│                  │
    │                      │                      │                  │
    │                      │  Check connection    │                  │
    │                      │─────────────────────────────────────────>│
    │                      │                      │                  │
    │                      │  OK                  │                  │
    │                      │<─────────────────────────────────────────│
    │                      │                      │                  │
    │  { status, services }│                      │                  │
    │<─────────────────────│                      │                  │
    │                      │                      │                  │
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

**时序图:**
```
┌────────┐          ┌──────────────┐          ┌───────┐
│ Client │          │ Data Service │          │ MinIO │
└───┬────┘          └──────┬───────┘          └───┬───┘
    │                      │                      │
    │  POST /api/v1/images/   │                      │
    │  upload              │                      │
    │  [file, image_type]  │                      │
    │─────────────────────>│                      │
    │                      │                      │
    │                      │  Validate file type  │
    │                      │──────┐               │
    │                      │      │               │
    │                      │<─────┘               │
    │                      │                      │
    │                      │  Generate image_id   │
    │                      │──────┐               │
    │                      │      │               │
    │                      │<─────┘               │
    │                      │                      │
    │                      │  Upload to temp/     │
    │                      │─────────────────────>│
    │                      │                      │
    │                      │  OK                  │
    │                      │<─────────────────────│
    │                      │                      │
    │  { success,          │                      │
    │    image_id,         │                      │
    │    image_url }       │                      │
    │<─────────────────────│                      │
    │                      │                      │
```

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

**时序图:**
```
┌────────┐          ┌──────────────┐          ┌───────┐          ┌───────┐
│ Client │          │ Data Service │          │ MySQL │          │ MinIO │
└───┬────┘          └──────┬───────┘          └───┬───┘          └───┬───┘
    │                      │                      │                  │
    │  GET /api/v1/images/    │                      │                  │
    │  {image_id}          │                      │                  │
    │─────────────────────>│                      │                  │
    │                      │                      │                  │
    │                      │  Check temp storage  │                  │
    │                      │──────┐               │                  │
    │                      │      │               │                  │
    │                      │<─────┘               │                  │
    │                      │                      │                  │
    │                      │  [If not in temp]    │                  │
    │                      │  Query image info    │                  │
    │                      │─────────────────────>│                  │
    │                      │                      │                  │
    │                      │  Image record        │                  │
    │                      │<─────────────────────│                  │
    │                      │                      │                  │
    │                      │  Download image      │                  │
    │                      │─────────────────────────────────────────>│
    │                      │                      │                  │
    │                      │  Image content       │                  │
    │                      │<─────────────────────────────────────────│
    │                      │                      │                  │
    │  Image stream        │                      │                  │
    │<─────────────────────│                      │                  │
    │                      │                      │                  │
```

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| image_id | string | 图片ID |

**响应:** 图片文件流

---

### 3. 报告数据上传

#### POST /api/v1/reports/upload

上传JSON参数和图片，生成报告ID并保存数据到数据库。

**时序图:**
```
┌────────┐          ┌──────────────┐          ┌───────┐          ┌───────┐
│ Client │          │ Data Service │          │ MySQL │          │ MinIO │
└───┬────┘          └──────┬───────┘          └───┬───┘          └───┬───┘
    │                      │                      │                  │
    │  POST /api/v1/reports/  │                      │                  │
    │  upload              │                      │                  │
    │  [json, images]      │                      │                  │
    │─────────────────────>│                      │                  │
    │                      │                      │                  │
    │                      │  Parse JSON          │                  │
    │                      │──────┐               │                  │
    │                      │      │               │                  │
    │                      │<─────┘               │                  │
    │                      │                      │                  │
    │                      │  Generate report_id  │                  │
    │                      │──────┐               │                  │
    │                      │      │               │                  │
    │                      │<─────┘               │                  │
    │                      │                      │                  │
    │                      │  Create report       │                  │
    │                      │─────────────────────>│                  │
    │                      │                      │                  │
    │                      │  [For each image]    │                  │
    │                      │  Upload image        │                  │
    │                      │─────────────────────────────────────────>│
    │                      │                      │                  │
    │                      │  Save cover,         │                  │
    │                      │  definitions,        │                  │
    │                      │  assets, etc.        │                  │
    │                      │─────────────────────>│                  │
    │                      │                      │                  │
    │  { success,          │                      │                  │
    │    report_id,        │                      │                  │
    │    statistics }      │                      │                  │
    │<─────────────────────│                      │                  │
    │                      │                      │                  │
```

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

**时序图:**
```
┌────────┐          ┌──────────────┐          ┌────────────────┐          ┌───────┐          ┌───────┐
│ Client │          │ Data Service │          │ Report Service │          │ MySQL │          │ MinIO │
└───┬────┘          └──────┬───────┘          └───────┬────────┘          └───┬───┘          └───┬───┘
    │                      │                          │                      │                  │
    │  POST /api/v1/upload/   │                          │                      │                  │
    │  batch               │                          │                      │                  │
    │  [json, images]      │                          │                      │                  │
    │─────────────────────>│                          │                      │                  │
    │                      │                          │                      │                  │
    │                      │  Parse JSON & save       │                      │                  │
    │                      │──────────────────────────────────────────────────>│                  │
    │                      │                          │                      │                  │
    │                      │  Upload images           │                      │                  │
    │                      │─────────────────────────────────────────────────────────────────────>│
    │                      │                          │                      │                  │
    │                      │  POST /generate (xlsx)   │                      │                  │
    │                      │─────────────────────────>│                      │                  │
    │                      │                          │                      │                  │
    │                      │  POST /generate (pdf)    │                      │                  │
    │                      │─────────────────────────>│                      │                  │
    │                      │                          │                      │                  │
    │  { success,          │                          │                      │                  │
    │    report_id,        │                          │                      │                  │
    │    report_info }     │                          │                      │                  │
    │<─────────────────────│                          │                      │                  │
    │                      │                          │                      │                  │
```

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

### 4. 报告数据查询（内部服务调用）

以下端点主要供 Report Service 内部调用获取报告数据。

#### GET /api/v1/reports/{report_id}/cover

获取报告封面信息。

**时序图:**
```
┌────────────────┐          ┌──────────────┐          ┌───────┐
│ Report Service │          │ Data Service │          │ MySQL │
└───────┬────────┘          └──────┬───────┘          └───┬───┘
        │                          │                      │
        │  GET /api/v1/reports/       │                      │
        │  {report_id}/cover       │                      │
        │─────────────────────────>│                      │
        │                          │                      │
        │                          │  Query cover         │
        │                          │─────────────────────>│
        │                          │                      │
        │                          │  Cover record        │
        │                          │<─────────────────────│
        │                          │                      │
        │  { cover data }          │                      │
        │<─────────────────────────│                      │
        │                          │                      │
```

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
  "review_date": "2025.01"
}
```

---

#### GET /api/v1/reports/{report_id}/definitions

获取报告相关定义。

#### GET /api/v1/reports/{report_id}/assets

获取报告资产列表。

#### GET /api/v1/reports/{report_id}/attack-trees

获取报告攻击树。

#### GET /api/v1/reports/{report_id}/tara-results

获取TARA分析结果。

---

### 5. 图片访问

#### GET /api/v1/reports/{report_id}/images/{image_id}

获取报告关联的图片。

**时序图:**
```
┌────────┐          ┌──────────────┐          ┌───────┐          ┌───────┐
│ Client │          │ Data Service │          │ MySQL │          │ MinIO │
└───┬────┘          └──────┬───────┘          └───┬───┘          └───┬───┘
    │                      │                      │                  │
    │  GET /api/v1/reports/   │                      │                  │
    │  {id}/images/{img}   │                      │                  │
    │─────────────────────>│                      │                  │
    │                      │                      │                  │
    │                      │  Query image record  │                  │
    │                      │─────────────────────>│                  │
    │                      │                      │                  │
    │                      │  Image info          │                  │
    │                      │<─────────────────────│                  │
    │                      │                      │                  │
    │                      │  Download image      │                  │
    │                      │─────────────────────────────────────────>│
    │                      │                      │                  │
    │                      │  Image content       │                  │
    │                      │<─────────────────────────────────────────│
    │                      │                      │                  │
    │  Image stream        │                      │                  │
    │<─────────────────────│                      │                  │
    │                      │                      │                  │
```

---

#### GET /api/v1/reports/{report_id}/image-by-path

根据MinIO路径获取图片。

**查询参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| path | string | MinIO对象路径 |

**响应:** 图片文件流

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
    "version": "V1.0"
  },
  "definitions": {...},
  "assets": {...},
  "attack_trees": {...},
  "tara_results": {...}
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
