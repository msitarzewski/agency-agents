"use server";

import { query } from "@/lib/db";

// Map question scores and domains appropriately.
// DRISK has 10 domains, and 6 Risk layers.

// Layer A: Inherent Risk = Threat × Vulnerability × Impact (1–5 each)
// Layer B: Control Effectiveness (multiplier 0.6–1.0)
// Layer C: Response Capability (multiplier 0.7–1.0)
// Layer D: Residual Risk = Inherent × Control × Response
// Layer E: Compliance Readiness
// Layer F: Optimisation Score (under/correctly/over-protected)
// Confidence Score

export async function calculateAndStoreRiskScores(assessmentId: string) {
  // 1. Fetch all responses for this assessment alongside question data
  const responsesQuery = await query(`
    SELECT 
      ar.selected_score, 
      ar.is_not_applicable,
      aq.weight,
      aq.id as question_id,
      ad.domain_number,
      ad.id as domain_id
    FROM assessment_responses ar
    JOIN assessment_questions aq ON ar.question_id = aq.id
    JOIN assessment_domains ad ON aq.domain_id = ad.id
    WHERE ar.assessment_id = $1
  `, [assessmentId]);

  const responses = responsesQuery.rows;

  if (responses.length === 0) {
    console.log("No responses found for assessment:", assessmentId);
    return;
  }

  // Calculate generic statistics
  let totalQuestions = responses.length;
  let answeredQuestions = 0;
  
  // Initialize Domain scores
  const domainScores: Record<number, { domain_id: string, score: number, maxScore: number }> = {};
  for(let i=1; i<=10; i++) {
    domainScores[i] = { domain_id: '', score: 0, maxScore: 0 };
  }

  responses.forEach(r => {
    if (r.domain_number) {
        domainScores[r.domain_number].domain_id = r.domain_id;
    }
    
    if (r.selected_score !== null && r.selected_score !== undefined && !r.is_not_applicable) {
      answeredQuestions++;
      // Weighted score = Base Score × Question Weight
      const weight = r.weight || 1;
      domainScores[r.domain_number].score += r.selected_score * weight;
      domainScores[r.domain_number].maxScore += 5 * weight;
    }
  });

  // Calculate Confidence Score
  // Base 100%, minus penalty for unanswered or NA. (Simplified for MVP)
  const answerRatio = totalQuestions > 0 ? answeredQuestions / totalQuestions : 0;
  let confidenceScore = Math.round(answerRatio * 100);
  
  // Layer A: Inherent Risk (Threat * Vulnerability * Impact)
  // We approximate these from related domains if explicit tags don't exist in the MVP DB setup.
  // Domain 3 = Threat, Domain 4/5/8 = Vulnerability, Domain 2 = Impact
  const getDomainAvg = (dNum: number) => {
    const ds = domainScores[dNum];
    if (!ds || ds.maxScore === 0) return 3; // default mid
    return Math.max(1, Math.ceil((ds.score / ds.maxScore) * 5));
  };

  const threat = getDomainAvg(3);
  const vulnerability = Math.ceil((getDomainAvg(4) + getDomainAvg(5) + getDomainAvg(8)) / 3);
  const impact = getDomainAvg(2);

  const layerA = threat * vulnerability * impact; // max 125

  // Layer B: Control Effectiveness (Multiplier 0.6 - 1.0)
  // Derived from Domain 4, 5, 6
  const controlStrength = Math.ceil((getDomainAvg(4) + getDomainAvg(5) + getDomainAvg(6)) / 3);
  let layerB = 1.0;
  if(controlStrength <= 2) layerB = 0.6; // Strong
  else if(controlStrength <= 4) layerB = 0.8; // Moderate
  else layerB = 1.0; // Weak

  // Layer C: Response Capability (Multiplier 0.7 - 1.0)
  // Derived from Domain 7
  const responseStrength = getDomainAvg(7);
  let layerC = 1.0;
  if(responseStrength <= 2) layerC = 0.7; // Strong
  else if(responseStrength <= 4) layerC = 0.85; // Moderate
  else layerC = 1.0; // Weak

  // Layer D: Residual Risk
  const layerD = layerA * layerB * layerC;

  // Layer E: Compliance Readiness
  // Derived from Domain 10
  const complianceScore = getDomainAvg(10); // 1-5
  const layerE = complianceScore <= 2 ? 'High' : (complianceScore <= 4 ? 'Moderate' : 'Low');

  // Layer F: Optimisation Score
  let layerF = 'Correctly Protected';
  if (layerB === 0.6 && layerA < 20) layerF = 'Over-protected';
  if (layerB === 1.0 && layerA > 40) layerF = 'Under-protected';

  // Risk Band Classification based on Residual Risk (Layer D)
  // 0–15 Low, 16–30 Moderate, 31–50 High, 51–75 Very High, 76+ Critical
  let riskBand = 'Low';
  if (layerD >= 76) riskBand = 'Critical';
  else if (layerD >= 51) riskBand = 'Very High';
  else if (layerD >= 31) riskBand = 'High';
  else if (layerD >= 16) riskBand = 'Moderate';

  // Clear existing scores for this assessment
  await query('DELETE FROM risk_scores WHERE assessment_id = $1', [assessmentId]);

  // Store scores in risk_scores table
  const insertScore = async (layer: string, value: number | null, band: string | null, multiplier: number | null, metadata: any, domain_id: string | null = null) => {
    await query(`
      INSERT INTO risk_scores (assessment_id, layer, domain_id, score_value, band, multiplier, metadata)
      VALUES ($1, $2, $3, $4, $5, $6, $7)
    `, [assessmentId, layer, domain_id, value, band, multiplier, JSON.stringify(metadata)]);
  };

  await insertScore('inherent', layerA, null, null, { threat, vulnerability, impact });
  await insertScore('control', null, null, layerB, { controlStrength });
  await insertScore('response', null, null, layerC, { responseStrength });
  await insertScore('residual', layerD, riskBand, null, { confidenceScore });
  await insertScore('compliance', complianceScore, layerE, null, {});
  await insertScore('optimisation', null, layerF, null, {});

  // Store Domain Scores
  for (let i = 1; i <= 10; i++) {
    const ds = domainScores[i];
    if (ds && ds.domain_id) {
       await insertScore('domain', ds.score, null, null, { maxScore: ds.maxScore, domain_number: i }, ds.domain_id);
    }
  }

  // Update assessment with final risk band? (Optional depending on spec, we rely on layer D row)
  console.log(`Successfully calculated risk scores for assessment: ${assessmentId}`);
}
