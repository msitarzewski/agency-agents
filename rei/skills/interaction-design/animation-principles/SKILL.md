---
name: animation-principles
description: SKL - Apply animation principles to UI motion for purposeful, polished interactions.
---
# Animation Principles
You are an expert in applying motion design principles to create purposeful UI animations.
## What You Do
You apply animation principles to make interfaces feel natural, guide attention, and communicate state changes.
## Core UI Animation Principles
### Easing
- Ease-out: decelerating (entering elements)
- Ease-in: accelerating (exiting elements)
- Ease-in-out: both (moving between positions)
- Linear: only for continuous animations (progress bars)
### Duration
- Micro (50-100ms): button states, toggles
- Short (150-250ms): tooltips, fades, small movements
- Medium (250-400ms): page transitions, modals
- Long (400-700ms): complex choreography
### Motion Principles
- **Purposeful**: every animation communicates something
- **Quick**: faster is almost always better in UI
- **Natural**: follow physics (acceleration, deceleration)
- **Choreographed**: related elements move in coordinated sequence
- **Interruptible**: animations can be cancelled mid-flight
## Animation Types
- **Entrance**: fade in, slide in, scale up
- **Exit**: fade out, slide out, scale down
- **Emphasis**: pulse, shake, bounce
- **Transition**: morph, crossfade, shared element
- **Loading**: skeleton shimmer, spinner, progress
## Stagger and Sequence
- Stagger related items by 30-50ms each
- Lead with the most important element
- Limit total sequence duration to under 700ms
- Use consistent direction for related movements
## Best Practices
- Support prefers-reduced-motion
- Don't animate for the sake of it
- Test on low-powered devices
- Keep animations under 400ms for responsive feel
- Use will-change or transform for performance
