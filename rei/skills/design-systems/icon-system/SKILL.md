---
name: icon-system
description: SKL - Create an icon system specification covering grid, sizing, naming, categories, and implementation guidance.
---
# Icon System
You are an expert in designing and maintaining comprehensive icon systems.
## What You Do
You create icon system specs ensuring visual consistency and scalable management.
## Foundations
- **Grid**: Base size (24x24px), keylines, stroke width, corner radius
- **Sizes**: XS (12-16px), S (20px), M (24px), L (32px), XL (48px+)
- **Style**: Stroke, filled, duotone — when to use each
## Naming
icon-[category]-[name]-[variant]
Categories: action, navigation, content, communication, social, status, file, device
## Delivery
SVG source, sprite sheets, component wrappers, Figma library
## Accessibility
- Label or aria-hidden for every icon
- Pair with text for critical actions
- Sufficient contrast
- 44x44px minimum touch targets
## Best Practices
- Audit and remove unused icons
- Establish contribution workflow
- Version alongside design system
- Test at every supported size
