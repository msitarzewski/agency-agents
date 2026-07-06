# TradingAgents-CN 测试目录

这个目录包含了TradingAgents-CN项目的所有测试文件，用于验证功能正确性、API集成和模型测试。

## 目录结构

```
tests/
├── README.md                           # 本文件
├── __init__.py                         # Python包初始化
├── integration/                        # 集成测试
│   ├── __init__.py
│   └── test_dashscope_integration.py   # 阿里百炼集成测试
├── test_*.py                          # 各种功能测试
└── debug_*.py                         # 调试和诊断工具
```

## 测试分类

### 🔧 API和集成测试
- `test_all_apis.py` - 所有API密钥测试
- `test_correct_apis.py` - Google和Reddit API测试
- `test_analysis_with_apis.py` - API集成分析测试
- `test_toolkit_tools.py` - 工具包测试
- `integration/test_dashscope_integration.py` - 阿里百炼集成测试

### 📊 数据源测试
- `fast_tdx_test.py` - Tushare数据接口快速连接测试
- `test_tdx_integration.py` - Tushare数据接口完整集成测试

### ⚡ 性能测试
- `test_redis_performance.py` - Redis性能基准测试
- `quick_redis_test.py` - Redis快速连接测试

### 🤖 AI模型测试
- `test_chinese_output.py` - 中文输出测试
- `test_gemini*.py` - Google Gemini模型系列测试
- `test_embedding_models.py` - 嵌入模型测试
- `test_google_memory_fix.py` - Google AI内存功能测试

### 🌐 Web界面测试
- `test_web_interface.py` - Web界面功能测试

### 🔍 调试和诊断工具
- `debug_imports.py` - 导入问题诊断
- `diagnose_gemini_25.py` - Gemini 2.5模型诊断
- `check_gemini_models.py` - Gemini模型可用性检查

### 🧪 功能测试
- `test_analysis.py` - 基础分析功能测试
- `test_format_fix.py` - 格式化修复测试
- `test_progress.py` - 进度跟踪测试

## 运行测试

### 运行所有测试
```bash
# 从项目根目录运行
python -m pytest tests/

# 或者直接运行特定测试
cd tests
python test_chinese_output.py
```

### 运行特定类别的测试
```bash
# API测试
python tests/test_all_apis.py

# Gemini模型测试
python tests/test_gemini_correct.py

# Web界面测试
python tests/test_web_interface.py

# 阿里百炼集成测试
python tests/integration/test_dashscope_integration.py

# Tushare数据接口测试
python tests/fast_tdx_test.py
python tests/test_tdx_integration.py

# Redis性能测试
python tests/quick_redis_test.py
python tests/test_redis_performance.py
```

### 诊断工具
```bash
# 诊断Gemini模型问题
python tests/diagnose_gemini_25.py

# 检查导入问题
python tests/debug_imports.py

# 检查所有可用的Gemini模型
python tests/check_gemini_models.py
```

## 测试环境要求

### 必需的环境变量
在运行测试前，请确保在`.env`文件中配置了以下API密钥：

```env
# 阿里百炼API（必需）
DASHSCOPE_API_KEY=your_dashscope_key

# Google AI API（可选，用于Gemini测试）
GOOGLE_API_KEY=your_google_key

# 金融数据API（可选）
FINNHUB_API_KEY=your_finnhub_key

# Reddit API（可选）
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
REDDIT_USER_AGENT=your_user_agent
```

### Python依赖
```bash
pip install -r requirements.txt
```

### 测试结果解读
- **所有测试通过**：功能完全正常，可以使用完整功能
- **部分测试通过**：基本功能正常，可能需要检查配置
- **大部分测试失败**：存在问题，需要排查API密钥和环境配置

## 贡献指南

添加新测试时，请遵循以下规范：

1. **测试文件命名**: `test_功能名称.py`
2. **调试工具命名**: `debug_问题描述.py` 或 `diagnose_问题描述.py`
3. **测试函数命名**: `test_具体功能()`
4. **文档**: 在函数开头添加清晰的文档字符串
5. **分类**: 根据功能将测试放在适当的类别中

### 测试模板

```python
#!/usr/bin/env python3
"""
新功能测试
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env", override=True)

def test_new_feature():
    """测试新功能"""
    try:
        print("🧪 测试新功能")
        print("=" * 50)

        # 测试代码

        print("✅ 测试成功")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 新功能测试")
    print("=" * 60)

    success = test_new_feature()

    if success:
        print("🎉 所有测试通过！")
    else:
        print("❌ 测试失败")

if __name__ == "__main__":
    main()
```

## 最近更新

- ✅ 添加了Google Gemini模型系列测试
- ✅ 添加了Web界面Google模型选择测试
- ✅ 添加了API集成测试（Google、Reddit）
- ✅ 添加了中文输出功能测试
- ✅ 添加了内存系统和嵌入模型测试
- ✅ 整理了所有测试文件到tests目录
- ✅ 添加了调试和诊断工具

## 测试最佳实践

1. **测试隔离**：每个测试应该独立运行
2. **清晰命名**：测试函数名应该清楚描述测试内容
3. **错误处理**：测试应该能够处理各种错误情况
4. **文档化**：为复杂的测试添加详细注释
5. **快速反馈**：测试应该尽快给出结果

## 故障排除

### 常见问题
1. **API密钥问题** - 检查.env文件配置
2. **网络连接问题** - 确认网络和防火墙设置
3. **依赖包问题** - 确保所有依赖已安装
4. **模型兼容性** - 检查模型名称和版本

### 调试技巧
1. 启用详细输出查看错误信息
2. 单独运行测试函数定位问题
3. 使用诊断工具检查配置
4. 查看Web应用日志了解运行状态

## 许可证

本项目遵循Apache 2.0许可证。


## 新增的测试文件

### 集成测试
- `quick_test.py` - 快速集成测试，验证基本功能
- `test_smart_system.py` - 智能系统完整测试
- `demo_fallback_system.py` - 降级系统演示和测试

### 运行方法
```bash
# 快速测试
python tests/quick_test.py

# 智能系统测试
python tests/test_smart_system.py

# 降级系统演示
python tests/demo_fallback_system.py
```
