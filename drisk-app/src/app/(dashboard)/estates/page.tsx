import { getEstates } from "@/app/actions/estate";
import { PlusCircle, Search, Map } from "lucide-react";
import Link from "next/link";

export default async function EstatesPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string }>;
}) {
  const params = await searchParams;
  const estates = await getEstates(params);

  return (
    <div className="flex flex-col gap-6 w-full max-w-6xl mx-auto p-4 md:p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">Estates</h1>
          <p className="text-slate-500 dark:text-slate-400">Manage client estates grouping multiple sites.</p>
        </div>
        <Link 
          href="/estates/new" 
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 disabled:pointer-events-none disabled:opacity-50 bg-sky-600 text-white hover:bg-sky-700 h-10 px-4 py-2"
        >
          <PlusCircle className="mr-2 h-4 w-4" />
          Add Estate
        </Link>
      </div>

      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 border border-slate-200 dark:border-slate-800 rounded-md px-3 py-2 bg-white dark:bg-slate-950 w-full max-w-md">
          <Search className="h-4 w-4 text-slate-500" />
          <form className="flex-1" action={async (formData) => {
            "use server";
          }}>
            <input 
              name="search"
              placeholder="Search estates or clients..." 
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
                  <th className="h-12 px-4 align-middle font-medium">Estate Name</th>
                  <th className="h-12 px-4 align-middle font-medium">Client</th>
                  <th className="h-12 px-4 align-middle font-medium">Region</th>
                  <th className="h-12 px-4 align-middle font-medium text-center">Sites</th>
                  <th className="h-12 px-4 align-middle font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {estates.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-slate-500">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <Map className="h-8 w-8 text-slate-400" />
                        <p>No estates found</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  estates.map((estate) => (
                    <tr key={estate.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                      <td className="p-4 align-middle font-medium text-slate-900 dark:text-slate-100">
                        {estate.name}
                      </td>
                      <td className="p-4 align-middle">
                        <Link href={`/clients/${estate.client_id}/edit`} className="text-sky-600 hover:text-sky-700 dark:hover:text-sky-400 font-medium">
                          {estate.client_name}
                        </Link>
                      </td>
                      <td className="p-4 align-middle">{estate.region || "—"}</td>
                      <td className="p-4 align-middle text-center">
                        <span className="inline-flex items-center justify-center px-2 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-xs font-medium">
                          {estate.sites_count}
                        </span>
                      </td>
                      <td className="p-4 align-middle text-right">
                        <Link 
                          href={`/estates/${estate.id}/edit`}
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
