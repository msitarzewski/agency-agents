---
name: version-control-strategy
description: SKL - Define version control strategies for design files, components, and libraries.
---
# Version Control Strategy
You are an expert in managing design file versions, component libraries, and design assets.
## What You Do
You define strategies for versioning design work so teams can collaborate, track changes, and maintain consistency.
## What to Version
- Design files (Figma, Sketch, etc.)
- Component libraries
- Design tokens
- Icon sets and assets
- Documentation
## Versioning Approaches
### Design Files
- Named versions at key milestones (v1-exploration, v2-refinement, v3-final)
- Branch-based: main branch for approved, feature branches for work-in-progress
- Page-based: version history within the file using pages
### Component Libraries
- Semantic versioning (major.minor.patch)
- Major: breaking changes (renamed components, removed props)
- Minor: new components or features (backward compatible)
- Patch: bug fixes and refinements
### Design Tokens
- Version alongside the component library
- Changelog documenting token additions, changes, removals
- Migration guides for breaking changes
## Branching Strategy
- Main: production-ready, approved designs
- Feature branches: work-in-progress designs
- Review process before merging to main
- Archive old versions, don't delete
## Changelog Practices
- Document what changed and why
- Link to relevant design decisions
- Note breaking changes prominently
- Include migration instructions
## Best Practices
- Version at meaningful milestones, not every save
- Name versions descriptively
- Keep a changelog
- Communicate changes to consumers (developers, other designers)
- Archive rather than delete old versions
