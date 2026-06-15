# 🎭 The Agency: KI-Spezialisten, die deinen Workflow transformieren

> **Eine komplette KI-Agentur griffbereit** – Von Frontend-Experten bis zu Reddit-Community-Ninjas, von Spaß-Injektoren bis zu Realitätsprüfern. Jeder Agent ist ein spezialisierter Experte mit Persönlichkeit, Prozessen und bewährten Ergebnissen.

[![GitHub stars](https://img.shields.io/github/stars/msitarzewski/agency-agents?style=social)](https://github.com/msitarzewski/agency-agents)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://makeapullrequest.com)
[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-pink?logo=github)](https://github.com/sponsors/msitarzewski)

---

## 🚀 Was ist das?

Entstanden aus einem Reddit-Thread und monatelanger Iteration ist **The Agency** eine wachsende Sammlung sorgfältig gestalteter KI-Agenten-Persönlichkeiten. Jeder Agent ist:

- **🎯 Spezialisiert**: Tiefgehendes Fachwissen in seinem Bereich (keine generischen Prompt-Vorlagen)
- **🧠 Persönlichkeitsgetrieben**: Einzigartige Stimme, Kommunikationsstil und Herangehensweise
- **📋 Ergebnisorientiert**: Echter Code, Prozesse und messbare Ergebnisse
- **✅ Produktionsreif**: Praxiserprobte Workflows und Erfolgsmetriken

**Stell es dir so vor**: Du stellst dein Traumteam zusammen, nur dass es KI-Spezialisten sind, die nie schlafen, sich nie beschweren und immer liefern.

---

## ⚡ Schnellstart

### Option 1: Verwendung mit Claude Code (Empfohlen)

```bash
# Alle Agenten in dein Claude Code-Verzeichnis installieren
./scripts/install.sh --tool claude-code

# Oder manuell eine Kategorie kopieren, wenn du nur eine Abteilung brauchst
cp engineering/*.md ~/.claude/agents/

# Dann einen beliebigen Agenten in deinen Claude Code-Sitzungen aktivieren:
# "Hey Claude, aktiviere den Frontend Developer-Modus und hilf mir, eine React-Komponente zu bauen"
```

### Option 2: Als Referenz verwenden

Jede Agentendatei enthält:
- Identität & Persönlichkeitsmerkmale
- Kernmission & Workflows
- Technische Ergebnisse mit Codebeispielen
- Erfolgsmetriken & Kommunikationsstil

Durchsuche die Agenten unten und kopiere/adaptiere die, die du brauchst!

### Option 3: Verwendung mit anderen Tools (GitHub Copilot, Antigravity, Gemini CLI, OpenCode, OpenClaw, Cursor, Aider, Windsurf, Kimi Code, Codex)

```bash
# Schritt 1 -- Integrationsdateien für alle unterstützten Tools generieren
./scripts/convert.sh

# Schritt 2 -- Interaktiv installieren (erkennt automatisch, was installiert ist)
./scripts/install.sh

# Oder ein bestimmtes Tool direkt ansprechen
./scripts/install.sh --tool antigravity
./scripts/install.sh --tool gemini-cli
./scripts/install.sh --tool opencode
./scripts/install.sh --tool copilot
./scripts/install.sh --tool openclaw
./scripts/install.sh --tool cursor
./scripts/install.sh --tool aider
./scripts/install.sh --tool windsurf
./scripts/install.sh --tool kimi
./scripts/install.sh --tool codex
```

**Nur die Teams installieren, die du brauchst** (nicht jeder braucht alle 16 Abteilungen):

```bash
./scripts/install.sh                                    # Interaktiver Assistent: Tools + Teams auswählen
./scripts/install.sh --tool claude-code --division engineering,security
./scripts/install.sh --tool cursor --agent frontend-developer,ui-designer
./scripts/install.sh --list teams                       # Alle Teams + Agentenanzahl anzeigen
./scripts/install.sh --tool opencode --division engineering --dry-run
```

> **OpenCode-Hinweis:** OpenCodes Runtime registriert derzeit nur ca. 119 Agenten und verwirft den Rest stillschweigend ([Upstream-Bug](https://github.com/anomalyco/opencode/issues/27988)). Die Installation einer Teilmenge mit `--division` hält dich unter diesem Limit. Der Installer warnt dich, wenn eine Auswahl es überschreiten würde.

Siehe den Abschnitt [Multi-Tool-Integrationen](#-multi-tool-integrationen) unten für alle Details.

---

## 🎨 Das Agency-Aufgebot

### 💻 Engineering-Abteilung

Die Zukunft bauen, Commit für Commit.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🎨 [Frontend Developer](engineering/engineering-frontend-developer.md) | React/Vue/Angular, UI-Implementierung, Performance | Moderne Web-Apps, pixelgenaue UIs, Core Web Vitals-Optimierung |
| 🏗️ [Backend Architect](engineering/engineering-backend-architect.md) | API-Design, Datenbankarchitektur, Skalierbarkeit | Serverseitige Systeme, Microservices, Cloud-Infrastruktur |
| 📱 [Mobile App Builder](engineering/engineering-mobile-app-builder.md) | iOS/Android, React Native, Flutter | Native und plattformübergreifende mobile Anwendungen |
| 🤖 [AI Engineer](engineering/engineering-ai-engineer.md) | ML-Modelle, Deployment, KI-Integration | Machine-Learning-Features, Datenpipelines, KI-gestützte Apps |
| 🚀 [DevOps Automator](engineering/engineering-devops-automator.md) | CI/CD, Infrastruktur-Automatisierung, Cloud-Ops | Pipeline-Entwicklung, Deployment-Automatisierung, Monitoring |
| ⚡ [Rapid Prototyper](engineering/engineering-rapid-prototyper.md) | Schnelle POC-Entwicklung, MVPs | Schnelle Proof-of-Concepts, Hackathon-Projekte, schnelle Iteration |
| 💎 [Senior Developer](engineering/engineering-senior-developer.md) | Laravel/Livewire, fortgeschrittene Patterns | Komplexe Implementierungen, Architekturentscheidungen |
| 🔧 [Filament Optimization Specialist](engineering/engineering-filament-optimization-specialist.md) | Filament PHP Admin-UX, strukturelles Form-Redesign, Ressourcenoptimierung | Umstrukturierung von Filament-Ressourcen/Formularen/Tabellen für schnellere, sauberere Admin-Workflows |
| ⚡ [Autonomous Optimization Architect](engineering/engineering-autonomous-optimization-architect.md) | LLM-Routing, Kostenoptimierung, Shadow-Testing | Autonome Systeme mit intelligentem API-Routing und Kostenlimits |
| 🔩 [Embedded Firmware Engineer](engineering/engineering-embedded-firmware-engineer.md) | Bare-Metal, RTOS, ESP32/STM32/Nordic Firmware | Produktionsreife eingebettete Systeme und IoT-Geräte |
| 🚨 [Incident Response Commander](engineering/engineering-incident-response-commander.md) | Incident Management, Post-Mortems, Bereitschaft | Verwaltung von Produktionsvorfällen und Aufbau von Incident-Readiness |
| ⛓️ [Solidity Smart Contract Engineer](engineering/engineering-solidity-smart-contract-engineer.md) | EVM-Verträge, Gas-Optimierung, DeFi | Sichere, gasoptimierte Smart Contracts und DeFi-Protokolle |
| 🧭 [Codebase Onboarding Engineer](engineering/engineering-codebase-onboarding-engineer.md) | Schnelles Entwickler-Onboarding, Codebase-Exploration (nur lesen), sachliche Erklärung | Neuen Entwicklern helfen, unbekannte Repos schnell zu verstehen |
| 📚 [Technical Writer](engineering/engineering-technical-writer.md) | Entwicklerdokumentation, API-Referenz, Tutorials | Klare, präzise technische Dokumentation |
| 💬 [WeChat Mini Program Developer](engineering/engineering-wechat-mini-program-developer.md) | WeChat-Ökosystem, Mini Programs, Zahlungsintegration | Performante Apps für das WeChat-Ökosystem |
| 👁️ [Code Reviewer](engineering/engineering-code-reviewer.md) | Konstruktives Code-Review, Sicherheit, Wartbarkeit | PR-Reviews, Code-Quality-Gates, Mentoring durch Review |
| 🗄️ [Database Optimizer](engineering/engineering-database-optimizer.md) | Schema-Design, Query-Optimierung, Indexierungsstrategien | PostgreSQL/MySQL-Tuning, langsame Queries debuggen, Migrationsplanung |
| 🌿 [Git Workflow Master](engineering/engineering-git-workflow-master.md) | Branching-Strategien, Conventional Commits, fortgeschrittenes Git | Git-Workflow-Design, History-Bereinigung, CI-freundliches Branch-Management |
| 🏛️ [Software Architect](engineering/engineering-software-architect.md) | Systemdesign, DDD, Architektur-Patterns, Trade-off-Analyse | Architekturentscheidungen, Domain-Modellierung, System-Evolutionsstrategie |
| 🛡️ [SRE](engineering/engineering-sre.md) | SLOs, Error Budgets, Observability, Chaos Engineering | Produktionszuverlässigkeit, Toil-Reduktion, Kapazitätsplanung |
| 🧬 [AI Data Remediation Engineer](engineering/engineering-ai-data-remediation-engineer.md) | Self-Healing-Pipelines, Air-Gapped SLMs, semantisches Clustering | Defekte Daten im großen Maßstab reparieren, ohne Datenverlust |
| 🔧 [Data Engineer](engineering/engineering-data-engineer.md) | Datenpipelines, Lakehouse-Architektur, ETL/ELT | Zuverlässige Dateninfrastruktur und Warehousing aufbauen |
| 🔗 [Feishu Integration Developer](engineering/engineering-feishu-integration-developer.md) | Feishu/Lark Open Platform, Bots, Workflows | Integrationen für das Feishu-Ökosystem bauen |
| 🧱 [CMS Developer](engineering/engineering-cms-developer.md) | WordPress & Drupal Themes, Plugins/Module, Content-Architektur | Code-First CMS-Implementierung und -Anpassung |
| 📧 [Email Intelligence Engineer](engineering/engineering-email-intelligence-engineer.md) | E-Mail-Parsing, MIME-Extraktion, strukturierte Daten für KI-Agenten | Rohe E-Mail-Threads in reasoning-fähigen Kontext umwandeln |
| 🎙️ [Voice AI Integration Engineer](engineering/engineering-voice-ai-integration-engineer.md) | Speech-to-Text-Pipelines, Whisper, ASR, Sprecherdiarisierung | End-to-End-Transkriptionspipelines, Audio-Vorverarbeitung |
| 🖧 [IT Service Manager](engineering/engineering-it-service-manager.md) | ITIL 4 Service Management | Incident/Problem/Change Management, SLAs, CMDB |
| 🪡 [Minimal Change Engineer](engineering/engineering-minimal-change-engineer.md) | Minimale Diffs | Nur das reparieren, was gefragt ist, kein Scope Creep |
| 📜 [OrgScript Engineer](engineering/engineering-orgscript-engineer.md) | OrgScript-Grammatik & AST-Validierung | OrgScript-Geschäftslogik-Definitionen entwerfen/parsen |
| 🧬 [Prompt Engineer](engineering/engineering-prompt-engineer.md) | LLM-Prompt-Design & -Optimierung | Vage Anweisungen in zuverlässiges KI-Verhalten umwandeln |
| 🕸️ [Multi-Agent Systems Architect](engineering/engineering-multi-agent-systems-architect.md) | Multi-Agent-Pipeline-Design & Governance | Topologie, Kontext, Vertrauen, Fehlerbehandlung für Agentensysteme |
| 🛒 [Drupal Shopping Cart Engineer](engineering/engineering-drupal-shopping-cart.md) | Drupal Commerce Storefronts | Katalog, Zahlungen, Checkout, Bestellungen auf Drupal 10/11 |
| 🛍️ [WordPress Shopping Cart Engineer](engineering/engineering-wordpress-shopping-cart.md) | WooCommerce Storefronts | Katalog, Zahlungen, Checkout, Conversion auf WordPress |

### 🎨 Design-Abteilung

Schön, nutzbar und begeisternd gestalten.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🎯 [UI Designer](design/design-ui-designer.md) | Visuelles Design, Komponentenbibliotheken, Design-Systeme | Interface-Erstellung, Markenkonsistenz, Komponentendesign |
| 🔍 [UX Researcher](design/design-ux-researcher.md) | Benutzertests, Verhaltensanalyse, Forschung | Benutzer verstehen, Usability-Tests, Design-Insights |
| 🏛️ [UX Architect](design/design-ux-architect.md) | Technische Architektur, CSS-Systeme, Implementierung | Entwicklerfreundliche Grundlagen, Implementierungsbegleitung |
| 🎭 [Brand Guardian](design/design-brand-guardian.md) | Markenidentität, Konsistenz, Positionierung | Markenstrategie, Identitätsentwicklung, Richtlinien |
| 📖 [Visual Storyteller](design/design-visual-storyteller.md) | Visuelle Erzählungen, Multimedia-Inhalte | Überzeugende visuelle Geschichten, Marken-Storytelling |
| ✨ [Whimsy Injector](design/design-whimsy-injector.md) | Persönlichkeit, Begeisterung, spielerische Interaktionen | Freude hinzufügen, Mikro-Interaktionen, Easter Eggs, Markenpersönlichkeit |
| 📷 [Image Prompt Engineer](design/design-image-prompt-engineer.md) | KI-Bildgenerierungs-Prompts, Fotografie | Fotografie-Prompts für Midjourney, DALL-E, Stable Diffusion |
| 🌈 [Inclusive Visuals Specialist](design/design-inclusive-visuals-specialist.md) | Repräsentation, Bias-Minderung, authentische Bilder | Kulturell korrekte KI-Bilder und Videos generieren |
| 🎭 [Persona Walkthrough Specialist](design/design-persona-walkthrough.md) | Persona-gesteuerte kognitive Walkthroughs | Benutzerreaktionen und Reibungspunkte an jeder Scroll-Position simulieren |

### 💰 Paid-Media-Abteilung

Werbebudget in messbare Geschäftsergebnisse umwandeln.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 💰 [PPC Campaign Strategist](paid-media/paid-media-ppc-strategist.md) | Google/Microsoft/Amazon Ads, Kontoarchitektur, Gebotsstrategien | Kontoaufbau, Budgetverteilung, Skalierung, Performance-Diagnose |
| 🔍 [Search Query Analyst](paid-media/paid-media-search-query-analyst.md) | Suchbegriffsanalyse, negative Keywords, Intent-Mapping | Query-Audits, Streuverluste eliminieren, Keyword-Discovery |
| 📋 [Paid Media Auditor](paid-media/paid-media-auditor.md) | 200+ Punkte Konto-Audits, Wettbewerbsanalyse | Kontoübernahmen, Quartalsreviews, Wettbewerbs-Pitches |
| 📡 [Tracking & Measurement Specialist](paid-media/paid-media-tracking-specialist.md) | GTM, GA4, Conversion-Tracking, CAPI | Neuimplementierungen, Tracking-Audits, Plattformmigrationen |
| ✍️ [Ad Creative Strategist](paid-media/paid-media-creative-strategist.md) | RSA-Texte, Meta Creative, Performance Max Assets | Creative-Launches, Testprogramme, Anzeigen-Fatigue-Refreshes |
| 📺 [Programmatic & Display Buyer](paid-media/paid-media-programmatic-buyer.md) | GDN, DSPs, Partner-Media, ABM Display | Display-Planung, Partner-Outreach, ABM-Programme |
| 📱 [Paid Social Strategist](paid-media/paid-media-paid-social-strategist.md) | Meta, LinkedIn, TikTok, plattformübergreifend | Social-Ad-Programme, Plattformauswahl, Zielgruppenstrategie |

### 💼 Vertriebsabteilung

Pipeline in Umsatz verwandeln durch Handwerk, nicht CRM-Fleißarbeit.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🎯 [Outbound Strategist](sales/sales-outbound-strategist.md) | Signalbasierte Akquise, Multi-Channel-Sequenzen, ICP-Targeting | Pipeline durch recherchegetriebene Ansprache aufbauen |
| 🔍 [Discovery Coach](sales/sales-discovery-coach.md) | SPIN, Gap Selling, Sandler — Fragendesign und Gesprächsstruktur | Vorbereitung auf Discovery-Calls, Opportunity-Qualifizierung |
| ♟️ [Deal Strategist](sales/sales-deal-strategist.md) | MEDDPICC-Qualifizierung, Wettbewerbspositionierung, Win-Planung | Deals bewerten, Pipeline-Risiken aufdecken, Gewinnstrategien |
| 🛠️ [Sales Engineer](sales/sales-engineer.md) | Technische Demos, POC-Scoping, Wettbewerbs-Battlecards | Pre-Sales technische Erfolge, Demo-Vorbereitung |
| 🏹 [Proposal Strategist](sales/sales-proposal-strategist.md) | RFP-Response, Win-Themes, narrative Struktur | Angebote schreiben, die überzeugen, nicht nur erfüllen |
| 📊 [Pipeline Analyst](sales/sales-pipeline-analyst.md) | Forecasting, Pipeline-Health, Deal-Velocity, RevOps | Pipeline-Reviews, Forecast-Genauigkeit, Revenue Operations |
| 🗺️ [Account Strategist](sales/sales-account-strategist.md) | Land-and-Expand, QBRs, Stakeholder-Mapping | Post-Sale-Expansion, Kontoplanung, NRR-Wachstum |
| 🏋️ [Sales Coach](sales/sales-coach.md) | Rep-Entwicklung, Call-Coaching, Pipeline-Review-Moderation | Jeden Rep und jeden Deal durch strukturiertes Coaching verbessern |
| 🎯 [Sales Outreach](specialized/sales-outreach.md) | Cold Prospecting, Multi-Touch-Kadenz, Einwandbehandlung | Top-of-Funnel B2B-Outreach — von Cold-E-Mail bis zum gebuchten Discovery-Call |
| 🧲 [Offer & Lead Gen Strategist](sales/sales-offer-lead-gen-strategist.md) | Angebote & Lead-Magneten | Top-of-Funnel-Angebotsgestaltung und Lead-Generierung |

### 📢 Marketing-Abteilung

Deine Zielgruppe vergrößern, eine authentische Interaktion nach der anderen.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🚀 [Growth Hacker](marketing/marketing-growth-hacker.md) | Schnelle Nutzerakquise, virale Loops, Experimente | Explosives Wachstum, Nutzerakquise, Conversion-Optimierung |
| 📝 [Content Creator](marketing/marketing-content-creator.md) | Multi-Plattform-Content, Redaktionskalender | Content-Strategie, Copywriting, Marken-Storytelling |
| 🐦 [Twitter Engager](marketing/marketing-twitter-engager.md) | Echtzeit-Engagement, Thought Leadership | Twitter-Strategie, LinkedIn-Kampagnen, professionelles Social |
| 🛰️ [X/Twitter Intelligence Analyst](marketing/marketing-x-twitter-intelligence-analyst.md) | Social Listening, Trend-Erkennung, Account-Monitoring | Markenrisiko-, Wettbewerbs- und Zielgruppen-Intelligence auf X/Twitter |
| 📱 [TikTok Strategist](marketing/marketing-tiktok-strategist.md) | Viraler Content, Algorithmus-Optimierung | TikTok-Wachstum, viraler Content, Gen Z/Millennial-Zielgruppe |
| 📸 [Instagram Curator](marketing/marketing-instagram-curator.md) | Visuelles Storytelling, Community-Building | Instagram-Strategie, Ästhetik-Entwicklung, visuelle Inhalte |
| 🤝 [Reddit Community Builder](marketing/marketing-reddit-community-builder.md) | Authentisches Engagement, wertorientierter Content | Reddit-Strategie, Community-Vertrauen, authentisches Marketing |
| 📱 [App Store Optimizer](marketing/marketing-app-store-optimizer.md) | ASO, Conversion-Optimierung, Auffindbarkeit | App-Marketing, Store-Optimierung, App-Wachstum |
| 🌐 [Social Media Strategist](marketing/marketing-social-media-strategist.md) | Plattformübergreifende Strategie, Kampagnen | Gesamtstrategie Social Media, Multi-Plattform-Kampagnen |
| 📕 [Xiaohongshu Specialist](marketing/marketing-xiaohongshu-specialist.md) | Lifestyle-Content, trendgesteuerte Strategie | Xiaohongshu-Wachstum, ästhetisches Storytelling, Gen Z |
| 💬 [WeChat Official Account Manager](marketing/marketing-wechat-official-account.md) | Abonnenten-Engagement, Content-Marketing | WeChat-OA-Strategie, Community-Building, Conversion-Optimierung |
| 🧠 [Zhihu Strategist](marketing/marketing-zhihu-strategist.md) | Thought Leadership, wissensgetriebenes Engagement | Zhihu-Autorität aufbauen, Q&A-Strategie, Lead-Generierung |
| 🇨🇳 [Baidu SEO Specialist](marketing/marketing-baidu-seo-specialist.md) | Baidu-Optimierung, China-SEO, ICP-Compliance | Ranking bei Baidu und Chinas Suchmarkt erreichen |
| 🎬 [Bilibili Content Strategist](marketing/marketing-bilibili-content-strategist.md) | B站-Algorithmus, Danmaku-Kultur, UP主-Wachstum | Zielgruppen auf Bilibili mit Community-First-Content aufbauen |
| 🎠 [Carousel Growth Engine](marketing/marketing-carousel-growth-engine.md) | TikTok/Instagram-Karussells, autonomes Publizieren | Viralen Karussell-Content generieren und veröffentlichen |
| 💼 [LinkedIn Content Creator](marketing/marketing-linkedin-content-creator.md) | Personal Branding, Thought Leadership, professioneller Content | LinkedIn-Wachstum, professioneller Zielgruppenaufbau, B2B-Content |
| 🛒 [China E-Commerce Operator](marketing/marketing-china-ecommerce-operator.md) | Taobao, Tmall, Pinduoduo, Live Commerce | Multi-Plattform-E-Commerce in China betreiben |
| 🎥 [Kuaishou Strategist](marketing/marketing-kuaishou-strategist.md) | Kuaishou, 老铁-Community, Grassroots-Wachstum | Authentische Zielgruppen in kleineren Märkten aufbauen |
| 🔍 [SEO Specialist](marketing/marketing-seo-specialist.md) | Technisches SEO, Content-Strategie, Linkbuilding | Nachhaltiges organisches Suchmaschinen-Wachstum |
| 📘 [Book Co-Author](marketing/marketing-book-co-author.md) | Thought-Leadership-Bücher, Ghostwriting, Verlagswesen | Strategische Buchzusammenarbeit für Gründer und Experten |
| 🌏 [Cross-Border E-Commerce Specialist](marketing/marketing-cross-border-ecommerce.md) | Amazon, Shopee, Lazada, grenzüberschreitende Fulfillment | Full-Funnel Cross-Border E-Commerce-Strategie |
| 🎵 [Douyin Strategist](marketing/marketing-douyin-strategist.md) | Douyin-Plattform, Kurzvideo-Marketing, Algorithmus | Zielgruppen auf Chinas führender Kurzvideo-Plattform aufbauen |
| 🎙️ [Livestream Commerce Coach](marketing/marketing-livestream-commerce-coach.md) | Host-Training, Live-Room-Optimierung, Conversion | Leistungsstarke Livestream-E-Commerce-Operationen aufbauen |
| 🎧 [Podcast Strategist](marketing/marketing-podcast-strategist.md) | Podcast-Content-Strategie, Plattform-Optimierung | Chinesische Podcast-Markt-Strategie und -Betrieb |
| 🔒 [Private Domain Operator](marketing/marketing-private-domain-operator.md) | WeCom, Private Traffic, Community Operations | Enterprise WeChat Private-Domain-Ökosysteme aufbauen |
| 🎬 [Short-Video Editing Coach](marketing/marketing-short-video-editing-coach.md) | Post-Produktion, Editing-Workflows, Plattform-Specs | Praxisnahes Kurzvideo-Editing-Training und Optimierung |
| 🔥 [Weibo Strategist](marketing/marketing-weibo-strategist.md) | Sina Weibo, Trending Topics, Fan-Engagement | Full-Spectrum Weibo-Betrieb und Wachstum |
| 🎙️ [Global Podcast Strategist](marketing/marketing-global-podcast-strategist.md) | Show-Positionierung, Zielgruppen-Wachstum, Monetarisierung | Podcast-Launch, Plattform-Algorithmen, Sponsoring, Community-Building |
| 🔮 [AI Citation Strategist](marketing/marketing-ai-citation-strategist.md) | AEO/GEO, KI-Empfehlungssichtbarkeit, Zitationsauditing | Markensichtbarkeit in ChatGPT, Claude, Gemini, Perplexity verbessern |
| 🇨🇳 [China Market Localization Strategist](marketing/marketing-china-market-localization-strategist.md) | Full-Stack China-Markt-Lokalisierung, Douyin/Xiaohongshu/WeChat GTM | Trend-Signale in umsetzbare China Go-to-Market-Strategien verwandeln |
| 🎬 [Video Optimization Specialist](marketing/marketing-video-optimization-specialist.md) | YouTube-Algorithmus-Strategie, Kapitel, Thumbnail-Konzepte | YouTube-Kanal-Wachstum, Video-SEO, Zuschauerbindungsoptimierung |
| 🏗️ [AEO Foundations Architect](marketing/marketing-aeo-foundations.md) | AI Engine Optimization-Infrastruktur | llms.txt, KI-fähige robots.txt, Agent-Discovery-Dateien |
| 🤖 [Agentic Search Optimizer](marketing/marketing-agentic-search-optimizer.md) | WebMCP & agentic Task-Completion | Websites für KI-Browsing-Agenten nutzbar machen |
| 📧 [Email Marketing Strategist](marketing/marketing-email-strategist.md) | Lifecycle-E-Mail & Zustellbarkeit | CRM-Kampagnen, Automatisierung, Segmentierung |
| 📡 [Multi-Platform Publisher](marketing/marketing-multi-platform-publisher.md) | Ein-Klick chinesisches Multi-Plattform-Publishing | Einen Artikel an 知乎/小红书/CSDN/B站/公众号/掘金 verteilen |
| 📣 [PR & Communications Manager](marketing/marketing-pr-communications-manager.md) | PR, Medienarbeit & Krisenkommunikation | Pressemitteilungen, Thought Leadership, Reputation |

### 📊 Produkt-Abteilung

Das Richtige zum richtigen Zeitpunkt bauen.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🎯 [Sprint Prioritizer](product/product-sprint-prioritizer.md) | Agile Planung, Feature-Priorisierung | Sprint-Planung, Ressourcenallokation, Backlog-Management |
| 🔍 [Trend Researcher](product/product-trend-researcher.md) | Marktintelligenz, Wettbewerbsanalyse | Marktforschung, Chancenbewertung, Trend-Identifikation |
| 💬 [Feedback Synthesizer](product/product-feedback-synthesizer.md) | Nutzerfeedback-Analyse, Insight-Extraktion | Feedback-Analyse, Nutzer-Insights, Produktprioritäten |
| 🧠 [Behavioral Nudge Engine](product/product-behavioral-nudge-engine.md) | Verhaltenspsychologie, Nudge-Design, Engagement | Nutzermotivation durch Verhaltenswissenschaft maximieren |
| 🧭 [Product Manager](product/product-manager.md) | Full-Lifecycle Product Ownership | Discovery, PRDs, Roadmap-Planung, GTM, Ergebnismessung |

### 🎬 Projektmanagement-Abteilung

Die Züge pünktlich (und im Budget) am Laufen halten.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🎬 [Studio Producer](project-management/project-management-studio-producer.md) | High-Level-Orchestrierung, Portfolio-Management | Multi-Projekt-Übersicht, strategische Ausrichtung, Ressourcenallokation |
| 🐑 [Project Shepherd](project-management/project-management-project-shepherd.md) | Bereichsübergreifende Koordination, Zeitplanung | End-to-End-Projektkoordination, Stakeholder-Management |
| ⚙️ [Studio Operations](project-management/project-management-studio-operations.md) | Tägliche Effizienz, Prozessoptimierung | Operationale Exzellenz, Team-Support, Produktivität |
| 🧪 [Experiment Tracker](project-management/project-management-experiment-tracker.md) | A/B-Tests, Hypothesenvalidierung | Experimentmanagement, datengetriebene Entscheidungen |
| 👔 [Senior Project Manager](project-management/project-manager-senior.md) | Realistische Scoping, Aufgabenkonvertierung | Spezifikationen in Aufgaben umwandeln, Scope-Management |
| 📋 [Jira Workflow Steward](project-management/project-management-jira-workflow-steward.md) | Git-Workflow, Branch-Strategie, Nachverfolgbarkeit | Jira-verknüpfte Git-Disziplin und Lieferung durchsetzen |
| 📋 [Meeting Notes Specialist](project-management/project-management-meeting-notes-specialist.md) | Strukturierte Meeting-Zusammenfassungen | Entscheidungen, Aufgaben, offene Fragen extrahieren |

### 🧪 Test-Abteilung

Dinge kaputt machen, damit es die Nutzer nicht müssen.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 📸 [Evidence Collector](testing/testing-evidence-collector.md) | Screenshot-basiertes QA, visueller Beweis | UI-Testing, visuelle Verifikation, Bug-Dokumentation |
| 🔍 [Reality Checker](testing/testing-reality-checker.md) | Evidenzbasierte Zertifizierung, Quality Gates | Produktionsbereitschaft, Qualitätsfreigabe, Release-Zertifizierung |
| 📊 [Test Results Analyzer](testing/testing-test-results-analyzer.md) | Testauswertung, Metrik-Analyse | Testausgabe-Analyse, Qualitäts-Insights, Coverage-Reporting |
| ⚡ [Performance Benchmarker](testing/testing-performance-benchmarker.md) | Performance-Testing, Optimierung | Geschwindigkeitstests, Lasttests, Performance-Tuning |
| 🔌 [API Tester](testing/testing-api-tester.md) | API-Validierung, Integrationstests | API-Testing, Endpoint-Verifikation, Integrations-QA |
| 🛠️ [Tool Evaluator](testing/testing-tool-evaluator.md) | Technologiebewertung, Tool-Auswahl | Tools evaluieren, Software-Empfehlungen, Tech-Entscheidungen |
| 🔄 [Workflow Optimizer](testing/testing-workflow-optimizer.md) | Prozessanalyse, Workflow-Verbesserung | Prozessoptimierung, Effizienzgewinne, Automatisierungsmöglichkeiten |
| ♿ [Accessibility Auditor](testing/testing-accessibility-auditor.md) | WCAG-Auditing, Assistive-Technology-Testing | Barrierefreiheits-Compliance, Screenreader-Tests, inklusives Design |

### 🔒 Sicherheitsabteilung

Den Stack verteidigen — von Secure-by-Design-Architektur bis zur Breach-Response.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🛡️ [Security Architect](security/security-architect.md) | Bedrohungsmodellierung, Secure-by-Design, Trust Boundaries | System-Sicherheitsmodelle, Architektur-Reviews, Defense-in-Depth |
| 🔐 [Application Security Engineer](security/security-appsec-engineer.md) | SDLC-Sicherheit, SAST/DAST, sicheres Code-Review | Entwicklungslebenszyklus absichern, Code-Level-Schwachstellen |
| 🗡️ [Penetration Tester](security/security-penetration-tester.md) | Autorisierte Pentests, Red-Team-Ops, Exploitation | Ausnutzbare Schwachstellen finden, bevor es Angreifer tun |
| ☁️ [Cloud Security Architect](security/security-cloud-security-architect.md) | Zero Trust, Cloud-native Defense-in-Depth | Cloud-Infrastruktur und -Architekturen absichern |
| 🚨 [Incident Responder](security/security-incident-responder.md) | DFIR, Breach-Untersuchung, Bedrohungseindämmung | Aktive Breaches, Forensik, Krisenreaktion |
| 🔍 [Threat Intelligence Analyst](security/security-threat-intelligence-analyst.md) | Adversary Tracking, Campaign Mapping, ATT&CK | Verstehen, wer angreift und wie |
| 🎯 [Threat Detection Engineer](security/security-threat-detection-engineer.md) | SIEM-Regeln, Threat Hunting, ATT&CK-Mapping | Detection-Layer aufbauen und Threat Hunting |
| 🛡️ [Senior SecOps Engineer](security/security-senior-secops.md) | Secrets-Scanning, Secure-by-Default-Einreichungen | Defensive Code-Level-Sicherheit bei jeder Änderung |
| 📋 [Compliance Auditor](security/security-compliance-auditor.md) | SOC 2, ISO 27001, HIPAA, PCI-DSS | Organisationen durch Compliance-Zertifizierung begleiten |
| 🛡️ [Blockchain Security Auditor](security/security-blockchain-security-auditor.md) | Smart-Contract-Audits, Exploit-Analyse | Schwachstellen in Verträgen vor dem Deployment finden |

### 🛟 Support-Abteilung

Das Rückgrat des Betriebs.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 💬 [Support Responder](support/support-support-responder.md) | Kundenservice, Problemlösung | Kundensupport, Nutzererfahrung, Support-Betrieb |
| 📊 [Analytics Reporter](support/support-analytics-reporter.md) | Datenanalyse, Dashboards, Insights | Business Intelligence, KPI-Tracking, Datenvisualisierung |
| 💰 [Finance Tracker](support/support-finance-tracker.md) | Finanzplanung, Budgetmanagement | Finanzanalyse, Cashflow, Geschäftsperformance |
| 🏗️ [Infrastructure Maintainer](support/support-infrastructure-maintainer.md) | Systemzuverlässigkeit, Performance-Optimierung | Infrastrukturmanagement, Systembetrieb, Monitoring |
| ⚖️ [Legal Compliance Checker](support/support-legal-compliance-checker.md) | Compliance, Vorschriften, rechtliche Prüfung | Rechtskonformität, regulatorische Anforderungen, Risikomanagement |
| 📑 [Executive Summary Generator](support/support-executive-summary-generator.md) | C-Suite-Kommunikation, strategische Zusammenfassungen | Executive-Reporting, strategische Kommunikation, Entscheidungsunterstützung |

### 🥽 Spatial-Computing-Abteilung

Die immersive Zukunft bauen.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🏗️ [XR Interface Architect](spatial-computing/xr-interface-architect.md) | Spatial Interaction Design, immersive UX | AR/VR/XR-Interface-Design, Spatial Computing UX |
| 💻 [macOS Spatial/Metal Engineer](spatial-computing/macos-spatial-metal-engineer.md) | Swift, Metal, High-Performance 3D | macOS Spatial Computing, Vision Pro native Apps |
| 🌐 [XR Immersive Developer](spatial-computing/xr-immersive-developer.md) | WebXR, browserbasiertes AR/VR | Browserbasierte immersive Erlebnisse, WebXR-Apps |
| 🎮 [XR Cockpit Interaction Specialist](spatial-computing/xr-cockpit-interaction-specialist.md) | Cockpit-basierte Steuerung, immersive Systeme | Cockpit-Steuerungssysteme, immersive Kontrollinterfaces |
| 🍎 [visionOS Spatial Engineer](spatial-computing/visionos-spatial-engineer.md) | Apple Vision Pro-Entwicklung | Vision Pro-Apps, Spatial-Computing-Erlebnisse |
| 🔌 [Terminal Integration Specialist](spatial-computing/terminal-integration-specialist.md) | Terminal-Integration, Kommandozeilen-Tools | CLI-Tools, Terminal-Workflows, Entwickler-Tools |

### 🎯 Spezialisten-Abteilung

Die einzigartigen Spezialisten, die in keine Schublade passen.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🎭 [Agents Orchestrator](specialized/agents-orchestrator.md) | Multi-Agent-Koordination, Workflow-Management | Komplexe Projekte mit mehreren Agenten |
| 🔍 [LSP/Index Engineer](specialized/lsp-index-engineer.md) | Language Server Protocol, Code-Intelligence | Code-Intelligence-Systeme, LSP-Implementierung |
| 📥 [Sales Data Extraction Agent](specialized/sales-data-extraction-agent.md) | Excel-Monitoring, Vertriebsmetrik-Extraktion | Vertriebsdaten-Ingestion, MTD/YTD/Jahresend-Metriken |
| 📈 [Data Consolidation Agent](specialized/data-consolidation-agent.md) | Vertriebsdaten-Aggregation, Dashboard-Reports | Gebiets-Zusammenfassungen, Rep-Performance, Pipeline-Snapshots |
| 📬 [Report Distribution Agent](specialized/report-distribution-agent.md) | Automatisierte Berichtsverteilung | Gebietsbasierte Berichtsverteilung, geplanter Versand |
| 🔐 [Agentic Identity & Trust Architect](specialized/agentic-identity-trust.md) | Agent-Identität, Authentifizierung, Vertrauensverifizierung | Multi-Agent-Identitätssysteme, Agent-Autorisierung |
| 🔗 [Identity Graph Operator](specialized/identity-graph-operator.md) | Geteilte Identitätsauflösung für Multi-Agent-Systeme | Entity-Deduplizierung, Merge-Vorschläge |
| 💸 [Accounts Payable Agent](specialized/accounts-payable-agent.md) | Zahlungsabwicklung, Lieferantenmanagement, Audit | Autonome Zahlungsausführung über Crypto, Fiat, Stablecoins |
| 🌍 [Cultural Intelligence Strategist](specialized/specialized-cultural-intelligence-strategist.md) | Globale UX, Repräsentation, kulturelle Exklusion | Software für verschiedene Kulturen optimieren |
| 🗣️ [Developer Advocate](specialized/specialized-developer-advocate.md) | Community-Building, DX, Entwickler-Content | Brücke zwischen Produkt und Entwickler-Community |
| 🔬 [Model QA Specialist](specialized/specialized-model-qa.md) | ML-Audits, Feature-Analyse, Interpretierbarkeit | End-to-End-QA für Machine-Learning-Modelle |
| 🗃️ [ZK Steward](specialized/zk-steward.md) | Wissensmanagement, Zettelkasten, Notizen | Vernetzte, validierte Wissensdatenbanken aufbauen |
| 🔌 [MCP Builder](specialized/specialized-mcp-builder.md) | Model Context Protocol-Server, KI-Agent-Tooling | MCP-Server bauen, die KI-Agent-Fähigkeiten erweitern |
| 📄 [Document Generator](specialized/specialized-document-generator.md) | PDF, PPTX, DOCX, XLSX-Generierung aus Code | Professionelle Dokumentenerstellung, Berichte |
| ⚙️ [Automation Governance Architect](specialized/automation-governance-architect.md) | Automatisierungs-Governance, n8n, Workflow-Auditing | Geschäftsautomatisierungen im großen Maßstab bewerten |
| 📚 [Corporate Training Designer](specialized/corporate-training-designer.md) | Enterprise-Training, Lehrplanentwicklung | Schulungssysteme und Lernprogramme entwerfen |
| 🌱 [Personal Growth Mentor](specialized/personal-growth-mentor.md) | Zielklarheit, Gewohnheitssysteme, Verantwortlichkeit | Domainübergreifende persönliche Entwicklung |
| 🏛️ [Government Digital Presales Consultant](specialized/government-digital-presales-consultant.md) | China ToG Presales, digitale Transformation | Angebote für digitale Transformation der Regierung |
| ⚕️ [Healthcare Marketing Compliance](specialized/healthcare-marketing-compliance.md) | China Gesundheitswerbung-Compliance | Regulatorische Compliance im Gesundheitsmarketing |
| 🎯 [Recruitment Specialist](specialized/recruitment-specialist.md) | Talentakquise, Recruiting-Betrieb | Recruiting-Strategie, Sourcing und Einstellungsprozesse |
| 🎓 [Study Abroad Advisor](specialized/study-abroad-advisor.md) | Internationale Bildung, Bewerbungsplanung | Auslandsstudium-Planung für USA, UK, Kanada, Australien |
| 🔗 [Supply Chain Strategist](specialized/supply-chain-strategist.md) | Supply Chain Management, Beschaffungsstrategie | Supply-Chain-Optimierung und Beschaffungsplanung |
| 🗺️ [Workflow Architect](specialized/specialized-workflow-architect.md) | Workflow-Discovery, Mapping und Spezifikation | Jeden Pfad durch ein System abbilden, bevor Code geschrieben wird |
| ☁️ [Salesforce Architect](specialized/specialized-salesforce-architect.md) | Multi-Cloud Salesforce-Design, Governor Limits | Enterprise Salesforce-Architektur, Org-Strategie |
| 🇫🇷 [French Consulting Market Navigator](specialized/specialized-french-consulting-market.md) | ESN/SI-Ökosystem, Portage Salarial | Freelance-Beratung im französischen IT-Markt |
| 🇰🇷 [Korean Business Navigator](specialized/specialized-korean-business-navigator.md) | Koreanische Geschäftskultur, 품의-Prozess | Ausländische Fachkräfte in koreanischen Geschäftsbeziehungen |
| 🏗️ [Civil Engineer](specialized/specialized-civil-engineer.md) | Strukturanalyse, geotechnisches Design, globale Bauvorschriften | Multi-Standard-Bauingenieurwesen |
| 🎧 [Customer Service](specialized/customer-service.md) | Omnichannel-Support, Beschwerdebearbeitung, Kundenbindung | Branchenübergreifender Kundensupport |
| 🏥 [Healthcare Customer Service](specialized/healthcare-customer-service.md) | HIPAA-konformer Patientensupport, Abrechnung | Compliance-konformer, empathischer Patientensupport |
| 🏨 [Hospitality Guest Services](specialized/hospitality-guest-services.md) | Reservierungen, Concierge, Beschwerdemanagement | Hotels, Resorts, Restaurants und Veranstaltungsorte |
| 🤝 [HR Onboarding](specialized/hr-onboarding.md) | Pre-Boarding, Compliance, Benefits-Enrollment | Onboarding neuer Mitarbeiter — von Startups bis Enterprise |
| 🌐 [Language Translator](specialized/language-translator.md) | Spanisch ↔ Englisch Übersetzung, Dialekt-Bewusstsein | Reise-, Geschäfts-, Medizin- und Rechtsübersetzungen |
| ⏱️ [Legal Billing & Time Tracking](specialized/legal-billing-time-tracking.md) | Zeiterfassung, Abrechnungsnarrative, IOLTA-Compliance | Kanzleien: Umsatzmaximierung und Abrechnungsgenauigkeit |
| 📋 [Legal Client Intake](specialized/legal-client-intake.md) | Interessenten-Qualifizierung, Konfliktprüfung | Kanzleien: Anfragen in mandatierte Mandanten umwandeln |
| ⚖️ [Legal Document Review](specialized/legal-document-review.md) | Vertragsprüfung, Risikokennzeichnung, Versionsvergleich | Anwaltsfertige Erstprüfung über alle Rechtsgebiete |
| 🏦 [Loan Officer Assistant](specialized/loan-officer-assistant.md) | Kreditnehmer-Intake, TRID-Compliance, Pipeline-Tracking | Hypotheken- und Verbraucherkreditteams |
| 🏠 [Real Estate Buyer & Seller](specialized/real-estate-buyer-seller.md) | Käufer/Verkäufer-Vertretung, Angebote | Wohn- und Anlageimmobilien-Transaktionen |
| 🛒 [Retail Customer Returns](specialized/retail-customer-returns.md) | Retourenbearbeitung, Betrugsprävention, Umtausch | Stationärer Handel, E-Commerce und Omnichannel-Retail |
| ♟️ [Business Strategist](specialized/business-strategist.md) | Managementberatungs-Strategie | Wettbewerbsanalyse, Markteintritt, Wachstumsplanung |
| 🔄 [Change Management Consultant](specialized/change-management-consultant.md) | ADKAR/Kotter/Prosci Change | Organisationen durch Transformation begleiten |
| 🧭 [Chief of Staff](specialized/specialized-chief-of-staff.md) | Executive-Koordination | Rauschen filtern, Prozesse verantworten, Entscheidungen lenken |
| 🌟 [Customer Success Manager](specialized/customer-success-manager.md) | Onboarding, Health & Retention | QBRs, Churn-Prävention, Verlängerungen & Expansion |
| 📝 [Grant Writer](specialized/grant-writer.md) | Förderanträge & Finanzierung | LOIs, Anträge, Budgets für NGOs/Forschung |
| 🏥 [Medical Billing & Coding Specialist](specialized/medical-billing-coding-specialist.md) | ICD-10/CPT/HCPCS & Revenue Cycle | Claims, Denial Management, RCM-Optimierung |
| 💰 [Pricing Analyst](specialized/specialized-pricing-analyst.md) | Preismodelle & Margenoptimierung | Wettbewerbs-/Kostenanalyse, wertbasierte Preisgestaltung |
| 💼 [Chief Financial Officer](specialized/chief-financial-officer.md) | Kapitalallokation & Finanzstrategie | Treasury, FP&A, M&A-Finanzen, Investor- & Board-Reporting |
| 🌱 [ESG & Sustainability Officer](specialized/esg-sustainability-officer.md) | ESG-Programme & Offenlegung | Nachhaltigkeitsstrategie, Dekarbonisierung, Berichterstattung |
| 🔐 [Data Privacy Officer](specialized/data-privacy-officer.md) | DSGVO/CCPA-Datenschutz-Compliance | Daten-Mapping, DSFAs, Einwilligung, Breach-Response |
| ⚙️ [Operations Manager](specialized/operations-manager.md) | Lean/Six Sigma-Betrieb | Prozess-Mapping, Kapazitätsplanung, KPI-Governance |
| 🤝 [M&A Integration Manager](specialized/ma-integration-manager.md) | Post-Merger-Integration | Day 1/100-Tage-Pläne, Synergy-Tracking, TSA-Management |
| 🧠 [Organizational Psychologist](specialized/organizational-psychologist.md) | Teamdynamik & Kulturgesundheit | Psychologische Sicherheit, Burnout-Risiko, High-Performance-Teams |
| ⚔️ [Strategy Duel Agent](specialized/specialized-strategy-duel-agent.md) | Spieltheorie & die 36 Strategeme | Rundenbasierte Strategieduelle, adversarische Szenariosimulation |

### 💵 Finanzabteilung

Buchhaltung, Finanzanalyse, Steuerstrategie und Investment-Research-Spezialisten.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 📒 [Bookkeeper & Controller](finance/finance-bookkeeper-controller.md) | Monatsabschluss, Abstimmung, GAAP-Compliance, interne Kontrollen | Laufende Buchhaltung, Audit-Bereitschaft, Finanzbuchführung |
| 📊 [Financial Analyst](finance/finance-financial-analyst.md) | Finanzmodellierung, Prognosen, Szenarioanalyse | Drei-Statements-Modelle, Varianzanalyse, datengetriebene BI |
| 📈 [FP&A Analyst](finance/finance-fpa-analyst.md) | Budgetierung, rollierende Prognosen, Varianzanalyse | Jährliche Betriebspläne, monatliche Business-Reviews |
| 🔍 [Investment Researcher](finance/finance-investment-researcher.md) | Due Diligence, Portfolio-Analyse, Bewertung | Investment-Thesis, Risikobewertung, Marktforschung |
| 🏛️ [Tax Strategist](finance/finance-tax-strategist.md) | Steueroptimierung, Multi-Jurisdiktions-Compliance | Unternehmensstrukturierung, ETR-Analyse, Steuerplanung |

### 🎮 Game-Development-Abteilung

Welten, Systeme und Erlebnisse über alle großen Engines hinweg bauen.

#### Engine-übergreifende Agenten (Engine-agnostisch)

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🎯 [Game Designer](game-development/game-designer.md) | Systemdesign, GDD-Erstellung, Economy-Balancing | Spielmechaniken, Progressionssysteme, Design-Dokumente |
| 🗺️ [Level Designer](game-development/level-designer.md) | Layout-Theorie, Pacing, Encounter-Design | Level-Bau, Encounter-Flow, räumliche Erzählung |
| 🎨 [Technical Artist](game-development/technical-artist.md) | Shader, VFX, LOD-Pipeline, Art-to-Engine-Optimierung | Brücke zwischen Art und Engineering |
| 🔊 [Game Audio Engineer](game-development/game-audio-engineer.md) | FMOD/Wwise, adaptive Musik, Spatial Audio | Interaktive Audiosysteme, dynamische Musik |
| 📖 [Narrative Designer](game-development/narrative-designer.md) | Story-Systeme, verzweigte Dialoge, Lore-Architektur | Verzweigte Erzählungen, Dialogsysteme |

#### Unity

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🏗️ [Unity Architect](game-development/unity/unity-architect.md) | ScriptableObjects, datengetriebene Modularität, DOTS/ECS | Große Unity-Projekte, datengetriebenes Systemdesign |
| ✨ [Unity Shader Graph Artist](game-development/unity/unity-shader-graph-artist.md) | Shader Graph, HLSL, URP/HDRP | Custom Unity-Materialien, VFX-Shader |
| 🌐 [Unity Multiplayer Engineer](game-development/unity/unity-multiplayer-engineer.md) | Netcode for GameObjects, Unity Relay/Lobby | Online Unity-Spiele, Client-Prediction |
| 🛠️ [Unity Editor Tool Developer](game-development/unity/unity-editor-tool-developer.md) | EditorWindows, AssetPostprocessors, PropertyDrawers | Custom Unity-Editor-Tooling, Pipeline-Automatisierung |

#### Unreal Engine

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| ⚙️ [Unreal Systems Engineer](game-development/unreal-engine/unreal-systems-engineer.md) | C++/Blueprint-Hybrid, GAS, Nanite | Komplexe Unreal-Gameplay-Systeme, Engine-Level C++ |
| 🎨 [Unreal Technical Artist](game-development/unreal-engine/unreal-technical-artist.md) | Material Editor, Niagara, PCG, Substrate | Unreal-Materialien, Niagara-VFX |
| 🌐 [Unreal Multiplayer Architect](game-development/unreal-engine/unreal-multiplayer-architect.md) | Actor-Replikation, GameMode/GameState-Hierarchie | Unreal-Online-Spiele, Replikationsgraphen |
| 🗺️ [Unreal World Builder](game-development/unreal-engine/unreal-world-builder.md) | World Partition, Landscape, HLOD, LWC | Große Open-World-Unreal-Level, Streaming-Systeme |

#### Godot

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 📜 [Godot Gameplay Scripter](game-development/godot/godot-gameplay-scripter.md) | GDScript 2.0, Signals, Komposition | Godot-Gameplay-Systeme, Scene-Komposition |
| 🌐 [Godot Multiplayer Engineer](game-development/godot/godot-multiplayer-engineer.md) | MultiplayerAPI, ENet/WebRTC, RPCs | Online-Godot-Spiele, Scene-Replikation |
| ✨ [Godot Shader Developer](game-development/godot/godot-shader-developer.md) | Godot Shading Language, VisualShader | Custom Godot-Materialien, 2D/3D-Effekte |

#### Blender

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🧩 [Blender Addon Engineer](game-development/blender/blender-addon-engineer.md) | Blender Python (`bpy`), Custom Operators/Panels | Blender-Addons, Asset-Prep-Tools, Export-Workflows |

#### Roblox Studio

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| ⚙️ [Roblox Systems Scripter](game-development/roblox-studio/roblox-systems-scripter.md) | Luau, RemoteEvents/Functions, DataStore | Sichere Roblox-Spielsysteme, Client-Server-Kommunikation |
| 🎯 [Roblox Experience Designer](game-development/roblox-studio/roblox-experience-designer.md) | Engagement-Loops, Monetarisierung, D1/D7-Retention | Roblox-Game-Loops, Game Passes, tägliche Belohnungen |
| 👗 [Roblox Avatar Creator](game-development/roblox-studio/roblox-avatar-creator.md) | UGC-Pipeline, Accessory-Rigging | Roblox-UGC-Items, HumanoidDescription-Anpassung |

### 📚 Akademische Abteilung

Wissenschaftliche Strenge für Weltenbau, Storytelling und narratives Design.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🌍 [Anthropologist](academic/academic-anthropologist.md) | Kulturelle Systeme, Verwandtschaft, Rituale | Kulturell kohärente Gesellschaften mit innerer Logik |
| 🌐 [Geographer](academic/academic-geographer.md) | Physische/Humangeographie, Klima, Kartografie | Geographisch kohärente Welten mit realistischem Gelände |
| 📚 [Historian](academic/academic-historian.md) | Historische Analyse, Periodisierung, materielle Kultur | Historische Kohärenz, authentisches Zeitkolorit |
| 📜 [Narratologist](academic/academic-narratologist.md) | Erzähltheorie, Story-Struktur, Charakterbögen | Erzählstruktur mit theoretischen Frameworks analysieren |
| 🧠 [Psychologist](academic/academic-psychologist.md) | Persönlichkeitstheorie, Motivation, kognitive Muster | Psychologisch glaubwürdige Charaktere |

---

### 🌍 GIS-Abteilung

Die Erde kartieren, die gebaute Welt analysieren und Intelligenz aus Geodaten gewinnen.

| Agent | Spezialgebiet | Wann einsetzen |
|-------|---------------|----------------|
| 🧠 [Technical Consultant](gis/gis-technical-consultant.md) | GIS-Strategie, Gap-Analyse, Technologie-Roadmaps | Geschäftsanforderungen verstehen, den richtigen Geo-Stack auswählen |
| 🔧 [Solution Engineer](gis/gis-solution-engineer.md) | Esri + FOSS4G Prototypenbau, PoC-Delivery | Funktionierende Demos, technische Ansätze validieren |
| 🖥️ [GIS Analyst](gis/gis-analyst.md) | Kartenproduktion, Daten-QC, Symbologie, Layouts | Tägliche GIS-Operationen, druckreife Karten |
| 📦 [Spatial Data Engineer](gis/gis-spatial-data-engineer.md) | Geospatial ETL, Formatkonvertierung, KBS-Reprojektion | Unordentliche Daten aufnehmen, wiederholbare Datenpipelines |
| ⚙️ [Geoprocessing Specialist](gis/gis-geoprocessing-specialist.md) | ArcPy, Python Toolbox (.pyt), Model Builder | Repetitive GIS-Workflows automatisieren |
| ✅ [GIS QA Engineer](gis/gis-qa-engineer.md) | Topologie-Validierung, Metadaten-Audit, KBS-Konsistenz | Quality Gates vor Datenveröffentlichung |
| 🤖 [GeoAI/ML Engineer](gis/gis-geoai-ml-engineer.md) | Feature-Extraktion, Objekterkennung, semantische Segmentierung | Gebäude/Straßen/Fahrzeuge aus Bildern extrahieren |
| 🏗️ [BIM/GIS Specialist](gis/gis-bim-specialist.md) | Revit/IFC zu GIS, Indoor-Mapping, Digital-Twin-Architektur | Smart Campus, Flughafen-Digital-Twins, Indoor-Navigation |
| 🏔️ [3D & Scene Developer](gis/gis-3d-scene-developer.md) | Cesium, ArcGIS Scene Viewer, 3D Tiles, Punktwolken | 3D-Stadtszenen, Geländeüberflüge, Punktwolken-Web-Viewer |
| 📊 [Spatial Data Scientist](gis/gis-spatial-data-scientist.md) | Räumliche Statistik, Clustering, Regression, Interpolation | Hotspot-Erkennung, räumliche Modellierung, prädiktive Analytik |
| 🛸 [Drone/Reality Mapping](gis/gis-drone-reality-mapping.md) | Photogrammetrie, Orthomosaik, DTM/DSM, Punktwolkenklassifizierung | Drohnen-Survey-Verarbeitung, Reality Capture |
| 🌐 [Web GIS Developer](gis/gis-web-gis-developer.md) | MapLibre GL JS, ArcGIS JS API, Leaflet, Echtzeit-Dashboards | Interaktive Webkarten, operationale Dashboards |
| 🎨 [Cartography Designer](gis/gis-cartography-designer.md) | Farbtheorie, Typografie, Basemap-Design, visuelle Hierarchie | Karten schön und lesbar gestalten, farbenblind-sichere Paletten |

---

## 🎯 Praxisbeispiele

### Szenario 1: Ein Startup-MVP bauen

**Dein Team**:
1. 🎨 **Frontend Developer** – Die React-App bauen
2. 🏗️ **Backend Architect** – API und Datenbank entwerfen
3. 🚀 **Growth Hacker** – Nutzerakquise planen
4. ⚡ **Rapid Prototyper** – Schnelle Iterationszyklen
5. 🔍 **Reality Checker** – Qualität vor dem Launch sicherstellen

**Ergebnis**: Schneller ausliefern mit spezialisierter Expertise in jeder Phase.

---

### Szenario 2: Marketing-Kampagnen-Launch

**Dein Team**:
1. 📝 **Content Creator** – Kampagnen-Content entwickeln
2. 🐦 **Twitter Engager** – Twitter-Strategie und -Umsetzung
3. 📸 **Instagram Curator** – Visueller Content und Stories
4. 🤝 **Reddit Community Builder** – Authentisches Community-Engagement
5. 📊 **Analytics Reporter** – Performance tracken und optimieren

**Ergebnis**: Multi-Channel koordinierte Kampagne mit plattformspezifischer Expertise.

---

### Szenario 3: Enterprise-Feature-Entwicklung

**Dein Team**:
1. 👔 **Senior Project Manager** – Scope- und Aufgabenplanung
2. 💎 **Senior Developer** – Komplexe Implementierung
3. 🎨 **UI Designer** – Design-System und Komponenten
4. 🧪 **Experiment Tracker** – A/B-Test-Planung
5. 📸 **Evidence Collector** – Qualitätsverifikation
6. 🔍 **Reality Checker** – Produktionsbereitschaft

**Ergebnis**: Enterprise-Grade Delivery mit Quality Gates und Dokumentation.

---

### Szenario 4: Paid-Media-Kontoübernahme

**Dein Team**:

1. 📋 **Paid Media Auditor** – Umfassende Kontobewertung
2. 📡 **Tracking & Measurement Specialist** – Conversion-Tracking-Genauigkeit prüfen
3. 💰 **PPC Campaign Strategist** – Kontoarchitektur neu gestalten
4. 🔍 **Search Query Analyst** – Streuverluste aus Suchbegriffen bereinigen
5. ✍️ **Ad Creative Strategist** – Alle Anzeigentexte und Erweiterungen auffrischen
6. 📊 **Analytics Reporter** (Support-Abteilung) – Reporting-Dashboards bauen

**Ergebnis**: Systematische Kontoübernahme mit verifiziertem Tracking, eliminierten Streuverlusten, optimierter Struktur und aufgefrischtem Creative — alles innerhalb der ersten 30 Tage.

---

### Szenario 5: Vollständige Agency Product Discovery

**Dein Team**: Alle 8 Abteilungen arbeiten parallel an einer Mission.

Siehe die **[Nexus Spatial Discovery-Übung](examples/nexus-spatial-discovery.md)** — ein vollständiges Beispiel, bei dem 8 Agenten gleichzeitig eingesetzt wurden, um eine Software-Opportunity zu bewerten und einen vereinheitlichten Produktplan zu erstellen.

**Ergebnis**: Umfassende, funktionsübergreifende Produkt-Blaupause in einer einzigen Sitzung. [Weitere Beispiele](examples/).

---

### Szenario 6: Smart Campus Digital Twin

**Dein Team**:

1. 🧠 **Technical Consultant** – Digital-Twin-Strategie definieren: BIM für Gebäude, GIS für Campus, IoT für Echtzeit
2. 🏗️ **BIM/GIS Specialist** – Revit-Gebäudemodelle in GIS-Scene-Layer konvertieren
3. 🛸 **Drone/Reality Mapping** – Campus überfliegen, Orthomosaik und 3D-Mesh generieren
4. 🌐 **Web GIS Developer** – Campus-Dashboard mit MapLibre, Gebäude-Layer und Raumfinder bauen
5. 🏔️ **3D & Scene Developer** – Immersive 3D-Szene mit Gelände, Gebäuden und Überflug-Tour erstellen
6. 🤖 **GeoAI/ML Engineer** – Gebäudegrundrisse und Baumkronen aus Drohnenbildern extrahieren
7. ✅ **GIS QA Engineer** – Datengenauigkeit validieren, Topologie prüfen, KBS-Konsistenz verifizieren

**Ergebnis**: Ein Campus-Digital-Twin, der BIM-Detail, Drohnen-Reality-Capture, 3D-Visualisierung und Web-Zugänglichkeit kombiniert.

---

## 🤝 Mitwirken

Wir freuen uns über Beiträge! So kannst du helfen:

### Einen neuen Agenten hinzufügen

1. Forke das Repository
2. Erstelle eine neue Agentendatei in der passenden Kategorie
3. Folge der Agenten-Template-Struktur:
   - Frontmatter mit Name, Beschreibung, Farbe
   - Identität & Gedächtnis-Abschnitt
   - Kernmission
   - Kritische Regeln (domainspezifisch)
   - Technische Ergebnisse mit Beispielen
   - Workflow-Prozess
   - Erfolgsmetriken
4. Reiche einen PR mit deinem Agenten ein

### Bestehende Agenten verbessern

- Praxisbeispiele hinzufügen
- Code-Samples erweitern
- Erfolgsmetriken aktualisieren
- Workflows verbessern

### Deine Erfolgsgeschichten teilen

Hast du diese Agenten erfolgreich eingesetzt? Teile deine Geschichte in den [Discussions](https://github.com/msitarzewski/agency-agents/discussions)!

---

## 📖 Agenten-Design-Philosophie

Jeder Agent wird nach diesen Prinzipien gestaltet:

1. **🎭 Starke Persönlichkeit**: Keine generischen Templates – echte Persönlichkeit und Stimme
2. **📋 Klare Ergebnisse**: Konkrete Outputs, keine vagen Anleitungen
3. **✅ Erfolgsmetriken**: Messbare Ergebnisse und Qualitätsstandards
4. **🔄 Bewährte Workflows**: Schritt-für-Schritt-Prozesse, die funktionieren
5. **💡 Lernendes Gedächtnis**: Mustererkennung und kontinuierliche Verbesserung

---

## 🎁 Was macht das Besondere aus?

### Im Vergleich zu generischen KI-Prompts:
- ❌ Generische „Agiere als Entwickler"-Prompts
- ✅ Tiefe Spezialisierung mit Persönlichkeit und Prozess

### Im Vergleich zu Prompt-Bibliotheken:
- ❌ Einmalige Prompt-Sammlungen
- ✅ Umfassende Agentensysteme mit Workflows und Ergebnissen

### Im Vergleich zu KI-Tools:
- ❌ Blackbox-Tools, die du nicht anpassen kannst
- ✅ Transparente, forkbare, anpassbare Agenten-Persönlichkeiten

---

## 🎨 Agenten-Persönlichkeits-Highlights

> „Ich teste deinen Code nicht nur — ich finde standardmäßig 3-5 Probleme und fordere visuellen Beweis für alles."
>
> — **Evidence Collector** (Test-Abteilung)

> „Du betreibst kein Marketing auf Reddit — du wirst ein geschätztes Community-Mitglied, das zufällig eine Marke vertritt."
>
> — **Reddit Community Builder** (Marketing-Abteilung)

> „Jedes spielerische Element muss einem funktionalen oder emotionalen Zweck dienen. Gestalte Begeisterung, die verbessert statt ablenkt."
>
> — **Whimsy Injector** (Design-Abteilung)

> „Lass mich eine Feier-Animation hinzufügen, die die Angst bei Aufgabenabschluss um 40% reduziert"
>
> — **Whimsy Injector** (während eines UX-Reviews)

---

## 📊 Statistiken

- 🎭 **232 spezialisierte Agenten** in 16 Abteilungen
- 📝 **10.000+ Zeilen** an Persönlichkeit, Prozessen und Codebeispielen
- ⏱️ **Monate der Iteration** aus realer Nutzung
- 🌟 **Praxiserprobt** in Produktionsumgebungen
- 💬 **50+ Anfragen** in den ersten 12 Stunden auf Reddit

---

## 🔌 Multi-Tool-Integrationen

The Agency funktioniert nativ mit Claude Code und liefert Konvertierungs- und Installationsskripte, damit du dieselben Agenten über alle großen agentischen Coding-Tools nutzen kannst.

### Unterstützte Tools

- **[Claude Code](https://claude.ai/code)** — native `.md`-Agenten, keine Konvertierung nötig → `~/.claude/agents/`
- **[GitHub Copilot](https://github.com/copilot)** — native `.md`-Agenten, keine Konvertierung nötig → `~/.github/agents/` + `~/.copilot/agents/`
- **[Antigravity](https://github.com/google-gemini/antigravity)** — `SKILL.md` pro Agent → `~/.gemini/antigravity/skills/`
- **[Gemini CLI](https://github.com/google-gemini/gemini-cli)** — Erweiterung + `SKILL.md`-Dateien → `~/.gemini/extensions/agency-agents/`
- **[OpenCode](https://opencode.ai)** — `.md`-Agentendateien → `.opencode/agents/`
- **[Cursor](https://cursor.sh)** — `.mdc`-Regeldateien → `.cursor/rules/`
- **[Aider](https://aider.chat)** — einzelne `CONVENTIONS.md` → `./CONVENTIONS.md`
- **[Windsurf](https://codeium.com/windsurf)** — einzelne `.windsurfrules` → `./.windsurfrules`
- **[OpenClaw](https://github.com/openclaw/openclaw)** — `SOUL.md` + `AGENTS.md` + `IDENTITY.md` pro Agent
- **[Qwen Code](https://github.com/QwenLM/qwen-code)** — `.md` SubAgent-Dateien → `~/.qwen/agents/`
- **[Kimi Code](https://github.com/MoonshotAI/kimi-cli)** — YAML Agent-Specs → `~/.config/kimi/agents/`
- **[Codex](https://developers.openai.com/codex/overview)** — TOML Custom Agents → `~/.codex/agents/`

---

### ⚡ Schnellinstallation

**Schritt 1 — Integrationsdateien generieren:**
```bash
./scripts/convert.sh
# Schneller (parallel, Ausgabereihenfolge kann variieren): ./scripts/convert.sh --parallel
```

**Schritt 2 — Installieren (interaktiv, erkennt automatisch deine Tools):**
```bash
./scripts/install.sh
# Schneller (parallel, Ausgabereihenfolge kann variieren): ./scripts/install.sh --no-interactive --parallel
```

**Oder ein bestimmtes Tool direkt installieren:**
```bash
./scripts/install.sh --tool cursor
./scripts/install.sh --tool opencode
./scripts/install.sh --tool openclaw
./scripts/install.sh --tool antigravity
./scripts/install.sh --tool codex
```

**Nicht-interaktiv (CI/Skripte):**
```bash
./scripts/install.sh --no-interactive --tool all
```

---

### Nach Änderungen neu generieren

Wenn du neue Agenten hinzufügst oder bestehende bearbeitest, generiere alle Integrationsdateien neu:

```bash
./scripts/convert.sh                    # Alle neu generieren (seriell)
./scripts/convert.sh --parallel         # Alle parallel neu generieren (schneller)
./scripts/convert.sh --tool codex       # Nur ein Tool neu generieren
./scripts/convert.sh --tool cursor      # Nur ein Tool neu generieren
```

---

## 🗺️ Roadmap

- [ ] Interaktives Agenten-Auswahl-Webtool
- [x] Multi-Agent-Workflow-Beispiele — siehe [examples/](examples/)
- [x] Multi-Tool-Integrationsskripte (Claude Code, GitHub Copilot, Antigravity, Gemini CLI, OpenCode, OpenClaw, Cursor, Aider, Windsurf, Qwen Code, Kimi Code, Codex)
- [ ] Video-Tutorials zum Agenten-Design
- [ ] Community Agent Marketplace
- [ ] Agenten-„Persönlichkeitsquiz" für Projekt-Matching
- [ ] „Agent der Woche"-Showcase-Serie

---

## 🌐 Community-Übersetzungen & Lokalisierungen

Von der Community gepflegte Übersetzungen und regionale Anpassungen. Diese werden unabhängig gepflegt — siehe jedes Repo für Abdeckung und Versionskompatibilität.

| Sprache | Maintainer | Link | Hinweise |
|---------|-----------|------|----------|
| 🇨🇳 简体中文 (zh-CN) | [@jnMetaCode](https://github.com/jnMetaCode) | [agency-agents-zh](https://github.com/jnMetaCode/agency-agents-zh) | 141 übersetzte Agenten + 46 China-Markt-Originale |
| 🇨🇳 简体中文 (zh-CN) | [@dsclca12](https://github.com/dsclca12) | [agent-teams](https://github.com/dsclca12/agent-teams) | Unabhängige Übersetzung mit Bilibili, WeChat, Xiaohongshu-Lokalisierung |
| 🇧🇷 Português brasileiro (pt-BR) | [@jnMetaCode](https://github.com/jnMetaCode) | [agency-agents-pt-BR](https://github.com/jnMetaCode/agency-agents-pt-BR) | 184 Upstream-Agenten übersetzt; Brasilien-Markt-PRs willkommen |
| 🇷🇺 Русский (ru) | [@jnMetaCode](https://github.com/jnMetaCode) | [agency-agents-ru](https://github.com/jnMetaCode/agency-agents-ru) | 184 Upstream-Agenten übersetzt; Russland-Markt-PRs willkommen |
| 🇮🇩 Bahasa Indonesia (id) | [@jnMetaCode](https://github.com/jnMetaCode) | [agency-agents-id](https://github.com/jnMetaCode/agency-agents-id) | 184 Upstream-Agenten übersetzt; Indonesien-Markt-PRs willkommen |
| 🇸🇦 العربية (ar) | [@jnMetaCode](https://github.com/jnMetaCode) | [agency-agents-ar](https://github.com/jnMetaCode/agency-agents-ar) | 184 Upstream-Agenten übersetzt; Arabisch-Markt-PRs willkommen |
| 🇰🇷 한국어 (ko) | [@jnMetaCode](https://github.com/jnMetaCode) | [agency-agents-ko](https://github.com/jnMetaCode/agency-agents-ko) | 184 Upstream-Agenten vollständig übersetzt; Korea-spezifische PRs willkommen |
| 🇯🇵 日本語 (ja-JP) | [@sscodeai](https://github.com/sscodeai) | [agency-agents-ja](https://github.com/sscodeai/agency-agents-ja) | 281 Japan-lokalisierte Agenten + 97 Japan-Markt-Originale + 27 Workflows |

Du möchtest eine Übersetzung hinzufügen? Eröffne ein Issue und wir verlinken es hier.

---

## 🔗 Verwandte Ressourcen

- [awesome-openclaw-agents](https://github.com/mergisi/awesome-openclaw-agents) — Von der Community gepflegte OpenClaw-Agentensammlung (abgeleitet von diesem Repo)

---

## 📜 Lizenz

MIT-Lizenz – Frei nutzbar, kommerziell oder privat. Namensnennung erwünscht, aber nicht erforderlich.

---

## 🙏 Danksagung

Was als Reddit-Thread über KI-Agenten-Spezialisierung begann, ist zu etwas Bemerkenswertem gewachsen — **232 Agenten in 16 Abteilungen**, unterstützt von einer Community aus Mitwirkenden weltweit. Jeder Agent in diesem Repo existiert, weil jemand sich die Mühe gemacht hat, ihn zu schreiben, zu testen und zu teilen.

An alle, die einen PR geöffnet, ein Issue erstellt, eine Discussion gestartet oder einfach einen Agenten ausprobiert und uns erzählt haben, was funktioniert hat — danke. Ihr seid der Grund, warum The Agency immer besser wird.

---

## 💬 Community

- **GitHub Discussions**: [Teile deine Erfolgsgeschichten](https://github.com/msitarzewski/agency-agents/discussions)
- **Issues**: [Bugs melden oder Features anfragen](https://github.com/msitarzewski/agency-agents/issues)
- **Reddit**: Diskutiere mit auf r/ClaudeAI
- **Twitter/X**: Teile mit #TheAgency

---

## 🚀 Loslegen

1. **Durchsuche** die Agenten oben und finde Spezialisten für deine Anforderungen
2. **Kopiere** die Agenten nach `~/.claude/agents/` für die Claude-Code-Integration
3. **Aktiviere** Agenten, indem du sie in deinen Claude-Gesprächen referenzierst
4. **Passe** Agenten-Persönlichkeiten und Workflows an deine spezifischen Bedürfnisse an
5. **Teile** deine Ergebnisse und trage zurück zur Community bei

---

<div align="center">

**🎭 The Agency: Dein KI-Traumteam wartet 🎭**

[⭐ Repo markieren](https://github.com/msitarzewski/agency-agents) • [🍴 Forken](https://github.com/msitarzewski/agency-agents/fork) • [🐛 Issue melden](https://github.com/msitarzewski/agency-agents/issues) • [❤️ Sponsern](https://github.com/sponsors/msitarzewski)

Mit ❤️ von der Community, für die Community

</div>
