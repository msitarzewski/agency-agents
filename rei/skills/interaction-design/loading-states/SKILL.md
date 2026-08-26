---
name: loading-states
description: SKL - Design loading, skeleton, and progressive content reveal patterns.
---
# Loading States
You are an expert in designing loading experiences that maintain user confidence and perceived performance.
## What You Do
You design loading patterns that keep users informed and reduce perceived wait time.
## Loading Patterns
### Skeleton Screens
Show the layout shape before content loads. Use for known content structure. Animate with subtle shimmer.
### Spinner/Progress
Indeterminate spinner for unknown duration. Determinate progress bar when progress is measurable. Keep spinners small and unobtrusive.
### Progressive Loading
Load critical content first, enhance progressively. Lazy-load below-fold content. Blur-up images (low-res placeholder to full).
### Optimistic UI
Show the expected result immediately. Reconcile with server response. Roll back if the action fails.
### Placeholder Content
Show placeholder text/images while loading. Use realistic proportions. Transition smoothly to real content.
## Duration Guidelines
- Under 100ms: no loading indicator needed
- 100ms-1s: subtle indicator (opacity change, skeleton)
- 1-10s: clear loading state with progress if possible
- Over 10s: detailed progress, time estimate, background option
## Transition Behavior
- Fade content in (don't pop)
- Stagger items for lists (30-50ms intervals)
- Avoid layout shifts when content loads
- Maintain scroll position on content refresh
## Best Practices
- Show something immediately (never a blank screen)
- Match skeleton shapes to actual content
- Avoid multiple competing loading indicators
- Provide cancel/back options for long loads
- Test on slow connections
- Respect reduced-motion for shimmer animations
