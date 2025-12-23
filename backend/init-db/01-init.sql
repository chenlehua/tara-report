-- TARA报告系统数据库初始化脚本
-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建数据库(如果不存在)
CREATE DATABASE IF NOT EXISTS tara_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE tara_db;

-- ==================== 报告主表 ====================
CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(50) PRIMARY KEY COMMENT '报告ID',
    name VARCHAR(255) COMMENT '报告名称',
    status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING' COMMENT '报告状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_report_status (status),
    INDEX idx_report_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告主表';

-- ==================== 图片表 ====================
CREATE TABLE IF NOT EXISTS images (
    id VARCHAR(50) PRIMARY KEY COMMENT '图片ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    image_type ENUM('item_boundary', 'system_architecture', 'software_architecture', 'dataflow', 'attack_tree', 'other') NOT NULL COMMENT '图片类型',
    original_name VARCHAR(255) COMMENT '原始文件名',
    minio_path VARCHAR(500) NOT NULL COMMENT 'MinIO存储路径',
    minio_bucket VARCHAR(100) NOT NULL COMMENT 'MinIO桶名',
    file_size INT COMMENT '文件大小(字节)',
    content_type VARCHAR(100) COMMENT '内容类型',
    attack_tree_id VARCHAR(50) COMMENT '攻击树ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    INDEX idx_image_report_id (report_id),
    INDEX idx_image_type (image_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图片表';

-- ==================== 封面表 ====================
CREATE TABLE IF NOT EXISTS covers (
    id VARCHAR(50) PRIMARY KEY COMMENT '封面ID',
    report_id VARCHAR(50) NOT NULL UNIQUE COMMENT '报告ID',
    report_title VARCHAR(255) DEFAULT '威胁分析和风险评估报告' COMMENT '报告标题',
    report_title_en VARCHAR(255) DEFAULT 'Threat Analysis And Risk Assessment Report' COMMENT '报告英文标题',
    project_name VARCHAR(255) COMMENT '项目名称',
    data_level VARCHAR(50) DEFAULT '秘密' COMMENT '数据等级',
    document_number VARCHAR(100) COMMENT '文档编号',
    version VARCHAR(50) DEFAULT 'V1.0' COMMENT '版本',
    author_date VARCHAR(100) COMMENT '编制/日期',
    review_date VARCHAR(100) COMMENT '审核/日期',
    sign_date VARCHAR(100) COMMENT '会签/日期',
    approve_date VARCHAR(100) COMMENT '批准/日期',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='封面表';

-- ==================== 项目定义表 ====================
CREATE TABLE IF NOT EXISTS definitions (
    id VARCHAR(50) PRIMARY KEY COMMENT '定义ID',
    report_id VARCHAR(50) NOT NULL UNIQUE COMMENT '报告ID',
    title VARCHAR(255) DEFAULT 'TARA分析报告 - 相关定义' COMMENT '标题',
    functional_description LONGTEXT COMMENT '功能描述',
    item_boundary_image_id VARCHAR(50) COMMENT '项目边界图片ID',
    system_architecture_image_id VARCHAR(50) COMMENT '系统架构图片ID',
    software_architecture_image_id VARCHAR(50) COMMENT '软件架构图片ID',
    assumptions JSON COMMENT '假设列表 [{id, description}]',
    terminology JSON COMMENT '术语表 [{abbreviation, english, chinese}]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目定义表';

-- ==================== 资产数据流配置表 ====================
CREATE TABLE IF NOT EXISTS asset_dataflows (
    id VARCHAR(50) PRIMARY KEY COMMENT '配置ID',
    report_id VARCHAR(50) NOT NULL UNIQUE COMMENT '报告ID',
    title VARCHAR(255) DEFAULT '资产列表 Asset List' COMMENT '标题',
    dataflow_image_id VARCHAR(50) COMMENT '数据流图片ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='资产数据流配置表';

-- ==================== 资产表 ====================
CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR(50) PRIMARY KEY COMMENT '数据库ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    asset_id VARCHAR(50) NOT NULL COMMENT '资产ID(业务ID)',
    name VARCHAR(255) NOT NULL COMMENT '资产名称',
    category VARCHAR(100) COMMENT '分类',
    remarks TEXT COMMENT '备注',
    authenticity BOOLEAN DEFAULT FALSE COMMENT '真实性',
    integrity BOOLEAN DEFAULT FALSE COMMENT '完整性',
    non_repudiation BOOLEAN DEFAULT FALSE COMMENT '不可抵赖性',
    confidentiality BOOLEAN DEFAULT FALSE COMMENT '机密性',
    availability BOOLEAN DEFAULT FALSE COMMENT '可用性',
    authorization BOOLEAN DEFAULT FALSE COMMENT '权限',
    dataflow_image_id VARCHAR(50) COMMENT '数据流图片ID',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    INDEX idx_asset_report_id (report_id),
    INDEX idx_asset_asset_id (asset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='资产表';

-- ==================== 攻击树表 ====================
CREATE TABLE IF NOT EXISTS attack_trees (
    id VARCHAR(50) PRIMARY KEY COMMENT '攻击树ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    asset_id VARCHAR(50) COMMENT '关联资产ID',
    asset_name VARCHAR(255) COMMENT '资产名称',
    title VARCHAR(255) COMMENT '攻击树标题',
    description TEXT COMMENT '攻击树描述',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    INDEX idx_attack_tree_report_id (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='攻击树表';

-- 添加攻击树外键到图片表
ALTER TABLE images ADD FOREIGN KEY (attack_tree_id) REFERENCES attack_trees(id) ON DELETE SET NULL;

-- ==================== TARA分析结果表 ====================
CREATE TABLE IF NOT EXISTS tara_results (
    id VARCHAR(50) PRIMARY KEY COMMENT '结果ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    asset_id VARCHAR(50) NOT NULL COMMENT '资产ID',
    asset_name VARCHAR(255) NOT NULL COMMENT '资产名称',
    subdomain1 VARCHAR(255) COMMENT '子域1',
    subdomain2 VARCHAR(255) COMMENT '子域2',
    subdomain3 VARCHAR(255) COMMENT '子域3',
    category VARCHAR(100) COMMENT '分类',
    security_attribute VARCHAR(100) COMMENT '安全属性',
    stride_model VARCHAR(100) COMMENT 'STRIDE模型',
    threat_scenario TEXT COMMENT '威胁场景',
    attack_path TEXT COMMENT '攻击路径',
    wp29_mapping VARCHAR(255) COMMENT 'WP29映射',
    attack_vector VARCHAR(50) DEFAULT '本地' COMMENT '攻击向量',
    attack_complexity VARCHAR(50) DEFAULT '低' COMMENT '攻击复杂度',
    privileges_required VARCHAR(50) DEFAULT '低' COMMENT '权限要求',
    user_interaction VARCHAR(50) DEFAULT '不需要' COMMENT '用户交互',
    safety_impact VARCHAR(50) DEFAULT '中等的' COMMENT '安全影响',
    financial_impact VARCHAR(50) DEFAULT '中等的' COMMENT '经济影响',
    operational_impact VARCHAR(50) DEFAULT '中等的' COMMENT '操作影响',
    privacy_impact VARCHAR(50) DEFAULT '可忽略不计的' COMMENT '隐私影响',
    security_requirement TEXT COMMENT '安全需求',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    INDEX idx_tara_result_report_id (report_id),
    INDEX idx_tara_result_asset_id (asset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='TARA分析结果表';

-- 授权
GRANT ALL PRIVILEGES ON tara_db.* TO 'tara_user'@'%';
FLUSH PRIVILEGES;
