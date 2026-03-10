import { query } from "@/lib/db";
import Link from "next/link";
import { ChevronLeft, ArrowRight, ShieldAlert, CheckCircle, BarChart3, AlertTriangle } from "lucide-react";

export const dynamic = "force-dynamic";

type VulnerabilityRow = {
  selected_score: number;
  question_text: string;
  weight: number;
  domain_name: string;
  domain_number: number;
};

export default async function AssessmentReview({ params }: { params: { id: string } }) {
  const assessmentId = params.id;
  
  const aRes = await query(`
    SELECT a.*, s.name as site_name, t.name as template_name,
           u.first_name || ' ' || u.last_name as assessor_name
    FROM assessments a
    JOIN sites s ON a.site_id = s.id
    JOIN assessment_templates t ON a.template_id = t.id
    LEFT JOIN users u ON a.assessor_id = u.id
    WHERE a.id = $1
  `, [assessmentId]);

  if (aRes.rowCount === 0) return <div>Assessment not found</div>;
  const assessment = aRes.rows[0];

  const scoreRes = await query(`SELECT score_value, band, metadata FROM risk_scores WHERE assessment_id = $1 AND layer = 'residual'`, [assessmentId]);
  const residualScore = scoreRes.rows[0]?.score_value ? parseFloat(scoreRes.rows[0].score_value).toFixed(1) : 0;
  const riskBand = scoreRes.rows[0]?.band || 'Unknown';
  const confidenceScore = scoreRes.rows[0]?.metadata?.confidenceScore ?? null;
  const confidenceLabel = confidenceScore === null ? 'N/A' : confidenceScore >= 90 ? 'High' : confidenceScore >= 70 ? 'Medium' : 'Low';
  const confidenceColor = confidenceScore === null ? 'text-slate-500' : confidenceScore >= 90 ? 'text-emerald-600' : confidenceScore >= 70 ? 'text-blue-600' : 'text-amber-600';

  // Top vulnerabilities: highest weighted-score responses
  const vulnRes = await query(`
    SELECT ar.selected_score, aq.question_text, aq.weight, ad.name as domain_name, ad.domain_number
    FROM assessment_responses ar
    JOIN assessment_questions aq ON ar.question_id = aq.id
    JOIN assessment_domains ad ON aq.domain_id = ad.id
    WHERE ar.assessment_id = $1
      AND ar.selected_score IS NOT NULL
      AND ar.is_not_applicable = false
    ORDER BY (ar.selected_score * aq.weight) DESC
    LIMIT 5
  `, [assessmentId]);
  const topVulnerabilities = vulnRes.rows;

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-6 lg:p-8 space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link href="/assessments" className="text-muted-foreground hover:text-foreground">
              <ChevronLeft className="h-4 w-4" />
            </Link>
            <span className="text-sm font-medium text-muted-foreground">
              Assessments
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Assessment Review</h1>
          <p className="text-muted-foreground mt-1">
            {assessment.site_name} · {assessment.assessed_at ? new Date(assessment.assessed_at).toLocaleDateString() : new Date().toLocaleDateString()}
          </p>
        </div>
        <div className="flex gap-2">
           <Link 
            href={`/assessments/${assessmentId}`}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 py-2 px-4 whitespace-nowrap"
          >
            Reopen Assessment
          </Link>
          <Link 
            href={`/reports/new?assessmentId=${assessmentId}`}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-primary text-primary-foreground hover:bg-primary/90 h-10 py-2 px-4 shadow whitespace-nowrap"
          >
            Create Action Plan
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="border rounded-xl bg-card shadow-sm p-6 col-span-1 border-t-4 border-t-amber-500">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">Residual Risk</h3>
            <ShieldAlert className="h-5 w-5 text-amber-500" />
          </div>
          <div className="mt-4 flex items-end gap-3">
             <span className="text-5xl font-extrabold">{residualScore}</span>
             <span className="text-lg font-semibold text-amber-600 mb-1 capitalize border border-amber-200 bg-amber-50 px-2 rounded">{riskBand} Band</span>
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            calculated dynamically based on Inherent Risk, Control effectiveness, and response capabilities.
          </p>
        </div>
        
        <div className="border rounded-xl bg-card shadow-sm p-6 col-span-1 border-t-4 border-t-blue-500">
           <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">Confidence Score</h3>
            <CheckCircle className="h-5 w-5 text-blue-500" />
          </div>
          <div className="mt-4 flex items-end gap-3">
             <span className={`text-5xl font-extrabold ${confidenceColor}`}>
               {confidenceScore !== null ? `${confidenceScore}%` : '—'}
             </span>
             <span className={`text-lg font-semibold mb-1 ${confidenceColor}`}>{confidenceLabel}</span>
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            Based on question completion rate. 90–100% = High, 70–89% = Medium, below 70% = Low.
          </p>
        </div>

        <div className="border rounded-xl bg-card shadow-sm p-6 col-span-1 border-t-4 border-t-slate-500">
           <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">Information</h3>
            <BarChart3 className="h-5 w-5 text-slate-500" />
          </div>
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between">
               <span className="text-muted-foreground">Assessor</span>
               <span className="font-medium">{assessment.assessor_name}</span>
            </div>
            <div className="flex justify-between">
               <span className="text-muted-foreground">Type</span>
               <span className="font-medium capitalize">{assessment.assessment_type}</span>
            </div>
            <div className="flex justify-between">
               <span className="text-muted-foreground">Template</span>
               <span className="font-medium">{assessment.template_name}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="border rounded-xl bg-card text-card-foreground shadow-sm">
        <div className="p-6 border-b">
           <h2 className="text-xl font-bold">Top Vulnerabilities</h2>
           <p className="text-sm text-muted-foreground mt-1">High-risk responses driving the risk score</p>
        </div>
        <div className="p-0">
          {topVulnerabilities.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground text-sm">
              No high-risk responses recorded for this assessment.
            </div>
          ) : (
            <ul className="divide-y">
              {topVulnerabilities.map((v: VulnerabilityRow, i: number) => (
                <li key={i} className="p-4 sm:px-6 flex items-start gap-4">
                  <div className="bg-red-100 dark:bg-red-900/30 text-red-600 p-2 rounded-full shrink-0">
                    <AlertTriangle className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm">{v.question_text}</h4>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-muted-foreground">
                        Domain {v.domain_number}: {v.domain_name}
                      </span>
                      <span className="text-xs font-semibold text-red-600 bg-red-100 dark:bg-red-900/30 px-1.5 rounded">
                        Score {v.selected_score} × Weight {v.weight}
                      </span>
                    </div>
                  </div>
                  <Link
                    href={`/assessments/${assessmentId}`}
                    className="shrink-0 inline-flex items-center text-sky-600 hover:text-sky-700 text-xs font-medium gap-1"
                  >
                    Review <ArrowRight className="h-3 w-3" />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      
    </div>
  );
}
