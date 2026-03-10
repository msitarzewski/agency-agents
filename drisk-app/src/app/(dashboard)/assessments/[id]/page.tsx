import { query } from "@/lib/db";
import { redirect } from "next/navigation";
import { ChevronLeft, Save, Check } from "lucide-react";
import Link from "next/link";
import { AssessmentForm } from "./AssessmentForm"; // Client component

export const dynamic = "force-dynamic";

export default async function AssessmentScreen({ params }: { params: { id: string } }) {
  const assessmentId = params.id;
  
  // 1. Fetch assessment details
  const aRes = await query(`
    SELECT a.*, s.name as site_name, t.name as template_name
    FROM assessments a
    JOIN sites s ON a.site_id = s.id
    JOIN assessment_templates t ON a.template_id = t.id
    WHERE a.id = $1
  `, [assessmentId]);

  if (aRes.rowCount === 0) return <div>Assessment not found</div>;
  const assessment = aRes.rows[0];

  // 2. Fetch all domains and questions for the template
  const dqRes = await query(`
    SELECT d.id as domain_id, d.name as domain_name, d.domain_number,
           q.id as question_id, q.question_text, q.question_number, q.answer_options
    FROM assessment_domains d
    JOIN assessment_questions q ON q.domain_id = d.id
    WHERE d.template_id = $1
    ORDER BY d.sort_order, q.sort_order
  `, [assessment.template_id]);

  // Group questions by domain
  const domainsMap = new Map();
  for (const row of dqRes.rows) {
    if (!domainsMap.has(row.domain_id)) {
      domainsMap.set(row.domain_id, {
        id: row.domain_id,
        name: row.domain_name,
        domain_number: row.domain_number,
        questions: []
      });
    }
    domainsMap.get(row.domain_id).questions.push({
      id: row.question_id,
      text: row.question_text,
      number: row.question_number,
      options: row.answer_options
    });
  }
  const domains = Array.from(domainsMap.values());

  // 3. Fetch existing responses
  const respRes = await query(`
    SELECT question_id, selected_score, comment, is_not_applicable
    FROM assessment_responses
    WHERE assessment_id = $1
  `, [assessmentId]);

  const existingResponses = respRes.rows.reduce((acc, row) => {
    acc[row.question_id] = {
      score: row.selected_score,
      comment: row.comment,
      na: row.is_not_applicable
    };
    return acc;
  }, {});

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-6 lg:p-8 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b pb-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link href="/assessments" className="text-muted-foreground hover:text-foreground">
              <ChevronLeft className="h-4 w-4" />
            </Link>
            <span className="text-sm font-medium text-muted-foreground">
              Back to Assessments
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">{assessment.site_name}</h1>
          <p className="text-muted-foreground">
            {assessment.template_name} · {assessment.status}
          </p>
        </div>
      </div>

      <AssessmentForm 
        assessmentId={assessmentId}
        domains={domains}
        initialResponses={existingResponses}
      />
    </div>
  );
}
