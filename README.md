# 🎭 Mi set de agentes

> Roster curado de **35 agentes** para un operador solo que enseña, programa, hace marketing y vende — con foco en el mercado colombiano.

Derivado de [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) (MIT). La rama `main` conserva el catálogo completo de 282 agentes y sigue sincronizable con upstream; esta rama (`mi-set`) es el set de trabajo.

---

## ⚡ Instalación

```bash
# Claude Code — con symlinks, así los cambios en el repo se propagan solos
./scripts/install.sh --tool claude-code --link

# Otras herramientas: generar primero, instalar después
./scripts/convert.sh
./scripts/install.sh --tool codex
./scripts/install.sh --tool gemini-cli

# Ver el plan sin escribir nada
./scripts/install.sh --tool claude-code --link --dry-run
```

Luego basta con nombrarlos en la conversación:

```
Usa el Colombia WhatsApp Operator para diseñar el flujo de venta de mi curso.
Activa Minimal Change Engineer. Arregla SOLO este bug, sin refactorizar nada más.
```

---

## 🇨🇴 Agentes Colombia

Adaptados desde los playbooks de mercado chino. No se convirtieron uno a uno: la mayoría de los agentes chinos ya tenían equivalente occidental en el roster (Douyin↔TikTok, Xiaohongshu↔Instagram, Weibo↔X), así que solo se convirtieron los tres con un vacío real.

| Agente | Qué hace |
|---|---|
| 💚 **Colombia WhatsApp Operator** | Dominio propio sobre WhatsApp: Cloud API, plantillas HSM, ventana de 24h, Habeas Data (Ley 1581), y pago con Nequi / Daviplata / PSE / Bre-B / contra entrega |
| 🛒 **Colombia E-Commerce Operator** | MercadoLibre, Falabella, Éxito, Rappi + transportadoras reales + modelo de costo que cobra el rechazo de contra entrega + factura electrónica DIAN |
| 🇨🇴 **Colombia Market Strategist** | Segmentación por estrato 1-6, tono por región (usted/vos/tú), y calendario comercial local (Día de la Madre, prima, Amor y Amistad, puentes de Ley Emiliani) |

---

## 🎨 Roster

### 💻 Engineering (8)
| Agente | Vibe |
|---|---|
| 🪡 Minimal Change Engineer | El diff más pequeño que resuelve el problema — cada línea extra es un pasivo |
| 👁️ Code Reviewer | Revisa como mentor, no como portero |
| ⚡ Rapid Prototyper | De idea a prototipo funcional antes de que termine la reunión |
| 🏗️ Backend Architect | Bases de datos, APIs, nube y escala |
| 🖥️ Frontend Developer | Apps web responsivas y accesibles |
| 🌿 Git Workflow Master | Historia limpia, commits atómicos, ramas que cuentan una historia |
| 🧬 Prompt Engineer | No escribe prompts: escribe contratos entre humanos y modelos |
| 📚 Technical Writer | La documentación que los devs sí leen |

### 🔒 Security (2)
| Agente | Vibe |
|---|---|
| 🔎 AI-Generated Code Security Auditor | Asume que el asistente optimizó para el demo, no para producción |
| 🔐 Application Security Engineer | Que el dev escriba código seguro sin darse cuenta |

### 🧪 Testing (2)
| Agente | Vibe |
|---|---|
| 🧐 Reality Checker | Por defecto dice "NEEDS WORK" |
| 📸 Evidence Collector | No aprueba nada sin prueba visual |

### 📢 Marketing (11)
| Agente | Vibe |
|---|---|
| 🔮 AI Citation Strategist | Descubre por qué la IA recomienda a tu competencia y lo reconfigura |
| 🏗️ AEO Foundations Architect | La capa base que todos saltan: que la IA pueda leerte |
| 🔍 SEO Specialist | Tráfico orgánico sostenible |
| ✍️ Content Creator | Historias por cada plataforma donde vive tu audiencia |
| 💼 LinkedIn Content Creator | Convierte tu expertise en contenido que te encuentra clientes |
| 🎵 TikTok Strategist | Surfea el algoritmo desde la cultura, no desde el brief |
| 📸 Instagram Curator | Estética de grilla y comunidad |
| 🎬 Video Optimization Specialist | Obsesionado con la retención de audiencia |
| 💚 Colombia WhatsApp Operator | *(ver arriba)* |
| 🛒 Colombia E-Commerce Operator | *(ver arriba)* |
| 🇨🇴 Colombia Market Strategist | *(ver arriba)* |

### 🎯 Specialized (6)
| Agente | Vibe |
|---|---|
| 📚 Corporate Training Designer | Programas de formación que cambian comportamiento, con Kirkpatrick |
| 💰 Pricing Analyst | El punto donde el valor capturado se encuentra con el entregado |
| 📄 Document Generator | PDF, PPTX, DOCX y XLSX generados con código |
| 🔌 MCP Builder | Construye las herramientas que hacen útiles a los agentes |
| 🗃️ ZK Steward | Zettelkasten de Luhmann: notas atómicas y conectadas |
| 🧭 Chief of Staff | "No soy dueño de ninguna función. Soy dueño del espacio entre todas." |

### 💼 Sales (2)
| Agente | Vibe |
|---|---|
| 🧲 Offer & Lead Gen Strategist | Construye la oferta que no se puede ignorar |
| 🏹 Proposal Strategist | Convierte RFPs en historias que el comprador no suelta |

### 📊 Product · 🎓 Academic · 🔍 Research · 🎨 Design (4)
| Agente | Vibe |
|---|---|
| 🧭 Product Manager | Envía lo correcto, no lo siguiente |
| 📊 Statistician | El plural de anécdota no es data, y un p-valor no es una prueba |
| 🔍 Research Synthesist | Cien citas en la misma dirección siguen siendo una sola evidencia |
| 📷 Image Prompt Engineer | Traduce conceptos visuales a prompts precisos |

---

## 🧩 Anatomía de un agente

```yaml
---
name: Nombre del agente
description: Qué hace y en qué se especializa
color: green          # obligatorio
emoji: 🎯
vibe: El gancho de personalidad en una línea
---
```

Cuerpo con secciones estándar: `Identity & Memory`, `Core Mission`, `Critical Rules`, `Technical Deliverables`, `Workflow Process`, `Communication Style`, `Success Metrics`.

Validar tras cualquier cambio:

```bash
./scripts/lint-agents.sh          # frontmatter y estructura
./scripts/check-divisions.sh      # divisions.json ↔ disco ↔ scripts ↔ CI
./scripts/check-tools.sh          # tools.json ↔ install.sh ↔ convert.sh
```

---

## 🗂️ Divisiones activas

`academic` · `design` · `engineering` · `marketing` · `product` · `research` · `sales` · `security` · `specialized` · `testing`

Eliminadas en esta rama por no aplicar al perfil: `finance` (era 100% tributación de EE.UU.), `game-development`, `gis`, `healthcare`, `paid-media`, `project-management`, `spatial-computing`, `support`. Todas siguen disponibles en `main`.

---

## 🔄 Volver al catálogo completo

```bash
git checkout main                              # los 282 agentes
git checkout main -- gis/                      # recuperar una división suelta
git checkout main -- specialized/grant-writer.md   # o un agente puntual
```

---

## 📜 Licencia

MIT — igual que el proyecto original. Ver [LICENSE](LICENSE).
