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

获取报告相关定义，包括项目描述、架构图路径、假设条件和术语表。

**时序图:**
```
┌────────────────┐          ┌──────────────┐          ┌───────┐
│ Report Service │          │ Data Service │          │ MySQL │
└───────┬────────┘          └──────┬───────┘          └───┬───┘
        │                          │                      │
        │  GET /api/v1/reports/    │                      │
        │  {report_id}/definitions │                      │
        │─────────────────────────>│                      │
        │                          │                      │
        │                          │  Query definitions   │
        │                          │─────────────────────>│
        │                          │                      │
        │                          │  Definitions record  │
        │                          │<─────────────────────│
        │                          │                      │
        │  { definitions data }    │                      │
        │<─────────────────────────│                      │
        │                          │                      │
```

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |

**响应示例:**
```json
{
  "title": "智能网联汽车网关系统",
  "functional_description": "该系统负责车辆内部网络与外部网络的通信管理，包括数据转发、协议转换、安全防护等功能。",
  "item_boundary_image": "RPT-20250115-ABC12345/item_boundary/IMG-abc123def456.png",
  "system_architecture_image": "RPT-20250115-ABC12345/system_architecture/IMG-def456abc789.png",
  "software_architecture_image": "RPT-20250115-ABC12345/software_architecture/IMG-789abc123def.png",
  "dataflow_image": "RPT-20250115-ABC12345/dataflow/IMG-456def789abc.png",
  "assumptions": [
    {
      "id": "A001",
      "content": "假设车辆处于正常运行状态"
    },
    {
      "id": "A002",
      "content": "假设攻击者具有一定的技术能力"
    }
  ],
  "terminology": [
    {
      "term": "ECU",
      "definition": "Electronic Control Unit，电子控制单元"
    },
    {
      "term": "CAN",
      "definition": "Controller Area Network，控制器局域网"
    }
  ]
}
```

---

#### GET /api/v1/reports/{report_id}/assets

获取报告资产列表，包括数据流图和所有资产的安全属性。

**时序图:**
```
┌────────────────┐          ┌──────────────┐          ┌───────┐
│ Report Service │          │ Data Service │          │ MySQL │
└───────┬────────┘          └──────┬───────┘          └───┬───┘
        │                          │                      │
        │  GET /api/v1/reports/    │                      │
        │  {report_id}/assets      │                      │
        │─────────────────────────>│                      │
        │                          │                      │
        │                          │  Query definitions   │
        │                          │  (for dataflow_image)│
        │                          │─────────────────────>│
        │                          │                      │
        │                          │  Query assets        │
        │                          │─────────────────────>│
        │                          │                      │
        │                          │  Query cover         │
        │                          │  (for title prefix)  │
        │                          │─────────────────────>│
        │                          │                      │
        │                          │  Records             │
        │                          │<─────────────────────│
        │                          │                      │
        │  { title, dataflow_image,│                      │
        │    assets[] }            │                      │
        │<─────────────────────────│                      │
        │                          │                      │
```

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |

**响应示例:**
```json
{
  "title": "智能网联汽车网关系统 - 资产列表 Asset List",
  "dataflow_image": "RPT-20250115-ABC12345/dataflow/IMG-456def789abc.png",
  "assets": [
    {
      "id": "AS001",
      "name": "车载诊断数据",
      "category": "数据资产",
      "remarks": "包括车辆状态、故障码等诊断信息",
      "authenticity": true,
      "integrity": true,
      "non_repudiation": false,
      "confidentiality": true,
      "availability": true,
      "authorization": true
    },
    {
      "id": "AS002",
      "name": "用户隐私数据",
      "category": "数据资产",
      "remarks": "包括位置信息、驾驶习惯等",
      "authenticity": true,
      "integrity": true,
      "non_repudiation": true,
      "confidentiality": true,
      "availability": false,
      "authorization": true
    },
    {
      "id": "AS003",
      "name": "网关ECU",
      "category": "硬件资产",
      "remarks": "负责内外网数据转发",
      "authenticity": false,
      "integrity": true,
      "non_repudiation": false,
      "confidentiality": false,
      "availability": true,
      "authorization": false
    }
  ]
}
```

**资产安全属性说明:**

| 属性 | 说明 |
|------|------|
| authenticity | 真实性 - 确保数据来源可信 |
| integrity | 完整性 - 确保数据未被篡改 |
| non_repudiation | 不可否认性 - 确保操作可追溯 |
| confidentiality | 机密性 - 确保数据不被泄露 |
| availability | 可用性 - 确保服务持续可用 |
| authorization | 授权性 - 确保访问经过授权 |

---

#### GET /api/v1/reports/{report_id}/attack-trees

获取报告攻击树列表，包含每个资产对应的攻击树图片。

**时序图:**
```
┌────────────────┐          ┌──────────────┐          ┌───────┐
│ Report Service │          │ Data Service │          │ MySQL │
└───────┬────────┘          └──────┬───────┘          └───┬───┘
        │                          │                      │
        │  GET /api/v1/reports/    │                      │
        │  {report_id}/attack-trees│                      │
        │─────────────────────────>│                      │
        │                          │                      │
        │                          │  Query attack_trees  │
        │                          │  ORDER BY sort_order │
        │                          │─────────────────────>│
        │                          │                      │
        │                          │  Attack tree records │
        │                          │<─────────────────────│
        │                          │                      │
        │  { title, attack_trees[] }                      │
        │<─────────────────────────│                      │
        │                          │                      │
```

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |

**响应示例:**
```json
{
  "title": "攻击树分析 Attack Tree Analysis",
  "attack_trees": [
    {
      "asset_id": "AS001",
      "asset_name": "车载诊断数据",
      "title": "车载诊断数据攻击树",
      "image": "RPT-20250115-ABC12345/attack_tree_0/IMG-tree001abc.png"
    },
    {
      "asset_id": "AS002",
      "asset_name": "用户隐私数据",
      "title": "用户隐私数据攻击树",
      "image": "RPT-20250115-ABC12345/attack_tree_1/IMG-tree002def.png"
    },
    {
      "asset_id": "AS003",
      "asset_name": "网关ECU",
      "title": "网关ECU攻击树",
      "image": "RPT-20250115-ABC12345/attack_tree_2/IMG-tree003ghi.png"
    }
  ]
}
```

---

#### GET /api/v1/reports/{report_id}/tara-results

获取TARA（威胁分析和风险评估）分析结果，包含完整的威胁场景、攻击路径和安全措施。

**时序图:**
```
┌────────────────┐          ┌──────────────┐          ┌───────┐
│ Report Service │          │ Data Service │          │ MySQL │
└───────┬────────┘          └──────┬───────┘          └───┬───┘
        │                          │                      │
        │  GET /api/v1/reports/    │                      │
        │  {report_id}/tara-results│                      │
        │─────────────────────────>│                      │
        │                          │                      │
        │                          │  Query tara_results  │
        │                          │  ORDER BY sort_order │
        │                          │─────────────────────>│
        │                          │                      │
        │                          │  TARA result records │
        │                          │<─────────────────────│
        │                          │                      │
        │  { title, results[] }    │                      │
        │<─────────────────────────│                      │
        │                          │                      │
```

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |

**响应示例:**
```json
{
  "title": "TARA分析结果 TARA Analysis Results",
  "results": [
    {
      "asset_id": "AS001",
      "asset_name": "车载诊断数据",
      "subdomain1": "网关系统",
      "subdomain2": "诊断模块",
      "subdomain3": "OBD接口",
      "category": "数据资产",
      "security_attribute": "机密性",
      "stride_model": "信息泄露",
      "threat_scenario": "攻击者通过OBD接口读取车辆诊断数据，获取车辆敏感信息",
      "attack_path": "物理接入OBD接口 -> 发送诊断请求 -> 读取诊断响应数据",
      "wp29_mapping": "WP.29 7.2.2.3",
      "attack_vector": "物理",
      "attack_complexity": "低",
      "privileges_required": "无",
      "user_interaction": "无",
      "safety_impact": "无",
      "financial_impact": "中",
      "operational_impact": "低",
      "privacy_impact": "高",
      "security_goal": "防止未授权访问诊断数据",
      "security_requirement": "实施诊断认证机制，对敏感数据进行加密存储"
    },
    {
      "asset_id": "AS002",
      "asset_name": "用户隐私数据",
      "subdomain1": "网关系统",
      "subdomain2": "远程通信模块",
      "subdomain3": "T-Box",
      "category": "数据资产",
      "security_attribute": "机密性",
      "stride_model": "信息泄露",
      "threat_scenario": "攻击者通过中间人攻击截获远程通信数据，获取用户位置等隐私信息",
      "attack_path": "搭建伪基站 -> 劫持通信链路 -> 解密通信数据",
      "wp29_mapping": "WP.29 7.2.2.5",
      "attack_vector": "相邻网络",
      "attack_complexity": "高",
      "privileges_required": "无",
      "user_interaction": "无",
      "safety_impact": "无",
      "financial_impact": "低",
      "operational_impact": "无",
      "privacy_impact": "严重",
      "security_goal": "保护用户隐私数据在传输过程中的机密性",
      "security_requirement": "采用TLS 1.3加密通信，实施证书双向认证"
    }
  ]
}
```

**TARA结果字段说明:**

| 字段 | 说明 |
|------|------|
| asset_id | 资产ID |
| asset_name | 资产名称 |
| subdomain1/2/3 | 子域层级（系统/模块/组件） |
| category | 资产类别 |
| security_attribute | 安全属性（机密性/完整性/可用性等） |
| stride_model | STRIDE威胁模型分类 |
| threat_scenario | 威胁场景描述 |
| attack_path | 攻击路径 |
| wp29_mapping | WP.29法规映射 |
| attack_vector | 攻击向量（网络/相邻网络/本地/物理） |
| attack_complexity | 攻击复杂度（低/高） |
| privileges_required | 所需权限（无/低/高） |
| user_interaction | 用户交互（无/需要） |
| safety_impact | 安全影响（无/低/中/高/严重） |
| financial_impact | 财务影响（无/低/中/高/严重） |
| operational_impact | 运营影响（无/低/中/高/严重） |
| privacy_impact | 隐私影响（无/低/中/高/严重） |
| security_goal | 安全目标 |
| security_requirement | 安全需求/对策 |

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
