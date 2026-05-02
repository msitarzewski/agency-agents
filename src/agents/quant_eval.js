/**
 * AGENT 1 — QUANT-EVAL-15
 * Evaluates the validated payload to classify edge, energy, and tradability.
 *
 * @param {Object} payload - Validated payload object
 * @returns {Object} swarm_overlay.quant_eval
 */
function evaluateQuant(payload) {
  try {
    const stateVector = payload.state_vector;
    let countTop = 0; // ⊤
    let countBottom = 0; // ⊥
    let countIndet = 0; // ⊥⊤

    stateVector.forEach(item => {
      if (item === '⊤') countTop++;
      else if (item === '⊥') countBottom++;
      else if (item === '⊥⊤') countIndet++;
    });

    // 1A. EDGE TYPE CLASSIFICATION:
    let edgeType = 'no_edge';
    if (countTop >= 8 && countIndet <= 2) {
      edgeType = 'flow_only';
    } else if (countBottom >= 6 && countTop < 8) {
      edgeType = 'extremity_only';
    } else if (countTop >= 6 && countBottom >= 3) {
      edgeType = 'hybrid';
    }

    // 1B. ENERGY DETECTION:
    let energy = 'low_energy';
    if (countTop >= 10) {
      energy = 'high_energy';
    } else if (countTop >= 6) {
      energy = 'normal';
    }

    // 1C. TRADABLE FLAG:
    const tradable = (countTop >= 6 && edgeType !== 'no_edge');

    // 1D. PROBABILITY FORMULA:
    let probability = 0.30 + (countTop / 15) * 0.45;
    probability = Math.min(0.75, parseFloat(probability.toFixed(2)));

    // 1E. DIRECTION: Use payload.signal.direction directly
    const direction = payload.signal.direction;

    return {
      count_top: countTop,
      count_bottom: countBottom,
      count_indet: countIndet,
      edge_type: edgeType,
      energy: energy,
      tradable: tradable,
      probability: probability,
      direction: direction
    };
  } catch (error) {
    // Return safe defaults on error
    return {
      count_top: 0,
      count_bottom: 0,
      count_indet: 0,
      edge_type: 'no_edge',
      energy: 'low_energy',
      tradable: false,
      probability: 0.30,
      direction: 'neutral'
    };
  }
}

module.exports = {
  evaluateQuant
};
