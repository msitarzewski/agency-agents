import Link from "next/link";
import { query } from "@/lib/db";
import { Plus, Search, FileText, ArrowRight } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function AssessmentsPage() {
  // Fetch from DB:
  const res = await query(`
    SELECT a.id, a.assessment_type, a.status, a.assessed_at, 
           s.name as site_name, t.name as template_name
    FROM assessments a
    JOIN sites s ON a.site_id = s.id
    JOIN assessment_templates t ON a.template_id = t.id
    ORDER BY a.created_at DESC
  `);
  
  const assessments = res.rows;

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Assessments</h1>
          <p className="text-muted-foreground mt-1">Manage and review site assessments</p>
        </div>
        <Link 
          href="/assessments/new" 
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background bg-primary text-primary-foreground hover:bg-primary/90 h-10 py-2 px-4 whitespace-nowrap"
        >
          <Plus className="mr-2 h-4 w-4" /> Start Assessment
        </Link>
      </div>

      <div className="border rounded-xl bg-card text-card-foreground shadow-sm overflow-hidden">
        <div className="p-4 border-b bg-muted/20 flex gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="search"
              placeholder="Search assessments..."
              className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pl-9"
            />
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-muted-foreground uppercase bg-muted/40">
              <tr>
                <th className="px-6 py-4 font-medium">Site</th>
                <th className="px-6 py-4 font-medium">Template</th>
                <th className="px-6 py-4 font-medium">Type</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Date</th>
                <th className="px-6 py-4 text-right font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {assessments.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                    <FileText className="h-8 w-8 mx-auto mb-3 opacity-20" />
                    <p>No assessments found</p>
                  </td>
                </tr>
              ) : (
                assessments.map((a: any) => (
                  <tr key={a.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-6 py-4 font-medium">{a.site_name}</td>
                    <td className="px-6 py-4 text-muted-foreground">{a.template_name}</td>
                    <td className="px-6 py-4 capitalize">{a.assessment_type || 'Standard'}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        a.status === 'completed' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400' :
                        a.status === 'in_progress' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
                        'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300'
                      }`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-muted-foreground">
                      {a.assessed_at ? new Date(a.assessed_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link 
                        href={`/assessments/${a.id}${a.status === 'completed' ? '/review' : ''}`}
                        className="inline-flex items-center text-primary font-medium hover:underline"
                      >
                        {a.status === 'completed' ? 'View Report' : 'Resume'} <ArrowRight className="ml-1 h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
