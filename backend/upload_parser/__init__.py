"""
TARA报告上传解析模块

提供以下功能:
- 文件上传解析
- 图片存储(MinIO)
- 数据持久化(MySQL)
- API接口

使用方法:
    from upload_parser import app, router
    
    # 独立运行
    python -m upload_parser.app
    
    # 集成到主应用
    from upload_parser.api import router
    main_app.include_router(router)
"""
from .app import app, create_app
from .api import router, ReportParserService
from .config import settings

__version__ = "1.0.0"

__all__ = [
    "app",
    "create_app",
    "router",
    "ReportParserService",
    "settings"
]
