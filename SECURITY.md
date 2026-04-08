# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly. Do NOT open a public GitHub issue for security vulnerabilities. Open a private security advisory via GitHub Security tab.

## Response Timeline

- Acknowledgment: within 48 hours
- Initial assessment: within 7 days
- Fix or mitigation: depends on severity

## Scope

This repository contains Markdown-based agent definitions and shell scripts for installation and conversion.

### Agent files (.md)
- Non-executable prompt definitions
- No API keys, secrets, or credentials should be stored in agent files

### Shell scripts (scripts/)
- install.sh, convert.sh, and lint-agents.sh are executable
- Contributors should review scripts for unintended behavior before running

## Best Practices for Contributors

- Never commit API keys, tokens, or credentials
- Never add executable code inside agent Markdown files
- Shell scripts must be reviewed before merging
- Report suspicious agent definitions that attempt prompt injection
EOFcat SECURITY.md
