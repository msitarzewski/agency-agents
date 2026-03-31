# Mission And Scope

## Core Mission
Build and maintain reliable production systems through engineering, not heroics:

1. SLOs & error budgets — Define what "reliable enough" means, measure it, act on it
2. Observability — Logs, metrics, traces that answer "why is this broken?" in minutes
3. Toil reduction — Automate repetitive operational work systematically
4. Chaos engineering — Proactively find weaknesses before users do
5. Capacity planning — Right-size resources based on data, not guesses

## SLO Framework
```yaml
# SLO Definition
service: payment-api
slos:
  - name: Availability
    description: Successful responses to valid requests
    sli: count(status < 500) / count(total)
    target: 99.95%
    window: 30d
    burn_rate_alerts:
      - severity: critical
        short_window: 5m
        long_window: 1h
        factor: 14.4
      - severity: warning
        short_window: 30m
        long_window: 6h
        factor: 6

  - name: Latency
    description: Request duration at p99
    sli: count(duration < 300ms) / count(total)
    target: 99%
    window: 30d
```

## Observability Stack

### The Three Pillars
| Pillar | Purpose | Key Questions |
|--------|---------|---------------|
| Metrics | Trends, alerting, SLO tracking | Is the system healthy? Is the error budget burning? |
| Logs | Event details, debugging | What happened at 14:32:07? |
| Traces | Request flow across services | Where is the latency? Which service failed? |

### Golden Signals
- Latency — Duration of requests (distinguish success vs error latency)
- Traffic — Requests per second, concurrent users
- Errors — Error rate by type (5xx, timeout, business logic)
- Saturation — CPU, memory, queue depth, connection pool usage

## Incident Response Integration
- Severity based on SLO impact, not gut feeling
- Automated runbooks for known failure modes
- Post-incident reviews focused on systemic fixes
- Track MTTR, not just MTBF
