import { query } from "@/lib/db";
import { redirect } from "next/navigation";
import { Plus } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function NewAssessmentPage() {
  const sitesRes = await query(`SELECT id, name FROM sites ORDER BY name`);
  const templatesRes = await query(`SELECT id, name, version FROM assessment_templates WHERE is_active = true ORDER BY name`);

  async function createAssessment(formData: FormData) {
    "use server";
    
    const siteId = formData.get("siteId") as string;
    const templateId = formData.get("templateId") as string;
    const type = formData.get("type") as string;
    
    const { query } = require("@/lib/db");
    
    // In a real app we'd get the assessor_id from session. We'll pick the first user.
    const userRes = await query(`SELECT id FROM users LIMIT 1`);
    const assessorId = userRes.rows[0]?.id;
    
    if (!assessorId) throw new Error("No users found");

    const res = await query(`
      INSERT INTO assessments (site_id, template_id, assessor_id, status, assessment_type, assessed_at)
      VALUES ($1, $2, $3, 'draft', $4, CURRENT_DATE)
      RETURNING id
    `, [siteId, templateId, assessorId, type]);

    const assessmentId = res.rows[0].id;
    redirect(`/assessments/${assessmentId}`);
  }

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 lg:p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">New Assessment</h1>
        <p className="text-muted-foreground mt-1">Start a new site risk assessment</p>
      </div>

      <div className="border rounded-xl bg-card text-card-foreground shadow-sm">
        <form action={createAssessment} className="p-6 space-y-4">
          
          <div className="space-y-2">
            <label htmlFor="siteId" className="text-sm font-medium leading-none">Select Site</label>
            <select 
              id="siteId" 
              name="siteId" 
              required
              className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background"
            >
              <option value="">-- Choose a Site --</option>
              {sitesRes.rows.map((site: any) => (
                <option key={site.id} value={site.id}>{site.name}</option>
              ))}
            </select>
            {sitesRes.rows.length === 0 && (
              <p className="text-xs text-red-500">No sites exist. Please create a site first.</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="templateId" className="text-sm font-medium leading-none">Assessment Template</label>
            <select 
              id="templateId" 
              name="templateId" 
              required
              className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background"
            >
              <option value="">-- Choose a Template --</option>
              {templatesRes.rows.map((t: any) => (
                <option key={t.id} value={t.id}>{t.name} (v{t.version})</option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label htmlFor="type" className="text-sm font-medium leading-none">Assessment Type</label>
            <select 
              id="type" 
              name="type" 
              required
              className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background"
              defaultValue="standard"
            >
              <option value="rapid">Tier 1: Rapid Triage</option>
              <option value="standard">Tier 2: Standard Assessment</option>
              <option value="enhanced">Tier 3: Enhanced Assessment</option>
              <option value="scenario">Tier 4: Scenario/Event-Specific</option>
            </select>
          </div>

          <div className="pt-4 flex justify-end gap-2">
             <button 
                type="submit" 
                disabled={sitesRes.rows.length === 0 || templatesRes.rows.length === 0}
                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-primary text-primary-foreground hover:bg-primary/90 h-10 py-2 px-4 shadow whitespace-nowrap"
             >
                <Plus className="mr-2 h-4 w-4" /> Start Assessment
             </button>
          </div>
        </form>
      </div>
    </div>
  );
}
