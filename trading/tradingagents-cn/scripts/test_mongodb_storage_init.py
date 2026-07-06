#!/usr/bin/env python3
"""
测试 TradingAgents MongoDB 存储初始化
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 初始化日志
from tradingagents.utils.logging_init import init_logging
init_logging()

from tradingagents.config.config_manager import ConfigManager

def main():
    """主函数"""
    print("=" * 60)
    print("📊 测试 TradingAgents MongoDB 存储初始化")
    print("=" * 60)

    try:
        # 创建配置管理器实例
        config_manager = ConfigManager()
        
        # 检查 MongoDB 存储是否已初始化
        if config_manager.mongodb_storage is None:
            print("\n❌ MongoDB 存储未初始化")
            print("\n请检查以下环境变量:")
            print("  • USE_MONGODB_STORAGE=true")
            print("  • MONGODB_CONNECTION_STRING=mongodb://...")
            print("  • MONGODB_DATABASE_NAME=tradingagents")
            return
        
        # 检查连接状态
        if not config_manager.mongodb_storage.is_connected():
            print("\n❌ MongoDB 未连接")
            return
        
        print("\n✅ MongoDB 存储已初始化并连接成功")
        
        # 测试保存一条记录
        print("\n📝 测试保存 token 使用记录...")
        
        from tradingagents.config.config_manager import token_tracker
        
        record = token_tracker.track_usage(
            provider="dashscope",
            model_name="qwen-turbo",
            input_tokens=100,
            output_tokens=50,
            session_id="test_init_001",
            analysis_type="test"
        )
        
        if record:
            print(f"✅ 测试记录创建成功:")
            print(f"  • 供应商: {record.provider}")
            print(f"  • 模型: {record.model_name}")
            print(f"  • 输入 Token: {record.input_tokens}")
            print(f"  • 输出 Token: {record.output_tokens}")
            print(f"  • 成本: ¥{record.cost:.6f}")
            print(f"  • 会话 ID: {record.session_id}")
        else:
            print("❌ 测试记录创建失败")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

