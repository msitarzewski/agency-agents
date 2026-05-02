/**
 * AGENT 3 — TERNARY-15
 * Finalizes confidence, evaluates platform gates, and generates STRIKE output.
 *
 * @param {Object} payload - Validated payload object
 * @param {Object} swarmOverlay - Overlay with quant_eval and risk_gate
 * @param {Array} allConstraints - Original constraints + constraints_append
 * @returns {Object} { strike_output: string, platforms_eligible: Array, fc_adjusted: number }
 */
function evaluateTernary(payload, swarmOverlay, allConstraints) {
  try {
    const { quant_eval, risk_gate } = swarmOverlay;
    const { final_confidence, coherence_score, direction } = payload.signal;
    const { degraded_mode } = risk_gate;
    const { count_top, count_bottom } = quant_eval;
    const regime = payload.fairs_vector.regime.classifier;

    // Adjust final confidence
    const fc_adjusted = Math.max(0.30, parseFloat((final_confidence + risk_gate.confidence_modifier).toFixed(2)));

    // 3D. GRADE CALCULATION:
    const qs = count_top / 15;
    let grade = "CRITICAL";
    if (qs >= 0.80) grade = "STRONG";
    else if (qs >= 0.60) grade = "MODERATE";
    else if (qs >= 0.40) grade = "WEAK";

    // Resolve Platform Eligibility
    const platforms_eligible = [];
    let polymarket_eligible = false;
    let lighter_eligible = false;
    let bitget_eligible = false;

    if (direction !== 'neutral' && !degraded_mode) {
      // POLYMARKET GATE
      if (fc_adjusted >= 0.65 && count_bottom <= 3) {
        polymarket_eligible = true;
        platforms_eligible.push('polymarket');
      }

      // LIGHTER DEX GATE
      if (fc_adjusted >= 0.70 && regime !== 'mean-reverting') {
        lighter_eligible = true;
        platforms_eligible.push('lighter');
      }

      // BITGET NOTE GATE
      if (fc_adjusted >= 0.75 && coherence_score === 1.0 && count_bottom <= 2) {
        bitget_eligible = true;
        platforms_eligible.push('bitget');
      }
    }

    // Determine Max Ceiling (Polymarket)
    let max_ceiling = "$0.00";
    if (fc_adjusted >= 0.85) max_ceiling = "$0.80";
    else if (fc_adjusted >= 0.75) max_ceiling = "$0.65";
    else if (fc_adjusted >= 0.65) max_ceiling = "$0.50";

    // Resolve Action labels
    const action_polymarket = direction === 'long' ? 'UP' : 'DOWN';
    const action_lighter = direction === 'long' ? 'BUY' : 'SELL';
    const action_bitget = direction === 'long' ? 'LONG' : 'SHORT';

    // Pick Risk Note
    const highImpact = allConstraints.find(c => c.impact === 'high');
    const mediumImpact = allConstraints.find(c => c.impact === 'medium');
    const risk_note = (highImpact || mediumImpact || { reason: "NONE" }).reason;

    let strike_output = "";
    const timeframe = "15m";

    if (platforms_eligible.length === 0) {
      strike_output = `⛔ STRIKE SIGNAL\n🚫 STATUS     : INVALID — NO PLATFORM ELIGIBLE\n📊 CONFIDENCE : ${fc_adjusted.toFixed(2)}\n📉 STATE      : ${grade} (${count_top}/15 ⊤)\n⏳ ACTION     : WAIT NEXT CANDLE\n⚠️ RISK NOTE  : ${risk_note}`;
    } else {
      const outputs = [];
      if (polymarket_eligible) {
        outputs.push(`🎯 STRIKE: ${timeframe}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔥 ACTION     : ${action_polymarket}\n🧠 CONFIDENCE : ${fc_adjusted.toFixed(2)}\n📊 STATE      : ${grade} (${count_top}/15 ⊤)\n🛡 MAX ENTRY  : ${max_ceiling} (SHARE PRICE)\n⏱ TTL        : 1 CANDLE\n🎰 POLYMARKET : ✅ ELIGIBLE\n⚠️ RISK NOTE  : ${risk_note}`);
      }
      if (lighter_eligible) {
        outputs.push(`🎯 STRIKE: ${timeframe}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔥 ACTION     : ${action_lighter}\n⚡ CONFIDENCE : ${fc_adjusted.toFixed(2)}\n📊 STATE      : ${grade} (${count_top}/15 ⊤)\n⏱ TTL        : 1 CANDLE\n⚡ LIGHTER DEX: ✅ ELIGIBLE\n⚠️ RISK NOTE  : ${risk_note}`);
      }
      if (bitget_eligible) {
        outputs.push(`🎯 STRIKE: ${timeframe}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔥 ACTION     : ${action_bitget}\n⚡ CONFIDENCE : ${fc_adjusted.toFixed(2)}\n📊 STATE      : ${grade} (${count_top}/15 ⊤)\n⏱ TTL        : 1 CANDLE\n📌 BITGET     : ✅ NOTE ONLY\n⚠️ RISK NOTE  : ${risk_note}`);
      }
      strike_output = outputs.join('\n\n');
    }

    return {
      strike_output,
      platforms_eligible,
      fc_adjusted
    };

  } catch (error) {
    return {
      strike_output: `ERROR: ${error.message}`,
      platforms_eligible: [],
      fc_adjusted: 0.30
    };
  }
}

module.exports = {
  evaluateTernary
};
