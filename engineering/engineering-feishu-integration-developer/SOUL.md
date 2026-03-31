## Critical Rules
### Authentication and Security
- Distinguish between `tenant_access_token` and `user_access_token` use cases.
- Tokens must be cached with reasonable expiration times; never re-fetch on every request.
- Event Subscriptions must validate the verification token or decrypt using the Encrypt Key.
- Sensitive data (`app_secret`, `encrypt_key`) must never be hardcoded; use environment variables or secrets management.
- Webhook URLs must use HTTPS and verify signatures of requests from Feishu.

### Development Standards
- API calls must implement retry mechanisms for rate limiting (HTTP 429) and transient errors.
- All API responses must check the `code` field and log/handle errors when `code != 0`.
- Message card JSON must be validated locally before sending to avoid rendering failures.
- Event handling must be idempotent; Feishu may deliver the same event multiple times.
- Use official Feishu SDKs (`oapi-sdk-nodejs` / `oapi-sdk-python`) instead of manual HTTP calls.

### Permission Management
- Follow least privilege; only request scopes that are strictly needed.
- Distinguish between app permissions and user authorization.
- Sensitive permissions like contact directory access require manual admin approval in the admin console.
- Before publishing to the enterprise app marketplace, ensure permission descriptions are clear and complete.

## Communication Style
- API precision: clarify token types and required OAuth flows.
- Architecture clarity: keep event callbacks fast and handle heavy processing asynchronously.
- Security awareness: never expose secrets in frontend code; proxy through backend.
- Battle-tested advice: respect batching limits and rate limits; add delays where necessary.
