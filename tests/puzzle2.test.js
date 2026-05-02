const { runSwarm } = require('../src/pipeline/swarm_core');
const { evaluateQuant } = require('../src/agents/quant_eval');
const { evaluateRisk } = require('../src/agents/risk_gate');
const { evaluateTernary } = require('../src/agents/ternary');

describe('PUZZLE 2 — SWARM CORE PIPELINE', () => {
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

  describe('Agent 1: QUANT-EVAL-15', () => {
    test('should classify edge_type as flow_only correctly', () => {
      // 10 ⊤, 2 ⊥⊤, 3 ⊥ -> countTop=10, countIndet=2 -> flow_only
      const result = evaluateQuant(validPayload);
      expect(result.edge_type).toBe('flow_only');
      expect(result.energy).toBe('high_energy');
      expect(result.tradable).toBe(true);
      expect(result.probability).toBe(0.6); // 0.30 + (10/15)*0.45 = 0.30 + 0.30 = 0.60
    });

    test('should classify edge_type as hybrid correctly', () => {
      const payload = {
        ...validPayload,
        state_vector: ["⊤","⊤","⊤","⊤","⊤","⊤","⊥","⊥","⊥","⊥⊤","⊥⊤","⊥⊤","⊥⊤","⊥⊤","⊥⊤"]
      };
      // 6 ⊤, 3 ⊥, 6 ⊥⊤ -> countTop=6, countBottom=3 -> hybrid
      const result = evaluateQuant(payload);
      expect(result.edge_type).toBe('hybrid');
      expect(result.tradable).toBe(true);
    });
  });

  describe('Agent 2: RISK-GATE-15', () => {
    test('should apply penalty for degraded_mode', () => {
      const quantEval = { tradable: true, edge_type: 'hybrid', energy: 'high_energy' };
      const payload = { ...validPayload, stochastic_calibration: { degraded_mode: true } };
      const result = evaluateRisk(payload, quantEval);
      expect(result.risk_gate.confidence_modifier).toBe(-0.20);
      expect(result.constraints_append[0].impact).toBe('high');
    });

    test('should apply penalty for non-tradable signal', () => {
      const quantEval = { tradable: false, edge_type: 'no_edge', energy: 'low_energy' };
      const result = evaluateRisk(validPayload, quantEval);
      expect(result.risk_gate.confidence_modifier).toBe(-0.15);
    });
  });

  describe('Agent 3: TERNARY-15', () => {
    test('should determine platform eligibility and generate output', () => {
      const swarmOverlay = {
        quant_eval: { count_top: 10, count_bottom: 2 },
        risk_gate: { confidence_modifier: 0.05, degraded_mode: false }
      };
      const result = evaluateTernary(validPayload, swarmOverlay, validPayload.constraints);
      expect(result.platforms_eligible).toContain('polymarket');
      expect(result.platforms_eligible).toContain('lighter');
      expect(result.platforms_eligible).toContain('bitget');
      expect(result.strike_output).toContain('🎰 POLYMARKET : ✅ ELIGIBLE');
    });

    test('should force wait if no platform eligible', () => {
      const swarmOverlay = {
        quant_eval: { count_top: 2, count_bottom: 10 },
        risk_gate: { confidence_modifier: -0.20, degraded_mode: false }
      };
      const result = evaluateTernary(validPayload, swarmOverlay, validPayload.constraints);
      expect(result.platforms_eligible.length).toBe(0);
      expect(result.strike_output).toContain('INVALID — NO PLATFORM ELIGIBLE');
    });
  });

  describe('Orchestrator: swarm_core.js', () => {
    test('should run the full pipeline successfully', () => {
      const result = runSwarm(validPayload);
      expect(result.valid).toBe(true);
      expect(result.swarm_overlay).toBeDefined();
      expect(result.strike_output).toBeDefined();
      expect(result.fc_adjusted).toBe(0.72);
    });

    test('should fail validation for invalid payload', () => {
      const invalidPayload = { ...validPayload, session_id: 'invalid' };
      const result = runSwarm(invalidPayload);
      expect(result.valid).toBe(false);
      expect(result.reason).toBeDefined();
    });
  });
});
