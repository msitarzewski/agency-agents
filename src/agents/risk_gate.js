/**
 * AGENT 2 — RISK-GATE-15
 * Evaluates risk parameters and applies confidence modifiers.
 *
 * @param {Object} payload - Validated payload object
 * @param {Object} quantEval - Output from Agent 1
 * @returns {Object} { risk_gate: Object, constraints_append: Array }
 */
function evaluateRisk(payload, quantEval) {
  try {
    const degradedMode = payload.stochastic_calibration.degraded_mode;
    const { tradable, edge_type, energy } = quantEval;

    // 2B. CONFIDENCE MODIFIER RULES (apply highest penalty only)
    let confidenceModifier = 0.00;
    let append = {
      type: "SWARM_RISK_OVERRIDE",
      impact: "low",
      reason: "no risk override — signal within normal parameters"
    };

    if (degradedMode === true) {
      confidenceModifier = -0.20;
      append = {
        type: "SWARM_RISK_OVERRIDE",
        impact: "high",
        reason: "degraded_mode active — all confidence penalized"
      };
    } else if (edge_type === 'flow_only' && energy === 'low_energy') {
      confidenceModifier = -0.20;
      append = {
        type: "SWARM_RISK_OVERRIDE",
        impact: "high",
        reason: "flow_only + low_energy — weak edge detected"
      };
    } else if (tradable === false) {
      confidenceModifier = -0.15;
      append = {
        type: "SWARM_RISK_OVERRIDE",
        impact: "high",
        reason: "signal not tradable — insufficient state quality"
      };
    }

    return {
      risk_gate: {
        confidence_modifier: confidenceModifier,
        degraded_mode: degradedMode
      },
      constraints_append: [append]
    };

  } catch (error) {
    return {
      risk_gate: {
        confidence_modifier: -0.20,
        degraded_mode: true
      },
      constraints_append: [{
        type: "SWARM_RISK_OVERRIDE",
        impact: "high",
        reason: `Risk evaluation error: ${error.message}`
      }]
    };
  }
}

module.exports = {
  evaluateRisk
};
