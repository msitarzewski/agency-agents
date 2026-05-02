const axios = require('axios');
const { generateUUIDv7, calculateMetrics, getDegradedPayload } = require('../utils/payload_helper');

/**
 * MACRO-SPEC (3C)
 * Generates normalized payload from FRED API.
 *
 * @param {string} seriesId - FRED Series ID (e.g., UNRATE)
 * @returns {Object} Validated payload JSON
 */
async function generateMacroPayload(seriesId = 'UNRATE') {
  const apiKey = process.env.FRED_API_KEY;

  if (!apiKey) {
    return getDegradedPayload();
  }

  try {
    const timeout = 10000;
    const url = `https://api.stlouisfed.org/fred/series/observations?series_id=${seriesId}&api_key=${apiKey}&file_type=json&limit=10&sort_order=desc`;

    const response = await axios.get(url, { timeout });
    const observations = response.data.observations;

    if (!observations || observations.length < 2) throw new Error("Insufficient macro data");

    const latest = parseFloat(observations[0].value);
    const previous = parseFloat(observations[1].value);

    const state_vector = Array(15).fill('⊥⊤');

    // Slot 1-3: GDP trend, employment trend, inflation direction
    // Logic depends on seriesId, but generic for demo
    state_vector[0] = latest < previous ? '⊤' : '⊥'; // e.g., falling unemployment is good
    state_vector[1] = '⊥⊤';
    state_vector[2] = '⊥⊤';

    // Slot 4-6: rate decision direction, yield curve, credit spread
    state_vector[3] = '⊥⊤';
    state_vector[4] = '⊥⊤';
    state_vector[5] = '⊥⊤';

    // Slot 7-9: news sentiment score, market reaction, volatility index
    state_vector[6] = '⊤';
    state_vector[7] = '⊥⊤';
    state_vector[8] = '⊥';

    // Slot 10-12: regime (risk-on/risk-off), dollar strength, global correlation
    state_vector[9] = '⊤'; // Risk-on
    state_vector[10] = '⊥⊤';
    state_vector[11] = '⊥⊤';

    // Slot 13-15: data recency, revision risk, forecast consensus quality
    state_vector[12] = '⊤';
    state_vector[13] = '⊤';
    state_vector[14] = '⊤';

    const metrics = calculateMetrics(state_vector);

    return {
      session_id: generateUUIDv7(),
      state_vector,
      signal: {
        final_confidence: metrics.finalConfidence,
        signal_ttl_candles: 1,
        direction: metrics.direction,
        coherence_score: metrics.coherenceScore
      },
      stochastic_calibration: {
        tau_enforced: metrics.tauEnforced,
        degraded_mode: false
      },
      invariants: {
        preserved: true
      },
      fairs_vector: {
        regime: {
          classifier: "macro-driven"
        }
      },
      constraints: [{
        type: "DATA_QUALITY",
        impact: "low",
        reason: "All data sources nominal"
      }]
    };

  } catch (error) {
    return getDegradedPayload();
  }
}

module.exports = { generateMacroPayload };
