"""
初始化模型目录到数据库

使用方法:
    python scripts/init_model_catalog.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import db_manager
from app.services.config_service import ConfigService


async def main():
    """初始化模型目录"""
    print("=" * 60)
    print("初始化模型目录到数据库")
    print("=" * 60)
    print()

    try:
        # 初始化数据库连接
        print("🔌 正在连接数据库...")
        await db_manager.init_mongodb()
        print("✅ 数据库连接成功")
        print()

        # 创建 ConfigService 实例并传入 db_manager
        config_service = ConfigService(db_manager=db_manager)

        # 初始化默认模型目录
        print("📦 正在初始化默认模型目录...")
        success = await config_service.init_default_model_catalog()
        
        if success:
            print()
            print("✅ 模型目录初始化成功！")
            print()
            
            # 显示已初始化的目录
            catalogs = await config_service.get_model_catalog()
            print(f"📊 已初始化 {len(catalogs)} 个厂家的模型目录：")
            print()
            
            for catalog in catalogs:
                print(f"  🏢 {catalog.provider_name} ({catalog.provider})")
                print(f"     模型数量: {len(catalog.models)}")
                print(f"     模型列表:")
                for model in catalog.models[:5]:  # 只显示前5个
                    print(f"       - {model.display_name}")
                if len(catalog.models) > 5:
                    print(f"       ... 还有 {len(catalog.models) - 5} 个模型")
                print()
            
            print("=" * 60)
            print("✨ 完成！现在您可以在前端界面管理模型目录了")
            print("=" * 60)
        else:
            print("❌ 模型目录初始化失败")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 关闭数据库连接
        try:
            await db_manager.close()
            print()
            print("🔌 数据库连接已关闭")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())

