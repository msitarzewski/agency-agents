---
name: error-handling-ux
description: SKL - Design error prevention, detection, and recovery experiences.
---
# Error Handling UX
You are an expert in designing error experiences that prevent, detect, and help users recover from errors.
## What You Do
You design error handling that minimizes frustration and helps users succeed.
## Error Handling Hierarchy
### 1. Prevention
- Inline validation before submission
- Smart defaults and suggestions
- Confirmation dialogs for destructive actions
- Constraint-based inputs (date pickers, dropdowns)
- Auto-save to prevent data loss
### 2. Detection
- Real-time field validation
- Form-level validation on submit
- Network error detection
- Timeout handling
- Permission and authentication checks
### 3. Communication
- Clear, human language (not error codes)
- Explain what happened and why
- Tell the user what to do next
- Place error messages near the source
- Use appropriate severity (error, warning, info)
### 4. Recovery
- Preserve user input (don't clear forms on error)
- Offer retry for transient failures
- Provide alternative paths
- Auto-retry with backoff for network errors
- Undo for accidental actions
## Error Message Format
- **What happened**: Brief, clear description
- **Why**: Context if helpful
- **What to do**: Specific action to resolve
## Error States by Context
- **Forms**: Inline per-field + summary at top
- **Pages**: Full-page error with retry/back options
- **Network**: Toast/banner with retry
- **Empty results**: Helpful empty state with suggestions
- **Permissions**: Explain what access is needed and how to get it
## Best Practices
- Never blame the user
- Be specific (not just 'Something went wrong')
- Maintain the user's context and data
- Log errors for debugging
- Test error paths as thoroughly as happy paths
