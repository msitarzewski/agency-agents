const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
  WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak
} = require('docx');
const fs = require('fs');

const VERDE = "2d6a4f";
const VERDE_CLARO = "e8f5e9";
const GRIS = "f5f5f5";
const GRIS_HEADER = "d5e8d5";
const NEGRO = "1a1a1a";
const ROJO = "c0392b";

const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [new TextRun({ text, bold: true, color: VERDE, size: 36 })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300, after: 160 },
    children: [new TextRun({ text, bold: true, color: NEGRO, size: 28 })]
  });
}

function h3(text) {
  return new Paragraph({
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, size: 24, color: VERDE })]
  });
}

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [new TextRun({ text, size: 22, ...opts })]
  });
}

function pMixed(runs) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    children: runs.map(r => new TextRun({ size: 22, ...r }))
  });
}

function bullet(text, ref = "bullet-main") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, size: 22 })]
  });
}

function numbered(text, ref) {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, size: 22 })]
  });
}

function codeBlock(lines) {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    shading: { fill: "f4f4f4", type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    children: lines.map((l, i) => [
      new TextRun({ text: l, font: "Courier New", size: 18, color: "333333" }),
      i < lines.length - 1 ? new TextRun({ text: "\r", break: 1 }) : null
    ]).flat().filter(Boolean)
  });
}

function separador() {
  return new Paragraph({
    spacing: { before: 200, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: "cccccc" } },
    children: [new TextRun("")]
  });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function cajaDestacada(titulo, items) {
  const rows = [
    new TableRow({
      tableHeader: true,
      children: [new TableCell({
        columnSpan: 2,
        borders: cellBorders,
        shading: { fill: GRIS_HEADER, type: ShadingType.CLEAR },
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: titulo, bold: true, size: 24, color: VERDE })]
        })]
      })]
    }),
    ...items.map(([col1, col2]) => new TableRow({
      children: [
        new TableCell({
          borders: cellBorders,
          width: { size: 3120, type: WidthType.DXA },
          shading: { fill: GRIS, type: ShadingType.CLEAR },
          children: [new Paragraph({ children: [new TextRun({ text: col1, bold: true, size: 20 })] })]
        }),
        new TableCell({
          borders: cellBorders,
          width: { size: 6240, type: WidthType.DXA },
          children: [new Paragraph({ children: [new TextRun({ text: col2, size: 20 })] })]
        })
      ]
    }))
  ];
  return new Table({ columnWidths: [3120, 6240], margins: { top: 80, bottom: 80, left: 150, right: 150 }, rows });
}

function tablaSimple(headers, rows, widths) {
  return new Table({
    columnWidths: widths,
    margins: { top: 80, bottom: 80, left: 150, right: 150 },
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => new TableCell({
          borders: cellBorders,
          width: { size: widths[i], type: WidthType.DXA },
          shading: { fill: GRIS_HEADER, type: ShadingType.CLEAR },
          children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: h, bold: true, size: 20, color: NEGRO })] })]
        }))
      }),
      ...rows.map((row, ri) => new TableRow({
        children: row.map((cell, ci) => new TableCell({
          borders: cellBorders,
          width: { size: widths[ci], type: WidthType.DXA },
          shading: { fill: ri % 2 === 0 ? "ffffff" : GRIS, type: ShadingType.CLEAR },
          children: [new Paragraph({ children: [new TextRun({ text: cell, size: 20 })] })]
        }))
      }))
    ]
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, color: VERDE, font: "Arial" },
        paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: NEGRO, font: "Arial" },
        paragraph: { spacing: { before: 300, after: 160 }, outlineLevel: 1 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullet-main", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullet-sub", levels: [{ level: 0, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1080, hanging: 360 } } } }] },
      { reference: "num-pasos", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "num-dias", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "num-anuncios", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "num-faq", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "num-wf", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "num-semana", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1260, bottom: 1440, left: 1260 } } },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: "cccccc" } },
        children: [new TextRun({ text: "Funnel Biodescodificación — GoHighLevel México", size: 18, color: "888888", italics: true })]
      })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Página ", size: 18, color: "888888" }),
          new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "888888" }),
          new TextRun({ text: " de ", size: 18, color: "888888" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, color: "888888" })
        ]
      })] })
    },
    children: [

      // ============================================================
      // PORTADA
      // ============================================================
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 1200, after: 400 },
        children: [new TextRun({ text: "FUNNEL COMPLETO DE VENTAS", bold: true, size: 56, color: VERDE, font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 200 },
        children: [new TextRun({ text: "Sesiones de Biodescodificación", size: 40, color: NEGRO, font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 200 },
        children: [new TextRun({ text: "Mercado Mexicano · GoHighLevel", size: 28, color: "888888", italics: true })]
      }),
      separador(),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 200, after: 100 },
        children: [new TextRun({ text: "Precio regular: $1,100 MXN  |  Precio especial: $800 MXN", size: 24, color: NEGRO })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 1000 },
        children: [new TextRun({ text: "Implementación completa en 1 semana", size: 22, color: "888888", italics: true })]
      }),
      pageBreak(),

      // ============================================================
      // ÍNDICE DE CONTENIDO
      // ============================================================
      h1("Contenido del Documento"),
      p("1. Análisis de Competencia"),
      p("2. Guiones de Anuncios (5 anuncios listos para grabar)"),
      p("3. Landing Page — Estructura y Textos Completos"),
      p("4. Guión del Video Explicativo (2:30 min)"),
      p("5. Configuración GoHighLevel — Paso a Paso"),
      p("6. Mensajes de WhatsApp (todas las etapas)"),
      p("7. Chatbot WhatsApp para Precalificar Leads"),
      p("8. Métricas y KPIs por Etapa"),
      p("9. Calendario de Contenido Orgánico — 30 Días"),
      p("10. Lead Magnet y Mejoras Prioritarias"),
      pageBreak(),

      // ============================================================
      // SECCIÓN 1: ANÁLISIS DE COMPETENCIA
      // ============================================================
      h1("1. Análisis de Competencia"),
      h2("Christian Flèche"),
      cajaDestacada("Christian Flèche — Perfil Competitivo", [
        ["Mensaje central", "\"El cuerpo habla lo que la mente calla\""],
        ["Emociones activadas", "Curiosidad + esperanza + alivio"],
        ["Estructura de oferta", "Contenido gratuito → charlas en vivo → formaciones profesionales"],
        ["Contenido en redes", "Casos clínicos anónimos, preguntas tipo \"¿sabías que el asma...?\", citas filosóficas"],
        ["Diferenciador", "Credibilidad científica + lenguaje accesible"],
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),
      h2("Enric Corbera / Bioneuroemoción"),
      cajaDestacada("Enric Corbera — Perfil Competitivo", [
        ["Mensaje central", "\"Tú eres el autor de tu realidad y de tu enfermedad\""],
        ["Emociones activadas", "Responsabilidad personal + poder + transformación"],
        ["Estructura de oferta", "YouTube masivo → cursos online → certificaciones"],
        ["Contenido", "Videos largos (20-40 min), frases en carrusel, testimonios de sanación en video"],
        ["Diferenciador", "Escala masiva, comunidad, academia propia"],
        ["Precio", "Cursos desde $197 USD — muy aspiracional"],
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),
      h2("Patrones que Convierten (Insights Clave)"),
      bullet("Gancho: síntoma físico conocido → pregunta retórica sobre la emoción"),
      bullet("Validación: \"la medicina lo está reconociendo\""),
      bullet("Historia personal del terapeuta (vulnerabilidad genera confianza)"),
      bullet("Caso de cliente transformado (antes/después emocional)"),
      bullet("Urgencia: cupos limitados / precio especial temporal"),
      bullet("Objeciones pre-respondidas: \"no es magia, es biología\""),
      bullet("Llamado a acción suave: \"agenda una sesión exploratoria\""),
      separador(),
      h2("Ventajas de Tu Posicionamiento en México"),
      bullet("Precio $800 MXN = barrera de entrada muy baja vs formaciones internacionales"),
      bullet("WhatsApp es el canal de cierre en México, no el email"),
      bullet("\"Exploratoria\" o \"de diagnóstico\" convierte mejor que \"sesión\""),
      bullet("La gente compra ALIVIO, no información"),
      bullet("El dolor físico es el gancho; la esperanza es el anzuelo"),
      pageBreak(),

      // ============================================================
      // SECCIÓN 2: GUIONES DE ANUNCIOS
      // ============================================================
      h1("2. Guiones de Anuncios"),
      p("Cinco guiones listos para grabar. Anuncios 1-3 para Instagram/Facebook Reels. Anuncios 4-5 formato nativo TikTok.", { italics: true }),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Anuncio #1 — \"La Migraña\" (Instagram/Facebook, 30 seg)"),
      tablaSimple(["Tiempo", "Acción / Texto"], [
        ["0-3s", "GANCHO: Texto en pantalla: \"¿Por qué te duele la cabeza aunque ya tomaste pastillas?\""],
        ["3-10s", "PROBLEMA: \"Llevas años con migraña. Ya fuiste con el neurólogo, tomaste medicamentos, cambiaste la dieta... y el dolor sigue volviendo.\""],
        ["10-20s", "GIRO: \"Lo que nadie te ha dicho es que la migraña frecuente tiene una emoción detrás: conflictos donde sientes que no puedes pensar con claridad, decisiones que te generan presión, o situaciones donde sientes que no te escuchan.\""],
        ["20-27s", "SOLUCIÓN: \"En una sesión de biodescodificación identificamos exactamente qué conflicto emocional está generando ese síntoma y trabajamos para liberarlo.\""],
        ["27-30s", "CTA: \"Esta semana tengo lugares disponibles con precio especial. Agenda tu sesión en el link de mi bio.\" | Texto: \"Sesión $800 MXN — Lugares limitados\""],
      ], [1200, 8160]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Anuncio #2 — \"El Dolor de Espalda\" (Instagram/Facebook, 45 seg)"),
      tablaSimple(["Tiempo", "Acción / Texto"], [
        ["0-4s", "GANCHO: Texto: \"El dolor de espalda no siempre es físico.\" (Tú sosteniendo algo pesado — metáfora visual)"],
        ["4-15s", "HISTORIA: \"Ana llevaba 3 años con dolor lumbar crónico. Fisioterapia, quiropráctica, acupuntura... El alivio duraba 2 semanas y volvía.\""],
        ["15-28s", "DESCUBRIMIENTO: \"Cuando trabajamos juntas descubrimos que el dolor comenzó exactamente cuando asumió el negocio de su familia que no quería. Su cuerpo cargaba literalmente lo que su mente no podía decir que no.\""],
        ["28-38s", "MECANISMO: \"La biodescodificación conecta el síntoma físico con el conflicto emocional que lo originó. No es magia — es biología del estrés.\""],
        ["38-45s", "CTA: \"Si tienes un síntoma que no cede con tratamientos, puede haber una emoción detrás. Agenda tu sesión esta semana con precio especial de $800.\""],
      ], [1200, 8160]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Anuncio #3 — \"Tiroides\" (Instagram/Facebook, 35 seg)"),
      tablaSimple(["Tiempo", "Acción / Texto"], [
        ["0-4s", "DATO IMPACTANTE: Texto en pantalla: \"El 70% de los problemas de tiroides afectan a mujeres. ¿Coincidencia?\""],
        ["4-16s", "CONTEXTO: \"La tiroides regula el metabolismo y la energía. En biodescodificación, se relaciona con conflictos de tiempo — sentir que no hay suficiente tiempo, que vas muy rápido o muy lento, que no puedes con todo.\""],
        ["16-28s", "VALIDACIÓN: \"No estoy diciendo que tires tu tratamiento médico. Estoy diciendo que si trabajas el conflicto emocional que está detrás, el cuerpo responde diferente.\""],
        ["28-35s", "CTA: \"Agenda una sesión y descubrimos juntas qué está detrás de lo que sientes.\" | Texto: \"$800 MXN — Agenda en el link\""],
      ], [1200, 8160]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Anuncio #4 — Formato Nativo TikTok (30 seg)"),
      p("Formato: \"POV / Trend + educativo\" | Música: trending suave o ASMR"),
      tablaSimple(["Tiempo", "Acción / Texto"], [
        ["0-2s", "Texto animado: \"Cosas que la medicina no te dice 🧠\""],
        ["2-8s", "VOZ rápida estilo TikTok: \"¿Sabías que el colon irritable se relaciona con el conflicto de no poder 'soltar' algo en tu vida? ¿O que el acné en la mandíbula aparece cuando sientes que no puedes defender tu territorio?\""],
        ["8-18s", "VOZ: \"Se llama biodescodificación y lleva 30 años estudiando la conexión entre emociones y síntomas físicos.\""],
        ["18-25s", "VOZ: \"Tengo sesiones individuales donde identificamos QUÉ emoción está detrás de TU síntoma específico.\""],
        ["25-30s", "\"Link en bio. Esta semana precio especial $800. Cuéntame en comentarios: ¿qué síntoma llevas tiempo cargando?\" (CTA a comentarios aumenta alcance orgánico)"],
      ], [1200, 8160]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Anuncio #5 — Storytelling Emocional TikTok (45 seg)"),
      p("Formato: \"Storytime con giro\""),
      tablaSimple(["Tiempo", "Acción / Texto"], [
        ["0-3s", "GANCHO: \"Le dije a mi doctora que mi cuerpo me estaba hablando y me miró raro 👀\""],
        ["3-20s", "HISTORIA: \"Tenía gastritis desde hace 2 años. Nexium, dieta, nada funcionaba. Un día aprendí que la gastritis se relaciona con 'algo que no puedo digerir' en mi vida — una situación, una persona, una decisión. Me pregunté: ¿qué no puedo digerir ahora? Y la respuesta me cayó como balde de agua fría.\""],
        ["20-35s", "SOLUCIÓN: \"La biodescodificación no reemplaza al médico. Trabaja en paralelo: mientras tratas el síntoma físico, también sanas el conflicto emocional que lo generó.\""],
        ["35-45s", "CTA + INTERACCIÓN: \"Si quieres saber qué emoción puede estar detrás de tu síntoma, comenta cuál es y te respondo. O agenda una sesión conmigo — link en bio, esta semana con descuento especial.\""],
      ], [1200, 8160]),
      pageBreak(),

      // ============================================================
      // SECCIÓN 3: LANDING PAGE
      // ============================================================
      h1("3. Landing Page — Estructura y Textos Completos"),

      h2("Sección 1: Hero (Arriba del doblez)"),
      cajaDestacada("Sección Hero", [
        ["Headline principal", "¿Tu cuerpo lleva años enviándote mensajes que aún no has sabido leer?"],
        ["Subheadline", "La biodescodificación identifica el conflicto emocional detrás de tu síntoma físico — para que puedas sanarlo desde la raíz, no solo callarlo."],
        ["CTA principal", "Botón verde → \"Agenda tu sesión hoy — $800 MXN\""],
        ["Texto bajo CTA", "✓ Precio regular $1,100 · Ahorra $300 esta semana"],
        ["Elemento visual", "Tu foto profesional cálida O miniatura del video explicativo"],
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Sección 2: Identificación del Problema"),
      p("Título: \"¿Te identificas con esto?\""),
      bullet("Tienes un síntoma físico que no mejora aunque haces todo lo que el médico dice"),
      bullet("Sientes que tu cuerpo reacciona a situaciones de estrés o conflicto"),
      bullet("Has notado que los síntomas empeoran en momentos difíciles de tu vida"),
      bullet("Intuyes que \"algo más\" está detrás de lo que sientes"),
      bullet("Buscas una respuesta que la medicina convencional no te ha dado"),
      new Paragraph({ spacing: { before: 120 }, children: [new TextRun("")] }),
      pMixed([
        { text: "Párrafo gancho: ", bold: true },
        { text: "\"No estás loca. No es psicosomático en el sentido de 'te lo inventas'. Tu cuerpo está respondiendo biológicamente a conflictos emocionales que no han sido resueltos. La biodescodificación te ayuda a encontrar exactamente cuáles son.\"", italics: true }
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Sección 3: Video Explicativo"),
      p("Título: \"¿Qué es la biodescodificación y cómo puede ayudarte?\""),
      p("→ Reproductor de video embebido (YouTube unlisted o Vimeo) — Ver guión completo en Sección 4."),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Sección 4: Cómo Funciona (3 Pasos)"),
      p("Título: \"Así funciona tu sesión\""),
      tablaSimple(["Paso", "Nombre", "Descripción"], [
        ["1", "Identificación", "Exploramos juntas el síntoma físico que experimentas y el contexto de vida en que apareció por primera vez."],
        ["2", "Decodificación", "Identificamos el conflicto emocional biológico que tu cuerpo está expresando a través de ese síntoma."],
        ["3", "Integración", "Trabajamos la toma de conciencia y te doy herramientas para que puedas soltar ese conflicto desde adentro."],
      ], [900, 2000, 6460]),
      p("Duración: La sesión dura aproximadamente 60-75 minutos y se realiza por videollamada o en persona.", { italics: true }),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Sección 5: Beneficios"),
      p("Título: \"Lo que puedes experimentar después de tu sesión\""),
      bullet("Claridad sobre el origen emocional de tu síntoma"),
      bullet("Alivio en la carga emocional que has cargado sin saberlo"),
      bullet("Nuevas perspectivas sobre situaciones que te generan conflicto"),
      bullet("Herramientas concretas para trabajar desde casa"),
      bullet("Una dirección clara hacia dónde enfocar tu proceso de sanación"),
      new Paragraph({ spacing: { before: 120 }, children: [new TextRun("")] }),
      pMixed([
        { text: "Disclaimer ético: ", bold: true },
        { text: "\"La biodescodificación es una terapia complementaria. No reemplaza el diagnóstico ni tratamiento médico. Trabaja en paralelo con tu proceso médico convencional.\"", italics: true }
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Sección 6: Testimonios"),
      p("Formato para cada testimonio: Foto + Nombre + Ciudad + Síntoma + Texto + Estrellas ⭐⭐⭐⭐⭐"),
      tablaSimple(["Testimonio", "Texto sugerido"], [
        ["#1 — Dolor de espalda", "\"Llevaba 4 años con dolor de espalda baja crónico. En la sesión conecté ese dolor con una situación familiar que nunca había resuelto. Salí llorando — pero de alivio. Una semana después el dolor disminuyó notablemente.\" — [Nombre, Ciudad]"],
        ["#2 — Escéptica", "\"Yo era muy escéptica. Mi terapeuta me lo recomendó. No esperaba que en una sola sesión encontráramos exactamente cuándo y por qué empezó mi ansiedad. Fue como encontrar la pieza que faltaba.\" — [Nombre, Ciudad]"],
        ["#3 — Objeción de precio", "\"Pensé que era caro pero honestamente he gastado más en pastillas que no funcionan. Valió cada peso.\" — [Nombre, Ciudad]"],
      ], [2500, 6860]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Sección 7: Oferta con Urgencia"),
      cajaDestacada("Caja de Oferta (diseñar con fondo verde claro y borde verde)", [
        ["Título", "SESIÓN INDIVIDUAL DE BIODESCODIFICACIÓN"],
        ["Precio tachado", "$1,100 MXN"],
        ["Precio especial", "$800 MXN"],
        ["Incluye", "60-75 min sesión personalizada · Identificación del conflicto raíz · Herramientas de integración · Videollamada o presencial · Grabación opcional"],
        ["Urgencia", "Timer de cuenta regresiva (72 horas) — GHL Countdown Timer Widget"],
        ["Escasez", "Solo [X] lugares disponibles esta semana"],
        ["CTA botón", "AGENDA TU SESIÓN AHORA → Calendly / GHL Calendar"],
        ["Métodos de pago", "Transferencia, Mercado Pago, OXXO Pay, tarjeta débito/crédito"],
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Sección 8: Sobre Ti (Credibilidad)"),
      p("Párrafo 1 — Credenciales: \"[Tu nombre]. Terapeuta certificada en biodescodificación y [otras certificaciones]. Llevo [X] años acompañando a personas a encontrar el origen emocional de sus síntomas.\""),
      p("Párrafo 2 — Vulnerabilidad (historia personal breve de máx 3 líneas que humanice y genere conexión)."),
      p("Párrafo 3 — Escala: \"He trabajado con más de [X] personas en México con síntomas que van desde migraña crónica hasta enfermedades autoinmunes.\""),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Sección 9: Preguntas Frecuentes"),
      tablaSimple(["Pregunta", "Respuesta"], [
        ["¿Necesito creer en esto para que funcione?", "No. Trabaja con tu historia de vida real y los conflictos concretos que has vivido. No es fe — es un proceso de reflexión guiada."],
        ["¿Debo dejar mi tratamiento médico?", "No. Es terapia complementaria. Funciona mejor en paralelo con tu tratamiento médico."],
        ["¿Qué pasa si no tengo una enfermedad diagnosticada?", "Funciona igual para síntomas físicos, emocionales o situaciones de vida que se repiten."],
        ["¿Cuántas sesiones necesito?", "Una sesión puede darte claridad importante. Dependiendo de tu proceso, algunas personas avanzan con 3-5 sesiones. Lo vemos juntas en la primera."],
        ["¿Cómo es la sesión por videollamada?", "Por Zoom o Meet. Solo necesitas estar en un lugar tranquilo, con buena conexión. La efectividad es la misma que en persona."],
        ["¿Puedo pagar en partes?", "Sí, hablemos. Escríbeme por WhatsApp: [número]"],
      ], [3500, 5860]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Sección 10: Garantía"),
      p("\"Si al final de la sesión sientes que no obtuviste ningún valor o claridad, te devuelvo tu inversión. Sin preguntas, sin complicaciones. Llevo [X] años haciendo esto y nunca he tenido que aplicar esta garantía — pero existe porque creo genuinamente en este trabajo.\""),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Sección 11: CTA Final"),
      cajaDestacada("CTA Final", [
        ["Headline", "Tu cuerpo ha esperado suficiente."],
        ["Subheadline", "Esta semana puedes empezar a entender lo que está detrás de lo que sientes."],
        ["Botón principal", "Agenda tu sesión — $800 MXN"],
        ["Botón secundario", "¿Tienes dudas? → Botón WhatsApp \"Chatear ahora\""],
      ]),
      pageBreak(),

      // ============================================================
      // SECCIÓN 4: GUIÓN DEL VIDEO
      // ============================================================
      h1("4. Guión del Video Explicativo (2:30 min)"),
      p("Duración objetivo: 2 minutos 30 segundos. Para incrustar en la landing page.", { italics: true }),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),
      tablaSimple(["Tiempo", "Segmento", "Texto a decir"], [
        ["0:00 – 0:15", "Apertura emocional", "\"¿Alguna vez has sentido que tu cuerpo trata de decirte algo pero no sabes exactamente qué? Tienes un dolor que vuelve. Un síntoma que no mejora. Y en el fondo intuyes que tiene que ver con algo más que lo que el médico puede ver en un análisis.\""],
        ["0:15 – 0:45", "Qué es", "\"La biodescodificación es una disciplina que estudia la relación entre los conflictos emocionales que vivimos y los síntomas físicos que el cuerpo produce. No es alternativa a la medicina. Es complementaria. Lo que hace es encontrar el origen emocional del síntoma para que puedas trabajarlo desde adentro. Fue desarrollada principalmente por el Dr. Christian Flèche y lleva más de 30 años de investigación clínica.\""],
        ["0:45 – 1:15", "Cómo funciona el mecanismo", "\"Nuestro cuerpo tiene una inteligencia biológica. Cuando vivimos un conflicto emocional intenso — uno que nos genera una sensación de peligro, pérdida o desesperación — el cuerpo activa una respuesta biológica para ayudarnos a sobrevivir ese conflicto. Esa respuesta, cuando el conflicto no se resuelve, se queda activa. Y con el tiempo se convierte en un síntoma físico.\""],
        ["1:15 – 1:45", "Qué pasa en una sesión", "\"Primero, exploramos el síntoma — cuándo apareció, qué pasaba en tu vida en ese momento. Segundo, identificamos el conflicto emocional biológico que el cuerpo está expresando. Tercero, trabajamos la toma de conciencia — el primer paso para que el cuerpo pueda comenzar a soltar esa respuesta de estrés. La sesión dura entre 60 y 75 minutos.\""],
        ["1:45 – 2:10", "Para quién es", "\"Esta sesión es para ti si: tienes un síntoma físico que no mejora solo con medicina, sientes que hay algo emocional detrás, ya intentaste muchas cosas y buscas una perspectiva diferente, o simplemente quieres entenderte mejor.\""],
        ["2:10 – 2:30", "CTA", "\"Mi nombre es [nombre]. Soy terapeuta certificada en biodescodificación y llevo [X] años acompañando este proceso en personas en México. Esta semana tengo lugares disponibles con un precio especial de $800 pesos — abajo encuentras el botón para agendar directamente en mi calendario. Si tienes dudas antes, escríbeme por WhatsApp. Te espero.\""],
      ], [1100, 1800, 6460]),
      pageBreak(),

      // ============================================================
      // SECCIÓN 5: CONFIGURACIÓN GOHIGHLEVEL
      // ============================================================
      h1("5. Configuración GoHighLevel — Paso a Paso"),

      h2("5.1 Qué Reemplaza GHL en Tu Funnel"),
      tablaSimple(["Herramienta anterior", "GoHighLevel reemplaza con"], [
        ["Calendly", "GHL Calendar"],
        ["Brevo / Mailchimp", "GHL Email Marketing"],
        ["UltraMsg (WhatsApp API)", "GHL WhatsApp / SMS"],
        ["n8n Workflows", "GHL Automations"],
        ["Landing page (Carrd/WordPress)", "GHL Funnels"],
        ["Hotjar (heatmaps)", "GHL Analytics"],
        ["CRM en Google Sheets", "GHL CRM nativo"],
        ["Chatbot WhatsApp", "GHL Conversation AI"],
        ["Formularios / Quiz", "GHL Forms / Surveys"],
        ["Timer de urgencia", "GHL Countdown Timer widget"],
        ["Programa de referidos", "GHL Affiliate Manager"],
      ], [4680, 4680]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("5.2 Pipeline (CRM)"),
      p("Crea un pipeline llamado: \"Sesiones Biodescodificación\" con estas etapas:"),
      numbered("Lead Captado", "num-pasos"),
      numbered("Vio Landing (sin agendar)", "num-pasos"),
      numbered("Agendó Sesión", "num-pasos"),
      numbered("Sesión Realizada", "num-pasos"),
      numbered("Cliente Recurrente", "num-pasos"),
      numbered("Embajador (dejó testimonio + refirió)", "num-pasos"),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("5.3 Calendar"),
      cajaDestacada("Configuración GHL Calendar", [
        ["Nombre", "Sesión de Biodescodificación"],
        ["Duración", "75 minutos"],
        ["Buffer entre citas", "15 minutos"],
        ["Confirmación automática", "ON"],
        ["Pago requerido", "Conecta Stripe o Mercado Pago → $800 MXN al agendar"],
        ["Recordatorios", "Configurados en el Workflow de automatización"],
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("5.4 Funnel (Landing Page en GHL Sites)"),
      p("Ruta: GHL → Sites → Funnels → New Funnel"),
      p("Páginas a crear:"),
      bullet("/sesion-biodescodificacion — Landing principal"),
      bullet("/gracias-agenda — Confirmación post-agendamiento"),
      bullet("/gracias-registro — Captura email pre-Calendar"),
      p("Widgets clave de GHL a usar:"),
      bullet("Countdown Timer → urgencia real (se resetea por contacto)"),
      bullet("Video embed → tu video explicativo de 2:30 min"),
      bullet("Calendar widget → embebe directamente el GHL Calendar"),
      bullet("Survey/Form → captura email ANTES de mostrar el calendario"),
      bullet("Chat widget → conecta con tu inbox de GHL"),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("5.5 Workflows — Las 3 Automatizaciones"),
      h3("Workflow 1: Post-Agendamiento"),
      p("Trigger: Appointment Status → Booked"),
      tablaSimple(["Acción", "Descripción"], [
        ["1. Send Email", "Confirmación de sesión (inmediata)"],
        ["2. Send WhatsApp", "Confirmación inmediata"],
        ["3. Wait", "Hasta 24h antes de la cita"],
        ["4. Send WhatsApp", "Recordatorio 24h"],
        ["5. Send Email", "\"Prepárate para mañana\""],
        ["6. Wait", "Hasta 1h antes de la cita"],
        ["7. Send WhatsApp", "Link de videollamada"],
        ["8. Wait", "24h después de la cita"],
        ["9. Move Pipeline", "→ \"Sesión Realizada\""],
        ["10. Send WhatsApp", "Seguimiento post-sesión"],
        ["11. Wait", "6 días"],
        ["12. Send Email", "Solicitud de testimonio + oferta sesión 2"],
      ], [2000, 7360]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),
      h3("Workflow 2: Retargeting (Lead sin agendar)"),
      p("Trigger: Form Submitted + Appointment NOT booked en 2 horas"),
      tablaSimple(["Acción", "Descripción"], [
        ["1. Add Tag", "\"lead-sin-agendar\""],
        ["2. Move Pipeline", "→ \"Vio Landing\""],
        ["3. Send Email", "Historia de Mariana (Día 1)"],
        ["4. Wait", "3 días"],
        ["5. IF Tag \"agendó\" existe", "→ Stop | ELSE → continúa"],
        ["6. Send Email", "Tabla síntomas/emociones (Día 3)"],
        ["7. Wait", "4 días"],
        ["8. IF Tag \"agendó\" existe", "→ Stop | ELSE → continúa"],
        ["9. Send Email", "Última oportunidad (Día 7)"],
      ], [3000, 6360]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),
      h3("Workflow 3: Post-Sesión"),
      p("Trigger: Appointment Status → Completed (marcar manualmente)"),
      tablaSimple(["Acción", "Descripción"], [
        ["1. Add Tag", "\"sesion-realizada\""],
        ["2. Wait", "24 horas"],
        ["3. Send WhatsApp", "\"¿Cómo amaneciste?\""],
        ["4. Send Email", "Seguimiento emocional"],
        ["5. Wait", "6 días"],
        ["6. Send Email", "Solicitud testimonio + oferta sesión 2"],
        ["7. Send WhatsApp", "Link formulario testimonio"],
        ["8. Move Pipeline", "→ \"Sesión Realizada\""],
      ], [2500, 6860]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("5.6 Templates de Email en GHL"),
      p("Ruta: GHL → Marketing → Emails → Templates"),
      tablaSimple(["Código", "Asunto del Email"], [
        ["CONF-01", "✅ Tu sesión de biodescodificación está confirmada, [Nombre]"],
        ["PREP-01", "Mañana es tu sesión — cómo prepararte"],
        ["SEG-01", "¿Cómo estás hoy, [Nombre]?"],
        ["TEST-01", "¿Me cuentas cómo vas? (+ algo especial para ti)"],
        ["RET-01", "La historia de Mariana (y por qué me acordé de ti)"],
        ["RET-02", "¿Sabías que el dolor de espalda puede tener una emoción detrás?"],
        ["RET-03", "Última oportunidad: $800 MXN vence hoy"],
      ], [1800, 7560]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("5.7 Conversation AI (Chatbot WhatsApp)"),
      p("Ruta: GHL → Settings → Conversation AI → Activar"),
      p("Prompt base para el bot:"),
      codeBlock([
        "Eres la asistente virtual de [Tu nombre], terapeuta especializada",
        "en biodescodificación. Eres cálida, empática y hablas en español",
        "mexicano natural.",
        "",
        "Tu objetivo: entender qué síntoma o situación trae el usuario",
        "y guiarlo a agendar una sesión de biodescodificación.",
        "",
        "Preguntas que haces en orden:",
        "1. ¿Qué síntoma o situación te trajo aquí?",
        "2. ¿Cuánto tiempo llevas con esto?",
        "3. ¿Has trabajado antes el enfoque emocional?",
        "",
        "Al final: presenta la oferta de $800 MXN y envía el link",
        "de agendamiento. Si la persona tiene dudas complejas,",
        "transfiere al humano.",
        "",
        "NUNCA hagas diagnósticos médicos. Siempre aclara que es",
        "terapia complementaria, no sustituto de la medicina.",
      ]),
      p("Activar en: WhatsApp, Instagram DM, Facebook Messenger."),
      p("Transferir a humano si: preguntas sobre precios distintos, dudas médicas específicas o solicita hablar con la terapeuta."),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("5.8 Checklist de Implementación Semanal"),
      tablaSimple(["Día", "Tareas"], [
        ["Día 1", "Crear pipeline con 6 etapas · Configurar GHL Calendar (75 min, buffer 15 min) · Conectar Mercado Pago"],
        ["Día 2", "Construir funnel en GHL Sites con todos los textos · Subir video (YouTube unlisted → embed) · Activar countdown timer"],
        ["Día 3", "Crear los 3 Workflows de automatización en GHL"],
        ["Día 4", "Crear los 7 templates de email · Configurar mensajes WhatsApp · Activar Conversation AI"],
        ["Día 5", "Conectar Meta Ads a GHL · Grabar anuncio #1 (migraña) · Lanzar con $300 MXN para testear"],
        ["Días 6-7", "Prueba end-to-end del funnel completo · Verificar que todos los workflows disparan · Ajustar copy si es necesario"],
      ], [1200, 8160]),
      pageBreak(),

      // ============================================================
      // SECCIÓN 6: MENSAJES DE WHATSAPP
      // ============================================================
      h1("6. Mensajes de WhatsApp — Todas las Etapas"),

      h2("WA-1: Confirmación (inmediato al agendar)"),
      codeBlock([
        "Hola [Nombre] 🌿",
        "",
        "¡Tu sesión de biodescodificación está confirmada!",
        "",
        "📅 *[Día, fecha]*",
        "⏰ *[Hora]* (hora CDMX)",
        "",
        "Te mando el link de videollamada 30 minutos antes.",
        "Si necesitas reagendar o tienes alguna duda, escríbeme aquí mismo.",
        "",
        "¡Nos vemos pronto! ✨",
        "[Tu nombre]",
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("WA-2: Recordatorio 24h Antes"),
      codeBlock([
        "Hola [Nombre] 👋",
        "",
        "Te recuerdo que *mañana* tienes tu sesión:",
        "",
        "📅 [Fecha]",
        "⏰ [Hora] (CDMX)",
        "",
        "*Para prepararte:*",
        "✦ Busca un espacio tranquilo y privado",
        "✦ Ten agua a la mano",
        "✦ Piensa en qué síntoma quieres explorar",
        "",
        "Te mando el link de Zoom mañana 30 min antes.",
        "¡Nos vemos! 🌿",
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("WA-3: Recordatorio 1h Antes"),
      codeBlock([
        "¡Hola [Nombre]! 🌿",
        "",
        "Tu sesión empieza *en 1 hora* ([hora]).",
        "",
        "🔗 Link de videollamada:",
        "[LINK_ZOOM_O_MEET]",
        "",
        "Si necesitas algo antes, escríbeme aquí. ¡Te espero! ✨",
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("WA-4: Seguimiento 24h Después"),
      codeBlock([
        "Hola [Nombre] 🌿",
        "",
        "¿Cómo amaneciste hoy?",
        "",
        "Quería checar cómo te sientes después de nuestra sesión.",
        "Es normal tener movimiento emocional estos días.",
        "Sé amable contigo. 🌱",
        "",
        "Si hay algo que quieras compartir o alguna duda, aquí estoy.",
        "",
        "[Tu nombre]",
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("WA-5: Solicitud de Testimonio (Día 7)"),
      codeBlock([
        "Hola [Nombre] 💚",
        "",
        "Ha pasado una semana desde nuestra sesión. ¿Cómo has estado?",
        "",
        "Si la sesión te aportó algo valioso, me ayudaría mucho",
        "si pudieras dejarme tu opinión en este formulario:",
        "",
        "👉 [LINK_FORMULARIO]",
        "",
        "Son solo 2 minutos y me ayuda un montón para llegar",
        "a más personas que lo necesitan.",
        "",
        "¡Gracias de corazón! 🌿",
        "[Tu nombre]",
      ]),
      pageBreak(),

      // ============================================================
      // SECCIÓN 7: CHATBOT WHATSAPP
      // ============================================================
      h1("7. Chatbot WhatsApp para Precalificar Leads"),
      p("Viabilidad: MUY RECOMENDADO para México — alta tasa de uso de WhatsApp Business."),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),
      h2("Flujo del Chatbot"),
      tablaSimple(["Turno", "Mensaje"], [
        ["Bot (bienvenida)", "\"Hola 🌿 Soy [nombre del bot]. Para orientarte mejor, ¿qué síntoma o situación te trajo aquí?\n1️⃣ Síntoma físico (dolor, enfermedad)\n2️⃣ Situación emocional o de vida\n3️⃣ Solo quiero saber más sobre biodescodificación\""],
        ["Bot (si elige 1 o 2)", "\"Gracias por compartirme eso. ¿Cuánto tiempo llevas con esto?\n1️⃣ Menos de 6 meses\n2️⃣ Entre 6 meses y 2 años\n3️⃣ Más de 2 años\""],
        ["Bot (siguiente)", "\"Entiendo. Una última pregunta: ¿ya has trabajado antes tu salud desde el enfoque emocional?\n1️⃣ Nunca\n2️⃣ Algo (meditación, psicología, etc.)\n3️⃣ Sí, conozco la biodescodificación\""],
        ["Bot (cierre)", "\"¡Gracias [nombre]! Con lo que me compartes, creo que una sesión puede aportarte mucha claridad.\n\nOferta especial esta semana: *$800 MXN* (regular $1,100)\n👉 Agenda aquí: [LINK CALENDLY]\n\n¿Tienes alguna duda antes de agendar?\""],
        ["Si hay duda", "→ Escala a ti (humano)"],
        ["Sin respuesta en 2h", "→ Mensaje de seguimiento automático"],
      ], [2200, 7160]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),
      h2("Métricas Meta del Chatbot"),
      tablaSimple(["Métrica", "Meta"], [
        ["Tasa de respuesta al primer mensaje", "> 60%"],
        ["Tasa de calificación completada", "> 40%"],
        ["Tasa de click a Calendly", "> 25%"],
        ["Conversión click → agenda", "> 15%"],
      ], [4680, 4680]),
      pageBreak(),

      // ============================================================
      // SECCIÓN 8: MÉTRICAS Y KPIs
      // ============================================================
      h1("8. Métricas y KPIs por Etapa del Funnel"),

      h2("Fase 1 — Tráfico (Anuncios Meta)"),
      tablaSimple(["Métrica", "Meta", "Herramienta"], [
        ["CPM (costo por mil impresiones)", "< $80 MXN", "Meta Ads Manager"],
        ["CTR del anuncio", "> 2.5%", "Meta Ads Manager"],
        ["CPC (costo por clic)", "< $5 MXN", "Meta Ads Manager"],
        ["Costo por lead", "< $80 MXN", "Meta Ads Manager"],
        ["ROAS", "> 3x", "Meta Ads Manager"],
      ], [3120, 2000, 4240]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Fase 2 — Landing Page"),
      tablaSimple(["Métrica", "Meta", "Herramienta"], [
        ["Tasa de conversión", "> 4%", "GHL Analytics / GA4"],
        ["Tiempo en página", "> 2:30 min", "GA4"],
        ["Tasa de rebote", "< 60%", "GA4"],
        ["Video play rate", "> 40%", "Vimeo / Loom Stats"],
        ["Scroll depth", "> 70%", "Hotjar free"],
      ], [3120, 2000, 4240]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Fase 3 — Agendamiento"),
      tablaSimple(["Métrica", "Meta", "Herramienta"], [
        ["Tasa landing → agenda", "> 3%", "GHL Calendar Stats"],
        ["No-shows", "< 15%", "GHL / Manual"],
        ["Cancelaciones", "< 10%", "GHL Calendar Stats"],
        ["Costo por sesión agendada", "< $200 MXN", "Calculado manualmente"],
      ], [3120, 2000, 4240]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Fase 4 — Retención y Monetización"),
      tablaSimple(["Métrica", "Meta", "Herramienta"], [
        ["Tasa 1a → 2a sesión", "> 35%", "GHL Pipeline"],
        ["NPS (encuesta satisfacción)", "> 60", "GHL Surveys"],
        ["Tasa de testimonio", "> 40%", "GHL Reputation"],
        ["Referidos por cliente", "> 0.3", "GHL Affiliate Manager"],
        ["LTV (valor de vida del cliente)", "> $2,400 MXN", "GHL Reports"],
      ], [3120, 2000, 4240]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Dashboard Semanal (revisar cada lunes)"),
      bullet("¿Cuántos leads entraron esta semana?"),
      bullet("¿Cuántos agendaron sesión?"),
      bullet("¿Cuántas sesiones se realizaron?"),
      bullet("¿Cuánto invertí en anuncios?"),
      bullet("¿Cuánto ingresé?"),
      bullet("ROAS = Ingresos totales ÷ Inversión en ads"),
      pageBreak(),

      // ============================================================
      // SECCIÓN 9: CALENDARIO DE CONTENIDO
      // ============================================================
      h1("9. Calendario de Contenido Orgánico — 30 Días"),

      h2("Semana 1 — Educación (construye autoridad)"),
      tablaSimple(["Día", "Formato", "Tema"], [
        ["Lunes", "Reel", "\"¿Qué es la biodescodificación en 60 segundos?\""],
        ["Martes", "Carrusel", "\"5 síntomas físicos y la emoción que puede esconder\""],
        ["Miércoles", "Historia", "Testimonio de cliente (con permiso)"],
        ["Jueves", "Reel", "\"El cuerpo no miente: cómo surgió la biodescodificación\""],
        ["Viernes", "Post", "Frase impactante de Flèche + reflexión tuya"],
        ["Sábado", "Historia", "Poll: \"¿Sabías que la migraña tiene una emoción detrás?\""],
        ["Domingo", "—", "Descanso"],
      ], [1400, 1400, 6560]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Semana 2 — Identificación (conecta con el problema)"),
      tablaSimple(["Día", "Formato", "Tema"], [
        ["Lunes", "Reel", "\"Si tienes esto, tu cuerpo te está hablando\" (lista de síntomas)"],
        ["Martes", "Carrusel", "\"La historia de Ana: 3 años de dolor de espalda\""],
        ["Miércoles", "Historia", "Q&A: responde preguntas de seguidores"],
        ["Jueves", "Reel", "\"¿Por qué la tiroides afecta más a mujeres?\""],
        ["Viernes", "Post", "\"Lo que la medicina convencional no te dice (y lo que sí)\""],
        ["Sábado", "Historia", "\"¿Con qué síntoma llevas más tiempo?\" (engagement)"],
        ["Domingo", "—", "Descanso"],
      ], [1400, 1400, 6560]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Semana 3 — Solución (presenta tu servicio)"),
      tablaSimple(["Día", "Formato", "Tema"], [
        ["Lunes", "Reel", "\"Así es una sesión de biodescodificación\" (detrás de cámaras)"],
        ["Martes", "Carrusel", "\"Preguntas frecuentes sobre biodescodificación\""],
        ["Miércoles", "Historia", "Cuenta regresiva a oferta especial"],
        ["Jueves", "Reel", "\"Esto NO es biodescodificación\" (desmitificar)"],
        ["Viernes", "Post", "Testimonio escrito con foto (con permiso)"],
        ["Sábado", "Historia", "\"Última semana con precio especial\" + link agenda"],
        ["Domingo", "—", "Descanso"],
      ], [1400, 1400, 6560]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Semana 4 — Urgencia + Comunidad"),
      tablaSimple(["Día", "Formato", "Tema"], [
        ["Lunes", "Reel", "\"Caso real: qué encontramos detrás del insomnio\""],
        ["Martes", "Carrusel", "\"Cómo prepararte para tu primera sesión\""],
        ["Miércoles", "Historia", "Testimonio en video 30 seg (con permiso)"],
        ["Jueves", "Reel", "\"Respondo los comentarios más comunes sobre biodescodificación\""],
        ["Viernes", "Post", "Reflexión personal + llamado a agendar"],
        ["Sábado", "Historia", "\"Últimos lugares esta semana\" + CTA directo"],
        ["Domingo", "—", "Recap del mes + anuncio del siguiente ciclo"],
      ], [1400, 1400, 6560]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Fórmula de Caption que Convierte"),
      tablaSimple(["Línea", "Función"], [
        ["Línea 1", "GANCHO — Pregunta o dato impactante"],
        ["Líneas 2-4", "PROBLEMA — Con el que se identifican"],
        ["Líneas 5-7", "SOLUCIÓN / INSIGHT — Valor real gratuito"],
        ["Línea 8", "CTA suave: \"¿Te identificas? Cuéntame en comentarios\""],
        ["Línea 9", "CTA duro (solo 2-3 veces/semana): \"Link en bio para agendar\""],
      ], [2000, 7360]),
      pageBreak(),

      // ============================================================
      // SECCIÓN 10: LEAD MAGNET Y MEJORAS
      // ============================================================
      h1("10. Lead Magnet y Mejoras Prioritarias"),

      h2("Lead Magnet Recomendado"),
      cajaDestacada("Quiz: \"Descubre qué emoción puede estar detrás de tu síntoma\"", [
        ["Formato", "Quiz de 5 preguntas → resultado personalizado por email"],
        ["Herramienta", "Tally.so (gratis e ilimitado) + GHL Workflow para enviar resultado"],
        ["Resultado incluye", "Emoción probable + mini-explicación + CTA a agendar sesión"],
        ["Por qué funciona", "Hiperpersonalizado · Alta tasa de compartir · Captura email naturalmente · Pre-vende la sesión antes de llegar a la landing"],
      ]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Mejoras Prioritarias por Impacto"),
      tablaSimple(["#", "Mejora", "Impacto estimado", "Costo"], [
        ["1", "Quiz lead magnet en landing", "+40% en captación de leads", "$0"],
        ["2", "Chatbot WhatsApp precalifica", "+25% en conversión", "$11 USD/mes (si no usas GHL AI)"],
        ["3", "Timer real en landing (urgencia)", "+15% en conversión", "$0 (GHL incluido)"],
        ["4", "Video testimonial (no solo texto)", "+20% en confianza", "$0 (solo grabar)"],
        ["5", "Botón WhatsApp flotante en landing", "+10% en conversión", "$0"],
        ["6", "Pixel Meta conectado a GHL", "Retargeting pago efectivo", "$0"],
        ["7", "OXXO Pay / Mercado Pago habilitado", "+20% en pagos completados", "$0 (comisión 3.6%)"],
        ["8", "Programa de referidos en GHL", "K-factor + crecimiento orgánico", "$0"],
        ["9", "Newsletter semanal vía GHL Email", "Retención y reactivación", "$0"],
        ["10", "Google Analytics 4 configurado", "Data real para optimizar", "$0"],
      ], [500, 3200, 2500, 3160]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Stack Tecnológico con GoHighLevel"),
      tablaSimple(["Función", "Herramienta", "Costo mensual"], [
        ["CRM + Pipeline", "GoHighLevel (incluido)", "Ya incluido en GHL"],
        ["Landing page", "GHL Funnels (incluido)", "Ya incluido en GHL"],
        ["Email marketing", "GHL Email (incluido)", "Ya incluido en GHL"],
        ["WhatsApp automation", "GHL WhatsApp (incluido)", "Ya incluido en GHL"],
        ["Chatbot IA", "GHL Conversation AI", "Ya incluido en GHL"],
        ["Calendario / Agendamiento", "GHL Calendar (incluido)", "Ya incluido en GHL"],
        ["Analytics", "GHL + Google Analytics 4", "$0 adicional"],
        ["Heatmaps", "Hotjar free tier", "$0"],
        ["Quiz / Lead magnet", "Tally.so", "$0"],
        ["Pagos México", "Mercado Pago", "$0 (3.6% por transacción)"],
        ["Video hosting", "YouTube (unlisted) o Loom", "$0"],
      ], [2500, 3500, 3360]),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("")] }),

      h2("Proyección Financiera Primer Mes"),
      tablaSimple(["Concepto", "Estimado"], [
        ["Inversión en anuncios Meta (para testear)", "$300-500 MXN / semana = $1,200-2,000 MXN/mes"],
        ["GHL (plan existente)", "Ya lo tienes"],
        ["Costo variable adicional", "~$0 con el stack actual"],
        ["Meta: 3 sesiones/semana a $800 MXN", "$9,600 MXN/mes de ingreso"],
        ["ROAS mínimo esperado", "4x-8x desde el primer mes"],
        ["Punto de equilibrio", "Solo necesitas 3 sesiones para cubrir la inversión en ads"],
      ], [4000, 5360]),
      new Paragraph({ spacing: { before: 400 }, children: [new TextRun("")] }),
      separador(),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "Documento generado como guía de implementación.", size: 20, italics: true, color: "888888" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 0 },
        children: [new TextRun({ text: "Reemplaza todos los datos entre [corchetes] con tu información real antes de publicar.", size: 20, color: ROJO })]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("funnel-biodescodificacion-ghl.docx", buffer);
  console.log("✅ Documento creado: funnel-biodescodificacion-ghl.docx");
});
