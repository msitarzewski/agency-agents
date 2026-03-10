"use client";

import { createEstate, updateEstate } from "@/app/actions/estate";
import { useRouter } from "next/navigation";
import { useTransition, useState } from "react";

export default function EstateForm({ 
  initialData, 
  clients 
}: { 
  initialData?: any,
  clients: { id: string; name: string }[]
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    const formData = new FormData(e.currentTarget);
    
    startTransition(async () => {
      try {
        if (initialData?.id) {
          await updateEstate(initialData.id, formData);
        } else {
          await createEstate(formData);
        }
        router.push("/estates");
      } catch (err: any) {
        setError(err.message || "An error occurred while saving the estate.");
      }
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-3 text-sm rounded bg-red-50 text-red-600 dark:bg-red-950/50 dark:text-red-400 border border-red-200 dark:border-red-900">
          {error}
        </div>
      )}
      
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2 md:col-span-2">
          <label htmlFor="name" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
            Estate Name <span className="text-red-500">*</span>
          </label>
          <input
            id="name"
            name="name"
            required
            defaultValue={initialData?.name}
            className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="e.g. Northern Operations"
          />
        </div>

        <div className="space-y-2 md:col-span-2">
          <label htmlFor="clientId" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
            Client <span className="text-red-500">*</span>
          </label>
          <select
            id="clientId"
            name="clientId"
            required
            defaultValue={initialData?.client_id || ""}
            className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="" disabled>Select a client...</option>
            {clients.map(c => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="space-y-2 md:col-span-2">
          <label htmlFor="region" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
            Region
          </label>
          <input
            id="region"
            name="region"
            defaultValue={initialData?.region}
            className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="e.g. Europe, North West UK, APAC"
          />
        </div>

        <div className="space-y-2 md:col-span-2">
          <label htmlFor="description" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
            Description
          </label>
          <textarea
            id="description"
            name="description"
            rows={4}
            defaultValue={initialData?.description}
            className="flex w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="Notes about this estate..."
          />
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
        <button
          type="button"
          onClick={() => router.back()}
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 disabled:pointer-events-none disabled:opacity-50 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-900 dark:text-slate-100 h-10 px-4 py-2"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isPending}
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 disabled:pointer-events-none disabled:opacity-50 bg-sky-600 text-white hover:bg-sky-700 h-10 px-4 py-2"
        >
          {isPending ? "Saving..." : initialData ? "Save Changes" : "Create Estate"}
        </button>
      </div>
    </form>
  );
}
