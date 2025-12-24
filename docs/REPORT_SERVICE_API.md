# Report Service API 规范

报告服务 - TARA报告生成和下载服务

## 服务信息

- **服务名称**: TARA Report Service
- **版本**: 1.0.0
- **端口**: 8002
- **描述**: 负责根据报告ID生成Excel和PDF报告，并提供下载功能

## 基础信息

### 基础URL

```
http://report-service:8002
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
  "name": "TARA Report Service",
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
    "minio": "healthy",
    "data_service": "healthy"
  }
}
```

---

### 2. 报告生成

#### POST /api/reports/{report_id}/generate

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
  "download_url": "/api/reports/RPT-20250115-ABC12345/download?format=xlsx",
  "file_name": "项目名称_RPT-20250115-ABC12345.xlsx"
}
```

**错误响应:**

| 状态码 | 说明 |
|--------|------|
| 404 | 报告不存在 |
| 500 | 获取报告数据失败 / 报告生成失败 |

---

### 3. 报告下载

#### GET /api/reports/{report_id}/download

下载报告文件（格式作为查询参数）。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |

**查询参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| format | string | xlsx | 报告格式: `xlsx` 或 `pdf` |

**响应:** 
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (xlsx)
- Content-Type: `application/pdf` (pdf)
- Content-Disposition: `attachment; filename*=UTF-8''项目名称_RPT-xxx.xlsx`

**错误响应:**

| 状态码 | 说明 |
|--------|------|
| 404 | 报告文件不存在，请先生成报告 |
| 500 | 下载报告失败 |

---

#### GET /api/reports/{report_id}/download/{format}

下载报告文件（格式作为路径参数）。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |
| format | string | 报告格式: `xlsx` 或 `pdf` |

**响应:** 同上

---

### 4. 报告预览

#### GET /api/reports/{report_id}/preview

获取报告预览数据。

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
  "file_path": "",
  "statistics": {
    "assets_count": 10,
    "threats_count": 25,
    "high_risk_count": 5,
    "measures_count": 25,
    "attack_trees_count": 3
  },
  "report_info": {
    "id": "RPT-20250115-ABC12345",
    "name": "威胁分析和风险评估报告",
    "project_name": "项目名称",
    "version": "V1.0",
    "created_at": "2025-01-15T10:30:00.000000",
    "file_path": "",
    "file_size": 0,
    "statistics": {}
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
    "item_boundary_image": "/api/reports/RPT-xxx/image-by-path?path=...",
    "system_architecture_image": "/api/reports/RPT-xxx/image-by-path?path=...",
    "software_architecture_image": "/api/reports/RPT-xxx/image-by-path?path=...",
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
    "attack_trees": [
      {
        "asset_id": "P001",
        "asset_name": "SOC",
        "title": "攻击树1",
        "image": "path/to/image",
        "image_url": "/api/reports/RPT-xxx/image-by-path?path=..."
      }
    ]
  },
  "tara_results": {
    "title": "TARA分析结果",
    "results": []
  },
  "downloads": {
    "xlsx": {
      "url": "/api/reports/RPT-xxx/download?format=xlsx",
      "file_size": 125840,
      "generated_at": "2025-01-15T10:35:00.000000"
    },
    "pdf": {
      "url": "/api/reports/RPT-xxx/download?format=pdf",
      "file_size": 256000,
      "generated_at": "2025-01-15T10:36:00.000000"
    }
  }
}
```

---

### 5. 报告状态

#### GET /api/reports/{report_id}/status

获取报告状态信息。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |

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
    },
    {
      "type": "pdf",
      "size": 256000,
      "generated_at": "2025-01-15T10:36:00.000000"
    }
  ]
}
```

**错误响应:**

| 状态码 | 说明 |
|--------|------|
| 404 | 报告不存在 |

---

## 报告格式

### Excel报告 (.xlsx)

Excel报告包含以下工作表：

1. **封面** - 报告基本信息
2. **相关定义** - 功能描述、假设条件、术语表
3. **资产列表** - 资产清单及安全属性
4. **攻击树分析** - 攻击树图表
5. **TARA分析结果** - 威胁分析详情

### PDF报告 (.pdf)

PDF报告包含与Excel相同的内容，支持中文字体显示。

---

## 服务依赖

### 数据服务 (Data Service)

报告服务需要从数据服务获取报告数据：

| 端点 | 说明 |
|------|------|
| GET /api/reports/{report_id}/cover | 获取封面数据 |
| GET /api/reports/{report_id}/definitions | 获取定义数据 |
| GET /api/reports/{report_id}/assets | 获取资产数据 |
| GET /api/reports/{report_id}/attack-trees | 获取攻击树数据 |
| GET /api/reports/{report_id}/tara-results | 获取TARA结果数据 |

### MinIO

- 存储生成的报告文件
- 获取图片文件用于嵌入报告

### MySQL

- 存储生成报告的元数据

---

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DATA_SERVICE_URL | http://data-service:8001 | 数据服务地址 |
| MYSQL_HOST | mysql | MySQL主机 |
| MYSQL_PORT | 3306 | MySQL端口 |
| MYSQL_USER | root | MySQL用户名 |
| MYSQL_PASSWORD | password | MySQL密码 |
| MYSQL_DATABASE | tara | MySQL数据库名 |
| MINIO_ENDPOINT | minio:9000 | MinIO端点 |
| MINIO_ACCESS_KEY | minioadmin | MinIO访问密钥 |
| MINIO_SECRET_KEY | minioadmin | MinIO密钥 |

---

## MinIO存储桶

| 存储桶名称 | 说明 |
|------------|------|
| tara-reports | 存储生成的报告文件 |
| tara-images | 存储图片文件 |

### 报告文件路径格式

```
{report_id}/{report_id}.xlsx
{report_id}/{report_id}.pdf
```

---

## 错误码

| HTTP状态码 | 说明 |
|------------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 使用示例

### 生成Excel报告

```bash
# 生成Excel报告
curl -X POST "http://report-service:8002/api/reports/RPT-20250115-ABC12345/generate?format=xlsx"

# 下载Excel报告
curl -O "http://report-service:8002/api/reports/RPT-20250115-ABC12345/download?format=xlsx"
```

### 生成PDF报告

```bash
# 生成PDF报告
curl -X POST "http://report-service:8002/api/reports/RPT-20250115-ABC12345/generate?format=pdf"

# 下载PDF报告
curl -O "http://report-service:8002/api/reports/RPT-20250115-ABC12345/download?format=pdf"
```

### 获取报告预览

```bash
curl "http://report-service:8002/api/reports/RPT-20250115-ABC12345/preview"
```

---

## 工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        Report Generation Flow                    │
└─────────────────────────────────────────────────────────────────┘

1. 客户端请求生成报告
   POST /api/reports/{report_id}/generate?format=xlsx

2. 报告服务从数据服务获取数据
   GET http://data-service:8001/api/reports/{report_id}/cover
   GET http://data-service:8001/api/reports/{report_id}/definitions
   GET http://data-service:8001/api/reports/{report_id}/assets
   GET http://data-service:8001/api/reports/{report_id}/attack-trees
   GET http://data-service:8001/api/reports/{report_id}/tara-results

3. 报告服务从MinIO下载图片到临时文件

4. 报告服务生成报告文件 (Excel/PDF)

5. 报告服务上传生成的报告到MinIO

6. 报告服务更新数据库记录

7. 返回生成结果和下载链接

8. 客户端下载报告
   GET /api/reports/{report_id}/download?format=xlsx
```

---

## 注意事项

1. **PDF中文支持**: 系统需要安装中文字体（如文泉驿正黑、思源黑体等）才能正确显示PDF中的中文内容

2. **大文件处理**: 对于包含大量图片的报告，生成时间可能较长，建议设置适当的超时时间

3. **临时文件清理**: 报告生成过程中会创建临时文件，生成完成后会自动清理

4. **并发限制**: 建议对报告生成接口进行并发限制，避免资源耗尽
