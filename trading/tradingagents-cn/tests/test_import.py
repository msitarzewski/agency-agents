#!/usr/bin/env python3
"""
测试模块导入
"""

try:
    print("🔄 测试基础模块导入...")
    
    # 测试基础模块
    from webapi.core.config import settings
    print("✅ 配置模块导入成功")
    
    from webapi.models.user import User
    print("✅ 用户模型导入成功")
    
    from webapi.services.analysis_service import get_analysis_service
    print("✅ 分析服务导入成功")
    
    print("🎉 所有模块导入成功！")
    
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
