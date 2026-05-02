/**
 * PUZZLE 1 — PAYLOAD GUARD
 * Validates the incoming payload before processing by other agents.
 *
 * @param {Object} payload - Pre-parsed JavaScript object
 * @returns {Object} { valid: boolean, payload?: Object, reason?: string, action?: string }
 */
function validatePayload(payload) {
  try {
    // 1. session_id must be UUIDv7 format
    // UUIDv7: xxxxxxxx-xxxx-7xxx-axxx-xxxxxxxxxxxx (where a is 8, 9, a, or b)
    const uuidv7Regex = /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (!payload.session_id || !uuidv7Regex.test(payload.session_id)) {
      return {
        valid: false,
        reason: "session_id must be UUIDv7 format",
        action: "REQUEST NEW PAYLOAD"
      };
    }

    // 2. state_vector must be array of exactly 15 items
    // each item must be one of: "⊤" | "⊥" | "⊥⊤"
    const validTernary = ["⊤", "⊥", "⊥⊤"];
    if (!Array.isArray(payload.state_vector) || payload.state_vector.length !== 15) {
      return {
        valid: false,
        reason: "state_vector must be array of exactly 15 items",
        action: "REQUEST NEW PAYLOAD"
      };
    }
    for (const item of payload.state_vector) {
      if (!validTernary.includes(item)) {
        return {
          valid: false,
          reason: "state_vector items must be one of: ⊤, ⊥, ⊥⊤",
          action: "REQUEST NEW PAYLOAD"
        };
      }
    }

    // 3. signal.final_confidence must be 0.30 - 0.95
    if (!payload.signal || typeof payload.signal.final_confidence !== 'number' ||
        payload.signal.final_confidence < 0.30 || payload.signal.final_confidence > 0.95) {
      return {
        valid: false,
        reason: "signal.final_confidence must be between 0.30 and 0.95",
        action: "REQUEST NEW PAYLOAD"
      };
    }

    // 4. signal.signal_ttl_candles must equal 1
    if (payload.signal.signal_ttl_candles !== 1) {
      return {
        valid: false,
        reason: "signal.signal_ttl_candles must equal 1",
        action: "REQUEST NEW PAYLOAD"
      };
    }

    // 5. stochastic_calibration.tau_enforced >= 0.15
    if (!payload.stochastic_calibration || typeof payload.stochastic_calibration.tau_enforced !== 'number' ||
        payload.stochastic_calibration.tau_enforced < 0.15) {
      return {
        valid: false,
        reason: "stochastic_calibration.tau_enforced must be >= 0.15",
        action: "REQUEST NEW PAYLOAD"
      };
    }

    // 6. invariants.preserved must be true
    if (!payload.invariants || payload.invariants.preserved !== true) {
      return {
        valid: false,
        reason: "invariants.preserved must be true",
        action: "REQUEST NEW PAYLOAD"
      };
    }

    // 7. constraints must be array of objects
    if (!Array.isArray(payload.constraints)) {
      return {
        valid: false,
        reason: "constraints must be array of objects",
        action: "REQUEST NEW PAYLOAD"
      };
    }
    for (const constraint of payload.constraints) {
      if (typeof constraint !== 'object' || constraint === null || Array.isArray(constraint)) {
        return {
          valid: false,
          reason: "constraints must be array of objects",
          action: "REQUEST NEW PAYLOAD"
        };
      }
    }

    return {
      valid: true,
      payload
    };

  } catch (error) {
    return {
      valid: false,
      reason: `Unexpected error during validation: ${error.message}`,
      action: "REQUEST NEW PAYLOAD"
    };
  }
}

module.exports = {
  validatePayload
};
