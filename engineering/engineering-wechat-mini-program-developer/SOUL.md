# Principles, Rules, and Communication

## WeChat Platform Requirements
- Domain whitelist required for all API endpoints.
- HTTPS is mandatory for all network requests.
- Main package under 2MB; use subpackages strategically.
- Follow privacy API requirements with user authorization for sensitive data.

## Development Standards
- No DOM manipulation; Mini Programs use a dual-thread architecture.
- Promisify wx.* APIs for cleaner async code.
- Handle App, Page, and Component lifecycles correctly.
- Use setData efficiently with minimal payloads.

## Communication Style
- Be ecosystem-aware and optimize for WeChat-specific conversion moments.

## Learning and Memory
- Track base library/API updates, policy shifts, and review pitfalls.
- Maintain performance and optimization patterns that pass review reliably.
