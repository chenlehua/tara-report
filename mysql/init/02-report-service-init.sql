-- ================================================================
-- Report Service Database Initialization Script
-- ================================================================
-- 报告服务专用表结构
-- 用于报告列表、报告预览、报告生成管理等功能
-- 与 data-service 的数据表分离，独立管理报告中心的数据
-- ================================================================

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ================================================================
-- 1. 报告主表 - 报告注册与基本信息
-- ================================================================
-- 用于报告列表展示和基本信息管理
CREATE TABLE IF NOT EXISTS rs_reports (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID，格式：RPT-YYYYMMDD-XXXXXXXX',
    project_name VARCHAR(200) COMMENT '项目名称',
    report_title VARCHAR(200) COMMENT '报告标题',
    report_title_en VARCHAR(200) COMMENT '报告英文标题',
    data_level VARCHAR(50) COMMENT '数据等级（秘密/内部/公开）',
    document_number VARCHAR(100) COMMENT '文档编号',
    version VARCHAR(50) COMMENT '版本号',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '报告状态: pending-待处理, processing-处理中, completed-已完成, failed-失败',
    source_type VARCHAR(20) DEFAULT 'upload' COMMENT '来源类型: upload-上传, sync-同步',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_report_id (report_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_project_name (project_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告服务-报告主表';


-- ================================================================
-- 2. 报告封面信息表
-- ================================================================
-- 存储报告封面的详细信息，用于预览展示
CREATE TABLE IF NOT EXISTS rs_report_covers (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    
    report_title VARCHAR(200) COMMENT '报告标题',
    report_title_en VARCHAR(200) COMMENT '报告英文标题',
    project_name VARCHAR(200) COMMENT '项目名称',
    data_level VARCHAR(50) COMMENT '数据等级',
    document_number VARCHAR(100) COMMENT '文档编号',
    version VARCHAR(50) COMMENT '版本',
    author_date VARCHAR(100) COMMENT '编制日期',
    review_date VARCHAR(100) COMMENT '审核日期',
    sign_date VARCHAR(100) COMMENT '会签日期',
    approve_date VARCHAR(100) COMMENT '批准日期',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_report_id (report_id),
    CONSTRAINT fk_rs_cover_report FOREIGN KEY (report_id) REFERENCES rs_reports(report_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告服务-报告封面信息表';


-- ================================================================
-- 3. 报告定义信息表
-- ================================================================
-- 存储报告相关定义，包括功能描述、架构图路径、假设条件和术语表
CREATE TABLE IF NOT EXISTS rs_report_definitions (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    
    title VARCHAR(200) COMMENT '定义标题/系统名称',
    functional_description TEXT COMMENT '功能描述',
    item_boundary_image VARCHAR(500) COMMENT '项目边界图MinIO路径',
    system_architecture_image VARCHAR(500) COMMENT '系统架构图MinIO路径',
    software_architecture_image VARCHAR(500) COMMENT '软件架构图MinIO路径',
    dataflow_image VARCHAR(500) COMMENT '数据流图MinIO路径',
    assumptions JSON COMMENT '假设条件JSON数组',
    terminology JSON COMMENT '术语表JSON数组',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_report_id (report_id),
    CONSTRAINT fk_rs_definitions_report FOREIGN KEY (report_id) REFERENCES rs_reports(report_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告服务-报告定义信息表';


-- ================================================================
-- 4. 报告资产表
-- ================================================================
-- 存储报告中的资产列表及其安全属性
CREATE TABLE IF NOT EXISTS rs_report_assets (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    
    asset_id VARCHAR(50) COMMENT '资产ID',
    name VARCHAR(200) COMMENT '资产名称',
    category VARCHAR(100) COMMENT '资产分类（数据资产/硬件资产/软件资产）',
    remarks TEXT COMMENT '备注说明',
    authenticity BOOLEAN DEFAULT FALSE COMMENT '真实性',
    integrity BOOLEAN DEFAULT FALSE COMMENT '完整性',
    non_repudiation BOOLEAN DEFAULT FALSE COMMENT '不可否认性',
    confidentiality BOOLEAN DEFAULT FALSE COMMENT '机密性',
    availability BOOLEAN DEFAULT FALSE COMMENT '可用性',
    authorization BOOLEAN DEFAULT FALSE COMMENT '授权性',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_report_id (report_id),
    INDEX idx_asset_id (asset_id),
    CONSTRAINT fk_rs_assets_report FOREIGN KEY (report_id) REFERENCES rs_reports(report_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告服务-报告资产表';


-- ================================================================
-- 5. 报告攻击树表
-- ================================================================
-- 存储报告中的攻击树信息
CREATE TABLE IF NOT EXISTS rs_report_attack_trees (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    
    asset_id VARCHAR(50) COMMENT '关联资产ID',
    asset_name VARCHAR(200) COMMENT '资产名称',
    title VARCHAR(300) COMMENT '攻击树标题',
    image VARCHAR(500) COMMENT '攻击树图MinIO路径',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_report_id (report_id),
    INDEX idx_sort_order (sort_order),
    CONSTRAINT fk_rs_attack_trees_report FOREIGN KEY (report_id) REFERENCES rs_reports(report_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告服务-报告攻击树表';


-- ================================================================
-- 6. 报告TARA分析结果表
-- ================================================================
-- 存储TARA威胁分析和风险评估结果
CREATE TABLE IF NOT EXISTS rs_report_tara_results (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    
    -- 资产识别
    asset_id VARCHAR(50) COMMENT '资产ID',
    asset_name VARCHAR(200) COMMENT '资产名称',
    subdomain1 VARCHAR(100) COMMENT '子领域一（系统级）',
    subdomain2 VARCHAR(100) COMMENT '子领域二（模块级）',
    subdomain3 VARCHAR(100) COMMENT '子领域三（组件级）',
    category VARCHAR(100) COMMENT '资产分类',
    
    -- 威胁场景
    security_attribute VARCHAR(100) COMMENT '安全属性（机密性/完整性/可用性等）',
    stride_model VARCHAR(50) COMMENT 'STRIDE威胁模型分类',
    threat_scenario TEXT COMMENT '潜在威胁场景描述',
    attack_path TEXT COMMENT '攻击路径描述',
    wp29_mapping VARCHAR(200) COMMENT 'WP.29法规条款映射',
    
    -- 威胁分析（CVSS相关）
    attack_vector VARCHAR(50) COMMENT '攻击向量（网络/相邻网络/本地/物理）',
    attack_complexity VARCHAR(50) COMMENT '攻击复杂度（低/高）',
    privileges_required VARCHAR(50) COMMENT '所需权限（无/低/高）',
    user_interaction VARCHAR(50) COMMENT '用户交互（无/需要）',
    
    -- 影响分析
    safety_impact VARCHAR(50) COMMENT '安全影响（无/低/中/高/严重）',
    financial_impact VARCHAR(50) COMMENT '财务影响（无/低/中/高/严重）',
    operational_impact VARCHAR(50) COMMENT '运营影响（无/低/中/高/严重）',
    privacy_impact VARCHAR(50) COMMENT '隐私影响（无/低/中/高/严重）',
    
    -- 安全需求
    security_goal TEXT COMMENT '安全目标',
    security_requirement TEXT COMMENT '安全需求/对策',
    
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_report_id (report_id),
    INDEX idx_asset_id (asset_id),
    INDEX idx_sort_order (sort_order),
    INDEX idx_operational_impact (operational_impact),
    CONSTRAINT fk_rs_tara_results_report FOREIGN KEY (report_id) REFERENCES rs_reports(report_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告服务-TARA分析结果表';


-- ================================================================
-- 7. 报告图片信息表
-- ================================================================
-- 存储报告关联的图片信息
CREATE TABLE IF NOT EXISTS rs_report_images (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    
    image_id VARCHAR(50) NOT NULL COMMENT '图片ID，格式：IMG-XXXXXXXXXXXX',
    image_type VARCHAR(50) COMMENT '图片类型（item_boundary/system_architecture/software_architecture/dataflow/attack_tree_N）',
    original_name VARCHAR(255) COMMENT '原始文件名',
    minio_path VARCHAR(500) COMMENT 'MinIO存储路径',
    minio_bucket VARCHAR(100) COMMENT 'MinIO桶名',
    file_size INT COMMENT '文件大小（字节）',
    content_type VARCHAR(100) COMMENT 'MIME类型',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    UNIQUE KEY uk_image_id (image_id),
    INDEX idx_report_id (report_id),
    INDEX idx_image_type (image_type),
    CONSTRAINT fk_rs_images_report FOREIGN KEY (report_id) REFERENCES rs_reports(report_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告服务-报告图片信息表';


-- ================================================================
-- 8. 报告统计信息表
-- ================================================================
-- 缓存报告的统计信息，用于快速展示报告列表
CREATE TABLE IF NOT EXISTS rs_report_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    
    assets_count INT DEFAULT 0 COMMENT '资产数量',
    threats_count INT DEFAULT 0 COMMENT '威胁数量',
    high_risk_count INT DEFAULT 0 COMMENT '高风险数量',
    measures_count INT DEFAULT 0 COMMENT '安全措施数量',
    attack_trees_count INT DEFAULT 0 COMMENT '攻击树数量',
    images_count INT DEFAULT 0 COMMENT '图片数量',
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_report_id (report_id),
    CONSTRAINT fk_rs_statistics_report FOREIGN KEY (report_id) REFERENCES rs_reports(report_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告服务-报告统计信息表';


-- ================================================================
-- 9. 生成报告文件表
-- ================================================================
-- 存储已生成的报告文件信息（Excel/PDF）
CREATE TABLE IF NOT EXISTS rs_generated_files (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    
    file_type VARCHAR(20) NOT NULL COMMENT '文件类型: xlsx, pdf',
    file_name VARCHAR(255) COMMENT '文件名',
    minio_path VARCHAR(500) COMMENT 'MinIO存储路径',
    minio_bucket VARCHAR(100) COMMENT 'MinIO桶名',
    file_size INT COMMENT '文件大小（字节）',
    
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
    
    UNIQUE KEY uk_report_type (report_id, file_type),
    INDEX idx_report_id (report_id),
    CONSTRAINT fk_rs_generated_files_report FOREIGN KEY (report_id) REFERENCES rs_reports(report_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告服务-生成报告文件表';


-- ================================================================
-- 10. 报告生成历史表
-- ================================================================
-- 记录报告生成的历史记录，用于审计和追踪
CREATE TABLE IF NOT EXISTS rs_generation_history (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    report_id VARCHAR(50) NOT NULL COMMENT '报告ID',
    
    file_type VARCHAR(20) NOT NULL COMMENT '文件类型: xlsx, pdf',
    status VARCHAR(20) NOT NULL COMMENT '生成状态: pending, processing, success, failed',
    error_message TEXT COMMENT '错误信息（如果失败）',
    file_size INT COMMENT '文件大小（字节）',
    generation_time_ms INT COMMENT '生成耗时（毫秒）',
    
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    
    INDEX idx_report_id (report_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_rs_history_report FOREIGN KEY (report_id) REFERENCES rs_reports(report_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告服务-报告生成历史表';


-- ================================================================
-- 初始化完成提示
-- ================================================================
SELECT 'Report Service database tables initialized successfully!' AS message;
SELECT 'Tables created:' AS info;
SELECT '  - rs_reports (报告主表)' AS table_info
UNION ALL SELECT '  - rs_report_covers (报告封面信息表)'
UNION ALL SELECT '  - rs_report_definitions (报告定义信息表)'
UNION ALL SELECT '  - rs_report_assets (报告资产表)'
UNION ALL SELECT '  - rs_report_attack_trees (报告攻击树表)'
UNION ALL SELECT '  - rs_report_tara_results (TARA分析结果表)'
UNION ALL SELECT '  - rs_report_images (报告图片信息表)'
UNION ALL SELECT '  - rs_report_statistics (报告统计信息表)'
UNION ALL SELECT '  - rs_generated_files (生成报告文件表)'
UNION ALL SELECT '  - rs_generation_history (报告生成历史表)';
