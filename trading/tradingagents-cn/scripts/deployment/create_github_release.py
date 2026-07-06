#!/usr/bin/env python3
"""
创建GitHub Release的脚本
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')


def run_command(command, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def create_release_notes():
    """创建发布说明"""
    release_notes = """
## 🌐 Web管理界面和Google AI支持

TradingAgents-CN v0.1.2 带来了重大更新，新增了完整的Web管理界面和Google AI模型支持！

### ✨ 主要新功能

#### 🌐 Streamlit Web管理界面
- 🎯 完整的Web股票分析平台
- 📊 直观的用户界面和实时进度显示
- 🤖 支持多种LLM提供商选择（阿里百炼/Google AI）
- 📈 可视化的分析结果展示
- 📱 响应式设计，支持移动端访问

#### 🤖 Google AI模型集成
- 🧠 完整的Google Gemini模型支持
- 🔧 支持gemini-2.0-flash、gemini-1.5-pro等模型
- 🌍 智能混合嵌入服务（Google AI推理 + 阿里百炼嵌入）
- 💾 完美的中文分析能力和稳定的LangChain集成

#### 🔧 多LLM提供商支持
- 🔄 Web界面支持LLM提供商无缝切换
- ⚙️ 自动配置最优嵌入服务
- 🎛️ 统一的配置管理界面

### 🔧 改进优化

- 📊 新增分析配置信息显示
- 🗂️ 项目结构优化（tests/docs/web目录规范化）
- 🔑 多种API服务配置支持
- 🧪 完整的测试体系（25+个测试文件）
- 📚 完整的使用文档和配置指南

### 🚀 快速开始

#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 配置API密钥
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，添加您的API密钥
# DASHSCOPE_API_KEY=your_dashscope_key  # 阿里百炼（推荐）
# GOOGLE_API_KEY=your_google_key        # Google AI（可选）
```

#### 3. 启动Web界面
```bash
# 启动Web管理界面
python -m streamlit run web/app.py

# 或使用快捷脚本
start_web.bat  # Windows
```

#### 4. 使用CLI工具
```bash
# 使用阿里百炼模型
python cli/main.py --stock AAPL --analysts market fundamentals

# 使用Google AI模型
python cli/main.py --llm-provider google --model gemini-2.0-flash --stock TSLA
```

### 📚 文档和支持

- 📖 [完整文档](./docs/)
- 🌐 [Web界面指南](./web/README.md)
- 🤖 [Google AI配置指南](./docs/configuration/google-ai-setup.md)
- 🧪 [测试指南](./tests/README.md)
- 💡 [示例代码](./examples/)

### 🎯 推荐配置

**最佳性能组合**：
- **LLM提供商**: Google AI
- **推荐模型**: gemini-2.0-flash
- **嵌入服务**: 阿里百炼（自动配置）
- **分析师**: 市场技术 + 基本面分析师

### 🙏 致谢

感谢 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 原始项目的开发者们，为金融AI领域提供了优秀的开源框架。

### 📄 许可证

本项目遵循 Apache 2.0 许可证。

---

**🚀 立即体验**: `python -m streamlit run web/app.py`
"""
    return release_notes.strip()

def show_release_info():
    """显示发布信息"""
    logger.info(f"🎉 TradingAgents-CN v0.1.2 已成功发布到GitHub！")
    logger.info(f"=")
    
    logger.info(f"\n📋 发布内容:")
    logger.info(f"  🌐 完整的Web管理界面")
    logger.info(f"  🤖 Google AI模型集成")
    logger.info(f"  🔧 多LLM提供商支持")
    logger.info(f"  🧪 完整的测试体系")
    logger.info(f"  📚 详细的使用文档")
    
    logger.info(f"\n🔗 GitHub链接:")
    logger.info(f"  📦 Release: https://github.com/hsliuping/TradingAgents-CN/releases/tag/cn-v0.1.2")
    logger.info(f"  📝 代码: https://github.com/hsliuping/TradingAgents-CN")
    
    logger.info(f"\n🚀 快速开始:")
    logger.info(f"  1. git clone https://github.com/hsliuping/TradingAgents-CN.git")
    logger.info(f"  2. cd TradingAgents-CN")
    logger.info(f"  3. pip install -r requirements.txt")
    logger.info(f"  4. python -m streamlit run web/app.py")
    
    logger.info(f"\n💡 主要特性:")
    logger.info(f"  ✅ Web界面股票分析")
    logger.info(f"  ✅ Google AI + 阿里百炼双模型支持")
    logger.info(f"  ✅ 实时分析进度显示")
    logger.info(f"  ✅ 多分析师协作决策")
    logger.info(f"  ✅ 完整的中文支持")

def main():
    """主函数"""
    logger.info(f"🚀 创建GitHub Release")
    logger.info(f"=")
    
    # 检查是否在正确的分支
    success, stdout, stderr = run_command("git branch --show-current")
    if not success or stdout.strip() != "main":
        logger.error(f"❌ 请确保在main分支上，当前分支: {stdout.strip()}")
        return False
    
    # 检查是否有未推送的提交
    success, stdout, stderr = run_command("git status --porcelain")
    if not success:
        logger.error(f"❌ Git状态检查失败: {stderr}")
        return False
    
    if stdout.strip():
        logger.error(f"❌ 发现未提交的更改，请先提交所有更改")
        return False
    
    logger.info(f"✅ Git状态检查通过")
    
    # 检查标签是否存在
    success, stdout, stderr = run_command("git tag -l cn-v0.1.2")
    if not success or "cn-v0.1.2" not in stdout:
        logger.error(f"❌ 标签 cn-v0.1.2 不存在")
        return False
    
    logger.info(f"✅ 版本标签检查通过")
    
    # 生成发布说明
    release_notes = create_release_notes()
    
    # 保存发布说明到文件
    with open("RELEASE_NOTES_v0.1.2.md", "w", encoding="utf-8") as f:
        f.write(release_notes)
    
    logger.info(f"✅ 发布说明已生成")
    
    # 显示GitHub Release创建指南
    logger.info(f"\n📋 GitHub Release创建指南:")
    logger.info(f"=")
    logger.info(f"1. 访问: https://github.com/hsliuping/TradingAgents-CN/releases/new")
    logger.info(f"2. 选择标签: cn-v0.1.2")
    logger.info(f"3. 发布标题: TradingAgents-CN v0.1.2 - Web管理界面和Google AI支持")
    logger.info(f"4. 复制 RELEASE_NOTES_v0.1.2.md 的内容到描述框")
    logger.info(f"5. 勾选 'Set as the latest release'")
    logger.info(f"6. 点击 'Publish release'")
    
    # 显示发布信息
    show_release_info()
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info(f"\n🎉 GitHub Release准备完成！")
        logger.info(f"请按照上述指南在GitHub上创建Release")
    else:
        logger.error(f"\n❌ GitHub Release准备失败")
        sys.exit(1)
