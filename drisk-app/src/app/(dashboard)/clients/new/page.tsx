import ClientForm from "@/components/clients/ClientForm";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function NewClientPage() {
  return (
    <div className="flex flex-col gap-6 w-full max-w-3xl mx-auto p-4 md:p-6">
      <div className="flex items-center gap-4">
        <Link 
          href="/clients" 
          className="inline-flex items-center justify-center rounded-md w-8 h-8 text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:hover:text-slate-50 dark:hover:bg-slate-800 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span className="sr-only">Back</span>
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">Add Client</h1>
          <p className="text-slate-500 dark:text-slate-400">Create a new organisation in the DRISK platform.</p>
        </div>
      </div>

      <div className="rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-6">
        <ClientForm />
      </div>
    </div>
  );
}
