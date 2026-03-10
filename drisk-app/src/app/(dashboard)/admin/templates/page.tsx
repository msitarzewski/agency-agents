import Link from "next/link";
import { query } from "@/lib/db";
import { Plus, Search, FileText, ArrowRight, Settings } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function AdminTemplatesPage() {
  const res = await query(`
    SELECT t.id, t.name, t.version, t.tier, t.is_active, t.created_at,
           (SELECT COUNT(*) FROM assessment_domains d WHERE d.template_id = t.id) as domain_count
    FROM assessment_templates t
    ORDER BY t.created_at DESC
  `);
  
  const templates = res.rows;

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Assessment Templates</h1>
          <p className="text-muted-foreground mt-1">Manage assessment forms and question banks</p>
        </div>
        <Link 
          href="/admin/templates/new" 
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 py-2 px-4 shadow-sm"
        >
          <Plus className="mr-2 h-4 w-4" /> Create Template
        </Link>
      </div>

      <div className="border rounded-xl bg-card text-card-foreground shadow-sm overflow-hidden">
        <div className="p-4 border-b bg-muted/20 flex gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="search"
              placeholder="Search templates..."
              className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 pl-9"
            />
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-muted-foreground uppercase bg-muted/40">
              <tr>
                <th className="px-6 py-4 font-medium">Name</th>
                <th className="px-6 py-4 font-medium">Version</th>
                <th className="px-6 py-4 font-medium">Tier</th>
                <th className="px-6 py-4 font-medium">Domains</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {templates.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                    <Settings className="h-8 w-8 mx-auto mb-3 opacity-20" />
                    <p>No templates found</p>
                  </td>
                </tr>
              ) : (
                templates.map((t: any) => (
                  <tr key={t.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-6 py-4 font-medium">{t.name}</td>
                    <td className="px-6 py-4 text-muted-foreground">v{t.version}</td>
                    <td className="px-6 py-4 text-muted-foreground">Tier {t.tier}</td>
                    <td className="px-6 py-4 text-muted-foreground">{t.domain_count} Domains</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        t.is_active ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300'
                      }`}>
                        {t.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link 
                        href={`/admin/templates/${t.id}`}
                        className="inline-flex items-center text-primary font-medium hover:underline"
                      >
                        Manage Questions <ArrowRight className="ml-1 h-4 w-4" />
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
