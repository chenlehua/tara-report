# Report Service API 规范

报告服务 - TARA报告生成、管理和下载服务

## 服务信息

- **服务名称**: TARA Report Service
- **版本**: 1.0.0
- **端口**: 8002
- **描述**: 负责报告列表查询、报告详情、生成Excel和PDF报告、下载和删除报告

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

**时序图:**
```
┌────────┐          ┌────────────────┐
│ Client │          │ Report Service │
└───┬────┘          └───────┬────────┘
    │                       │
    │  GET /                │
    │──────────────────────>│
    │                       │
    │  { name, version,     │
    │    status }           │
    │<──────────────────────│
    │                       │
```

**响应示例:**
```json
{
  "name": "TARA Report Service",
  "version": "1.0.0",
  "status": "running"
}
```

---

#### GET /api/v1/health

健康检查，返回服务和依赖状态。

**时序图:**
```
┌────────┐          ┌────────────────┐          ┌───────┐          ┌───────┐          ┌──────────────┐
│ Client │          │ Report Service │          │ MySQL │          │ MinIO │          │ Data Service │
└───┬────┘          └───────┬────────┘          └───┬───┘          └───┬───┘          └──────┬───────┘
    │                       │                       │                  │                     │
    │  GET /api/v1/health      │                       │                  │                     │
    │──────────────────────>│                       │                  │                     │
    │                       │                       │                  │                     │
    │                       │  SELECT 1             │                  │                     │
    │                       │──────────────────────>│                  │                     │
    │                       │                       │                  │                     │
    │                       │  Check connection     │                  │                     │
    │                       │──────────────────────────────────────────>│                     │
    │                       │                       │                  │                     │
    │                       │  GET /api/v1/health      │                  │                     │
    │                       │────────────────────────────────────────────────────────────────>│
    │                       │                       │                  │                     │
    │  { status, services } │                       │                  │                     │
    │<──────────────────────│                       │                  │                     │
    │                       │                       │                  │                     │
```

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

### 2. 报告列表

#### GET /api/v1/reports

获取报告列表。

**时序图:**
```
┌────────┐          ┌────────────────┐          ┌───────┐
│ Client │          │ Report Service │          │ MySQL │
└───┬────┘          └───────┬────────┘          └───┬───┘
    │                       │                       │
    │  GET /api/v1/reports     │                       │
    │  ?page=1&page_size=20 │                       │
    │──────────────────────>│                       │
    │                       │                       │
    │                       │  Count reports        │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Query reports        │
    │                       │  (paginated)          │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  [For each report]    │
    │                       │  Query cover          │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Count assets         │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Count tara_results   │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Count high_risk      │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Query generated_files│
    │                       │──────────────────────>│
    │                       │                       │
    │  { success, total,    │                       │
    │    page, reports }    │                       │
    │<──────────────────────│                       │
    │                       │                       │
```

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
      },
      "downloads": {
        "xlsx": {
          "url": "/api/v1/reports/RPT-xxx/download?format=xlsx",
          "file_size": 125840,
          "generated_at": "2025-01-15T10:35:00"
        },
        "pdf": {
          "url": "/api/v1/reports/RPT-xxx/download?format=pdf",
          "file_size": 256000,
          "generated_at": "2025-01-15T10:36:00"
        }
      }
    }
  ]
}
```

---

### 3. 报告详情

#### GET /api/v1/reports/{report_id}

获取报告完整信息。

**时序图:**
```
┌────────┐          ┌────────────────┐          ┌───────┐
│ Client │          │ Report Service │          │ MySQL │
└───┬────┘          └───────┬────────┘          └───┬───┘
    │                       │                       │
    │  GET /api/v1/reports/    │                       │
    │  {report_id}          │                       │
    │──────────────────────>│                       │
    │                       │                       │
    │                       │  Query report         │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Query cover          │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Query definitions    │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Query assets         │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Query attack_trees   │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Query tara_results   │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Query generated_files│
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Build response       │
    │                       │───────┐               │
    │                       │       │               │
    │                       │<──────┘               │
    │                       │                       │
    │  { report data,       │                       │
    │    statistics,        │                       │
    │    downloads }        │                       │
    │<──────────────────────│                       │
    │                       │                       │
```

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
  "downloads": {
    "xlsx": {...},
    "pdf": {...}
  },
  "cover": {...},
  "definitions": {...},
  "assets": {...},
  "attack_trees": {...},
  "tara_results": {
    "title": "TARA分析结果 TARA Analysis Results",
    "results": [
      {
        // 基础字段
        "asset_id": "AS001",
        "asset_name": "车载诊断数据",
        "stride_model": "I信息泄露",
        "attack_vector": "物理",
        "attack_complexity": "低",
        "privileges_required": "无",
        "user_interaction": "不需要",
        "safety_impact": "可忽略不计的",
        "financial_impact": "中等的",
        "operational_impact": "中等的",
        "privacy_impact": "重大的",
        // ... 其他基础字段
        
        // 攻击可行性计算字段（后端自动生成）
        "attack_vector_value": 0.2,
        "attack_complexity_value": 0.77,
        "privileges_required_value": 0.85,
        "user_interaction_value": 0.85,
        "attack_feasibility_value": 0.91,
        "attack_feasibility_level": "很低",
        
        // 影响分析计算字段（后端自动生成）
        "safety_impact_value": 0,
        "financial_impact_value": 1,
        "operational_impact_value": 1,
        "privacy_impact_value": 10,
        "total_impact_value": 12,
        "impact_level": "中等的",
        
        // 影响注释字段（后端自动生成）
        "safety_note": "没有受伤",
        "financial_note": "财务损失会产生中等影响",
        "operational_note": "操作损坏会导致车辆功能中等减少",
        "privacy_note": "隐私危害会产生重大影响",
        
        // 风险评估计算字段（后端自动生成）
        "risk_level": "Low",
        "risk_treatment": "保留风险",
        "calculated_security_goal": "/",
        "wp29_control_mapping": "M11"
      }
    ]
  }
}
```

> **注意**: `tara_results.results` 中的每条记录包含后端自动计算的派生列，详细字段说明请参考 [Data Service API - TARA Results](./DATA_SERVICE_API.md#get-apiv1reportsreport_idtara-results)。

**错误响应:**

| 状态码 | 说明 |
|--------|------|
| 404 | 报告不存在 |

---

### 4. 删除报告

#### DELETE /api/v1/reports/{report_id}

删除报告及其所有关联资源。

**时序图:**
```
┌────────┐          ┌────────────────┐          ┌───────┐          ┌───────┐
│ Client │          │ Report Service │          │ MySQL │          │ MinIO │
└───┬────┘          └───────┬────────┘          └───┬───┘          └───┬───┘
    │                       │                       │                  │
    │  DELETE /api/v1/reports/ │                       │                  │
    │  {report_id}          │                       │                  │
    │──────────────────────>│                       │                  │
    │                       │                       │                  │
    │                       │  Query report         │                  │
    │                       │──────────────────────>│                  │
    │                       │                       │                  │
    │                       │  Report record        │                  │
    │                       │<──────────────────────│                  │
    │                       │                       │                  │
    │                       │  Query images         │                  │
    │                       │──────────────────────>│                  │
    │                       │                       │                  │
    │                       │  [For each image]     │                  │
    │                       │  Delete from MinIO    │                  │
    │                       │─────────────────────────────────────────>│
    │                       │                       │                  │
    │                       │  Query generated_files│                  │
    │                       │──────────────────────>│                  │
    │                       │                       │                  │
    │                       │  [For each file]      │                  │
    │                       │  Delete from MinIO    │                  │
    │                       │─────────────────────────────────────────>│
    │                       │                       │                  │
    │                       │  Delete report        │                  │
    │                       │  (cascade delete)     │                  │
    │                       │──────────────────────>│                  │
    │                       │                       │                  │
    │  { success: true,     │                       │                  │
    │    message }          │                       │                  │
    │<──────────────────────│                       │                  │
    │                       │                       │                  │
```

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |

**响应示例:**
```json
{
  "success": true,
  "message": "报告已删除"
}
```

**错误响应:**

| 状态码 | 说明 |
|--------|------|
| 404 | 报告不存在 |

**注意事项:**
- 此操作不可逆，将永久删除报告及其所有关联资源
- 删除的内容包括：
  - 数据库中的报告记录（含封面、定义、资产、攻击树、TARA结果）
  - MinIO中存储的所有图片文件
  - MinIO中存储的生成报告文件（Excel、PDF）

---

### 5. 报告生成

#### POST /api/v1/reports/{report_id}/generate

生成报告文件（Excel或PDF）。

**时序图:**
```
┌────────┐          ┌────────────────┐          ┌──────────────┐          ┌───────┐          ┌───────┐
│ Client │          │ Report Service │          │ Data Service │          │ MySQL │          │ MinIO │
└───┬────┘          └───────┬────────┘          └──────┬───────┘          └───┬───┘          └───┬───┘
    │                       │                          │                      │                  │
    │  POST /api/v1/reports/   │                          │                      │                  │
    │  {id}/generate        │                          │                      │                  │
    │  ?format=xlsx         │                          │                      │                  │
    │──────────────────────>│                          │                      │                  │
    │                       │                          │                      │                  │
    │                       │  Check report exists     │                      │                  │
    │                       │─────────────────────────────────────────────────>│                  │
    │                       │                          │                      │                  │
    │                       │  GET cover, definitions, │                      │                  │
    │                       │  assets, attack-trees,   │                      │                  │
    │                       │  tara-results            │                      │                  │
    │                       │─────────────────────────>│                      │                  │
    │                       │                          │                      │                  │
    │                       │  [For each image]        │                      │                  │
    │                       │  Download from MinIO     │                      │                  │
    │                       │─────────────────────────────────────────────────────────────────────>│
    │                       │                          │                      │                  │
    │                       │  Generate Excel/PDF      │                      │                  │
    │                       │───────┐                  │                      │                  │
    │                       │       │                  │                      │                  │
    │                       │<──────┘                  │                      │                  │
    │                       │                          │                      │                  │
    │                       │  Upload to MinIO         │                      │                  │
    │                       │─────────────────────────────────────────────────────────────────────>│
    │                       │                          │                      │                  │
    │                       │  Save generated_report   │                      │                  │
    │                       │─────────────────────────────────────────────────>│                  │
    │                       │                          │                      │                  │
    │  { success,           │                          │                      │                  │
    │    download_url }     │                          │                      │                  │
    │<──────────────────────│                          │                      │                  │
    │                       │                          │                      │                  │
```

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

### 6. 报告下载

#### GET /api/v1/reports/{report_id}/download

下载报告文件（格式作为查询参数）。

**时序图:**
```
┌────────┐          ┌────────────────┐          ┌───────┐          ┌───────┐
│ Client │          │ Report Service │          │ MySQL │          │ MinIO │
└───┬────┘          └───────┬────────┘          └───┬───┘          └───┬───┘
    │                       │                       │                  │
    │  GET /api/v1/reports/    │                       │                  │
    │  {id}/download        │                       │                  │
    │  ?format=xlsx         │                       │                  │
    │──────────────────────>│                       │                  │
    │                       │                       │                  │
    │                       │  Query generated_report                  │
    │                       │──────────────────────>│                  │
    │                       │                       │                  │
    │                       │  Download file        │                  │
    │                       │─────────────────────────────────────────>│
    │                       │                       │                  │
    │                       │  Query cover          │                  │
    │                       │  (for filename)       │                  │
    │                       │──────────────────────>│                  │
    │                       │                       │                  │
    │  File stream          │                       │                  │
    │  (Content-Disposition)│                       │                  │
    │<──────────────────────│                       │                  │
    │                       │                       │                  │
```

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

---

#### GET /api/v1/reports/{report_id}/download/{format}

下载报告文件（格式作为路径参数）。

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |
| format | string | 报告格式: `xlsx` 或 `pdf` |

---

### 7. 报告预览

#### GET /api/v1/reports/{report_id}/preview

获取报告预览数据，包含完整的报告内容和后端自动计算的TARA派生列。

**时序图:**
```
┌────────┐          ┌────────────────┐          ┌──────────────┐          ┌───────┐
│ Client │          │ Report Service │          │ Data Service │          │ MySQL │
└───┬────┘          └───────┬────────┘          └──────┬───────┘          └───┬───┘
    │                       │                          │                      │
    │  GET /api/v1/reports/    │                          │                      │
    │  {id}/preview         │                          │                      │
    │──────────────────────>│                          │                      │
    │                       │                          │                      │
    │                       │  GET cover, definitions, │                      │
    │                       │  assets, attack-trees,   │                      │
    │                       │  tara-results (含计算列)  │                      │
    │                       │─────────────────────────>│                      │
    │                       │                          │                      │
    │                       │  Query generated_files   │                      │
    │                       │─────────────────────────────────────────────────>│
    │                       │                          │                      │
    │                       │  Query report & cover    │                      │
    │                       │─────────────────────────────────────────────────>│
    │                       │                          │                      │
    │  { preview data,      │                          │                      │
    │    downloads }        │                          │                      │
    │<──────────────────────│                          │                      │
    │                       │                          │                      │
```

**响应说明:**

预览数据包含与报告详情相同的结构，其中 `tara_results` 部分包含后端自动计算的派生列：

- **攻击可行性计算**: attack_vector_value, attack_complexity_value, privileges_required_value, user_interaction_value, attack_feasibility_value, attack_feasibility_level
- **影响分析计算**: safety_impact_value, financial_impact_value, operational_impact_value, privacy_impact_value, total_impact_value, impact_level
- **影响注释**: safety_note, financial_note, operational_note, privacy_note
- **风险评估计算**: risk_level, risk_treatment, calculated_security_goal, wp29_control_mapping

前端可直接使用这些预计算的值进行展示，无需在客户端重复计算。

---

### 8. 报告状态

#### GET /api/v1/reports/{report_id}/status

获取报告状态信息。

**时序图:**
```
┌────────┐          ┌────────────────┐          ┌───────┐
│ Client │          │ Report Service │          │ MySQL │
└───┬────┘          └───────┬────────┘          └───┬───┘
    │                       │                       │
    │  GET /api/v1/reports/    │                       │
    │  {id}/status          │                       │
    │──────────────────────>│                       │
    │                       │                       │
    │                       │  Query report         │
    │                       │──────────────────────>│
    │                       │                       │
    │                       │  Query generated_files│
    │                       │──────────────────────>│
    │                       │                       │
    │  { report_id, status, │                       │
    │    generated_files }  │                       │
    │<──────────────────────│                       │
    │                       │                       │
```

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

报告服务需要从数据服务获取报告原始数据：

| 端点 | 说明 |
|------|------|
| GET /api/v1/reports/{report_id}/cover | 获取封面数据 |
| GET /api/v1/reports/{report_id}/definitions | 获取定义数据 |
| GET /api/v1/reports/{report_id}/assets | 获取资产数据 |
| GET /api/v1/reports/{report_id}/attack-trees | 获取攻击树数据 |
| GET /api/v1/reports/{report_id}/tara-results | 获取TARA结果数据（含后端自动计算的派生列） |

### MinIO

- 存储生成的报告文件
- 获取图片文件用于嵌入报告

### MySQL

- 存储报告元数据和生成记录
- 查询报告列表和统计信息

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

---

## 错误码

| HTTP状态码 | 说明 |
|------------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 使用示例

### 获取报告列表

```bash
curl "http://report-service:8002/api/v1/reports?page=1&page_size=20"
```

### 获取报告详情

```bash
curl "http://report-service:8002/api/v1/reports/RPT-20250115-ABC12345"
```

### 删除报告

```bash
curl -X DELETE "http://report-service:8002/api/v1/reports/RPT-20250115-ABC12345"
```

### 生成报告

```bash
# 生成Excel报告
curl -X POST "http://report-service:8002/api/v1/reports/RPT-20250115-ABC12345/generate?format=xlsx"

# 生成PDF报告
curl -X POST "http://report-service:8002/api/v1/reports/RPT-20250115-ABC12345/generate?format=pdf"
```

### 下载报告

```bash
# 下载Excel
curl -O "http://report-service:8002/api/v1/reports/RPT-20250115-ABC12345/download?format=xlsx"

# 下载PDF
curl -O "http://report-service:8002/api/v1/reports/RPT-20250115-ABC12345/download/pdf"
```

---

## 完整工作流程

### 报告管理流程

```
┌────────┐          ┌───────┐          ┌────────────────┐          ┌───────┐
│ Client │          │ Nginx │          │ Report Service │          │ MySQL │
└───┬────┘          └───┬───┘          └───────┬────────┘          └───┬───┘
    │                   │                      │                       │
    │ [获取报告列表]    │                      │                       │
    │  GET /api/v1/reports │                      │                       │
    │──────────────────>│                      │                       │
    │                   │─────────────────────>│                       │
    │                   │                      │──────────────────────>│
    │  { reports }      │                      │                       │
    │<───────────────────────────────────────────                      │
    │                   │                      │                       │
    │ [获取报告详情]    │                      │                       │
    │  GET /api/v1/reports/{id}                   │                       │
    │──────────────────>│                      │                       │
    │                   │─────────────────────>│                       │
    │                   │                      │──────────────────────>│
    │  { report detail }│                      │                       │
    │<───────────────────────────────────────────                      │
    │                   │                      │                       │
    │ [删除报告]        │                      │                       │
    │  DELETE /api/v1/reports/{id}                │                       │
    │──────────────────>│                      │                       │
    │                   │─────────────────────>│                       │
    │                   │                      │  Delete from MinIO    │
    │                   │                      │  Delete from MySQL    │
    │                   │                      │──────────────────────>│
    │  { success }      │                      │                       │
    │<───────────────────────────────────────────                      │
    │                   │                      │                       │
```

---

## 注意事项

1. **PDF中文支持**: 系统需要安装中文字体才能正确显示PDF中的中文内容

2. **大文件处理**: 对于包含大量图片的报告，生成时间可能较长

3. **删除操作**: 删除报告是不可逆操作，会永久删除所有相关资源

4. **并发限制**: 建议对报告生成接口进行并发限制
