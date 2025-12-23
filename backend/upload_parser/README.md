# TARA 文件上传解析模块

## 概述

文件上传解析模块是TARA报告系统的核心组件之一，负责处理文件上传、JSON参数解析和数据持久化。

## 功能特性

- **自动生成报告ID**: 每次上传自动生成唯一的报告ID并返回前端
- **MinIO图片存储**: 上传的图片自动保存至MinIO对象存储
- **MySQL数据持久化**: 图片元数据和报告数据存储至MySQL
- **JSON参数解析**: 支持解析复杂的JSON参数文件
- **完整的API接口**: 提供各类数据的增删改查接口

## 数据库表结构

### 1. 报告主表 (reports)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(50) | 报告ID (主键) |
| name | VARCHAR(255) | 报告名称 |
| status | ENUM | 状态: PENDING/PROCESSING/COMPLETED/FAILED |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 2. 图片表 (images)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(50) | 图片ID (主键) |
| report_id | VARCHAR(50) | 报告ID (外键) |
| image_type | ENUM | 图片类型 |
| original_name | VARCHAR(255) | 原始文件名 |
| minio_path | VARCHAR(500) | MinIO存储路径 |
| minio_bucket | VARCHAR(100) | MinIO桶名 |
| file_size | INT | 文件大小 |
| content_type | VARCHAR(100) | 内容类型 |

### 3. 封面表 (covers)
包含报告标题、项目名称、版本等封面信息。

### 4. 项目定义表 (definitions)
包含功能描述、假设列表、术语表等项目定义信息。

### 5. 资产表 (assets)
包含资产ID、名称、分类、安全属性等资产信息。

### 6. 攻击树表 (attack_trees)
包含攻击树标题、描述和关联图片。

### 7. TARA分析结果表 (tara_results)
包含完整的TARA分析结果，包括威胁场景、攻击路径、影响评估等。

## API接口

### 报告管理
- `POST /api/upload-parser/reports` - 创建新报告
- `DELETE /api/upload-parser/reports/{report_id}` - 删除报告

### 图片管理
- `POST /api/upload-parser/reports/{report_id}/images` - 上传图片
- `POST /api/upload-parser/reports/{report_id}/images/batch` - 批量上传图片
- `GET /api/upload-parser/images/{image_id}` - 获取图片数据
- `GET /api/upload-parser/images/{image_id}/info` - 获取图片信息

### 数据查询
- `GET /api/upload-parser/reports/{report_id}/cover` - 获取封面
- `GET /api/upload-parser/reports/{report_id}/definitions` - 获取项目定义
- `GET /api/upload-parser/reports/{report_id}/assets` - 获取资产信息
- `GET /api/upload-parser/reports/{report_id}/attack-trees` - 获取攻击树
- `GET /api/upload-parser/reports/{report_id}/tara-results` - 获取TARA分析结果
- `GET /api/upload-parser/reports/{report_id}/full-data` - 获取完整报告数据

### JSON解析
- `POST /api/upload-parser/reports/{report_id}/parse-json` - 解析JSON并存储
- `POST /api/upload-parser/upload-complete` - 完整上传(JSON+图片)

## 部署方式

### 使用 Docker Compose

```bash
cd backend
docker-compose up -d
```

这将启动以下服务:
- MySQL (端口 3306)
- MinIO (端口 9000/9001)
- 上传解析服务 (端口 8001)
- 报告生成服务 (端口 8000)

### 本地开发

1. 安装依赖:
```bash
pip install -r requirements-upload-parser.txt
```

2. 配置环境变量:
```bash
cp .env.example .env
# 编辑 .env 文件
```

3. 启动服务:
```bash
python -m upload_parser.app
```

## 使用示例

### 1. 创建报告并上传JSON

```python
import httpx

# 创建报告
response = httpx.post("http://localhost:8001/api/upload-parser/reports", 
                      data={"name": "测试报告"})
report_id = response.json()["report_id"]

# 上传JSON数据
with open("data.json", "rb") as f:
    response = httpx.post(
        f"http://localhost:8001/api/upload-parser/reports/{report_id}/parse-json",
        files={"json_file": f}
    )
```

### 2. 上传图片

```python
with open("image.png", "rb") as f:
    response = httpx.post(
        f"http://localhost:8001/api/upload-parser/reports/{report_id}/images",
        files={"file": f},
        data={"image_type": "system_architecture"}
    )
image_id = response.json()["image_id"]
```

### 3. 获取完整数据并生成报告

```python
# 获取数据
response = httpx.get(
    f"http://localhost:8001/api/upload-parser/reports/{report_id}/full-data"
)
full_data = response.json()

# 调用报告生成
response = httpx.post(
    f"http://localhost:8000/api/reports/generate-by-id/{report_id}"
)
```

## 配置说明

### MinIO配置
| 变量 | 默认值 | 说明 |
|------|--------|------|
| MINIO_ENDPOINT | localhost:9000 | MinIO服务地址 |
| MINIO_ACCESS_KEY | minioadmin | 访问密钥 |
| MINIO_SECRET_KEY | minioadmin | 秘密密钥 |
| MINIO_BUCKET | tara-images | 存储桶名称 |
| MINIO_SECURE | false | 是否使用HTTPS |

### MySQL配置
| 变量 | 默认值 | 说明 |
|------|--------|------|
| MYSQL_HOST | localhost | 数据库主机 |
| MYSQL_PORT | 3306 | 数据库端口 |
| MYSQL_USER | tara_user | 用户名 |
| MYSQL_PASSWORD | tara_password | 密码 |
| MYSQL_DATABASE | tara_db | 数据库名 |

## 注意事项

1. 确保MySQL和MinIO服务正常运行
2. 图片文件大小限制为10MB
3. 支持的图片格式: PNG, JPG, JPEG, GIF, BMP, SVG, WEBP
4. 删除报告会级联删除所有关联数据和MinIO中的图片
