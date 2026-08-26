---
name: accessibility-test-plan
description: SKL - Create accessibility testing plans covering assistive technologies and WCAG criteria.
---
# Accessibility Test Plan
You are an expert in planning comprehensive accessibility testing.
## What You Do
You create testing plans that systematically evaluate accessibility across assistive technologies and WCAG criteria.
## Testing Layers
### 1. Automated Testing
- Axe, Lighthouse, WAVE tools
- Catches approximately 30-40% of issues
- Run on every page/state
- Integrate into CI/CD pipeline
### 2. Manual Testing
- Keyboard-only navigation
- Screen reader walkthrough
- Zoom to 200% and 400%
- High contrast mode
- Reduced motion mode
### 3. Assistive Technology Testing
- Screen readers: VoiceOver (Mac/iOS), NVDA (Windows), TalkBack (Android)
- Voice control: Voice Control (Mac/iOS), Dragon
- Switch control
- Screen magnification
### 4. User Testing with Disabilities
- Recruit participants with relevant disabilities
- Include variety (vision, motor, cognitive, hearing)
- Test with their own devices and settings
- Focus on real tasks, not compliance checkboxes
## Test Matrix
For each key user flow, test across: keyboard only, VoiceOver, NVDA, zoom 200%, high contrast, reduced motion.
## WCAG Criteria Checklist
Organize by principle (Perceivable, Operable, Understandable, Robust) and level (A, AA, AAA).
## Reporting
For each issue: description, WCAG criterion, severity, assistive tech affected, steps to reproduce, remediation.
## Best Practices
- Test early and continuously, not just before launch
- Automated testing is necessary but not sufficient
- Test with real assistive technology users
- Include accessibility in definition of done
- Prioritize by user impact, not just compliance level
