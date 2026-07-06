"""
测试脚本：验证模型配置参数是否正确传递到分析引擎

这个脚本会：
1. 模拟从数据库读取模型配置
2. 创建分析配置
3. 验证配置中是否包含正确的参数
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.simple_analysis_service import create_analysis_config


def test_model_config_params():
    """测试模型配置参数是否正确传递"""
    
    print("=" * 80)
    print("测试：模型配置参数传递")
    print("=" * 80)
    
    # 模拟从数据库读取的模型配置
    quick_model_config = {
        "max_tokens": 6000,
        "temperature": 0.8,
        "timeout": 200,
        "retry_times": 5,
        "api_base": "https://dashscope.aliyuncs.com/api/v1"
    }
    
    deep_model_config = {
        "max_tokens": 8000,
        "temperature": 0.5,
        "timeout": 300,
        "retry_times": 3,
        "api_base": "https://dashscope.aliyuncs.com/api/v1"
    }
    
    print("\n📋 输入参数：")
    print(f"  快速模型配置: {quick_model_config}")
    print(f"  深度模型配置: {deep_model_config}")
    
    # 创建分析配置
    config = create_analysis_config(
        research_depth="标准",
        selected_analysts=["market", "fundamentals"],
        quick_model="qwen-turbo",
        deep_model="qwen-max",
        llm_provider="dashscope",
        market_type="A股",
        quick_model_config=quick_model_config,
        deep_model_config=deep_model_config
    )
    
    print("\n✅ 配置创建成功！")
    print("\n📊 验证结果：")
    
    # 验证配置中是否包含模型参数
    if "quick_model_config" in config:
        print(f"  ✅ quick_model_config 存在")
        print(f"     - max_tokens: {config['quick_model_config']['max_tokens']}")
        print(f"     - temperature: {config['quick_model_config']['temperature']}")
        print(f"     - timeout: {config['quick_model_config']['timeout']}")
        print(f"     - retry_times: {config['quick_model_config']['retry_times']}")
    else:
        print(f"  ❌ quick_model_config 不存在")
    
    if "deep_model_config" in config:
        print(f"  ✅ deep_model_config 存在")
        print(f"     - max_tokens: {config['deep_model_config']['max_tokens']}")
        print(f"     - temperature: {config['deep_model_config']['temperature']}")
        print(f"     - timeout: {config['deep_model_config']['timeout']}")
        print(f"     - retry_times: {config['deep_model_config']['retry_times']}")
    else:
        print(f"  ❌ deep_model_config 不存在")
    
    # 验证其他配置
    print(f"\n📋 其他配置：")
    print(f"  - llm_provider: {config.get('llm_provider')}")
    print(f"  - quick_think_llm: {config.get('quick_think_llm')}")
    print(f"  - deep_think_llm: {config.get('deep_think_llm')}")
    print(f"  - research_depth: {config.get('research_depth')}")
    print(f"  - max_debate_rounds: {config.get('max_debate_rounds')}")
    print(f"  - max_risk_discuss_rounds: {config.get('max_risk_discuss_rounds')}")
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_model_config_params()

