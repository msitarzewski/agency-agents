import { getClients } from "@/app/actions/client";
import { PlusCircle, Search, Building2 } from "lucide-react";
import Link from "next/link";
import { revalidatePath } from "next/cache";

export default async function ClientsPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string; sector?: string }>;
}) {
  const params = await searchParams;
  const clients = await getClients(params);

  return (
    <div className="flex flex-col gap-6 w-full max-w-6xl mx-auto p-4 md:p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">Clients</h1>
          <p className="text-slate-500 dark:text-slate-400">Manage organisations using the DRISK platform.</p>
        </div>
        <Link 
          href="/clients/new" 
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 disabled:pointer-events-none disabled:opacity-50 bg-sky-600 text-white hover:bg-sky-700 h-10 px-4 py-2"
        >
          <PlusCircle className="mr-2 h-4 w-4" />
          Add Client
        </Link>
      </div>

      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 border border-slate-200 dark:border-slate-800 rounded-md px-3 py-2 bg-white dark:bg-slate-950 w-full max-w-md">
          <Search className="h-4 w-4 text-slate-500" />
          <form className="flex-1" action={async (formData) => {
            "use server";
            // In a real app we'd redirect to /clients?search={val}
            // For MVP simplicity, we can just use a client component or server action redirect
          }}>
            <input 
              name="search"
              placeholder="Search clients..." 
              className="flex h-6 w-full bg-transparent px-1 py-1 text-sm outline-none placeholder:text-slate-500 disabled:cursor-not-allowed disabled:opacity-50"
              defaultValue={params.search}
            />
          </form>
        </div>

        <div className="rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="h-12 px-4 align-middle font-medium">Name</th>
                  <th className="h-12 px-4 align-middle font-medium">Sector</th>
                  <th className="h-12 px-4 align-middle font-medium">Contact</th>
                  <th className="h-12 px-4 align-middle font-medium text-center">Sites</th>
                  <th className="h-12 px-4 align-middle font-medium text-center">Open Actions</th>
                  <th className="h-12 px-4 align-middle font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {clients.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-slate-500">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <Building2 className="h-8 w-8 text-slate-400" />
                        <p>No clients found</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  clients.map((client) => (
                    <tr key={client.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                      <td className="p-4 align-middle font-medium text-slate-900 dark:text-slate-100">
                        {client.name}
                      </td>
                      <td className="p-4 align-middle">{client.sector || "—"}</td>
                      <td className="p-4 align-middle">
                        <div className="flex flex-col">
                          <span>{client.contact_name || "—"}</span>
                          <span className="text-xs text-slate-500">{client.contact_email}</span>
                        </div>
                      </td>
                      <td className="p-4 align-middle text-center">
                        <span className="inline-flex items-center justify-center px-2 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-xs font-medium">
                          {client.sites_count}
                        </span>
                      </td>
                      <td className="p-4 align-middle text-center">
                        {client.open_actions_count > 0 ? (
                          <span className="inline-flex items-center justify-center px-2 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-500 text-xs font-medium">
                            {client.open_actions_count}
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="p-4 align-middle text-right">
                        <Link 
                          href={\`/clients/\${client.id}/edit\`}
                          className="text-sky-600 hover:text-sky-700 dark:hover:text-sky-400 font-medium text-sm"
                        >
                          Edit
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
    </div>
  );
}
