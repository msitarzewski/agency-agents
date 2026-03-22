# Charity Coin (CHA) Brand Guidelines

**Version:** 1.0
**Last Updated:** March 2026

---

## 1. Brand Story & Mission

### Mission Statement

Charity Coin transforms every transaction into tangible impact. By embedding charitable giving directly into the mechanics of a token, we make generosity automatic, transparent, and collectively powerful.

### Brand Story

Charity Coin was born from a simple observation: the crypto economy moves billions of dollars every day, yet the infrastructure for giving back is fragmented, opaque, and bolted on as an afterthought. We asked --- what if generosity were not an afterthought but a fundamental property of money itself?

CHA is the answer. Every transaction automatically allocates a portion to verified charitable causes chosen by the community. A deflationary burn mechanism ensures the token grows scarcer as impact grows larger. Governance puts the community in the driver's seat, voting on which causes receive funding and how the protocol evolves.

We are not a charity that happens to use crypto. We are a financial protocol where doing good is the default.

### Brand Pillars

| Pillar | Description |
|---|---|
| **Transparency** | Every fee, every burn, every donation is on-chain and verifiable. No black boxes. |
| **Community Ownership** | Token holders govern the protocol. Causes are chosen democratically. |
| **Effortless Impact** | Giving happens automatically with every transaction --- no extra steps. |
| **Financial Integrity** | Sound tokenomics, deflationary mechanics, and sustainable design. |
| **Inclusivity** | Anyone, anywhere, with any amount can participate in making the world better. |

---

## 2. Logo

### Description

The Charity Coin logo depicts a stylized coin viewed at a slight three-quarter angle. At the center of the coin sits a heart shape whose top curves transition into a flame motif, representing both compassion (heart) and transformation (flame/burn). The flame rises from the heart's center, symbolizing the deflationary burn mechanism that fuels charitable impact.

### Primary Logo

- Full-color version on light backgrounds: emerald coin with amber flame-heart
- Full-color version on dark backgrounds: lighter emerald coin with bright amber flame-heart
- The coin's edge has a subtle bevel conveying depth and credibility

### Logo Variations

| Variation | Usage |
|---|---|
| **Full-color (horizontal)** | Primary usage. Logo mark + "Charity Coin" wordmark to the right. |
| **Full-color (stacked)** | When horizontal space is limited. Wordmark below the mark. |
| **Logo mark only** | App icons, favicons, social avatars. Minimum 32px. |
| **Monochrome white** | On dark or photographic backgrounds. |
| **Monochrome dark** | On light backgrounds where color is not available. |

### Clear Space

Maintain a minimum clear space equal to the height of the flame tip around all sides of the logo. No other graphic elements, text, or edges should encroach on this space.

### Minimum Size

- **Digital:** 24px height for the mark only; 120px width for the full horizontal lockup.
- **Print:** 10mm height for the mark only; 50mm width for the full horizontal lockup.

### Logo Don'ts

- Do not rotate or skew the logo.
- Do not change the colors of individual logo elements.
- Do not place the full-color logo on busy or low-contrast backgrounds.
- Do not add drop shadows, outlines, or effects.
- Do not redraw or recreate the logo --- always use supplied assets.
- Do not animate individual parts of the logo without brand team approval.
- Do not stretch or distort the proportions.

---

## 3. Color Palette

### Primary --- Emerald Green

The emerald palette represents growth, trust, and the financial nature of the protocol.

| Swatch | Name | Hex | CSS Variable | Usage |
|---|---|---|---|---|
| | Primary 900 | `#064e3b` | --- | Darkest accent, rarely used |
| | Primary 800 | `#065f46` | `--color-primary-dark` | Hero gradients, deep backgrounds |
| | Primary 700 | `#047857` | `--color-primary` | **Primary brand color.** Buttons, headers, key actions |
| | Primary 600 | `#059669` | --- | Hover states, secondary accents |
| | Primary 500 | `#10b981` | `--color-primary-light` | Success indicators, highlights |
| | Primary 100 | `#d1fae5` | --- | Light backgrounds, subtle fills |
| | Primary 50 | `#ecfdf5` | --- | Hover states on outlines, tinted backgrounds |

### Secondary --- Amber

Amber represents energy, the burn mechanism, and warmth.

| Swatch | Name | Hex | CSS Variable | Usage |
|---|---|---|---|---|
| | Amber 600 | `#d97706` | `--color-secondary-dark` | Dark amber for contrast |
| | Amber 500 | `#f59e0b` | `--color-secondary` | **Secondary brand color.** Burn indicators, CTAs |
| | Amber 400 | `#fbbf24` | `--color-secondary-light` | Burn animations, glow effects |
| | Amber 100 | `#fef3c7` | --- | Light amber backgrounds |

### Accent --- Sky Blue

| Swatch | Name | Hex | CSS Variable | Usage |
|---|---|---|---|---|
| | Sky 700 | `#0369a1` | `--color-accent-dark` | Deep accent |
| | Sky 600 | `#0284c7` | `--color-accent` | Links, informational elements |
| | Sky 500 | `#0ea5e9` | `--color-accent-light` | Hover states on accent |

### Cause Colors

Each supported cause has a dedicated color for instant visual identification across the dApp.

| Cause | Color Name | Hex | CSS Variable | Tailwind Token |
|---|---|---|---|---|
| Global Health | Health Red | `#ef4444` | `--color-health` | `health-red` |
| Education | Education Blue | `#3b82f6` | `--color-edu` | `edu-blue` |
| Environment | Environment Green | `#22c55e` | `--color-env` | `env-green` |
| Clean Water | Water Cyan | `#06b6d4` | `--color-water` | `water-cyan` |
| Zero Hunger | Hunger Orange | `#f97316` | `--color-hunger` | `hunger-orange` |

**Cause color usage rules:**
- Use cause colors for badges, category indicators, and chart segments.
- Never use a cause color as a primary action color --- reserve that for the emerald palette.
- Each cause color has a `-light` variant for backgrounds (e.g., `bg-health-red-light`).

### Neutrals & Semantic Colors

| Token | Light Mode | Dark Mode | Usage |
|---|---|---|---|
| `--color-bg` | `#ffffff` | `#0f172a` | Page background |
| `--color-bg-secondary` | `#f9fafb` | `#1e293b` | Card / section background |
| `--color-text` | `#111827` | `#f1f5f9` | Primary body text |
| `--color-text-secondary` | `#6b7280` | `#94a3b8` | Secondary / muted text |
| `--color-border` | `#e5e7eb` | `#334155` | Dividers, card borders |

### Gradients

| Name | Definition | Usage |
|---|---|---|
| `gradient-primary` | `bg-gradient-to-r from-primary-600 to-primary-700` | Buttons, banners |
| `gradient-hero` | `bg-gradient-to-br from-primary-900 via-primary-800 to-primary-700` | Hero sections, page headers |
| `burn-glow` | `box-shadow: 0 0 20px rgba(245,158,11,0.3), 0 0 60px rgba(245,158,11,0.1)` | Burn event animations |

---

## 4. Typography

### Primary Typeface --- Inter

Inter is used for all UI text, body copy, and headings. It is an open-source variable font optimized for screen readability.

- **Source:** [Google Fonts](https://fonts.google.com/specimen/Inter) or self-hosted
- **Weights used:** 400 (Regular), 500 (Medium), 600 (SemiBold), 700 (Bold)

### Display / Hero Typeface Recommendations

For hero sections, landing pages, and marketing materials where a more expressive typeface is desired:

| Font | Style | Source | Notes |
|---|---|---|---|
| **Cal Sans** | Geometric sans-serif | [cal.com](https://github.com/calcom/font) | Open source. Strong, modern. Good for hero headlines. |
| **Plus Jakarta Sans** | Humanist sans-serif | Google Fonts | Warm, approachable. Pairs well with Inter body text. |
| **Space Grotesk** | Geometric sans-serif | Google Fonts | Techy but friendly. Works for dashboard headings. |

### Type Scale

| Level | Size | Weight | Line Height | Letter Spacing | Usage |
|---|---|---|---|---|---|
| Display | 48px / 3rem | 700 | 1.1 | -0.02em | Hero headlines |
| H1 | 36px / 2.25rem | 700 | 1.2 | -0.015em | Page titles |
| H2 | 30px / 1.875rem | 600 | 1.25 | -0.01em | Section headers |
| H3 | 24px / 1.5rem | 600 | 1.3 | -0.005em | Sub-section headers |
| H4 | 20px / 1.25rem | 600 | 1.35 | 0 | Card titles |
| Body Large | 18px / 1.125rem | 400 | 1.6 | 0 | Lead paragraphs |
| Body | 16px / 1rem | 400 | 1.6 | 0 | Default body text |
| Body Small | 14px / 0.875rem | 400 | 1.5 | 0 | Secondary text, captions |
| Caption | 12px / 0.75rem | 500 | 1.4 | 0.01em | Labels, badges, metadata |

### Monospace

Use `JetBrains Mono` or `Fira Code` for:
- Wallet addresses
- Transaction hashes
- Token amounts
- Code snippets

---

## 5. Tone of Voice

### Personality

Charity Coin speaks as a **knowledgeable ally** --- confident but never arrogant, optimistic but never naive. We are the friend who understands both DeFi mechanics and why clean water matters.

### Voice Attributes

| Attribute | What It Means | Example |
|---|---|---|
| **Empowering** | We put agency in users' hands. | "You choose the cause. Your vote shapes the future." |
| **Transparent** | We explain how things work plainly. | "2.5% of each transaction goes directly to verified charities --- here's the on-chain proof." |
| **Community-driven** | We speak as "we," not "the company." | "Together, we've burned 12M CHA and funded three new water projects." |
| **Accessible** | We avoid unnecessary jargon. | "When tokens are burned, they're permanently removed --- making your remaining tokens rarer." |
| **Grounded** | We celebrate real impact, not hype. | "Last quarter: 45,000 meals funded. Not promises --- deliveries." |

### Writing Guidelines

- **Lead with impact, follow with mechanics.** "Fund clean water with every swap" before "2.5% fee allocation via smart contract."
- **Use active voice.** "The community voted to add Education" not "Education was added by a community vote."
- **Be specific.** Numbers, dates, and on-chain references build trust.
- **Avoid hyperbole.** Never say "to the moon," "revolutionary," or "game-changing." Let the impact speak.
- **Respect the reader's intelligence.** Explain concepts without being condescending.

### Terminology

| Use | Don't Use |
|---|---|
| Token holders | Investors |
| Community | Users |
| Burn (with explanation on first use) | Destroy |
| Charitable allocation | Charity tax |
| Governance vote | Decision |
| CHA | $CHA, CHAR, CharityCoin |

---

## 6. Component & UI Patterns

### Buttons

Buttons follow a consistent pattern defined in `button.tsx`:

- **Default (Primary):** Emerald 700 background, white text. For primary actions (Connect Wallet, Vote, Swap).
- **Secondary:** Amber 500 background, white text. For burn-related actions and secondary CTAs.
- **Outline:** Emerald 700 border, emerald text. For secondary options alongside a primary button.
- **Ghost:** Gray text on transparent. For tertiary actions, navigation items.
- **Destructive:** Red 600 background. For irreversible actions only.
- **Link:** Emerald underline. For inline navigation.

Sizes: `sm` (32px), `md` (40px), `lg` (48px), `icon` (40x40px).

### Cards

- Use the `.glass-card` utility: white/80 background with backdrop blur, subtle border, 2xl border radius.
- Cards representing causes should include a left-side accent bar or top badge using the appropriate cause color.

### Spacing

Follow a 4px base grid. Use Tailwind's default spacing scale (4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96).

### Border Radius

| Token | Value | Usage |
|---|---|---|
| `rounded-md` | 6px | Small elements, badges |
| `rounded-lg` | 8px | Buttons, inputs |
| `rounded-xl` | 12px | Cards (small) |
| `rounded-2xl` | 16px | Cards (large), modals |
| `rounded-full` | 9999px | Avatars, pills |

---

## 7. Do's and Don'ts

### Do's

- Use the emerald-to-amber color relationship consistently: emerald for trust/action, amber for burn/energy.
- Maintain high contrast ratios (WCAG AA minimum) for all text.
- Use cause colors only in the context of their respective cause.
- Include on-chain proof links whenever citing impact numbers.
- Use the glass-card pattern for content containers.
- Test all designs in both light and dark modes.
- Use real data in mockups whenever possible --- it builds trust.
- Pair every metric with context ("12M CHA burned --- equivalent to 45,000 meals funded").

### Don'ts

- Don't use cause colors as decorative accents unrelated to their cause.
- Don't use more than two brand colors in a single component (emerald + amber is the limit).
- Don't use gradients on body text.
- Don't place the amber burn-glow effect on non-burn-related elements.
- Don't use stock photography of people holding coins or pointing at charts.
- Don't use the logo at sizes below the minimum without switching to the mark-only variant.
- Don't mix Inter with more than one display typeface in the same layout.
- Don't use language that sounds like financial advice ("invest," "returns," "guaranteed").
- Don't reference specific token price or price predictions in any brand materials.
