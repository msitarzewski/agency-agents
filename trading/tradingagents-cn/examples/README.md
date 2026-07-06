# TradingAgents 示例程序 - DeepSeek V3 预览版

本目录包含了 TradingAgents 框架的各种示例程序，帮助用户快速上手和理解如何使用不同的LLM提供商。

## ⚠️ 预览版说明

当前为DeepSeek V3集成预览版，重点展示DeepSeek V3的高性价比AI金融分析能力。

## 目录结构

```
examples/
├── README.md                        # 本文件
├── demo_deepseek_analysis.py        # 🆕 DeepSeek V3股票分析演示（推荐）
├── demo_news_filtering.py           # 新闻过滤演示 (v0.1.12新增)
├── simple_analysis_demo.py          # 简单分析演示
├── cli_demo.py                      # CLI命令行演示
├── batch_analysis.py                # 批量股票分析示例
├── custom_analysis_demo.py          # 自定义分析演示
├── config_management_demo.py        # 配置管理演示
├── data_dir_config_demo.py          # 数据目录配置演示
├── my_stock_analysis.py             # 个人股票分析示例
├── stock_list_example.py            # 股票列表示例
├── stock_query_examples.py          # 股票查询示例
├── test_news_timeout.py             # 新闻超时测试
├── token_tracking_demo.py           # Token跟踪演示
├── tushare_demo.py                  # Tushare数据源演示
├── dashscope_examples/              # 阿里百炼大模型示例
│   ├── demo_dashscope.py           # 完整的阿里百炼演示
│   ├── demo_dashscope_chinese.py   # 中文优化版本
│   ├── demo_dashscope_simple.py    # 简化版本（仅LLM测试）
│   └── demo_dashscope_no_memory.py # 禁用记忆功能版本
└── openai/                          # OpenAI 模型示例
    └── demo_openai.py              # OpenAI 演示程序
```

## 🚀 快速开始

### 🆕 使用DeepSeek V3（预览版推荐）

DeepSeek V3是新集成的高性价比大模型，具有以下优势：
- 💰 **超低成本**：相比GPT-4节省90%+费用
- 🇨🇳 **中文优化**：优秀的中文理解和生成能力
- 📊 **专业分析**：适合金融投资分析场景
- 🔧 **完整集成**：支持Token统计和成本跟踪

#### 1. 配置API密钥

```bash
# 获取DeepSeek API密钥
# 1. 访问 https://platform.deepseek.com/
# 2. 注册账号并创建API Key

# 设置环境变量
set DEEPSEEK_API_KEY=sk-your_deepseek_api_key
set FINNHUB_API_KEY=your_finnhub_api_key

# 或编辑项目根目录的 .env 文件
```

#### 2. 运行DeepSeek示例

```bash
# DeepSeek V3股票分析演示（推荐）
python examples/demo_deepseek_analysis.py
```

**示例特点**：
- 🎯 展示DeepSeek V3的基本面分析能力
- 💰 实时显示Token使用量和成本
- 📊 包含真实财务指标和投资建议
- 🇨🇳 完全中文化的分析报告

### 🇨🇳 使用阿里百炼大模型

阿里百炼是国产大模型，具有以下优势：
- 无需翻墙，网络稳定
- 中文理解能力强
- 成本相对较低
- 符合国内合规要求

#### 1. 配置API密钥

```bash
# 设置环境变量
set DASHSCOPE_API_KEY=your_dashscope_api_key
set FINNHUB_API_KEY=your_finnhub_api_key

# 或编辑项目根目录的 .env 文件
```

#### 2. 运行示例

```bash
# 中文优化版本（推荐）
python examples/dashscope_examples/demo_dashscope_chinese.py

# 完整功能版本
python examples/dashscope_examples/demo_dashscope.py

# 简化测试版本
python examples/dashscope_examples/demo_dashscope_simple.py

# 无记忆功能版本（兼容性更好）
python examples/dashscope_examples/demo_dashscope_no_memory.py

# 其他示例
python examples/simple_analysis_demo.py
python examples/cli_demo.py
python examples/demo_news_filtering.py
```

### 🌍 使用OpenAI模型

如果您有OpenAI API密钥，可以使用：

#### 1. 配置API密钥

```bash
set OPENAI_API_KEY=your_openai_api_key
set FINNHUB_API_KEY=your_finnhub_api_key
```

#### 2. 运行示例

```bash
python examples/openai/demo_openai.py
```

## 示例程序说明

### 🎯 核心分析示例

| 文件名 | 功能描述 | 适用场景 |
|--------|----------|----------|
| `demo_deepseek_analysis.py` | DeepSeek V3股票分析演示 | 完整分析流程展示 |
| `demo_news_filtering.py` | 新闻过滤演示 (v0.1.12新增) | 智能新闻分析 |
| `simple_analysis_demo.py` | 简单分析演示 | 初学者入门 |
| `custom_analysis_demo.py` | 自定义分析演示 | 高级配置展示 |
| `batch_analysis.py` | 批量股票分析示例 | 处理多只股票 |

### 🤖 LLM模型示例

#### 阿里百炼示例

| 文件名 | 功能描述 | 适用场景 |
|--------|----------|----------|
| `demo_dashscope_chinese.py` | 专门优化的中文股票分析 | 中文用户，完整分析报告 |
| `demo_dashscope.py` | 完整的TradingAgents演示 | 完整功能测试 |
| `demo_dashscope_simple.py` | 简化的LLM测试 | 快速验证模型连接 |
| `demo_dashscope_no_memory.py` | 禁用记忆功能的版本 | 兼容性问题排查 |

#### OpenAI示例

| 文件名 | 功能描述 | 适用场景 |
|--------|----------|----------|
| `demo_openai.py` | OpenAI模型演示 | 有OpenAI API密钥的用户 |

### 🛠️ 工具和配置示例

| 文件名 | 功能描述 | 适用场景 |
|--------|----------|----------|
| `cli_demo.py` | CLI命令行演示 | 命令行界面使用 |
| `config_management_demo.py` | 配置管理演示 | 配置文件操作 |
| `data_dir_config_demo.py` | 数据目录配置演示 | 自定义数据存储路径 |
| `token_tracking_demo.py` | Token跟踪演示 | 监控API使用情况 |
| `my_stock_analysis.py` | 个人股票分析示例 | 个性化配置 |

### 📊 数据源示例

| 文件名 | 功能描述 | 适用场景 |
|--------|----------|----------|
| `tushare_demo.py` | Tushare数据源演示 | 数据获取展示 |
| `stock_list_example.py` | 股票列表示例 | 批量处理股票代码 |
| `stock_query_examples.py` | 股票查询示例 | 各种查询方式 |

### 🧪 测试和调试

| 文件名 | 功能描述 | 适用场景 |
|--------|----------|----------|
| `test_news_timeout.py` | 新闻超时测试 | 网络连接调试 |

## 📖 使用指南

### 🎯 新手推荐路径

1. **第一步**: 从简单示例开始
   ```bash
   python examples/simple_analysis_demo.py
   ```

2. **第二步**: 尝试CLI界面
   ```bash
   python examples/cli_demo.py
   ```

3. **第三步**: 体验完整分析
   ```bash
   python examples/demo_deepseek_analysis.py
   ```

4. **第四步**: 探索新闻分析 (v0.1.12新增)
   ```bash
   python examples/demo_news_filtering.py
   ```

### 🔧 高级用户路径

1. **配置管理**: 学习如何管理配置
   ```bash
   python examples/config_management_demo.py
   ```

2. **批量分析**: 处理多只股票
   ```bash
   python examples/batch_analysis.py
   ```

3. **自定义分析**: 高级配置和定制
   ```bash
   python examples/custom_analysis_demo.py
   ```

4. **Token监控**: 监控API使用情况
   ```bash
   python examples/token_tracking_demo.py
   ```

### 📊 数据源选择

- **Tushare用户**: 使用 `tushare_demo.py`
- **股票列表处理**: 使用 `stock_list_example.py`
- **查询功能测试**: 使用 `stock_query_examples.py`

### 🤖 模型选择指南

| 模型 | 优势 | 适用场景 | 示例文件 |
|------|------|----------|----------|
| DeepSeek V3 | 免费、中文友好 | 日常使用、学习 | `demo_deepseek_analysis.py` |
| 阿里百炼 | 稳定、企业级 | 生产环境 | `dashscope_examples/` |
| OpenAI | 功能强大 | 高质量分析 | `openai/demo_openai.py` |

## 获取API密钥

### 阿里百炼 API 密钥

1. 访问 [阿里百炼控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 开通百炼服务
4. 在控制台获取API密钥

### FinnHub API 密钥

1. 访问 [FinnHub官网](https://finnhub.io/)
2. 注册免费账户
3. 在仪表板获取API密钥

### OpenAI API 密钥

1. 访问 [OpenAI平台](https://platform.openai.com/)
2. 注册账户并完成验证
3. 在API密钥页面创建新密钥

## 故障排除

### 常见问题

1. **API密钥错误**
   - 检查密钥是否正确复制
   - 确认已开通相应服务

2. **网络连接问题**
   - 阿里百炼：检查国内网络连接
   - OpenAI：可能需要科学上网

3. **依赖包问题**
   - 确保已安装所有依赖：`pip install -r requirements.txt`
   - 检查虚拟环境是否激活

4. **记忆功能错误**
   - 使用 `demo_dashscope_no_memory.py` 版本
   - 或参考测试目录的集成测试

### 获取帮助

- 查看项目文档：`docs/` 目录
- 运行集成测试：`tests/integration/` 目录
- 提交Issue：项目GitHub页面

## 🤝 贡献

欢迎提交新的示例程序！请确保：

1. 代码清晰易懂
2. 包含详细注释
3. 提供使用说明
4. 遵循项目代码规范

## 📞 支持

如果遇到问题，请：

1. 查看 [故障排除指南](../docs/troubleshooting/)
2. 提交 [Issue](https://github.com/your-repo/issues)
3. 加入我们的社区讨论

## 📝 更新日志

### v0.1.12 (2025-01-03)
- ✅ **修复**: 更正目录结构路径 (`dashscope/` → `dashscope_examples/`)
- ✅ **新增**: 完整的示例程序列表和分类说明
- ✅ **新增**: 新手和高级用户使用指南
- ✅ **新增**: 模型选择指南和数据源选择建议
- ✅ **优化**: 文档结构和可读性
- ✅ **覆盖**: 19个示例文件的完整说明

### 文档统计
- **总示例文件**: 19个
- **文档覆盖率**: 100%
- **分类数量**: 5个主要分类
- **使用指南**: 新手路径 + 高级路径

---

📍 **当前版本**: v0.1.12 | **最后更新**: 2025-01-03 | **文档状态**: ✅ 已同步

## 许可证

本项目遵循项目根目录的LICENSE文件。
