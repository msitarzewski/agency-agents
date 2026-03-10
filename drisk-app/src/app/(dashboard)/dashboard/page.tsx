import { getDashboardStats, getRecentAssessments } from "@/app/actions/dashboard";
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import Link from "next/link";
import {
  Users,
  Building2,
  ShieldAlert,
  AlertTriangle,
  ClipboardList,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

export const dynamic = "force-dynamic";

export default async function Dashboard() {
  const session = await getServerSession(authOptions);
  const [stats, recentAssessments] = await Promise.all([
    getDashboardStats(),
    getRecentAssessments(5),
  ]);

  const getRiskBandStyle = (band: string | null) => {
    if (!band) return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";
    const b = band.toLowerCase();
    if (b === "critical") return "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400";
    if (b === "very high") return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
    if (b === "high") return "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400";
    if (b === "moderate") return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
    return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
  };

  const statCards = [
    {
      label: "Total Clients",
      value: stats.totalClients,
      icon: Users,
      href: "/clients",
      color: "text-sky-600",
      bg: "bg-sky-50 dark:bg-sky-900/20",
    },
    {
      label: "Total Sites",
      value: stats.totalSites,
      icon: Building2,
      href: "/sites",
      color: "text-indigo-600",
      bg: "bg-indigo-50 dark:bg-indigo-900/20",
    },
    {
      label: "High / Critical Risk Sites",
      value: stats.highRiskSites,
      icon: ShieldAlert,
      href: "/sites",
      color: "text-red-600",
      bg: "bg-red-50 dark:bg-red-900/20",
    },
    {
      label: "Overdue Actions",
      value: stats.overdueActions,
      icon: AlertTriangle,
      href: "/assessments",
      color: "text-amber-600",
      bg: "bg-amber-50 dark:bg-amber-900/20",
    },
    {
      label: "Total Assessments",
      value: stats.totalAssessments,
      icon: ClipboardList,
      href: "/assessments",
      color: "text-emerald-600",
      bg: "bg-emerald-50 dark:bg-emerald-900/20",
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4 md:p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
          Dashboard
        </h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Welcome back, <span className="font-semibold text-slate-700 dark:text-slate-300">{session?.user?.name}</span>
          {session?.user?.role && (
            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-400 capitalize">
              {session.user.role}
            </span>
          )}
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {statCards.map((card) => (
          <Link
            key={card.label}
            href={card.href}
            className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-5 shadow-sm hover:shadow-md transition-shadow group"
          >
            <div className="flex items-start justify-between mb-3">
              <div className={`p-2 rounded-lg ${card.bg}`}>
                <card.icon className={`h-5 w-5 ${card.color}`} />
              </div>
              <ArrowRight className="h-4 w-4 text-slate-300 group-hover:text-slate-500 transition-colors mt-1" />
            </div>
            <div className={`text-3xl font-extrabold tracking-tight ${card.color}`}>
              {card.value}
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{card.label}</p>
          </Link>
        ))}
      </div>

      {/* Recent Assessments */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex items-center justify-between">
          <h2 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-sky-600" />
            Recent Assessments
          </h2>
          <Link
            href="/assessments"
            className="text-sm text-sky-600 hover:text-sky-700 dark:text-sky-400 font-medium flex items-center gap-1"
          >
            View all <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {recentAssessments.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <ClipboardList className="h-10 w-10 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
            <p className="text-slate-500 dark:text-slate-400 text-sm">No assessments yet.</p>
            <Link
              href="/assessments/new"
              className="mt-4 inline-flex items-center justify-center rounded-md text-sm font-medium bg-sky-600 text-white hover:bg-sky-700 h-9 px-4"
            >
              Start First Assessment
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-500 dark:text-slate-400 uppercase bg-slate-50/80 dark:bg-slate-900/50">
                <tr>
                  <th className="px-6 py-3 font-medium">Site</th>
                  <th className="px-6 py-3 font-medium">Type</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium">Risk Band</th>
                  <th className="px-6 py-3 font-medium">Date</th>
                  <th className="px-6 py-3 text-right font-medium">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {recentAssessments.map((a: any) => (
                  <tr key={a.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-900 dark:text-slate-100">
                      <Link href={`/sites/${a.site_id}`} className="hover:text-sky-600 transition-colors">
                        {a.site_name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-slate-500 dark:text-slate-400 capitalize">
                      {a.assessment_type || "Standard"}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        a.status === "completed"
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400"
                          : a.status === "in_progress"
                          ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400"
                          : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                      }`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {a.risk_band ? (
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${getRiskBandStyle(a.risk_band)}`}>
                          {a.risk_band}
                        </span>
                      ) : (
                        <span className="text-slate-400 dark:text-slate-600 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-500 dark:text-slate-400">
                      {a.assessed_at
                        ? new Date(a.assessed_at).toLocaleDateString()
                        : a.completed_at
                        ? new Date(a.completed_at).toLocaleDateString()
                        : "—"}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/assessments/${a.id}${a.status === "completed" ? "/review" : ""}`}
                        className="inline-flex items-center text-sky-600 hover:text-sky-700 font-medium text-sm gap-1"
                      >
                        {a.status === "completed" ? "View" : "Resume"}
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Links */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Link
          href="/clients/new"
          className="rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 p-5 text-center hover:border-sky-400 dark:hover:border-sky-600 hover:bg-sky-50/50 dark:hover:bg-sky-900/10 transition-all group"
        >
          <Users className="h-6 w-6 text-slate-400 group-hover:text-sky-600 mx-auto mb-2 transition-colors" />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 group-hover:text-sky-700 dark:group-hover:text-sky-400">
            Add Client
          </p>
        </Link>
        <Link
          href="/sites/new"
          className="rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 p-5 text-center hover:border-indigo-400 dark:hover:border-indigo-600 hover:bg-indigo-50/50 dark:hover:bg-indigo-900/10 transition-all group"
        >
          <Building2 className="h-6 w-6 text-slate-400 group-hover:text-indigo-600 mx-auto mb-2 transition-colors" />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 group-hover:text-indigo-700 dark:group-hover:text-indigo-400">
            Register Site
          </p>
        </Link>
        <Link
          href="/assessments/new"
          className="rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 p-5 text-center hover:border-emerald-400 dark:hover:border-emerald-600 hover:bg-emerald-50/50 dark:hover:bg-emerald-900/10 transition-all group"
        >
          <ClipboardList className="h-6 w-6 text-slate-400 group-hover:text-emerald-600 mx-auto mb-2 transition-colors" />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 group-hover:text-emerald-700 dark:group-hover:text-emerald-400">
            Start Assessment
          </p>
        </Link>
      </div>
    </div>
  );
}
