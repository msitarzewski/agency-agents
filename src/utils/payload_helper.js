const crypto = require('crypto');

/**
 * Generates a UUIDv7 string.
 * @returns {string}
 */
function generateUUIDv7() {
  const timestamp = Date.now();
  const hexTimestamp = timestamp.toString(16).padStart(12, '0');

  const randomValues = crypto.randomBytes(10).toString('hex');

  // Format: xxxxxxxx-xxxx-7xxx-axxx-xxxxxxxxxxxx
  // 3rd block starts with 7
  // 4th block starts with 8, 9, a, or b (using 8 here)
  const uuid = [
    hexTimestamp.slice(0, 8),
    hexTimestamp.slice(8, 12),
    '7' + randomValues.slice(0, 3),
    '8' + randomValues.slice(3, 6),
    randomValues.slice(6, 18)
  ].join('-');

  return uuid;
}

/**
 * Calculates payload metrics from state_vector counts.
 * @param {Array} stateVector
 * @returns {Object}
 */
function calculateMetrics(stateVector) {
  let countTop = 0;
  let countBottom = 0;
  let countIndet = 0;

  stateVector.forEach(item => {
    if (item === '⊤') countTop++;
    else if (item === '⊥') countBottom++;
    else if (item === '⊥⊤') countIndet++;
  });

  const base = countTop / 15;

  // FINAL CONFIDENCE: 0.30 + (base * 0.65)
  const finalConfidence = Math.min(0.95, Math.max(0.30, parseFloat((0.30 + (base * 0.65)).toFixed(2))));

  // TAU ENFORCED: MAX(0.15, base)
  const tauEnforced = Math.max(0.15, parseFloat(base.toFixed(2)));

  // COHERENCE SCORE
  // Slot 13-15 are indices 12, 13, 14
  const slot13_15 = stateVector.slice(12, 15);
  let coherenceScore = 1.0;
  if (slot13_15.includes('⊥')) {
    coherenceScore = 0.8;
  } else if (slot13_15.includes('⊥⊤')) {
    coherenceScore = 0.9;
  }

  // DIRECTION
  // Count ⊤ in slots 1-6 (indices 0-5)
  const slots1_6 = stateVector.slice(0, 6);
  const topIn1_6 = slots1_6.filter(i => i === '⊤').length;
  let direction = "neutral";
  if (topIn1_6 >= 4) direction = "long";
  else if (topIn1_6 <= 2) direction = "short";

  return {
    countTop,
    finalConfidence,
    tauEnforced,
    coherenceScore,
    direction
  };
}

/**
 * Returns a degraded payload when API fails or keys are missing.
 * @returns {Object}
 */
function getDegradedPayload() {
  const stateVector = Array(15).fill('⊥⊤');
  return {
    session_id: generateUUIDv7(),
    state_vector: stateVector,
    signal: {
      final_confidence: 0.30,
      signal_ttl_candles: 1,
      direction: "neutral",
      coherence_score: 0.9
    },
    stochastic_calibration: {
      tau_enforced: 0.15,
      degraded_mode: true
    },
    invariants: {
      preserved: false
    },
    fairs_vector: {
      regime: {
        classifier: "transitioning"
      }
    },
    constraints: [{
      type: "DATA_QUALITY",
      impact: "high",
      reason: "API error or missing credentials — entering degraded mode"
    }]
  };
}

module.exports = {
  generateUUIDv7,
  calculateMetrics,
  getDegradedPayload
};
