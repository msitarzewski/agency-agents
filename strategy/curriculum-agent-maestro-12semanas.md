# 🎓 Curriculum Agent Maestro No-Code — 12 Semanas

> Ruta estructurada para dominar la construcción y orquestación de agentes AI
> sin escribir código de producción. Orientado a perfiles de negocio, auditoría,
> operaciones y product management que quieren liderar transformaciones con AI.
>
> **Prerequisito**: Curiosidad. Nada más.
> **Meta final**: Portfolio de 3 agentes reales + capacidad de aplicar a roles AI-forward.

---

## 🗺️ Vista General

```
FASE 1 — FUNDAMENTOS (Semanas 1-4)
  Sem 1 · ¿Qué es un agente? MCP y el nuevo paradigma
  Sem 2 · Prompt engineering para agentes
  Sem 3 · Tool-use: darle superpoderes a tus agentes
  Sem 4 · Tu primer agente funcional end-to-end

FASE 2 — CONSTRUCCIÓN (Semanas 5-8)
  Sem 5 · Diseño de agentes especializados
  Sem 6 · Multi-agente: división de responsabilidades
  Sem 7 · Orquestación: quién manda a quién
  Sem 8 · Handoffs y calidad: que nada se pierda

FASE 3 — MAESTRÍA (Semanas 9-12)
  Sem 9 · Llevar agentes a producción (sin código)
  Sem 10 · Medición, iteración y mejora continua
  Sem 11 · Portfolio: presentar tu trabajo al mundo
  Sem 12 · Comunidad, posicionamiento y siguiente nivel
```

---

## FASE 1 — FUNDAMENTOS
### *Entiende el juego antes de jugarlo*

---

### 📅 SEMANA 1 — ¿Qué es un agente? MCP y el nuevo paradigma

**Objetivo**: Distinguir chatbot vs. agente vs. sistema multi-agente.
Entender qué es MCP (Model Context Protocol) y por qué cambia todo.

**Conceptos clave**:
- Agente = LLM + Tools + Memory + Autonomía
- MCP: el "USB-C" de los agentes (conecta modelos con herramientas del mundo real)
- Diferencia entre instrucción única vs. loop de razonamiento (ReAct)
- Claude Code como entorno de práctica no-code

**Ejercicio práctico**:
1. Instala Claude Code (CLI) en tu máquina
2. Abre el repositorio `agency-agents` y navega las 9 divisiones
3. Lee 3 archivos de agentes de divisiones distintas (ej: engineering, marketing, support)
4. Identifica: ¿qué tiene en común su estructura? (Identity, Mission, Rules, Deliverables)
5. Escribe en tu diario de aprendizaje: "Un agente es \_\_\_ y se diferencia de un chatbot en \_\_\_"

**Entregable**:
> 📄 `diario-semana-1.md` — Mapa mental con: definición de agente, 3 ejemplos del repo,
> y 1 caso de uso de tu trabajo/industria donde un agente ahorraría tiempo.

---

### 📅 SEMANA 2 — Prompt Engineering para Agentes

**Objetivo**: Escribir prompts que producen comportamiento confiable y repetible.
Pasar de "el agente a veces funciona" a "el agente siempre hace lo correcto".

**Conceptos clave**:
- System prompt vs. user prompt vs. assistant prefill
- Las 4 capas de un buen prompt de agente: Rol, Contexto, Tarea, Formato
- Few-shot examples: mostrar en lugar de solo decir
- Chain-of-thought: pedir razonamiento explícito
- Temperatura y determinismo en agentes de producción

**Ejercicio práctico**:
1. Toma un agente del repo (ej: `support/support-responder.md`)
2. Actívalo en Claude y dale 3 casos de prueba distintos
3. Identifica cuándo responde bien y cuándo falla
4. Reescribe el system prompt para cubrir los casos de falla
5. Documenta el antes/después con ejemplos de output

**Entregable**:
> 📄 `prompt-lab-semana-2.md` — Tabla comparativa: prompt original vs. tu versión mejorada,
> con 3 ejemplos de input/output para cada versión.

---

### 📅 SEMANA 3 — Tool-Use: Darle Superpoderes a tus Agentes

**Objetivo**: Entender cómo los agentes usan herramientas externas (tools/MCPs)
para actuar en el mundo, no solo responder texto.

**Conceptos clave**:
- Tool-use: el agente decide cuándo y cómo usar cada herramienta
- MCPs disponibles: Supabase, Gmail, Google Calendar, Figma, Vercel, n8n...
- Tool call loop: razona → llama tool → observa resultado → razona de nuevo
- Diferencia entre tool determinista (SQL query) vs. tool probabilista (búsqueda web)
- Errores comunes: tool hallucination, tool overuse, missing error handling

**Ejercicio práctico**:
1. Activa el agente `specialized/agents-orchestrator.md`
2. Dile que busque información en tu calendario (Google Calendar MCP)
3. Observa el loop: ¿cuántas tool calls hace? ¿cómo decide qué tool usar?
4. Configura un MCP nuevo que no hayas usado antes (ej: Gmail o Supabase)
5. Construye un mini-flujo: agente lee email → escribe resumen → lo guarda

**Entregable**:
> 📄 `tool-use-lab-semana-3.md` — Diagrama de flujo del mini-agente construido,
> con: herramientas usadas, descripción de cada tool call, resultado obtenido.

---

### 📅 SEMANA 4 — Tu Primer Agente Funcional End-to-End

**Objetivo**: Diseñar, construir y probar un agente completo para un problema real tuyo.
Integrar lo aprendido en semanas 1-3 en un solo entregable funcional.

**Conceptos clave**:
- Diseño orientado a problema: empezar por el pain point, no por la tecnología
- MVP de agente: 1 herramienta, 1 tarea, 1 usuario
- Testing básico: casos felices + casos de borde
- Documentación mínima para que otros puedan usarlo

**Ejercicio práctico**:
1. Identifica 1 tarea repetitiva en tu trabajo que toma 30+ minutos/semana
2. Diseña el agente en papel: ¿qué herramientas necesita? ¿qué inputs recibe? ¿qué output produce?
3. Crea el archivo del agente siguiendo el template de `agency-agents`
4. Actívalo en Claude Code y ejecuta 5 casos de prueba reales
5. Itera hasta que el agente resuelva el 80% de los casos sin intervención

**Entregable**:
> 🤖 `agente-semana-4/` — Tu primer agente propio con:
> - Archivo `.md` del agente (Identity, Mission, Rules, Tools, Deliverables)
> - 5 casos de prueba documentados (input → output real)
> - Nota de retrospectiva: ¿qué funcionó? ¿qué cambiarías?

---

## FASE 2 — CONSTRUCCIÓN
### *De un agente a un equipo de agentes*

---

### 📅 SEMANA 5 — Diseño de Agentes Especializados

**Objetivo**: Entender por qué los agentes especializados superan a los agentes generalistas.
Aprender a diseñar agentes con un único propósito muy bien definido.

**Conceptos clave**:
- Single Responsibility Principle aplicado a agentes
- Especialización por: dominio (auditoría, marketing), función (investigar, ejecutar, revisar)
- Anti-patrones: el agente "hace todo" que no hace nada bien
- Cómo definir el "Definition of Done" de un agente
- Métricas de calidad: precisión, consistencia, latencia, costo de tokens

**Ejercicio práctico**:
1. Toma el agente de la semana 4 y divide su trabajo en 2 agentes más pequeños
2. Agente A: solo recolecta información
3. Agente B: solo procesa y reporta
4. Prueba ambos por separado y luego en secuencia
5. Mide: ¿mejoró la calidad del output? ¿se redujo el error?

**Entregable**:
> 📄 `diseño-agentes-semana-5.md` — Diagrama de responsabilidades:
> agente original vs. versión especializada, con métricas de comparación.

---

### 📅 SEMANA 6 — Multi-Agente: División de Responsabilidades

**Objetivo**: Construir tu primer sistema donde múltiples agentes trabajan juntos
sin pisarse ni duplicar esfuerzo.

**Conceptos clave**:
- Topologías multi-agente: secuencial, paralelo, jerárquico
- Cómo definir fronteras entre agentes (interfaces claras)
- Shared context: qué información necesita pasar entre agentes
- Evitar el "teléfono descompuesto": contexto que se degrada en cada handoff
- Ejemplo NEXUS: 9 divisiones, cada una con agentes especializados

**Ejercicio práctico**:
1. Diseña un pipeline de 3 agentes para un reporte semanal de tu trabajo:
   - Agente 1 (Recolector): lee emails + calendario de la semana
   - Agente 2 (Analista): identifica logros, blockers, próximos pasos
   - Agente 3 (Redactor): genera el reporte en formato ejecutivo
2. Conecta los 3 usando Claude Code con los MCPs de Gmail y Google Calendar
3. Ejecuta el pipeline completo y evalúa el resultado

**Entregable**:
> 🤖 `pipeline-reporte-semanal/` — 3 archivos de agente + instrucciones de activación
> + 1 reporte real generado por el pipeline.

---

### 📅 SEMANA 7 — Orquestación: Quién Manda a Quién

**Objetivo**: Implementar un orquestador que coordina agentes, toma decisiones
sobre el flujo y maneja errores sin intervención humana.

**Conceptos clave**:
- Orquestador vs. sub-agente: roles y responsabilidades
- Routing: cómo el orquestador decide qué agente activar
- Conditional logic sin código: prompts que emulan if/else
- Retry logic: qué hacer cuando un agente falla
- El patrón NEXUS: máximo 3 intentos → escalación humana

**Ejercicio práctico**:
1. Activa `specialized/agents-orchestrator.md` como tu orquestador
2. Dale un proyecto pequeño de 3 tareas paralelas
3. Observa cómo divide, asigna y consolida
4. Simula un fallo: dile que el Agente 2 falló → ¿cómo maneja la escalación?
5. Documenta el árbol de decisiones que siguió el orquestador

**Entregable**:
> 📄 `orquestacion-semana-7.md` — Árbol de decisiones del orquestador documentado,
> con capturas del loop real y análisis de cómo manejó el caso de fallo.

---

### 📅 SEMANA 8 — Handoffs y Calidad: Que Nada Se Pierda

**Objetivo**: Implementar handoffs estructurados entre agentes que preserven
contexto y garanticen calidad antes de pasar el trabajo al siguiente agente.

**Conceptos clave**:
- NEXUS Handoff Template: el formato estándar
- Quality gates: criterios de aceptación antes de avanzar
- Evidence-based review: el agente revisor pide pruebas, no declaraciones
- El patrón Dev↔QA loop: implementar → revisar → PASS/FAIL → iterar
- "Fantasy approvals": el error más común en sistemas multi-agente

**Ejercicio práctico**:
1. Toma el pipeline de la semana 6 (reporte semanal)
2. Agrega un Agente Revisor entre el Analista y el Redactor
3. El Revisor debe verificar: ¿hay evidencia real para cada logro declarado?
4. Si falla la revisión → regresa al Analista con feedback específico
5. Itera hasta que el Revisor apruebe con evidencia

**Entregable**:
> 📄 `handoff-calidad-semana-8.md` — Pipeline actualizado con quality gate incluido
> + 1 ejemplo de ciclo completo: FAIL → feedback → retry → PASS.

---

## FASE 3 — MAESTRÍA
### *De experimentos a resultados reales y visibles*

---

### 📅 SEMANA 9 — Llevar Agentes a Producción (Sin Código)

**Objetivo**: Entender qué significa "producción" para un sistema de agentes
y cómo lograrlo usando herramientas no-code como n8n, Make o Power Automate.

**Conceptos clave**:
- Producción vs. experimento: confiabilidad, mantenimiento, observabilidad
- Triggers automáticos: agente que se activa sin intervención humana
- n8n como orquestador visual: conectar Claude con el mundo real
- Logging básico: registrar qué hizo el agente y cuándo
- Gestión de secretos: API keys sin exponerlas en prompts

**Ejercicio práctico**:
1. Instala n8n (cloud free tier o Docker local)
2. Conecta Claude API como un nodo en n8n
3. Construye un workflow automático: cada lunes a las 9am → activa el pipeline de reporte semanal → envía el resultado por email
4. Agrega un nodo de logging que registra cada ejecución en una hoja de Google Sheets
5. Ejecuta 2 semanas consecutivas sin intervención manual

**Entregable**:
> 🔄 `workflow-produccion-semana-9/` — Export del workflow de n8n (.json)
> + log de 2 ejecuciones reales + reflexión sobre qué falló y cómo lo arreglaste.

---

### 📅 SEMANA 10 — Medición, Iteración y Mejora Continua

**Objetivo**: Pasar de "parece que funciona" a "tengo datos que prueban que funciona".
Implementar métricas simples que guían la mejora del sistema.

**Conceptos clave**:
- Las 4 métricas que importan: precisión, cobertura, latencia, costo
- Evaluación cualitativa: rubrics de calidad para outputs de agentes
- A/B testing de prompts: versión A vs. versión B, medir diferencia
- Feedback loops: cómo el usuario final mejora el agente con sus correcciones
- Cuándo escalar vs. cuándo simplificar

**Ejercicio práctico**:
1. Toma tu pipeline de producción de la semana 9
2. Diseña una rubric de calidad de 5 criterios para el reporte final (escala 1-5 cada uno)
3. Evalúa las últimas 4 ejecuciones con la rubric
4. Identifica el criterio con peor puntaje promedio
5. Reescribe la parte del prompt responsable de ese criterio y mide el impacto

**Entregable**:
> 📊 `metricas-semana-10.md` — Dashboard de texto con las 4 métricas del pipeline,
> rubric de calidad completada para 4 ejecuciones, y versión mejorada del prompt con antes/después.

---

### 📅 SEMANA 11 — Portfolio: Presentar tu Trabajo al Mundo

**Objetivo**: Convertir tus 10 semanas de trabajo en un portfolio profesional
que demuestra capacidades reales a empleadores, clientes y comunidad.

**Conceptos clave**:
- El portfolio de agentes vs. el portfolio de código: qué mostrar
- Case study format: problema → solución → impacto medido
- GitHub como plataforma de portfolio para no-developers
- README que cuenta una historia, no solo documenta
- LinkedIn para AI builders: cómo posicionarse en 2026

**Ejercicio práctico**:
1. Organiza tu repositorio GitHub con todos los entregables de las 10 semanas
2. Escribe un README principal que cuente tu historia: antes → aprendizaje → ahora
3. Elige tu mejor agente (el de mayor impacto real) y escribe un case study de 1 página
4. Publica el case study en LinkedIn como artículo
5. Graba un video de 3 minutos demostrando el pipeline en vivo (Loom o similar)

**Entregable**:
> 🌐 Repositorio GitHub público con README + 1 case study publicado en LinkedIn
> + video de demo de 3 minutos.

---

### 📅 SEMANA 12 — Comunidad, Posicionamiento y Siguiente Nivel

**Objetivo**: Establecer tu presencia en la comunidad de builders de AI,
definir tu siguiente nivel de aprendizaje y mantener el momentum.

**Conceptos clave**:
- Comunidades que importan en 2026: Latent Space, Buildspace, AI Tinkerers, r/LocalLLaMA
- Contribution loop: aprender → construir → compartir → aprender más rápido
- Tu nicho de especialización: AI + tu industria (auditoría, operaciones, etc.)
- Siguiente stack a dominar: LangChain, Vellum, o Copilot Studio (Nivel 3)
- Mantener el ritmo: 1 agente nuevo por mes como práctica de mantenimiento

**Ejercicio práctico**:
1. Únete a 2 comunidades de builders (Discord, Slack, o foro)
2. Comparte tu case study de la semana 11 en una de las comunidades
3. Da feedback constructivo a 2 proyectos de otros builders
4. Define tu plan de las próximas 12 semanas: ¿qué stack? ¿qué rol objetivo?
5. Agenda 1 hora semanal fija en tu calendario para construir agentes — para siempre

**Entregable**:
> 📄 `plan-siguiente-nivel.md` — Documento de 1 página con:
> tu nicho de especialización elegido, 3 comunidades activas, stack objetivo,
> y calendario de práctica de los próximos 3 meses.

---

## 📦 Portfolio Completo al Finalizar

Al terminar las 12 semanas tendrás:

| # | Entregable | Qué demuestra |
|---|-----------|---------------|
| 1 | Diario de aprendizaje (12 entradas) | Consistencia y reflexión |
| 2 | Agente propio funcional (Sem 4) | Capacidad de construcción |
| 3 | Pipeline multi-agente (Sem 6) | Coordinación de sistemas |
| 4 | Sistema con orquestador + quality gates (Sem 8) | Pensamiento sistémico |
| 5 | Workflow en producción vía n8n (Sem 9) | Deployment real |
| 6 | Dashboard de métricas (Sem 10) | Mentalidad data-driven |
| 7 | Case study publicado en LinkedIn (Sem 11) | Comunicación ejecutiva |
| 8 | Plan de siguiente nivel (Sem 12) | Visión a largo plazo |

---

## 🧰 Stack de Herramientas (Todo Gratuito para Aprender)

| Herramienta | Para qué | Free tier |
|------------|---------|-----------|
| Claude Code | Entorno principal de agentes | ✅ |
| n8n Cloud | Automatización visual | ✅ 5 workflows |
| Supabase | Base de datos para agentes | ✅ 2 proyectos |
| GitHub | Portfolio y versionado | ✅ |
| Google Workspace | MCPs de Calendar/Gmail | ✅ |
| Loom | Videos de demo | ✅ 5 min |
| Notion | Diario de aprendizaje | ✅ |

---

## ⏱️ Tiempo de Inversión Semanal

```
Lectura / teoría          ░░░  1.5 hrs
Ejercicio práctico        ░░░░ 2.0 hrs
Documentar entregable     ░░   1.0 hrs
─────────────────────────────────────
Total por semana          ░░░░░░░  ~4.5 hrs
Total 12 semanas          ~54 hrs  (≈ 1 semana de trabajo)
```

---

## 🏆 Nivel de Salida vs. Requisitos IonQ

Al completar este curriculum, tu scorecard para el rol IonQ cambia así:

```
AI Mindset / Pasión         ██████████  100%  ✅ (ya estaba)
AI Platforms (LangChain…)   ████████░░   75%  ✅ (Sem 3, 7, 9)
Automation Hubs (n8n…)      ████████░░   75%  ✅ (Sem 9)
Custom GPT / Agentes        ██████████  100%  ✅ (Sem 4, 5, 6)
Audit Toolkit conceptual    ██████░░░░   60%  🔶 (Sem 10)
Data Stack                  ███░░░░░░░   30%  🔶 (base, no completo)
SQL / Python                ░░░░░░░░░░    0%  ❌ (fuera de scope)
```

> SQL y Python están fuera del scope no-code — son el siguiente paso natural
> después de completar este curriculum si el objetivo es el rol IonQ.

---

*Curriculum generado por: Skills Gap Analysis Agent · agency-agents / NEXUS*
*Versión 1.0 · 2026-03-10 · Optimizado para perfil AI-forward no-developer*
