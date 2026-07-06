#!/usr/bin/env python3
"""
测试 unified_config 获取的模型配置
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.unified_config import unified_config

def main():
    """主函数"""
    print("=" * 60)
    print("📊 测试 unified_config 模型配置")
    print("=" * 60)
    
    try:
        # 获取系统设置
        settings = unified_config.get_system_settings()
        
        print(f"\n系统设置中的模型相关配置:")
        print(f"  default_model: {settings.get('default_model')}")
        print(f"  quick_analysis_model: {settings.get('quick_analysis_model')}")
        print(f"  deep_analysis_model: {settings.get('deep_analysis_model')}")
        
        print(f"\n通过 unified_config 方法获取:")
        print(f"  get_default_model(): {unified_config.get_default_model()}")
        print(f"  get_quick_analysis_model(): {unified_config.get_quick_analysis_model()}")
        print(f"  get_deep_analysis_model(): {unified_config.get_deep_analysis_model()}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

