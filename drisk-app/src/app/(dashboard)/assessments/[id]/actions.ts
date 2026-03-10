"use server";

import { query } from "@/lib/db";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export async function saveResponsesAction(assessmentId: string, responses: Record<string, any>) {
  for (const [qId, data] of Object.entries(responses)) {
    if (data.score === undefined && !data.comment) continue;

    await query(`
      INSERT INTO assessment_responses (assessment_id, question_id, selected_score, comment, is_not_applicable)
      VALUES ($1, $2, $3, $4, $5)
      ON CONFLICT (assessment_id, question_id) 
      DO UPDATE SET 
        selected_score = EXCLUDED.selected_score,
        comment = EXCLUDED.comment,
        is_not_applicable = EXCLUDED.is_not_applicable,
        updated_at = CURRENT_TIMESTAMP
    `, [
      assessmentId, 
      qId, 
      data.score || null, 
      data.comment || null, 
      data.na || false
    ]);
  }
  
  await query(`
    UPDATE assessments
    SET status = 'in_progress', updated_at = CURRENT_TIMESTAMP
    WHERE id = $1 AND status = 'draft'
  `, [assessmentId]);

  revalidatePath(`/assessments/${assessmentId}`);
}

import { calculateAndStoreRiskScores } from "@/app/actions/scoring";

export async function completeAssessmentAction(assessmentId: string) {
  // Update assessment status
  await query(`
    UPDATE assessments
    SET status = 'completed', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
    WHERE id = $1
  `, [assessmentId]);

  // Task 10 - Auto-trigger scoring engine
  // This calculates Layer A, B, C, D, E, F and populates the risk_scores table
  await calculateAndStoreRiskScores(assessmentId);

  revalidatePath(`/assessments/${assessmentId}`);
  revalidatePath('/assessments');
  redirect(`/assessments/${assessmentId}/review`);
}
