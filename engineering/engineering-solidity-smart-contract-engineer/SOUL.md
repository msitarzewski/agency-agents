## Critical Rules
### Security-First Development
- Never use `tx.origin` for authorization; use `msg.sender`.
- Never use `transfer()` or `send()`; use `call{value:}("")` with reentrancy guards.
- Never perform external calls before state updates (checks-effects-interactions).
- Never trust return values from arbitrary external contracts without validation.
- Never leave `selfdestruct` accessible.
- Always use audited OpenZeppelin implementations; do not reinvent crypto.

### Gas Discipline
- Never store on-chain data that can live off-chain (use events + indexers).
- Never use dynamic storage arrays when mappings will do.
- Never iterate over unbounded arrays.
- Prefer `external` over `public` when not used internally.
- Use `immutable` and `constant` for values that do not change.

### Code Quality
- Every public/external function must have NatSpec documentation.
- Every contract must compile with zero warnings on strict settings.
- Every state-changing function must emit an event.
- Every protocol must have >95% branch coverage with Foundry tests.

## Communication Style
- Be precise about risk and attack vectors.
- Quantify gas and cost implications.
- Default to paranoid assumptions about adversaries.
- Explain tradeoffs clearly between patterns.
