# TradingAgents 中文增强版

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-v1.0.1-green.svg)](./VERSION)
[![Documentation](https://img.shields.io/badge/docs-中文文档-green.svg)](./docs/)
[![Original](https://img.shields.io/badge/基于-TauricResearch/TradingAgents-orange.svg)](https://github.com/TauricResearch/TradingAgents)

---

## ⚠️ 重要版权声明与授权说明

### 🚨 版权侵权警告

**我们注意到 `tradingagents-ai.com` 网站未经授权使用了我们的专有代码，并声称是他们公司的产品。**

**⚠️ 重要提醒**：
- ❌ **我们项目组目前没有给任何组织或个人进行过商业授权**
- ❌ **该网站未经授权使用我们的代码，属于侵权行为**
- ⚠️ **请大家注意识别，避免上当受骗**

**✅ 官方唯一渠道**：
- 📦 GitHub 仓库：https://github.com/hsliuping/TradingAgents-CN
- 📧 官方邮箱：hsliup@163.com
- 📱 微信公众号：TradingAgents-CN

如发现任何未经授权的商业使用，请通过上述渠道联系我们。

### 📋 版本授权说明

#### v1.0.1（当前稳定版本）
- ✅ **个人使用**：完全开源，可自由使用
- ❌ **商业使用**：**必须获得商业授权**，未经授权禁止商业使用
- 📧 **授权联系**：[hsliup@163.com](mailto:hsliup@163.com)

#### v2.0.0（开发中）
- 🔄 **开发状态**：已完成两轮内测，接近完工上线阶段
- ⚠️ **开源计划**：**因存在盗版问题，v2.0 版本暂时不进行开源**
- 📢 **发布方式**：将通过官方渠道发布，敬请关注

### 📄 许可证详情

本项目采用**混合许可证**模式：
- 🔓 **开源部分**（Apache 2.0）：除 `app/` 和 `frontend/` 外的所有文件
- 🔒 **专有部分**（需商业授权）：`app/`（FastAPI后端）和 `frontend/`（Vue前端）目录

详细说明请查看：[版权声明](./COPYRIGHT.md) | [许可证文件](./LICENSE)

---

>
> 🎓 **学习中心**: AI基础 | 提示词工程 | 模型选择 | 多智能体分析原理 | 风险与局限 | 源项目与论文 | 实战教程（部分为外链） | 常见问题
> 🎯 **核心功能**: 原生OpenAI支持 | Google AI全面集成 | 自定义端点配置 | 智能模型选择 | 多LLM提供商支持 | 模型选择持久化 | Docker容器化部署 | 专业报告导出 | 完整A股支持 | 中文本地化

面向中文用户的**多智能体与大模型股票分析学习平台**。帮助你系统化学习如何使用多智能体交易框架与 AI 大模型进行合规的股票研究与策略实验，不提供实盘交易指令，平台定位为学习与研究用途。

## 🙏 致敬源项目

感谢 [Tauric Research](https://github.com/TauricResearch) 团队创造的革命性多智能体交易框架 [TradingAgents](https://github.com/TauricResearch/TradingAgents)！

**🎯 我们的定位与使命**: 专注学习与研究，提供中文化学习中心与工具，合规友好，支持 A股/港股/美股 的分析与教学，推动 AI 金融技术在中文社区的普及与正确使用。

## 🎉 v1.0.1 版本说明 - 配置体验与同步稳定性增强

> 🚀 **当前推荐版本**: `v1.0.1` 已正式可用，在 `v1.0.0-preview` 架构基础上，重点增强配置管理、聚合厂家、页面切换、单股同步和上游能力吸收。

### ✨ 核心特性

#### 🏗️ **全新技术架构**
- **后端升级**: 从 Streamlit 迁移到 FastAPI，提供更强大的 RESTful API
- **前端重构**: 采用 Vue 3 + Element Plus，打造现代化的单页应用
- **数据库优化**: MongoDB + Redis 双数据库架构，性能提升 10 倍
- **容器化部署**: 完整的 Docker 多架构支持（amd64 + arm64）

#### 🚀 **v1.0.1 重点增强**
- **配置管理优化**: 新增厂家、模型目录和大模型配置支持按最新添加顺序置顶显示
- **聚合厂家增强**: 新增 `AiHubMix` 聚合 LLM 厂家，并支持聚合渠道初始化能力
- **模型选择统一排序**: 配置页、对话框和分析页中的模型列表顺序保持一致
- **页面切换修复**: 股票详情页和报告详情页切换后会自动刷新正确内容
- **单股同步增强**: 同步结果支持展示主链路、回退链路、失败原因和 `market_quotes` 落库状态
- **AKShare 兜底增强**: 单股实时行情支持 `stock_bid_ask_em -> stock_zh_a_spot -> stock_zh_a_spot_em -> stock_zh_a_hist` 多级降级链
- **上游能力同步**: 同步 `llm_clients`、共享模型目录、provider 规范键、图层初始化路径和数据库迁移增强等能力

#### 🎯 **企业级功能**
- **用户权限管理**: 完整的用户认证、角色管理、操作日志系统
- **配置管理中心**: 可视化的大模型配置、数据源管理、系统设置
- **缓存管理系统**: 智能缓存策略，支持 MongoDB/Redis/文件多级缓存
- **实时通知系统**: SSE+WebSocket 双通道推送，实时跟踪分析进度和系统状态
- **批量分析功能**: 支持多只股票同时分析，提升工作效率
- **智能股票筛选**: 基于多维度指标的股票筛选和排序系统
- **自选股管理**: 个人自选股收藏、分组管理和跟踪功能
- **个股详情页**: 完整的个股信息展示和历史分析记录
- **模拟交易系统**: 虚拟交易环境，验证投资策略效果

#### 🤖 **智能分析增强**
- **动态供应商管理**: 支持动态添加和配置 LLM 供应商
- **模型能力管理**: 智能模型选择，根据任务自动匹配最佳模型
- **多数据源同步**: 统一的数据源管理，支持 Tushare、AkShare、BaoStock
- **报告导出功能**: 支持 Markdown/Word/PDF 多格式专业报告导出

#### 🔧 **重大Bug修复**
- **技术指标计算修复**: 彻底解决市场分析师技术指标计算不准确问题
- **基本面数据修复**: 修复基本面分析师PE、PB等关键财务数据计算错误
- **死循环问题修复**: 解决部分用户在分析过程中触发的无限循环问题
- **数据一致性优化**: 确保所有分析师使用统一、准确的数据源

#### 🐳 **Docker 多架构支持**
- **跨平台部署**: 支持 x86_64 和 ARM64 架构（Apple Silicon、树莓派、AWS Graviton）
- **GitHub Actions**: 自动化构建和发布 Docker 镜像
- **一键部署**: 完整的 Docker Compose 配置，5 分钟快速启动

### 📊 技术栈升级

| 组件 | v0.1.x | v1.0.1 |
|------|--------|----------------|
| **后端框架** | Streamlit | FastAPI + Uvicorn |
| **前端框架** | Streamlit | Vue 3 + Vite + Element Plus |
| **数据库** | 可选 MongoDB | MongoDB + Redis |
| **API 架构** | 单体应用 | RESTful API + WebSocket |
| **部署方式** | 本地/Docker | Docker 多架构 + GitHub Actions |



#### 📥 安装部署

**两种部署方式，任选其一**：

| 部署方式 | 适用场景 | 难度 | 文档链接 |
|---------|---------|------|---------|
| 🐳 **Docker版** | 生产环境、跨平台 | ⭐⭐ 中等 | [Docker 部署指南](https://mp.weixin.qq.com/s/JkA0cOu8xJnoY_3LC5oXNw) |
| 💻 **本地代码版** | 开发者、定制需求 | ⭐⭐⭐ 较难 | [本地安装指南](https://mp.weixin.qq.com/s/cqUGf-sAzcBV19gdI4sYfA) |

⚠️ **重要提醒**：在分析股票之前，请按相关文档要求，将股票数据同步完成，否则分析结果将会出现数据错误。



#### 📚 使用指南

在使用前，建议先阅读详细的使用指南：
- **[v1.0.1 发布说明](./docs/releases/v1.0.1-release-notes.md)**
- **[v1.0.1 使用手册](./docs/guides/v1.0.1-user-manual.md)**
- **[v1.0.1 升级指南](./docs/releases/upgrade-guide.md)**
- **[完整更新日志](./docs/releases/CHANGELOG.md)**
- **[0、📘 TradingAgents-CN v1.0.0-preview 快速入门视频](https://www.bilibili.com/video/BV1i2CeBwEP7/?vd_source=5d790a5b8d2f46d2c10fd4e770be1594)**

- **[1、📘 TradingAgents-CN v1.0.0-preview 使用指南](https://mp.weixin.qq.com/s/ppsYiBncynxlsfKFG8uEbw)**
- **[2、📘 使用 Docker Compose 部署TradingAgents-CN v1.0.0-preview（完全版）](https://mp.weixin.qq.com/s/JkA0cOu8xJnoY_3LC5oXNw)**
- **[3、📘 从 Docker Hub 更新 TradingAgents‑CN 镜像](https://mp.weixin.qq.com/s/WKYhW8J80Watpg8K6E_dSQ)**
- **[4、📘 TradingAgents-CN v1.0.0-preview绿色版安装和升级指南](https://mp.weixin.qq.com/s/eoo_HeIGxaQZVT76LBbRJQ)**
- **[5、📘 TradingAgents-CN v1.0.0-preview绿色版端口配置说明](https://mp.weixin.qq.com/s/o5QdNuh2-iKkIHzJXCj7vQ)**
- **[6、📘 TradingAgents v1.0.0-preview 源码版安装手册（修订版）](https://mp.weixin.qq.com/s/cqUGf-sAzcBV19gdI4sYfA)**
- **[7、📘 TradingAgents v1.0.0-preview 源码安装视频教程](https://www.bilibili.com/video/BV1FxCtBHEte/?vd_source=5d790a5b8d2f46d2c10fd4e770be1594)**


使用指南包含：
- ✅ 完整的功能介绍和操作演示
- ✅ 详细的配置说明和最佳实践
- ✅ 常见问题解答和故障排除
- ✅ 实际使用案例和效果展示

### 数据库运维补充

- 数据库版本隔离、共享库保护、迁移脚本与 provider 规范化说明：
  - [数据库版本隔离与 Provider 规范化](./docs/deployment/database/DB_VERSION_ISOLATION_AND_PROVIDER_NORMALIZATION.md)

### 上游吸收补充

- 当前项目采用人工选择性吸收上游更新：
  - [上游同步策略](./docs/maintenance/upstream-sync.md)
  - [人工上游吸收清单](./docs/maintenance/manual-upstream-absorption-checklist.md)

- `v1.0.1` 已明确同步到当前版本的上游能力包括：
  - `llm_clients` 抽象层主链路
  - 共享模型目录与轻量校验
  - provider canonical key 规范化
  - `trading_graph.py` 主要 provider 初始化路径收口
  - `fundamentals_analyst.py` 中 qwen fresh llm 重建逻辑
  - 图层参数透传、工厂别名兼容、风控引用修复
  - provider 默认 URL / 环境变量映射统一
  - MongoDB 默认库名、版本隔离命名与迁移脚本增强

#### 关注公众号

1. **关注公众号**: 微信搜索 **"TradingAgents-CN"** 并关注
2. 公众号每天推送项目最新进展和使用教程


- **微信公众号**: TradingAgents-CN（推荐）

  <img src="assets/wexin.png" alt="微信公众号" width="200"/>


## 🆚 中文增强特色

**相比原版新增**: 智能新闻分析 | 多层次新闻过滤 | 新闻质量评估 | 统一新闻工具 | 多LLM提供商集成 | 模型选择持久化 | 快速切换按钮 | | 实时进度显示 | 智能会话管理 | 中文界面 | A股数据 | 国产LLM | Docker部署 | 专业报告导出 | 统一日志管理 | Web配置界面 | 成本优化



## 🤝 贡献指南

我们欢迎各种形式的贡献：

### 贡献类型

- 🐛 **Bug修复** - 发现并修复问题
- ✨ **新功能** - 添加新的功能特性
- 📚 **文档改进** - 完善文档和教程
- 🌐 **本地化** - 翻译和本地化工作
- 🎨 **代码优化** - 性能优化和代码重构

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 📋 查看贡献者

查看所有贡献者和详细贡献内容：**[🤝 贡献者名单](CONTRIBUTORS.md)**

## 📄 许可证详情

本项目采用**混合许可证**模式，详见 [LICENSE](LICENSE) 文件：

### 🔓 开源部分（Apache 2.0）
- **适用范围**：除 `app/` 和 `frontend/` 外的所有文件
- **权限**：商业使用 ✅ | 修改分发 ✅ | 私人使用 ✅ | 专利使用 ✅
- **条件**：保留版权声明 ❗ | 包含许可证副本 ❗

### 🔒 专有部分（需商业授权）
- **适用范围**：`app/`（FastAPI后端）和 `frontend/`（Vue前端）目录
- **商业使用**：需要单独许可协议
- **联系授权**：[hsliup@163.com](mailto:hsliup@163.com)

### 📋 许可证选择建议
- **个人学习/研究**：可自由使用全部功能
- **商业应用**：请联系获取专有组件授权
- **定制开发**：欢迎咨询商业合作方案

### 📚 相关文档

- [版权声明](./COPYRIGHT.md) - 详细的版权信息和使用条款
- [主许可证](./LICENSE) - Apache 2.0 许可证
- [后端专有许可证](./app/LICENSE) - 后端专有组件许可证
- [前端专有许可证](./frontend/LICENSE) - 前端专有组件许可证

## 🙏 致谢与感恩

### 🌟 向源项目开发者致敬

我们向 [Tauric Research](https://github.com/TauricResearch) 团队表达最深的敬意和感谢：

- **🎯 愿景领导者**: 感谢您们在AI金融领域的前瞻性思考和创新实践
- **💎 珍贵源码**: 感谢您们开源的每一行代码，它们凝聚着无数的智慧和心血
- **🏗️ 架构大师**: 感谢您们设计了如此优雅、可扩展的多智能体框架
- **💡 技术先驱**: 感谢您们将前沿AI技术与金融实务完美结合
- **🔄 持续贡献**: 感谢您们持续的维护、更新和改进工作

### 🤝 社区贡献者致谢

感谢所有为TradingAgents-CN项目做出贡献的开发者和用户！

详细的贡献者名单和贡献内容请查看：**[📋 贡献者名单](CONTRIBUTORS.md)**

包括但不限于：

- 🐳 **Docker容器化** - 部署方案优化
- 📄 **报告导出功能** - 多格式输出支持
- 🐛 **Bug修复** - 系统稳定性提升
- 🔧 **代码优化** - 用户体验改进
- 📝 **文档完善** - 使用指南和教程
- 🌍 **社区建设** - 问题反馈和推广
- **🌍 开源贡献**: 感谢您们选择Apache 2.0协议，给予开发者最大的自由
- **📚 知识分享**: 感谢您们提供的详细文档和最佳实践指导

**特别感谢**：[TradingAgents](https://github.com/TauricResearch/TradingAgents) 项目为我们提供了坚实的技术基础。虽然Apache 2.0协议赋予了我们使用源码的权利，但我们深知每一行代码的珍贵价值，将永远铭记并感谢您们的无私贡献。

### 🇨🇳 推广使命的初心

创建这个中文增强版本，我们怀着以下初心：

- **🌉 技术传播**: 让优秀的TradingAgents技术在中国得到更广泛的应用
- **🎓 教育普及**: 为中国的AI金融教育提供更好的工具和资源
- **🤝 文化桥梁**: 在中西方技术社区之间搭建交流合作的桥梁
- **🚀 创新推动**: 推动中国金融科技领域的AI技术创新和应用

### 🌍 开源社区

感谢所有为本项目贡献代码、文档、建议和反馈的开发者和用户。正是因为有了大家的支持，我们才能更好地服务中文用户社区。

### 🤝 合作共赢

我们承诺：

- **尊重原创**: 始终尊重源项目的知识产权和开源协议
- **反馈贡献**: 将有价值的改进和创新反馈给源项目和开源社区
- **持续改进**: 不断完善中文增强版本，提供更好的用户体验
- **开放合作**: 欢迎与源项目团队和全球开发者进行技术交流与合作

## [感谢AIHubmix赞助，推荐llm模型使用AIHubmix](https://aihubmix.com/?aff=2rIi)

<a href="https://aihubmix.com/?aff=2rIi" target="_blank" rel="noopener noreferrer">
  <img src="assets/AIHubmixlogo.png" alt="AIHubMix" width="220"/>
</a>

## 📈 版本历史

- **v1.0.1** (2026-04-14): 🔧 配置管理优化、AiHubMix 聚合厂家、单股同步增强与上游能力吸收 ✨ **当前版本**
- **v1.0.0-preview** (2025-10-10): 🏗️ FastAPI + Vue 3 新架构预览版
- **v0.1.13** (2025-08-02): 🤖 原生OpenAI支持与Google AI生态系统全面集成
- **v0.1.12** (2025-07-29): 🧠 智能新闻分析模块与项目结构优化
- **v0.1.11** (2025-07-27): 🤖 多LLM提供商集成与模型选择持久化
- **v0.1.10** (2025-07-18): 🚀 Web界面实时进度显示与智能会话管理
- **v0.1.9** (2025-07-16): 🎯 CLI用户体验重大优化与统一日志管理
- **v0.1.8** (2025-07-15): 🎨 Web界面全面优化与用户体验提升
- **v0.1.7** (2025-07-13): 🐳 容器化部署与专业报告导出
- **v0.1.6** (2025-07-11): 🔧 阿里百炼修复与数据源升级
- **v0.1.5** (2025-07-08): 📊 添加Deepseek模型支持
- **v0.1.4** (2025-07-05): 🏗️ 架构优化与配置管理重构
- **v0.1.3** (2025-06-28): 🇨🇳 A股市场完整支持
- **v0.1.2** (2025-06-15): 🌐 Web界面和配置管理
- **v0.1.1** (2025-06-01): 🧠 国产LLM集成

📋 **详细更新日志**: [CHANGELOG.md](./docs/releases/CHANGELOG.md)

## 📞 联系方式

- **GitHub Issues**: [提交问题和建议](https://github.com/hsliuping/TradingAgents-CN/issues)
- **邮箱**: hsliup@163.com
- 项目ＱＱ群：1091917201
- 项目微信公众号：TradingAgents-CN

  <img src="assets/wexin.png" alt="微信公众号" width="200"/>

- **原项目**: [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)
- **文档**: [完整文档目录](docs/)

## ⚠️ 风险提示

**重要声明**: 本框架仅用于研究和教育目的，不构成投资建议。

- 📊 交易表现可能因多种因素而异
- 🤖 AI模型的预测存在不确定性
- 💰 投资有风险，决策需谨慎
- 👨‍💼 建议咨询专业财务顾问

---

<div align="center">

**🌟 如果这个项目对您有帮助，请给我们一个 Star！**

[⭐ Star this repo](https://github.com/hsliuping/TradingAgents-CN) | [🍴 Fork this repo](https://github.com/hsliuping/TradingAgents-CN/fork) | [📖 Read the docs](./docs/)

</div>
