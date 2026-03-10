"use server";

import { query } from "@/lib/db";

export async function getDashboardStats() {
  const resultClient = await query(`SELECT count(*) as count FROM clients`);
  const resultSite = await query(`SELECT count(*) as count FROM sites`);
  const resultAssessment = await query(`SELECT count(*) as count FROM assessments`);
  const resultHighRisk = await query(`
    SELECT count(DISTINCT a.site_id) as count
    FROM risk_scores rs
    JOIN assessments a ON a.id = rs.assessment_id
    WHERE rs.layer = 'residual' AND (rs.band ILIKE 'critical' OR rs.band ILIKE 'very high' OR rs.band ILIKE 'high')
  `);
  const resultOverdueActions = await query(`
    SELECT count(*) as count
    FROM actions
    WHERE status != 'completed' AND status != 'verified closed' AND due_date < CURRENT_DATE
  `);

  return {
    totalClients: parseInt(resultClient.rows[0].count, 10),
    totalSites: parseInt(resultSite.rows[0].count, 10),
    totalAssessments: parseInt(resultAssessment.rows[0].count, 10),
    highRiskSites: parseInt(resultHighRisk.rows[0].count, 10),
    overdueActions: parseInt(resultOverdueActions.rows[0].count, 10)
  };
}

export async function getRecentAssessments(limit = 5) {
  const { rows } = await query(`
    SELECT a.id, a.assessment_type, a.status, a.completed_at, a.assessed_at,
           s.name as site_name, s.id as site_id,
           rs.band as risk_band, rs.score_value as risk_score
    FROM assessments a
    JOIN sites s ON a.site_id = s.id
    LEFT JOIN risk_scores rs ON rs.assessment_id = a.id AND rs.layer = 'residual'
    ORDER BY a.created_at DESC
    LIMIT $1
  `, [limit]);
  return rows;
}
