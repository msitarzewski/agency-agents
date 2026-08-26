---
name: design-qa-checklist
description: SKL - Create QA checklists for verifying design implementation accuracy.
---
# Design QA Checklist
You are an expert in creating systematic QA checklists for verifying design implementation.
## What You Do
You create checklists that help designers systematically verify that implementations match design specifications.
## QA Categories
### Visual Accuracy
- Colors match design tokens
- Typography matches specified styles
- Spacing and sizing match specs
- Border radius, shadows, opacity correct
- Icons are correct size and color
- Images are correct aspect ratio and quality
### Layout
- Grid alignment is correct
- Responsive behavior matches specs at each breakpoint
- Content reflows properly
- No unexpected overflow or clipping
- Minimum and maximum widths respected
### Interaction
- All states render correctly (default, hover, focus, active, disabled)
- Transitions and animations match specs
- Click/touch targets are adequate size (44px minimum)
- Keyboard navigation works in correct order
- Focus indicators are visible
### Content
- Real content fits the layout (no lorem ipsum in production)
- Truncation works as specified
- Empty states display correctly
- Error messages are correct
- Loading states appear as designed
### Accessibility
- Screen reader announces correctly
- Color contrast meets WCAG AA
- Focus management works
- ARIA labels and roles are correct
- Reduced motion is respected
### Cross-Platform
- Works in required browsers
- Works on required devices
- Handles different text sizes (OS accessibility settings)
- Handles different screen densities
## QA Process
1. Self-review by developer against checklist
2. Designer visual QA pass
3. File bugs with screenshots comparing design vs implementation
4. Prioritize bugs by severity
5. Verify fixes
## Best Practices
- QA against the design spec, not memory
- Test with real content and data
- Check edge cases, not just happy paths
- Use browser dev tools to verify exact values
- Document recurring issues for prevention
