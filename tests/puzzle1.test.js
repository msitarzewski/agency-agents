const { validatePayload } = require('../src/agents/payload_guard');

describe('PUZZLE 1 — PAYLOAD GUARD', () => {
  const validPayload = {
    "session_id": "01890a5d-ac96-7000-8000-000000000001",
    "state_vector": ["⊤","⊤","⊥","⊤","⊥⊤","⊤","⊤",
                     "⊥","⊤","⊤","⊥⊤","⊤","⊤","⊥","⊤"],
    "signal": {
      "final_confidence": 0.72,
      "signal_ttl_candles": 1,
      "direction": "long",
      "coherence_score": 1.0
    },
    "stochastic_calibration": {
      "tau_enforced": 0.18,
      "degraded_mode": false
    },
    "invariants": {
      "preserved": true
    },
    "fairs_vector": {
      "regime": {
        "classifier": "trending"
      }
    },
    "constraints": [
      {
        "type": "FLOW_DOMINANCE",
        "impact": "medium",
        "reason": "Flow confirms directional bias"
      }
    ]
  };

  test('should pass with valid payload', () => {
    const result = validatePayload(validPayload);
    expect(result.valid).toBe(true);
    expect(result.payload).toEqual(validPayload);
  });

  test('should fail if session_id is not UUIDv7', () => {
    const invalidPayload = { ...validPayload, session_id: 'not-a-uuid-v7' };
    const result = validatePayload(invalidPayload);
    expect(result.valid).toBe(false);
    expect(result.reason).toBe('session_id must be UUIDv7 format');
    expect(result.action).toBe('REQUEST NEW PAYLOAD');
  });

  test('should fail if session_id is UUIDv4 (not v7)', () => {
    // UUIDv4: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    const invalidPayload = { ...validPayload, session_id: 'f47ac10b-58cc-4372-a567-0e02b2c3d479' };
    const result = validatePayload(invalidPayload);
    expect(result.valid).toBe(false);
    expect(result.reason).toBe('session_id must be UUIDv7 format');
  });

  test('should fail if state_vector length is not 15', () => {
    const invalidPayload = { ...validPayload, state_vector: ["⊤", "⊥"] };
    const result = validatePayload(invalidPayload);
    expect(result.valid).toBe(false);
    expect(result.reason).toBe('state_vector must be array of exactly 15 items');
  });

  test('should fail if state_vector contains invalid items', () => {
    const invalidPayload = { ...validPayload };
    invalidPayload.state_vector = [...validPayload.state_vector];
    invalidPayload.state_vector[0] = "X";
    const result = validatePayload(invalidPayload);
    expect(result.valid).toBe(false);
    expect(result.reason).toBe('state_vector items must be one of: ⊤, ⊥, ⊥⊤');
  });

  test('should fail if signal.final_confidence is out of range', () => {
    const invalidPayload1 = { ...validPayload, signal: { ...validPayload.signal, final_confidence: 0.25 } };
    const result1 = validatePayload(invalidPayload1);
    expect(result1.valid).toBe(false);
    expect(result1.reason).toBe('signal.final_confidence must be between 0.30 and 0.95');

    const invalidPayload2 = { ...validPayload, signal: { ...validPayload.signal, final_confidence: 0.96 } };
    const result2 = validatePayload(invalidPayload2);
    expect(result2.valid).toBe(false);
    expect(result2.reason).toBe('signal.final_confidence must be between 0.30 and 0.95');
  });

  test('should fail if signal.signal_ttl_candles is not 1', () => {
    const invalidPayload = { ...validPayload, signal: { ...validPayload.signal, signal_ttl_candles: 2 } };
    const result = validatePayload(invalidPayload);
    expect(result.valid).toBe(false);
    expect(result.reason).toBe('signal.signal_ttl_candles must equal 1');
  });

  test('should fail if stochastic_calibration.tau_enforced < 0.15', () => {
    const invalidPayload = { ...validPayload, stochastic_calibration: { tau_enforced: 0.14 } };
    const result = validatePayload(invalidPayload);
    expect(result.valid).toBe(false);
    expect(result.reason).toBe('stochastic_calibration.tau_enforced must be >= 0.15');
  });

  test('should fail if invariants.preserved is not true', () => {
    const invalidPayload = { ...validPayload, invariants: { preserved: false } };
    const result = validatePayload(invalidPayload);
    expect(result.valid).toBe(false);
    expect(result.reason).toBe('invariants.preserved must be true');
  });

  test('should fail if constraints is not an array of objects', () => {
    const invalidPayload = { ...validPayload, constraints: "not-an-array" };
    const result = validatePayload(invalidPayload);
    expect(result.valid).toBe(false);
    expect(result.reason).toBe('constraints must be array of objects');

    const invalidPayload2 = { ...validPayload, constraints: [ "not-an-object" ] };
    const result2 = validatePayload(invalidPayload2);
    expect(result2.valid).toBe(false);
    expect(result2.reason).toBe('constraints must be array of objects');
  });
});
