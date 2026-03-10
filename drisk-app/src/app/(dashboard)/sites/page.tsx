import { getSites } from "@/app/actions/site";
import { PlusCircle, Search, MapPin } from "lucide-react";
import Link from "next/link";

export default async function SitesPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string; type?: string }>;
}) {
  const params = await searchParams;
  const sites = await getSites(params);

  return (
    <div className="flex flex-col gap-6 w-full max-w-6xl mx-auto p-4 md:p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">Sites</h1>
          <p className="text-slate-500 dark:text-slate-400">Manage all individual locations within estates.</p>
        </div>
        <Link 
          href="/sites/new" 
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 disabled:pointer-events-none disabled:opacity-50 bg-sky-600 text-white hover:bg-sky-700 h-10 px-4 py-2"
        >
          <PlusCircle className="mr-2 h-4 w-4" />
          Add Site
        </Link>
      </div>

      <div className="flex flex-col gap-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex items-center gap-2 border border-slate-200 dark:border-slate-800 rounded-md px-3 py-2 bg-white dark:bg-slate-950 flex-1 max-w-md">
            <Search className="h-4 w-4 text-slate-500" />
            <form className="flex-1" action={async (formData) => {
              "use server";
            }}>
              <input 
                name="search"
                placeholder="Search sites, estates, clients..." 
                className="flex h-6 w-full bg-transparent px-1 py-1 text-sm outline-none placeholder:text-slate-500"
                defaultValue={params.search}
              />
            </form>
          </div>
          
          <div className="flex items-center gap-2">
            <select 
              className="flex h-10 items-center justify-between rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 px-3 py-2 text-sm"
              defaultValue={params.type || ""}
              onChange={() => {}}
            >
              <option value="">All Types</option>
              <option value="Office">Office</option>
              <option value="Data Centre">Data Centre</option>
              <option value="Retail">Retail</option>
              <option value="Industrial">Industrial</option>
            </select>
          </div>
        </div>

        <div className="rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="h-12 px-4 align-middle font-medium">Site</th>
                  <th className="h-12 px-4 align-middle font-medium">Estate & Client</th>
                  <th className="h-12 px-4 align-middle font-medium">Location</th>
                  <th className="h-12 px-4 align-middle font-medium text-center">Type</th>
                  <th className="h-12 px-4 align-middle font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {sites.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-slate-500">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <MapPin className="h-8 w-8 text-slate-400" />
                        <p>No sites found</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  sites.map((site) => (
                    <tr key={site.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                      <td className="p-4 align-middle font-medium text-slate-900 dark:text-slate-100">
                        <Link href={`/sites/${site.id}`} className="hover:underline">
                          {site.name}
                        </Link>
                      </td>
                      <td className="p-4 align-middle">
                        <div className="flex flex-col">
                          <span className="font-medium">{site.estate_name}</span>
                          <span className="text-xs text-slate-500">{site.client_name}</span>
                        </div>
                      </td>
                      <td className="p-4 align-middle">
                        <div className="flex flex-col text-slate-600 dark:text-slate-300">
                          <span>{site.city || "—"}</span>
                          <span className="text-xs">{site.country}</span>
                        </div>
                      </td>
                      <td className="p-4 align-middle text-center">
                        <span className="inline-flex items-center justify-center px-2 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-xs font-medium text-slate-800 dark:text-slate-300">
                          {site.site_type || "N/A"}
                        </span>
                      </td>
                      <td className="p-4 align-middle text-right space-x-3">
                        <Link 
                          href={`/sites/${site.id}`}
                          className="text-sky-600 hover:text-sky-700 dark:hover:text-sky-400 font-medium text-sm"
                        >
                          Profile
                        </Link>
                        <Link 
                          href={`/sites/${site.id}/edit`}
                          className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200 font-medium text-sm"
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
