"use client";

import { createSite, updateSite } from "@/app/actions/site";
import { useRouter } from "next/navigation";
import { useTransition, useState } from "react";

export default function SiteForm({ 
  initialData, 
  estates 
}: { 
  initialData?: any,
  estates: { id: string; name: string; client_name: string }[]
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
          await updateSite(initialData.id, formData);
        } else {
          await createSite(formData);
        }
        router.push("/sites");
      } catch (err: any) {
        setError(err.message || "An error occurred while saving the site.");
      }
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {error && (
        <div className="p-3 text-sm rounded bg-red-50 text-red-600 dark:bg-red-950/50 dark:text-red-400 border border-red-200 dark:border-red-900">
          {error}
        </div>
      )}

      {/* Basic Info */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 border-b border-slate-200 dark:border-slate-800 pb-2">
          Basic Information
        </h3>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <label htmlFor="name" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Site Name <span className="text-red-500">*</span>
            </label>
            <input
              id="name"
              name="name"
              required
              defaultValue={initialData?.name}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="e.g. London HQ"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="estateId" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Estate <span className="text-red-500">*</span>
            </label>
            <select
              id="estateId"
              name="estateId"
              required
              defaultValue={initialData?.estate_id || ""}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="" disabled>Select an estate...</option>
              {estates.map(e => (
                <option key={e.id} value={e.id}>
                  {e.client_name} - {e.name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label htmlFor="siteType" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Site Type
            </label>
            <select
              id="siteType"
              name="siteType"
              defaultValue={initialData?.site_type || ""}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="" disabled>Select a site type...</option>
              <option value="Office">Office</option>
              <option value="Data Centre">Data Centre</option>
              <option value="Retail">Retail</option>
              <option value="Industrial">Industrial</option>
              <option value="Healthcare">Healthcare</option>
              <option value="Education">Education</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>
      </div>

      {/* Location */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 border-b border-slate-200 dark:border-slate-800 pb-2">
          Location
        </h3>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <label htmlFor="addressLine1" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Address Line 1
            </label>
            <input
              id="addressLine1"
              name="addressLine1"
              defaultValue={initialData?.address_line1}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
              placeholder="123 Example St"
            />
          </div>
          
          <div className="space-y-2 md:col-span-2">
            <label htmlFor="addressLine2" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Address Line 2
            </label>
            <input
              id="addressLine2"
              name="addressLine2"
              defaultValue={initialData?.address_line2}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="city" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              City
            </label>
            <input
              id="city"
              name="city"
              defaultValue={initialData?.city}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="postcode" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Postcode / ZIP
            </label>
            <input
              id="postcode"
              name="postcode"
              defaultValue={initialData?.postcode}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
            />
          </div>

          <div className="space-y-2 md:col-span-2">
            <label htmlFor="country" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Country
            </label>
            <input
              id="country"
              name="country"
              defaultValue={initialData?.country || "UK"}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
            />
          </div>

          {/* Coordinates section with notes for Phase 1 API integration */}
          <div className="space-y-2">
            <label htmlFor="latitude" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Latitude (for Police API)
            </label>
            <input
              id="latitude"
              name="latitude"
              type="number"
              step="any"
              defaultValue={initialData?.latitude}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
              placeholder="51.5072"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="longitude" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Longitude (for Police API)
            </label>
            <input
              id="longitude"
              name="longitude"
              type="number"
              step="any"
              defaultValue={initialData?.longitude}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
              placeholder="-0.1276"
            />
          </div>
        </div>
      </div>

      {/* Operational Details */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 border-b border-slate-200 dark:border-slate-800 pb-2">
          Operational Details
        </h3>
        <div className="grid gap-4 md:grid-cols-2">
          
          <div className="space-y-2">
            <label htmlFor="operatingHours" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Operating Hours
            </label>
            <input
              id="operatingHours"
              name="operatingHours"
              defaultValue={initialData?.operating_hours}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
              placeholder="e.g. 09:00 - 17:00 Mon-Fri"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="publicAccessLevel" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Public Access Level
            </label>
            <input
              id="publicAccessLevel"
              name="publicAccessLevel"
              defaultValue={initialData?.public_access_level}
              className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
              placeholder="e.g. Open, Restricted, None"
            />
          </div>

          <div className="space-y-2 md:col-span-2">
            <label htmlFor="occupancyProfile" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Occupancy Profile
            </label>
            <textarea
              id="occupancyProfile"
              name="occupancyProfile"
              rows={3}
              defaultValue={initialData?.occupancy_profile}
              className="flex w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
              placeholder="Number of staff, visitors, shift patterns..."
            />
          </div>

          <div className="space-y-2 md:col-span-2">
            <label htmlFor="vulnerableOccupants" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Vulnerable Occupants
            </label>
            <textarea
              id="vulnerableOccupants"
              name="vulnerableOccupants"
              rows={2}
              defaultValue={initialData?.vulnerable_occupants}
              className="flex w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
              placeholder="Details of any vulnerable individuals on site..."
            />
          </div>

          <div className="space-y-2 md:col-span-2">
            <label htmlFor="criticalServices" className="text-sm font-medium leading-none text-slate-900 dark:text-slate-100">
              Critical Services
            </label>
            <textarea
              id="criticalServices"
              name="criticalServices"
              rows={2}
              defaultValue={initialData?.critical_services}
              className="flex w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm"
              placeholder="Description of critical systems, utilities..."
            />
          </div>

        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
        <button
          type="button"
          onClick={() => router.back()}
          className="inline-flex items-center justify-center rounded-md text-sm font-medium border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-900 dark:text-slate-100 h-10 px-4 py-2"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isPending}
          className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-sky-600 text-white hover:bg-sky-700 h-10 px-4 py-2"
        >
          {isPending ? "Saving..." : initialData ? "Save Changes" : "Create Site"}
        </button>
      </div>
    </form>
  );
}
