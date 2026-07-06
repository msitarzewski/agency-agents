"""
测试启动配置验证器

用于验证配置验证器是否正常工作
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

from app.core.startup_validator import validate_startup_config, ConfigurationError


def main():
    """测试配置验证器"""
    print("🧪 测试启动配置验证器\n")
    
    try:
        result = validate_startup_config()
        
        print("\n✅ 配置验证通过！")
        print(f"   缺少的推荐配置: {len(result.missing_recommended)}")
        print(f"   警告信息: {len(result.warnings)}")
        
        if result.missing_recommended:
            print("\n💡 建议配置以下推荐项以获得更好的功能体验：")
            for config in result.missing_recommended:
                print(f"   • {config.key}: {config.description}")
                if config.help_url:
                    print(f"     获取地址: {config.help_url}")
        
        return 0
        
    except ConfigurationError as e:
        print(f"\n❌ 配置验证失败:\n{e}")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

