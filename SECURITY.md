# Security Policy & Best Practices

## Overview

This document outlines security considerations and best practices for agency-agents and its integration with AI tools.

## Known Security Considerations

### 1. Prompt Injection Prevention

**Issue**: Agent prompts may process untrusted user input (GitHub issues, comments, user messages).

**Risk**: Malicious users can embed hidden directives in issues or messages to manipulate agent behavior, potentially:
- Leaking sensitive information
- Bypassing security checks
- Executing unauthorized actions

**Mitigation**:
- Use `sanitizePromptInput()` utility (see below) for any user-provided data
- Never interpolate raw user input directly into prompts
- Validate and escape special characters before agent processing
- Use allowlists for acceptable input patterns when possible

**Example - BEFORE (unsafe)**:
```javascript
const agentPrompt = `Process this issue: ${userSubmittedIssue}`;
```

**Example - AFTER (safe)**:
```javascript
const sanitized = sanitizePromptInput(userSubmittedIssue);
const agentPrompt = `Process this issue: ${sanitized}`;
```

### 2. GitHub Actions Security

**Issue**: Shell scripts in CI/CD environments have access to high-privilege tokens.

**Risk**: 
- Prompt injection in GitHub Actions → token exfiltration
- Shell command injection → arbitrary code execution
- Credential leakage in logs

**Mitigation**:
- Never use `--yolo` mode in production workflows
- Restrict token permissions with `permissions:` in workflow files
- Use environment variables (GitHub Secrets) instead of hardcoding credentials
- Sanitize any AI-generated shell commands before execution
- Log only non-sensitive output

**Example - Secure workflow**:
```yaml
jobs:
  safe-agent:
    runs-on: ubuntu-latest
    permissions:
      contents: read  # ← Minimal needed
      pull-requests: read
    steps:
      - uses: actions/checkout@v3
      - name: Run agent
        run: |
          # Use secrets via environment, never in command line
          my-agent-tool --safe-mode
```

### 3. Shell Script Injection Protection

**Issue**: Dynamic shell commands without proper escaping are vulnerable to injection.

**Risk**: Attackers can break out of intended command structure to execute arbitrary commands.

**Mitigation**:
- Use `escapeShellArg()` for any variable that becomes a shell argument
- Prefer structured APIs over shell interpolation when possible
- Use `set -euo pipefail` and error trapping
- Never pipe untrusted data directly to `eval`, `bash`, or similar

**Example - BEFORE (unsafe)**:
```bash
agent_name=$1
eval "run_agent_$agent_name"  # VULNERABLE if $agent_name is user input
```

**Example - AFTER (safe)**:
```bash
agent_name=$1
if [[ "$agent_name" =~ ^[a-z-]+$ ]]; then
  "run_agent_$agent_name"  # Still safer than eval, but validate first
else
  echo "Invalid agent name"
  exit 1
fi
```

### 4. Hardcoded Credentials & Secrets

**Issue**: API keys, tokens, or credentials should never be committed to version control.

**Risk**: Exposed credentials can be abused by attackers; difficult to revoke if in git history.

**Mitigation**:
- Use `.env` files locally (add to `.gitignore`)
- Store secrets in GitHub Secrets or external secret managers
- Scan commits with `git-secrets` or similar tools
- Never commit `.env`, `.credential`, or similar files
- Rotate credentials if accidentally exposed

**Safe pattern**:
```bash
# Load from environment, not from file
if [[ -z "${AGENT_API_KEY:-}" ]]; then
  echo "Error: AGENT_API_KEY not set. Set via environment variable."
  exit 1
fi
```

### 5. Input Validation

**Issue**: Agents accept agent names, configuration parameters, and file paths from user input.

**Risk**: Path traversal, invalid configurations, or denial of service.

**Mitigation**:
- Validate agent names against a whitelist of known agents
- Validate file paths are within expected directories
- Reject suspicious patterns (e.g., `../`, absolute paths outside sandbox)
- Use type checking and schema validation for configuration

**Example**:
```javascript
function validateAgentName(name) {
  // Only allow lowercase letters, numbers, hyphens
  if (!/^[a-z0-9-]+$/.test(name)) {
    throw new Error(`Invalid agent name: "${name}"`);
  }
  return name;
}
```

## Recommended Tools & Practices

### For Node/JavaScript Projects
- **npm audit**: Built-in vulnerability scanner
- **snyk**: Continuous vulnerability monitoring
- **eslint-plugin-security**: Linting for common security issues

### For Bash Scripts
- **shellcheck**: Lint shell scripts for common mistakes
- **git-secrets**: Prevent credential leaks
- **set -euo pipefail**: Standard error handling pattern

### For GitHub Actions
- **GitHub Security Lab**: Detect vulnerable workflows
- **Dependabot**: Automated dependency updates
- **CODEOWNERS**: Enforce review on security-sensitive files

## Reporting Security Issues

If you discover a security vulnerability in agency-agents:

1. **Do NOT open a public GitHub issue** (avoids disclosure before fix)
2. Email security details to the maintainers
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)
4. Allow 90 days for the maintainers to address before public disclosure

## Compliance & Standards

This project follows security best practices from:
- OWASP Top 10
- GitHub Security Lab recommendations
- Node Security Project (NSP) guidelines
- Cloud Native Security best practices

## Future Improvements

- [ ] Add security linting to CI/CD pipeline
- [ ] Implement secret scanning in git history
- [ ] Create security audit checklist for new agent additions
- [ ] Add rate limiting to agent invocations
- [ ] Document secure deployment patterns for production use

---

**Last Updated**: 2026-03-17
**Maintainers**: Security Team
