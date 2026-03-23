# 🎭 The Agency：準備好改變你工作流程的 AI 專家

> **指尖上的完整 AI 團隊** — 從前端高手到 Reddit 社群忍者，從創意注入者到現實檢驗者。每位代理人都是擁有個性、流程和經過驗證成果的專業專家。

[![GitHub stars](https://img.shields.io/github/stars/msitarzewski/agency-agents?style=social)](https://github.com/msitarzewski/agency-agents)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://makeapullrequest.com)
[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-pink?logo=github)](https://github.com/sponsors/msitarzewski)

[English](README.md) | **繁體中文**

---

## 🚀 這是什麼？

起源於一則 Reddit 貼文，經過數月的迭代，**The Agency** 是一個不斷壯大的精心打造 AI 代理人個性集合。每位代理人都具備：

- **🎯 專業化**：在其領域擁有深厚專業知識（不是通用提示模板）
- **🧠 個性驅動**：獨特的聲音、溝通風格和方法
- **📋 成果導向**：真實的程式碼、流程和可衡量的結果
- **✅ 生產就緒**：經過實戰考驗的工作流程和成功指標

**你可以把它想成**：組建你的夢幻團隊，只不過他們是永不睡覺、從不抱怨、始終交付的 AI 專家。

---

## ⚡ 快速開始

### 方式一：搭配 Claude Code 使用（推薦）

```bash
# 將代理人複製到你的 Claude Code 目錄
cp -r agency-agents/* ~/.claude/agents/

# 然後在 Claude Code 工作階段中啟用任何代理人：
# "嘿 Claude，啟用前端開發者模式，幫我建立一個 React 元件"
```

### 方式二：作為參考使用

每個代理人檔案包含：
- 身份與個性特徵
- 核心任務與工作流程
- 技術成果與程式碼範例
- 成功指標與溝通風格

瀏覽下方的代理人，複製/改編你需要的！

### 方式三：搭配其他工具使用（Cursor、Aider、Windsurf、Gemini CLI、OpenCode）

```bash
# 步驟一 — 為所有支援的工具產生整合檔案
./scripts/convert.sh

# 步驟二 — 互動式安裝（自動偵測你已安裝的工具）
./scripts/install.sh

# 或直接指定特定工具
./scripts/install.sh --tool cursor
./scripts/install.sh --tool copilot
./scripts/install.sh --tool aider
./scripts/install.sh --tool windsurf
```

詳情請參閱下方的[多工具整合](#-多工具整合)章節。

---

## 🎨 代理人陣容

### 💻 工程部門

一次一個提交，打造未來。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 🎨 [前端開發者](engineering/engineering-frontend-developer.md) | React/Vue/Angular、UI 實作、效能 | 現代網頁應用、像素級精確 UI、Core Web Vitals 最佳化 |
| 🏗️ [後端架構師](engineering/engineering-backend-architect.md) | API 設計、資料庫架構、可擴展性 | 伺服器端系統、微服務、雲端基礎設施 |
| 📱 [行動應用建構者](engineering/engineering-mobile-app-builder.md) | iOS/Android、React Native、Flutter | 原生與跨平台行動應用 |
| 🤖 [AI 工程師](engineering/engineering-ai-engineer.md) | ML 模型、部署、AI 整合 | 機器學習功能、資料管線、AI 驅動應用 |
| 🚀 [DevOps 自動化專家](engineering/engineering-devops-automator.md) | CI/CD、基礎設施自動化、雲端運維 | 管線開發、部署自動化、監控 |
| ⚡ [快速原型建構者](engineering/engineering-rapid-prototyper.md) | 快速 POC 開發、MVP | 快速概念驗證、黑客松專案、快速迭代 |
| 💎 [資深開發者](engineering/engineering-senior-developer.md) | Laravel/Livewire、進階模式 | 複雜實作、架構決策 |
| 🔒 [安全工程師](engineering/engineering-security-engineer.md) | 威脅建模、安全程式碼審查、安全架構 | 應用程式安全、弱點評估、安全 CI/CD |
| ⚡ [自主最佳化架構師](engineering/engineering-autonomous-optimization-architect.md) | LLM 路由、成本最佳化、影子測試 | 需要智慧 API 選擇和成本防護的自主系統 |
| 🔩 [嵌入式韌體工程師](engineering/engineering-embedded-firmware-engineer.md) | 裸機、RTOS、ESP32/STM32/Nordic 韌體 | 生產級嵌入式系統和 IoT 裝置 |
| 🚨 [事件回應指揮官](engineering/engineering-incident-response-commander.md) | 事件管理、事後檢討、值班 | 管理生產事件和建立事件準備 |
| ⛓️ [Solidity 智慧合約工程師](engineering/engineering-solidity-smart-contract-engineer.md) | EVM 合約、Gas 最佳化、DeFi | 安全、Gas 最佳化的智慧合約和 DeFi 協議 |
| 📚 [技術文件撰寫者](engineering/engineering-technical-writer.md) | 開發者文件、API 參考、教學 | 清晰、準確的技術文件 |
| 🎯 [威脅偵測工程師](engineering/engineering-threat-detection-engineer.md) | SIEM 規則、威脅狩獵、ATT&CK 映射 | 建構偵測層和威脅狩獵 |
| 💬 [微信小程式開發者](engineering/engineering-wechat-mini-program-developer.md) | 微信生態系、小程式、支付整合 | 為微信生態系建構高效能應用 |
| 👁️ [程式碼審查者](engineering/engineering-code-reviewer.md) | 建設性程式碼審查、安全、可維護性 | PR 審查、程式碼品質關卡、透過審查指導 |
| 🗄️ [資料庫最佳化專家](engineering/engineering-database-optimizer.md) | Schema 設計、查詢最佳化、索引策略 | PostgreSQL/MySQL 調校、慢查詢除錯、遷移規劃 |
| 🌿 [Git 工作流程大師](engineering/engineering-git-workflow-master.md) | 分支策略、約定式提交、進階 Git | Git 工作流程設計、歷史清理、CI 友善分支管理 |
| 🏛️ [軟體架構師](engineering/engineering-software-architect.md) | 系統設計、DDD、架構模式、權衡分析 | 架構決策、領域建模、系統演進策略 |
| 🛡️ [SRE](engineering/engineering-sre.md) | SLO、錯誤預算、可觀測性、混沌工程 | 生產可靠性、苦工減少、容量規劃 |
| 🧬 [AI 資料修復工程師](engineering/engineering-ai-data-remediation-engineer.md) | 自修復管線、隔離式 SLM、語意聚類 | 以零資料遺失方式大規模修復損壞資料 |
| 🔧 [資料工程師](engineering/engineering-data-engineer.md) | 資料管線、Lakehouse 架構、ETL/ELT | 建構可靠的資料基礎設施和資料倉儲 |
| 🔗 [飛書整合開發者](engineering/engineering-feishu-integration-developer.md) | 飛書/Lark 開放平台、機器人、工作流程 | 為飛書生態系建構整合 |

### 🎨 設計部門

讓一切變得美麗、易用且令人愉悅。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 🎯 [UI 設計師](design/design-ui-designer.md) | 視覺設計、元件庫、設計系統 | 介面創建、品牌一致性、元件設計 |
| 🔍 [UX 研究員](design/design-ux-researcher.md) | 使用者測試、行為分析、研究 | 理解使用者、可用性測試、設計洞察 |
| 🏛️ [UX 架構師](design/design-ux-architect.md) | 技術架構、CSS 系統、實作 | 開發者友善的基礎、實作指導 |
| 🎭 [品牌守護者](design/design-brand-guardian.md) | 品牌識別、一致性、定位 | 品牌策略、識別開發、準則 |
| 📖 [視覺故事家](design/design-visual-storyteller.md) | 視覺敘事、多媒體內容 | 引人入勝的視覺故事、品牌敘事 |
| ✨ [趣味注入者](design/design-whimsy-injector.md) | 個性、愉悅、趣味互動 | 增添歡樂、微互動、彩蛋、品牌個性 |
| 📷 [圖片提示工程師](design/design-image-prompt-engineer.md) | AI 圖片生成提示、攝影 | Midjourney、DALL-E、Stable Diffusion 攝影提示 |
| 🌈 [包容性視覺專家](design/design-inclusive-visuals-specialist.md) | 代表性、偏見緩解、真實圖像 | 生成文化準確的 AI 圖片和影片 |

### 💰 付費媒體部門

將廣告支出轉化為可衡量的商業成果。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 💰 [PPC 活動策略師](paid-media/paid-media-ppc-strategist.md) | Google/Microsoft/Amazon Ads、帳戶架構、出價 | 帳戶建構、預算分配、擴展、效能診斷 |
| 🔍 [搜尋查詢分析師](paid-media/paid-media-search-query-analyst.md) | 搜尋詞分析、否定關鍵字、意圖映射 | 查詢審計、浪費消除、關鍵字發掘 |
| 📋 [付費媒體審計師](paid-media/paid-media-auditor.md) | 200+ 項帳戶審計、競爭分析 | 帳戶接管、季度審查、競爭提案 |
| 📡 [追蹤與衡量專家](paid-media/paid-media-tracking-specialist.md) | GTM、GA4、轉換追蹤、CAPI | 新實施、追蹤審計、平台遷移 |
| ✍️ [廣告創意策略師](paid-media/paid-media-creative-strategist.md) | RSA 文案、Meta 創意、Performance Max 素材 | 創意啟動、測試計畫、廣告疲勞更新 |
| 📺 [程序化與展示型購買者](paid-media/paid-media-programmatic-buyer.md) | GDN、DSP、合作夥伴媒體、ABM 展示 | 展示規劃、合作夥伴拓展、ABM 計畫 |
| 📱 [付費社群策略師](paid-media/paid-media-paid-social-strategist.md) | Meta、LinkedIn、TikTok、跨平台社群 | 社群廣告計畫、平台選擇、受眾策略 |

### 💼 銷售部門

透過技藝而非 CRM 繁忙工作將管線轉化為營收。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 🎯 [外向拓展策略師](sales/sales-outbound-strategist.md) | 訊號驅動開發、多通路序列、ICP 鎖定 | 透過研究驅動的拓展建構管線 |
| 🔍 [探索教練](sales/sales-discovery-coach.md) | SPIN、Gap Selling、Sandler — 問題設計與通話結構 | 準備探索電話、機會資格審查、指導業務 |
| ♟️ [交易策略師](sales/sales-deal-strategist.md) | MEDDPICC 資格審查、競爭定位、贏單規劃 | 交易評分、管線風險揭露、贏單策略建構 |
| 🛠️ [銷售工程師](sales/sales-engineer.md) | 技術演示、POC 範圍界定、競爭戰卡 | 售前技術贏單、演示準備、競爭定位 |
| 🏹 [提案策略師](sales/sales-proposal-strategist.md) | RFP 回應、贏單主題、敘事結構 | 撰寫具說服力的提案 |
| 📊 [管線分析師](sales/sales-pipeline-analyst.md) | 預測、管線健康、交易速度、RevOps | 管線審查、預測準確度、營收運營 |
| 🗺️ [客戶策略師](sales/sales-account-strategist.md) | 落地擴展、QBR、利害關係人映射 | 售後擴展、客戶規劃、NRR 增長 |
| 🏋️ [銷售教練](sales/sales-coach.md) | 業務發展、通話指導、管線審查引導 | 透過結構化指導提升每位業務和每筆交易 |

### 📢 行銷部門

一次一個真實互動，壯大你的受眾。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 🚀 [成長駭客](marketing/marketing-growth-hacker.md) | 快速用戶獲取、病毒循環、實驗 | 爆發式增長、用戶獲取、轉換最佳化 |
| 📝 [內容創作者](marketing/marketing-content-creator.md) | 多平台內容、編輯日曆 | 內容策略、文案撰寫、品牌敘事 |
| 🐦 [Twitter 互動者](marketing/marketing-twitter-engager.md) | 即時互動、思想領導力 | Twitter 策略、LinkedIn 活動、專業社群 |
| 📱 [TikTok 策略師](marketing/marketing-tiktok-strategist.md) | 病毒內容、演算法最佳化 | TikTok 增長、病毒內容、Z 世代/千禧世代受眾 |
| 📸 [Instagram 策展人](marketing/marketing-instagram-curator.md) | 視覺敘事、社群建設 | Instagram 策略、美學開發、視覺內容 |
| 🤝 [Reddit 社群建設者](marketing/marketing-reddit-community-builder.md) | 真實互動、價值驅動內容 | Reddit 策略、社群信任、真實行銷 |
| 📱 [App Store 最佳化專家](marketing/marketing-app-store-optimizer.md) | ASO、轉換最佳化、可發現性 | 應用行銷、商店最佳化、應用增長 |
| 🌐 [社群媒體策略師](marketing/marketing-social-media-strategist.md) | 跨平台策略、活動 | 整體社群策略、多平台活動 |
| 🔍 [SEO 專家](marketing/marketing-seo-specialist.md) | 技術 SEO、內容策略、連結建設 | 推動可持續的自然搜尋增長 |
| 📘 [書籍共同作者](marketing/marketing-book-co-author.md) | 思想領導力書籍、代筆、出版 | 為創辦人和專家進行策略性書籍合作 |
| 🎙️ [Podcast 策略師](marketing/marketing-podcast-strategist.md) | Podcast 內容策略、平台最佳化 | Podcast 市場策略和運營 |
| 💼 [LinkedIn 內容創作者](marketing/marketing-linkedin-content-creator.md) | 個人品牌、思想領導力、專業內容 | LinkedIn 增長、專業受眾建設、B2B 內容 |
| 🔮 [AI 引用策略師](marketing/marketing-ai-citation-strategist.md) | AEO/GEO、AI 推薦可見度、引用審計 | 提升品牌在 ChatGPT、Claude、Gemini、Perplexity 中的可見度 |

### 📊 產品部門

在正確的時間打造正確的事物。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 🎯 [Sprint 優先排序者](product/product-sprint-prioritizer.md) | 敏捷規劃、功能優先排序 | Sprint 規劃、資源分配、待辦清單管理 |
| 🔍 [趨勢研究員](product/product-trend-researcher.md) | 市場情報、競爭分析 | 市場研究、機會評估、趨勢識別 |
| 💬 [回饋綜合者](product/product-feedback-synthesizer.md) | 使用者回饋分析、洞察提取 | 回饋分析、使用者洞察、產品優先順序 |
| 🧠 [行為助推引擎](product/product-behavioral-nudge-engine.md) | 行為心理學、助推設計、互動 | 透過行為科學最大化使用者動機 |
| 🧭 [產品經理](product/product-manager.md) | 完整生命週期產品負責 | 探索、PRD、路線圖規劃、GTM、成果衡量 |

### 🎬 專案管理部門

讓列車準時（且在預算內）運行。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 🎬 [工作室製作人](project-management/project-management-studio-producer.md) | 高階協調、作品集管理 | 多專案監督、策略對齊、資源分配 |
| 🐑 [專案牧羊人](project-management/project-management-project-shepherd.md) | 跨功能協調、時程管理 | 端到端專案協調、利害關係人管理 |
| ⚙️ [工作室運營](project-management/project-management-studio-operations.md) | 日常效率、流程最佳化 | 營運卓越、團隊支援、生產力 |
| 🧪 [實驗追蹤者](project-management/project-management-experiment-tracker.md) | A/B 測試、假說驗證 | 實驗管理、資料驅動決策、測試 |
| 👔 [資深專案經理](project-management/project-manager-senior.md) | 務實範圍界定、任務轉換 | 將規格轉換為任務、範圍管理 |
| 📋 [Jira 工作流程管家](project-management/project-management-jira-workflow-steward.md) | Git 工作流程、分支策略、可追蹤性 | 執行 Jira 連結的 Git 紀律和交付 |

### 🧪 測試部門

在使用者遇到問題之前先發現它們。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 📸 [證據收集者](testing/testing-evidence-collector.md) | 截圖式 QA、視覺證明 | UI 測試、視覺驗證、錯誤記錄 |
| 🔍 [現實檢驗者](testing/testing-reality-checker.md) | 證據式認證、品質關卡 | 生產準備、品質核准、發布認證 |
| 📊 [測試結果分析師](testing/testing-test-results-analyzer.md) | 測試評估、指標分析 | 測試輸出分析、品質洞察、覆蓋率報告 |
| ⚡ [效能基準測試者](testing/testing-performance-benchmarker.md) | 效能測試、最佳化 | 速度測試、負載測試、效能調校 |
| 🔌 [API 測試者](testing/testing-api-tester.md) | API 驗證、整合測試 | API 測試、端點驗證、整合 QA |
| 🛠️ [工具評估者](testing/testing-tool-evaluator.md) | 技術評估、工具選擇 | 工具評估、軟體推薦、技術決策 |
| 🔄 [工作流程最佳化者](testing/testing-workflow-optimizer.md) | 流程分析、工作流程改善 | 流程最佳化、效率提升、自動化機會 |
| ♿ [無障礙審計師](testing/testing-accessibility-auditor.md) | WCAG 審計、輔助技術測試 | 無障礙合規、螢幕閱讀器測試、包容性設計驗證 |

### 🛟 支援部門

運營的骨幹。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 💬 [客服回應者](support/support-support-responder.md) | 客戶服務、問題解決 | 客戶支援、使用者體驗、支援營運 |
| 📊 [分析報告者](support/support-analytics-reporter.md) | 資料分析、儀表板、洞察 | 商業情報、KPI 追蹤、資料視覺化 |
| 💰 [財務追蹤者](support/support-finance-tracker.md) | 財務規劃、預算管理 | 財務分析、現金流、商業績效 |
| 🏗️ [基礎設施維護者](support/support-infrastructure-maintainer.md) | 系統可靠性、效能最佳化 | 基礎設施管理、系統營運、監控 |
| ⚖️ [法律合規檢查者](support/support-legal-compliance-checker.md) | 合規、法規、法律審查 | 法律合規、監管要求、風險管理 |
| 📑 [執行摘要產生器](support/support-executive-summary-generator.md) | C-suite 溝通、策略摘要 | 高階報告、策略溝通、決策支援 |

### 🥽 空間運算部門

建構沉浸式的未來。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 🏗️ [XR 介面架構師](spatial-computing/xr-interface-architect.md) | 空間互動設計、沉浸式 UX | AR/VR/XR 介面設計、空間運算 UX |
| 💻 [macOS Spatial/Metal 工程師](spatial-computing/macos-spatial-metal-engineer.md) | Swift、Metal、高效能 3D | macOS 空間運算、Vision Pro 原生應用 |
| 🌐 [XR 沉浸式開發者](spatial-computing/xr-immersive-developer.md) | WebXR、瀏覽器式 AR/VR | 瀏覽器式沉浸體驗、WebXR 應用 |
| 🎮 [XR 駕駛艙互動專家](spatial-computing/xr-cockpit-interaction-specialist.md) | 駕駛艙式控制、沉浸式系統 | 駕駛艙控制系統、沉浸式控制介面 |
| 🍎 [visionOS 空間工程師](spatial-computing/visionos-spatial-engineer.md) | Apple Vision Pro 開發 | Vision Pro 應用、空間運算體驗 |
| 🔌 [終端整合專家](spatial-computing/terminal-integration-specialist.md) | 終端整合、命令列工具 | CLI 工具、終端工作流程、開發者工具 |

### 🎯 專業部門

無法歸類的獨特專家。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 🎭 [代理人協調者](specialized/agents-orchestrator.md) | 多代理人協調、工作流程管理 | 需要多代理人協調的複雜專案 |
| 🔍 [LSP/Index 工程師](specialized/lsp-index-engineer.md) | Language Server Protocol、程式碼智慧 | 程式碼智慧系統、LSP 實作、語意索引 |
| 🔐 [代理身份與信任架構師](specialized/agentic-identity-trust.md) | 代理身份、認證、信任驗證 | 多代理身份系統、代理授權、稽核軌跡 |
| 🔗 [身份圖譜操作者](specialized/identity-graph-operator.md) | 多代理系統的共享身份解析 | 實體去重、合併提案、跨代理身份一致性 |
| 💸 [應付帳款代理](specialized/accounts-payable-agent.md) | 付款處理、供應商管理、審計 | 跨加密貨幣、法幣、穩定幣的自主付款執行 |
| 🛡️ [區塊鏈安全審計師](specialized/blockchain-security-auditor.md) | 智慧合約審計、漏洞分析 | 在部署前發現合約漏洞 |
| 📋 [合規審計師](specialized/compliance-auditor.md) | SOC 2、ISO 27001、HIPAA、PCI-DSS | 指導組織通過合規認證 |
| 🌍 [文化智慧策略師](specialized/specialized-cultural-intelligence-strategist.md) | 全球 UX、代表性、文化排斥 | 確保軟體在各文化中產生共鳴 |
| 🗣️ [開發者倡導者](specialized/specialized-developer-advocate.md) | 社群建設、DX、開發者內容 | 銜接產品和開發者社群 |
| 🔌 [MCP 建構者](specialized/specialized-mcp-builder.md) | Model Context Protocol 伺服器、AI 代理工具 | 建構擴展 AI 代理能力的 MCP 伺服器 |
| 📄 [文件產生器](specialized/specialized-document-generator.md) | 從程式碼生成 PDF、PPTX、DOCX、XLSX | 專業文件建立、報告、資料視覺化 |

### 🎮 遊戲開發部門

跨越所有主流引擎建構世界、系統和體驗。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 🎯 [遊戲設計師](game-development/game-designer.md) | 系統設計、GDD 撰寫、經濟平衡 | 設計遊戲機制、進度系統、撰寫設計文件 |
| 🗺️ [關卡設計師](game-development/level-designer.md) | 佈局理論、節奏、遭遇設計 | 建構關卡、設計遭遇流程、空間敘事 |
| 🎨 [技術美術](game-development/technical-artist.md) | 著色器、VFX、LOD 管線 | 銜接美術和工程、著色器撰寫 |
| 🔊 [遊戲音訊工程師](game-development/game-audio-engineer.md) | FMOD/Wwise、自適應音樂、空間音訊 | 互動音訊系統、動態音樂 |
| 📖 [敘事設計師](game-development/narrative-designer.md) | 故事系統、分支對話、世界觀架構 | 撰寫分支敘事、實作對話系統 |

引擎特定代理人（Unity、Unreal Engine、Godot、Blender、Roblox Studio）請參閱[英文版 README](README.md)。

### 📚 學術部門

為世界建構、敘事和敘事設計帶來學術嚴謹性。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 🌍 [人類學家](academic/academic-anthropologist.md) | 文化系統、親屬關係、儀式 | 設計具內在邏輯的文化連貫社會 |
| 🌐 [地理學家](academic/academic-geographer.md) | 自然/人文地理、氣候、製圖 | 建構地理連貫的世界 |
| 📚 [歷史學家](academic/academic-historian.md) | 歷史分析、分期、物質文化 | 驗證歷史連貫性、豐富時代細節 |
| 📜 [敘事學家](academic/academic-narratologist.md) | 敘事理論、故事結構、角色弧線 | 用既有理論框架分析和改善故事結構 |
| 🧠 [心理學家](academic/academic-psychologist.md) | 人格理論、動機、認知模式 | 建構以研究為基礎的心理學可信角色 |

### 🛠️ 個人開發者部門

一人軍隊，從構想到上線。

| 代理人 | 專長 | 適用場景 |
|--------|------|----------|
| 🛠️ [全端個人開發者](solo-builder/solo-builder-fullstack.md) | 設計到部署的端到端開發 | 完整產品的獨立建構和運維 |
| 🚀 [MVP 發射器](solo-builder/solo-builder-mvp-launcher.md) | 最速 MVP 發布、假說驗證 | 72 小時內將想法推向真實用戶 |
| 💰 [營收最佳化器](solo-builder/solo-builder-revenue-optimizer.md) | 定價策略、轉換最佳化、營收增長 | 個人開發產品的變現和收益優化 |

---

## 🎯 實際使用案例

### 案例一：建構新創 MVP

**你的團隊**：
1. 🎨 **前端開發者** — 建構 React 應用
2. 🏗️ **後端架構師** — 設計 API 和資料庫
3. 🚀 **成長駭客** — 規劃用戶獲取
4. ⚡ **快速原型建構者** — 快速迭代循環
5. 🔍 **現實檢驗者** — 確保上線前的品質

**結果**：在每個階段都有專業知識，更快交付。

---

### 案例二：行銷活動啟動

**你的團隊**：
1. 📝 **內容創作者** — 開發活動內容
2. 🐦 **Twitter 互動者** — Twitter 策略與執行
3. 📸 **Instagram 策展人** — 視覺內容和限動
4. 🤝 **Reddit 社群建設者** — 真實社群互動
5. 📊 **分析報告者** — 追蹤與最佳化績效

**結果**：跨通路協調活動，每個平台都有專業知識。

---

## 🤝 貢獻

我們歡迎貢獻！以下是你可以幫助的方式：

### 新增代理人

1. Fork 此儲存庫
2. 在適當的類別中建立新的代理人檔案
3. 遵循代理人模板結構：
   - 含有 name、description、color 的前置資料
   - 身份與記憶章節
   - 核心任務
   - 關鍵規則（領域特定）
   - 技術成果與範例
   - 工作流程
   - 成功指標
4. 提交 PR

### 改善現有代理人

- 新增實際案例
- 增強程式碼範例
- 更新成功指標
- 改善工作流程

### 分享你的成功故事

你成功使用了這些代理人嗎？在[討論區](https://github.com/msitarzewski/agency-agents/discussions)分享你的故事！

---

## 🔌 多工具整合

The Agency 原生支援 Claude Code，並提供轉換和安裝腳本，讓你可以在所有主要的代理編碼工具中使用相同的代理人。

### 支援的工具

- **[Claude Code](https://claude.ai/code)** — 原生 `.md` 代理人，無需轉換 → `~/.claude/agents/`
- **[GitHub Copilot](https://github.com/copilot)** — 原生 `.md` 代理人，無需轉換 → `~/.github/agents/`
- **[Antigravity](https://github.com/google-gemini/antigravity)** — 每個代理人一個 `SKILL.md` → `~/.gemini/antigravity/skills/`
- **[Gemini CLI](https://github.com/google-gemini/gemini-cli)** — 擴展 + `SKILL.md` 檔案 → `~/.gemini/extensions/agency-agents/`
- **[OpenCode](https://opencode.ai)** — `.md` 代理人檔案 → `.opencode/agents/`
- **[Cursor](https://cursor.sh)** — `.mdc` 規則檔案 → `.cursor/rules/`
- **[Aider](https://aider.chat)** — 單一 `CONVENTIONS.md` → `./CONVENTIONS.md`
- **[Windsurf](https://codeium.com/windsurf)** — 單一 `.windsurfrules` → `./.windsurfrules`
- **[Avante.nvim](https://github.com/yetone/avante.nvim)** — Neovim 自訂提示 → `~/.config/nvim/prompts/agency/`
- **[Cognetivy](https://cognetivy.com)** — 角色定義 → Cognetivy 儀表板

詳細的安裝說明請參閱各工具的 [integrations/](integrations/) 目錄。

---

## 📜 授權

MIT 授權條款 — 免費用於商業或個人用途。感謝署名但不強制要求。

---

## 🙏 致謝

起初只是一則關於 AI 代理人專業化的 Reddit 貼文，如今已發展成令人驚嘆的成果 — **147 位代理人橫跨 12 個部門**，由來自世界各地的貢獻者社群支持。這個儲存庫中的每位代理人之所以存在，是因為有人用心撰寫、測試並分享。

感謝所有提交 PR、提出 Issue、發起討論，或只是嘗試了一位代理人並告訴我們效果如何的人 — 謝謝你們。因為你們，The Agency 才能不斷進步。

---

## 💬 社群

- **GitHub Discussions**：[分享你的成功故事](https://github.com/msitarzewski/agency-agents/discussions)
- **Issues**：[回報錯誤或功能請求](https://github.com/msitarzewski/agency-agents/issues)
- **Reddit**：加入 r/ClaudeAI 的對話
- **Twitter/X**：使用 #TheAgency 分享

---

## 🚀 開始使用

1. **瀏覽**上方的代理人，找到適合你需求的專家
2. **複製**代理人到 `~/.claude/agents/` 以整合 Claude Code
3. **啟用**代理人，在你的 Claude 對話中引用它們
4. **自訂**代理人個性和工作流程以符合你的特定需求
5. **分享**你的成果並回饋社群

---

<div align="center">

**🎭 The Agency：你的 AI 夢幻團隊在等你 🎭**

[⭐ 為此儲存庫加星](https://github.com/msitarzewski/agency-agents) | [🍴 Fork 它](https://github.com/msitarzewski/agency-agents/fork) | [🐛 回報問題](https://github.com/msitarzewski/agency-agents/issues) | [❤️ 贊助](https://github.com/sponsors/msitarzewski)

由社群為社群製作，滿懷熱情

</div>
