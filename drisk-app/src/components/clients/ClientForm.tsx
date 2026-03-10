"use client";

import { createClient, updateClient } from "@/app/actions/client";
import { useRouter } from "next/navigation";
import { useTransition, useState } from "react";

export default function ClientForm({ initialData }: { initialData?: any }) {
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
          await updateClient(initialData.id, formData);
        } else {
          await createClient(formData);
        }
        router.push("/clients");
      } catch (err: any) {
        setError(err.message || "An error occurred while saving the client.");
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
            Organisation Name <span className="text-red-500">*</span>
          </label>
          <input
            id="name"
            name="name"
            required
            defaultValue={initialData?.name}
            className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="e.g. Acme Corporation"
          />
        </div>
        
        <div className="space-y-2">
          <label htmlFor="sector" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
            Sector
          </label>
          <input
            id="sector"
            name="sector"
            defaultValue={initialData?.sector}
            className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="e.g. Finance, Healthcare"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="contactName" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
            Primary Contact Name
          </label>
          <input
            id="contactName"
            name="contactName"
            defaultValue={initialData?.contact_name}
            className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="e.g. Jane Doe"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="contactEmail" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
            Contact Email
          </label>
          <input
            id="contactEmail"
            name="contactEmail"
            type="email"
            defaultValue={initialData?.contact_email}
            className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="jane@example.com"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="contactPhone" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
            Contact Phone
          </label>
          <input
            id="contactPhone"
            name="contactPhone"
            type="tel"
            defaultValue={initialData?.contact_phone}
            className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="+44 123 456 7890"
          />
        </div>

        <div className="space-y-2 md:col-span-2">
          <label htmlFor="riskAppetite" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
            Risk Appetite / Notes
          </label>
          <textarea
            id="riskAppetite"
            name="riskAppetite"
            rows={4}
            defaultValue={initialData?.risk_appetite}
            className="flex w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="Client's tolerance for security risks, compliance requirements, etc."
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
          {isPending ? "Saving..." : initialData ? "Save Changes" : "Create Client"}
        </button>
      </div>
    </form>
  );
}
