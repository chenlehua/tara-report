-- TARA Database Initialization Script
-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 确保数据库使用正确的字符集
ALTER DATABASE tara_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 授权
GRANT ALL PRIVILEGES ON tara_db.* TO 'tara'@'%';
FLUSH PRIVILEGES;

-- 初始化完成
SELECT 'TARA Database initialized successfully!' AS message;
