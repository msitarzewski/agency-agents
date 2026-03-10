# DRISK Platform — Technical Architecture & UX Foundation

**Source:** project-specs/drisk-setup.md, project-tasks/drisk-tasklist.md  
**Agent:** ArchitectUX  
**Date:** 2025-03-10

---

## 1. Overview

This document defines the technical architecture and UX foundation for the DRISK (Digital Risk Intelligence for Security) platform. It provides developers with solid foundations for implementation, including CSS design system, layout framework, information architecture, and component conventions.

---

## 2. Tech Stack Context

- **Frontend:** Next.js (React)
- **Database:** PostgreSQL (direct connection — Prisma, Drizzle, or `pg`)
- **Auth:** NextAuth, Passport, or custom auth (no Supabase)
- **Storage:** Local filesystem or S3-compatible (no Supabase Storage)
- **Hosting:** Vercel (or similar)

---

## 3. Primary Navigation (8 Items)

The main application navigation must include these 8 items in order:

| Order | Nav Item | Route | Purpose |
|-------|----------|-------|---------|
| 1 | Dashboard | `/dashboard` | Main dashboard (screen 2) |
| 2 | Clients | `/clients` | Client list (screen 3) |
| 3 | Estates | `/estates` | Estate list (screen 5) |
| 4 | Sites | `/sites` | Site list (screen 7) |
| 5 | Assessments | `/assessments` | Assessment list (screen 10) |
| 6 | Actions | `/actions` | Action list (screen 14) |
| 7 | Reports | `/reports` | Report list (screen 16) |
| 8 | Admin | `/admin` | Admin template & user management (screens 18, 19) |

**Theme toggle:** Always accessible in header/navigation (light/dark/system).

---

## 4. Information Architecture — 19 MVP Screens

### Screen Hierarchy

```
Login (unauthenticated)
└── Dashboard

Dashboard
├── Clients
│   ├── Client List
│   ├── Create Client
│   └── Edit Client
├── Estates
│   ├── Estate List
│   ├── Create Estate
│   └── Edit Estate
├── Sites
│   ├── Site List
│   ├── Create Site
│   ├── Edit Site
│   └── Site Profile
├── Assessments
│   ├── Assessment List
│   ├── Create Assessment
│   ├── Assessment Screen (questions)
│   └── Assessment Review
├── Actions
│   ├── Action List
│   └── Action Detail
├── Reports
│   ├── Report List
│   └── Report View
└── Admin
    ├── Template / Question Management
    └── User Management
```

### Screen-to-Route Mapping

| Screen | Route | Parent |
|--------|-------|--------|
| 1. Login | `/login` | — |
| 2. Main Dashboard | `/dashboard` | — |
| 3. Client List | `/clients` | — |
| 4. Create/Edit Client | `/clients/new`, `/clients/[id]` | Clients |
| 5. Estate List | `/estates` | — |
| 6. Create/Edit Estate | `/estates/new`, `/estates/[id]` | Estates |
| 7. Site List | `/sites` | — |
| 8. Create/Edit Site | `/sites/new`, `/sites/[id]` | Sites |
| 9. Site Profile | `/sites/[id]` | Sites |
| 10. Assessment List | `/assessments` | — |
| 11. Create Assessment | `/assessments/new` | Assessments |
| 12. Assessment Screen | `/assessments/[id]` | Assessments |
| 13. Assessment Review | `/assessments/[id]/review` | Assessments |
| 14. Action List | `/actions` | — |
| 15. Action Detail | `/actions/[id]` | Actions |
| 16. Report List | `/reports` | — |
| 17. Report View | `/reports/[id]` | Reports |
| 18. Admin Template | `/admin/templates` | Admin |
| 19. User Management | `/admin/users` | Admin |

---

## 5. CSS Design System

### File Location

- **Primary:** `css/design-system.css`
- **Imported:** In `app/globals.css` or root layout

### Color Palette (DRISK)

**Light Theme:**
- `--bg-primary`: `#ffffff`
- `--bg-secondary`: `#f8fafc`
- `--text-primary`: `#0f172a`
- `--text-secondary`: `#64748b`
- `--border-color`: `#e2e8f0`

**Dark Theme:**
- `--bg-primary`: `#0f172a`
- `--bg-secondary`: `#1e293b`
- `--text-primary`: `#f8fafc`
- `--text-secondary`: `#94a3b8`
- `--border-color`: `#334155`

**Brand Colors:**
- `--primary-500`: `#0ea5e9` (Sky blue — trust, clarity)
- `--primary-600`: `#0284c7`
- `--primary-700`: `#0369a1`
- `--secondary-500`: `#64748b`
- `--accent-500`: `#f59e0b` (Amber — alerts, attention)

**Risk Band Colors:**
- `--risk-low`: `#22c55e` (0–15)
- `--risk-moderate`: `#eab308` (16–30)
- `--risk-high`: `#f97316` (31–50)
- `--risk-very-high`: `#ef4444` (51–75)
- `--risk-critical`: `#b91c1c` (76+)

**Semantic Colors:**
- `--success`: `#22c55e`
- `--warning`: `#f59e0b`
- `--error`: `#ef4444`
- `--info`: `#0ea5e9`

### Typography Scale

| Token | Size | Use |
|-------|------|-----|
| `--text-xs` | 0.75rem (12px) | Labels, captions |
| `--text-sm` | 0.875rem (14px) | Body small, table cells |
| `--text-base` | 1rem (16px) | Body default |
| `--text-lg` | 1.125rem (18px) | Lead body |
| `--text-xl` | 1.25rem (20px) | H3 |
| `--text-2xl` | 1.5rem (24px) | H2 |
| `--text-3xl` | 1.875rem (30px) | H1 |

**Font Stack:**
- Primary: `system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- Monospace: `ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace`

### Spacing System (4px base)

| Token | Value | Use |
|-------|-------|-----|
| `--space-1` | 0.25rem (4px) | Tight gaps |
| `--space-2` | 0.5rem (8px) | Inline spacing |
| `--space-3` | 0.75rem (12px) | Form padding |
| `--space-4` | 1rem (16px) | Section padding |
| `--space-6` | 1.5rem (24px) | Section gaps |
| `--space-8` | 2rem (32px) | Major sections |
| `--space-12` | 3rem (48px) | Page sections |
| `--space-16` | 4rem (64px) | Hero spacing |

### Layout Breakpoints

| Breakpoint | Min Width | Target |
|------------|-----------|--------|
| `sm` | 640px | Tablet portrait |
| `md` | 768px | Tablet landscape |
| `lg` | 1024px | Desktop |
| `xl` | 1280px | Large desktop |

### Container Widths

| Token | Max Width |
|-------|-----------|
| `--container-sm` | 640px |
| `--container-md` | 768px |
| `--container-lg` | 1024px |
| `--container-xl` | 1280px |

---

## 6. Layout Framework

### Grid Patterns

- **List/Table:** Full width, single column on mobile; 2–3 columns on desktop for filters
- **Form:** Max 2 columns on desktop; single column on mobile
- **Dashboard:** 2–4 column grid on desktop; collapse to 1 on mobile
- **Site Profile:** Main content + sidebar; sidebar stacks below on mobile

### Responsive Strategy

- Mobile-first: Base styles for 320px+
- Breakpoints: sm (640), md (768), lg (1024), xl (1280)

---

## 7. Component Hierarchy

### Level 1: Layout Components
- `Layout` — App shell with nav + sidebar
- `Container` — Max-width wrapper
- `PageHeader` — Title + breadcrumb + actions

### Level 2: Content Components
- `Card` — Content blocks
- `DataTable` — Lists with sort/filter
- `FormSection` — Grouped form fields

### Level 3: Interactive Components
- `Button` (primary, secondary, ghost, danger)
- `Input`, `Select`, `Textarea`, `Checkbox`, `Radio`
- `Badge` (risk band, status)
- `Tabs` — Domain grouping
- `Modal` — Confirmations, forms

### Level 4: Utility Components
- `Spinner`, `Skeleton`
- `Toast` — Notifications
- `EmptyState` — No data messaging

---

## 8. Naming Conventions

### CSS Classes
- BEM: `block__element--modifier`
- Example: `card__header`, `card--elevated`

### React Components
- PascalCase: `SiteProfile`, `AssessmentList`
- File: `SiteProfile.tsx`

### Routes
- kebab-case: `/site-profile`, `/assessment-list`

### CSS Variables
- `--{category}-{name}`: `--color-primary-500`, `--space-4`

---

## 9. Theme Toggle Specification

### Required
- **Light** — User preference
- **Dark** — User preference
- **System** — Follow `prefers-color-scheme`

### Implementation

```html
<div class="theme-toggle" role="radiogroup" aria-label="Theme selection">
  <button class="theme-toggle-option" data-theme="light" role="radio">Light</button>
  <button class="theme-toggle-option" data-theme="dark" role="radio">Dark</button>
  <button class="theme-toggle-option" data-theme="system" role="radio">System</button>
</div>
```

### JavaScript
- Store preference in `localStorage` key `theme`
- Apply `data-theme="light"` or `data-theme="dark"` on `<html>`
- For `system`: remove `data-theme`, use `@media (prefers-color-scheme: dark)`

### Placement
- Header: Right side of nav, near user menu
- Always visible and accessible

---

## 10. Accessibility Foundation

- **WCAG 2.1 AA** minimum
- **Keyboard navigation:** Full tab order, focus indicators
- **Screen reader:** Semantic HTML, ARIA labels where needed
- **Color contrast:** 4.5:1 for normal text, 3:1 for large text
- **Touch targets:** 44px minimum for interactive elements

---

## 11. Risk Band Badge Styling

| Band | Score | Color | Background |
|------|-------|-------|------------|
| Low | 0–15 | `--risk-low` | `rgba(34, 197, 94, 0.15)` |
| Moderate | 16–30 | `--risk-moderate` | `rgba(234, 179, 8, 0.15)` |
| High | 31–50 | `--risk-high` | `rgba(249, 115, 22, 0.15)` |
| Very High | 51–75 | `--risk-very-high` | `rgba(239, 68, 68, 0.15)` |
| Critical | 76+ | `--risk-critical` | `rgba(185, 28, 28, 0.15)` |

---

## 12. Developer Handoff

### Priority Order
1. Implement design system variables in `css/design-system.css`
2. Create base layout with responsive container and nav
3. Build reusable component templates
4. Add content with proper hierarchy
5. Implement theme toggle and interactive polish

### Files to Create
- `css/design-system.css` — Variables and base styles
- `app/layout.tsx` — Root layout with nav
- `components/ui/` — Reusable components

---

**ArchitectUX** | DRISK Technical Architecture | Foundation ready for Step 3 (DB + API) and Step 4 (Scaffold)
