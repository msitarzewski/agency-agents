const { validatePayload } = require('../agents/payload_guard');
const { evaluateQuant } = require('../agents/quant_eval');
const { evaluateRisk } = require('../agents/risk_gate');
const { evaluateTernary } = require('../agents/ternary');

/**
 * SWARM CORE ORCHESTRATOR
 * Chains Agent 1 → 2 → 3 sequentially.
 *
 * @param {Object} payload - Input payload
 * @returns {Object} Full swarm execution result
 */
function runSwarm(payload) {
  // 4A. VALIDATION
  const validationResult = validatePayload(payload);
  if (!validationResult.valid) {
    return validationResult;
  }

  // Agent 1 — QUANT-EVAL-15
  const quantEval = evaluateQuant(payload);

  // Agent 2 — RISK-GATE-15
  const riskResult = evaluateRisk(payload, quantEval);

  // Combine swarm_overlay and constraints
  const swarmOverlay = {
    quant_eval: quantEval,
    risk_gate: riskResult.risk_gate
  };
  const allConstraints = [...payload.constraints, ...riskResult.constraints_append];

  // Agent 3 — TERNARY-15
  const ternaryResult = evaluateTernary(payload, swarmOverlay, allConstraints);

  // 4B. runSwarm() RETURN STRUCTURE
  return {
    valid: true,
    swarm_overlay: swarmOverlay,
    constraints: allConstraints,
    strike_output: ternaryResult.strike_output,
    platforms_eligible: ternaryResult.platforms_eligible,
    fc_adjusted: ternaryResult.fc_adjusted
  };
}

module.exports = {
  runSwarm
};
