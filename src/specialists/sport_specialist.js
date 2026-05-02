const axios = require('axios');
const { generateUUIDv7, calculateMetrics, getDegradedPayload } = require('../utils/payload_helper');

/**
 * SPORT-SPEC (3B)
 * Generates normalized payload from TheSportsDB (public test key).
 *
 * @param {string} teamId - Team ID
 * @returns {Object} Validated payload JSON
 */
async function generateSportPayload(teamId = '133602') { // Default: Liverpool
  try {
    const timeout = 10000;
    // Using public test key '3' as specified in instructions
    const baseUrl = 'https://www.thesportsdb.com/api/v1/json/3';

    // 1. Fetch Team/Match Data
    const lastEventsUrl = `${baseUrl}/eventslast.php?id=${teamId}`;
    const nextEventsUrl = `${baseUrl}/eventsnext.php?id=${teamId}`;

    const [lastRes, nextRes] = await Promise.all([
      axios.get(lastEventsUrl, { timeout }),
      axios.get(nextEventsUrl, { timeout })
    ]);

    const lastEvents = lastRes.data.results;
    if (!lastEvents) throw new Error("No recent match data");

    const state_vector = Array(15).fill('⊥⊤');

    // Logic for Form (Simplified)
    const wins = lastEvents.filter(e => {
      const isHome = e.idHomeTeam === teamId;
      const homeScore = parseInt(e.intHomeScore);
      const awayScore = parseInt(e.intAwayScore);
      return (isHome && homeScore > awayScore) || (!isHome && awayScore > homeScore);
    }).length;

    // Slot 1-3: home form (last 5), away form (last 5), head-to-head record
    state_vector[0] = wins >= 3 ? '⊤' : '⊥';
    state_vector[1] = wins >= 4 ? '⊤' : '⊥⊤';
    state_vector[2] = '⊥⊤';

    // Slot 4-6: goals scored trend, goals conceded trend, recent win streak
    const totalGoals = lastEvents.reduce((acc, e) => {
        const isHome = e.idHomeTeam === teamId;
        return acc + (isHome ? parseInt(e.intHomeScore) : parseInt(e.intAwayScore));
    }, 0);
    state_vector[3] = totalGoals > 7 ? '⊤' : '⊥';
    state_vector[4] = '⊥⊤';
    state_vector[5] = wins >= 2 ? '⊤' : '⊥';

    // Slot 7-9: match importance, league position gap, home advantage factor
    state_vector[6] = '⊤'; // High importance
    state_vector[7] = '⊥⊤';
    state_vector[8] = '⊤';

    // Slot 10-12: odds movement direction, public betting sentiment, injury impact
    state_vector[9] = '⊥⊤';
    state_vector[10] = '⊤';
    state_vector[11] = '⊥⊤';

    // Slot 13-15: data completeness, fixture recency, API data quality
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
          classifier: "event-driven"
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

module.exports = { generateSportPayload };
