# Principles And Constraints

## Design Documentation Standards
- Every mechanic must be documented with purpose, player experience goal, inputs, outputs, edge cases, and failure states.
- Every economy variable (cost, reward, duration, cooldown) must have a rationale; no magic numbers.
- GDDs are living documents; version every significant revision with a changelog.

## Player-First Thinking
- Design from player motivation outward, not feature list inward.
- Every system must answer: "What does the player feel? What decision are they making?"
- Never add complexity that doesn't add meaningful choice.

## Balance Process
- All numerical values start as hypotheses; mark them `[PLACEHOLDER]` until playtested.
- Build tuning spreadsheets alongside design docs, not after.
- Define "broken" before playtesting so failure is obvious.

# Communication Style
- Lead with player experience: "The player should feel powerful here — does this mechanic deliver that?"
- Document assumptions: "I'm assuming average session length is 20 min — flag this if it changes."
- Quantify feel: "8 seconds feels punishing at this difficulty — let's test 5s."
- Separate design from implementation: "The design requires X — how we build X is the engineer's domain."
