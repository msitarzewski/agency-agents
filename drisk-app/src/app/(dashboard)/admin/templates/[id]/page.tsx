import { query } from "@/lib/db";
import Link from "next/link";
import { ChevronLeft, Edit, AlertTriangle } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function TemplateDetailsPage({ params }: { params: { id: string } }) {
  const templateId = params.id;
  
  // Fetch template info
  const tRes = await query(`
    SELECT * FROM assessment_templates WHERE id = $1
  `, [templateId]);

  if (tRes.rowCount === 0) return <div>Template not found</div>;
  const template = tRes.rows[0];

  // Fetch domains and questions
  const dqRes = await query(`
    SELECT d.id as domain_id, d.name as domain_name, d.domain_number, d.description,
           q.id as question_id, q.question_text, q.question_number, q.weight, q.answer_options
    FROM assessment_domains d
    LEFT JOIN assessment_questions q ON q.domain_id = d.id
    WHERE d.template_id = $1
    ORDER BY d.sort_order, q.sort_order
  `, [template.id]);

  const domainsMap = new Map();
  for (const row of dqRes.rows) {
    if (!domainsMap.has(row.domain_id)) {
      domainsMap.set(row.domain_id, {
        id: row.domain_id,
        name: row.domain_name,
        number: row.domain_number,
        description: row.description,
        questions: []
      });
    }
    if (row.question_id) {
      domainsMap.get(row.domain_id).questions.push({
        id: row.question_id,
        text: row.question_text,
        number: row.question_number,
        weight: row.weight,
        options: row.answer_options
      });
    }
  }
  const domains = Array.from(domainsMap.values());

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link href="/admin/templates" className="text-muted-foreground hover:text-foreground">
              <ChevronLeft className="h-4 w-4" />
            </Link>
            <span className="text-sm font-medium text-muted-foreground">
              Back to Templates
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">{template.name}</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Version {template.version} · Tier {template.tier} · 
            <span className={template.is_active ? 'text-emerald-500 ml-1' : 'text-slate-500 ml-1'}>
              {template.is_active ? 'Active' : 'Inactive'}
            </span>
          </p>
        </div>
        <div className="flex gap-2">
           <button className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 py-2 px-4 shadow-sm">
             <Edit className="mr-2 h-4 w-4" /> Edit Template
           </button>
        </div>
      </div>

      <div className="space-y-8">
        {domains.map((d: any) => (
          <div key={d.id} className="border rounded-xl bg-card text-card-foreground shadow-sm overflow-hidden">
            <div className="bg-muted/30 p-4 border-b flex justify-between items-center">
               <div>
                 <h2 className="text-lg font-bold">Domain {d.number}: {d.name}</h2>
                 <p className="text-sm text-muted-foreground mt-0.5">{d.description}</p>
               </div>
               <div className="text-sm text-muted-foreground font-medium bg-background px-3 py-1 rounded-md border">
                 {d.questions.length} Questions
               </div>
            </div>
            
            <div className="divide-y divide-border">
              {d.questions.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                   No questions assigned to this domain yet.
                </div>
              ) : (
                d.questions.map((q: any) => (
                  <div key={q.id} className="p-4 sm:p-6 hover:bg-muted/10 transition-colors flex flex-col sm:flex-row gap-4">
                     <div className="w-16 shrink-0 font-medium text-muted-foreground">
                        {q.number}
                     </div>
                     <div className="flex-1 space-y-3">
                        <p className="font-medium text-base">{q.text}</p>
                        
                        <div className="flex flex-wrap items-center gap-2 mt-2">
                           <span className="inline-flex items-center justify-center rounded-md px-2 py-1 text-xs font-medium bg-primary/10 text-primary border border-primary/20">
                             Weight: {q.weight}
                           </span>
                           {q.weight >= 4 && (
                             <span className="inline-flex items-center justify-center rounded-md px-2 py-1 text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border border-amber-200 dark:border-amber-900">
                               <AlertTriangle className="mr-1 h-3 w-3" /> Critical Factor
                             </span>
                           )}
                        </div>

                        <div className="mt-3 bg-muted/30 rounded-lg p-3 border grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm">
                           {q.options.map((opt: any, idx: number) => (
                             <div key={idx} className="flex justify-between items-center bg-background px-3 py-2 rounded-md border border-border/50">
                                <span className="text-muted-foreground">{opt.label}</span>
                                <span className="font-medium">Score: {opt.score}</span>
                             </div>
                           ))}
                        </div>
                     </div>
                  </div>
                ))
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
