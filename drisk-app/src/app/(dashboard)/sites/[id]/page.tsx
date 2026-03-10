import { getSiteById, getLatestRiskScores, getAssessmentsBySiteId } from "@/app/actions/site";
import { getAssetsBySiteId } from "@/app/actions/asset";
import { 
  ArrowLeft, 
  MapPin, 
  Building2, 
  AlertTriangle, 
  ShieldAlert, 
  Activity, 
  FileText, 
  CheckSquare, 
  Paperclip,
  Server
} from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

export default async function SiteProfilePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ tab?: string }>;
}) {
  const { id } = await params;
  const { tab = "overview" } = await searchParams;
  
  const site = await getSiteById(id);
  if (!site) notFound();

  const [assets, riskScores, siteAssessments] = await Promise.all([
    getAssetsBySiteId(id),
    getLatestRiskScores(id),
    getAssessmentsBySiteId(id),
  ]);

  // Parse risk scores
  const residualScore = riskScores.find((s:any) => s.layer === 'residual');
  const domainScores = riskScores.filter((s:any) => s.layer === 'domain').sort((a:any, b:any) => {
    const aNum = a.metadata?.domain_number || 0;
    const bNum = b.metadata?.domain_number || 0;
    return aNum - bNum;
  });

  const getRiskColor = (band: string | null) => {
    if(!band) return "bg-slate-500 text-white";
    const b = band.toLowerCase();
    if(b === "critical") return "bg-purple-600 text-white";
    if(b === "very high") return "bg-red-600 text-white";
    if(b === "high") return "bg-amber-500 text-white";
    if(b === "moderate") return "bg-yellow-500 text-white";
    return "bg-green-500 text-white";
  };
  const getRiskTextColor = (band: string | null) => {
    if(!band) return "text-slate-500";
    const b = band.toLowerCase();
    if(b === "critical") return "text-purple-600 dark:text-purple-400";
    if(b === "very high") return "text-red-600 dark:text-red-400";
    if(b === "high") return "text-amber-500 dark:text-amber-400";
    if(b === "moderate") return "text-yellow-500 dark:text-yellow-400";
    return "text-green-500 dark:text-green-400";
  };
  const getRiskBgLight = (band: string | null) => {
    if(!band) return "bg-slate-100 text-slate-700";
    const b = band.toLowerCase();
    if(b === "critical") return "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400";
    if(b === "very high") return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
    if(b === "high") return "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400";
    if(b === "moderate") return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
    return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
  };

  const hasAssessment = residualScore || domainScores.length > 0;

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto p-4 md:p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Link 
            href="/sites" 
            className="inline-flex items-center justify-center rounded-md w-8 h-8 mt-1 text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:hover:text-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-50">{site.name}</h1>
              <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-xs font-semibold text-slate-800 dark:text-slate-300">
                {site.site_type || "No Type"}
              </span>
            </div>
            <p className="text-slate-500 dark:text-slate-400 flex items-center gap-2 text-sm">
              <Building2 className="h-4 w-4" /> {site.estate_name} • {site.client_name}
            </p>
            <p className="text-slate-500 dark:text-slate-400 flex items-center gap-2 text-sm mt-1">
              <MapPin className="h-4 w-4" /> {site.city}{site.city && site.country ? ", " : ""}{site.country}
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <Link 
            href={`/assessments/new?siteId=${site.id}`}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-sky-600 text-white hover:bg-sky-700 h-10 px-4 py-2"
          >
            Start Assessment
          </Link>
          <Link 
            href={`/sites/${site.id}/edit`}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-900 dark:text-slate-100 h-10 px-4 py-2"
          >
            Edit Site
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-800">
        <nav className="-mb-px flex space-x-6 overflow-x-auto">
          {[
            { id: "overview", label: "Overview", icon: Activity },
            { id: "assets", label: "Assets", icon: Server },
            { id: "assessments", label: "Assessments", icon: ShieldAlert },
            { id: "actions", label: "Actions", icon: CheckSquare },
            { id: "reports", label: "Reports", icon: FileText },
            { id: "evidence", label: "Evidence", icon: Paperclip },
          ].map((item) => (
            <Link
              key={item.id}
              href={`/sites/${site.id}?tab=${item.id}`}
              className={`
                whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors
                ${tab === item.id 
                  ? "border-sky-600 text-sky-600 dark:text-sky-500" 
                  : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 dark:text-slate-400 dark:hover:text-slate-300 dark:hover:border-slate-700"
                }
              `}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
              {item.id === "assets" && (
                <span className="ml-1 rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs text-slate-600 dark:text-slate-400">
                  {assets.length}
                </span>
              )}
            </Link>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-2">
        
        {/* OVERVIEW TAB */}
        {tab === "overview" && (
          <div className="grid gap-6 md:grid-cols-3">
            {/* Left Column: Risk Dashboard */}
            <div className="md:col-span-2 space-y-6">
              
              <div className="grid gap-4 sm:grid-cols-2">
                {/* Risk Score */}
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-6 flex flex-col items-center justify-center text-center shadow-sm relative overflow-hidden">
                  <div className={`absolute top-0 left-0 w-full h-1 ${getRiskColor(residualScore?.band)}`}></div>
                  <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-2">Residual Risk Score</h3>
                  {hasAssessment ? (
                    <>
                      <div className={`text-5xl font-extrabold mb-2 tracking-tighter ${getRiskTextColor(residualScore?.band)}`}>
                        {parseFloat(residualScore?.score_value).toFixed(1)}
                      </div>
                      <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${getRiskBgLight(residualScore?.band)}`}>
                        {residualScore?.band} RISK
                      </div>
                      <div className="text-xs text-slate-400 mt-4 flex items-center gap-2">
                        <span>Confidence: {residualScore?.metadata?.confidenceScore || 0}%</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="text-5xl font-extrabold text-slate-300 dark:text-slate-700 mb-2 tracking-tighter">--</div>
                      <div className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 text-xs font-semibold">
                        UNASSESSED
                      </div>
                    </>
                  )}
                </div>

                {/* Domain Chart */}
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-6 shadow-sm flex flex-col items-center justify-center min-h-[200px]">
                  <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-4 self-start">Domain Breakdown</h3>
                  {hasAssessment ? (
                    <div className="w-full h-32 flex items-end justify-between gap-2 px-2">
                      {domainScores.map((ds:any) => {
                        const score = Number(ds.score_value || 0);
                        const maxScore = Number(ds.metadata?.maxScore || 1);
                        const pct = Math.min(100, Math.max(0, (score / maxScore) * 100));
                        const dNum = ds.metadata?.domain_number;
                        
                        return (
                          <div key={ds.id} className="w-full flex flex-col items-center gap-2 group" title={`D${dNum}: ${score}/${maxScore}`}>
                            <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-t-sm relative h-full flex items-end overflow-hidden">
                              <div 
                                className={`w-full transition-all ${pct > 75 ? 'bg-red-500' : pct > 40 ? 'bg-amber-500' : 'bg-green-500'}`} 
                                style={{ height: `${pct}%` }}
                              ></div>
                            </div>
                            <span className="text-[10px] text-slate-400 font-mono">D{dNum}</span>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="flex-1 flex items-center justify-center">
                      <p className="text-sm text-slate-400 italic">Complete an assessment to see breakdown.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Vulnerabilities & Details */}
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-500" /> Top Vulnerabilities
                  </h3>
                </div>
                <div className="p-6">
                  {site.vulnerable_occupants || site.critical_services ? (
                    <div className="space-y-4">
                      {site.vulnerable_occupants && (
                        <div>
                          <h4 className="text-sm font-medium text-slate-900 dark:text-slate-300 mb-1">Vulnerable Occupants</h4>
                          <p className="text-sm text-slate-600 dark:text-slate-400">{site.vulnerable_occupants}</p>
                        </div>
                      )}
                      {site.critical_services && (
                        <div>
                          <h4 className="text-sm font-medium text-slate-900 dark:text-slate-300 mb-1">Critical Services</h4>
                          <p className="text-sm text-slate-600 dark:text-slate-400">{site.critical_services}</p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500 italic">No vulnerability profiles documented.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column: Meta info */}
            <div className="space-y-6">
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-6 shadow-sm">
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-4">Site Information</h3>
                <dl className="space-y-4 text-sm">
                  <div>
                    <dt className="text-slate-500 dark:text-slate-400 mb-1">Operating Hours</dt>
                    <dd className="font-medium text-slate-900 dark:text-slate-200">{site.operating_hours || "Not specified"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 dark:text-slate-400 mb-1">Public Access Level</dt>
                    <dd className="font-medium text-slate-900 dark:text-slate-200">{site.public_access_level || "Not specified"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 dark:text-slate-400 mb-1">Occupancy Profile</dt>
                    <dd className="font-medium text-slate-900 dark:text-slate-200">{site.occupancy_profile || "Not specified"}</dd>
                  </div>
                  {site.latitude && site.longitude && (
                    <div>
                      <dt className="text-slate-500 dark:text-slate-400 mb-1">Coordinates</dt>
                      <dd className="font-medium font-mono text-xs text-sky-600 dark:text-sky-400">
                        {site.latitude}, {site.longitude}
                      </dd>
                    </div>
                  )}
                </dl>
              </div>
              
              {/* Future UK Police API Widget Placeholder */}
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-6 shadow-sm border-dashed">
                <div className="flex items-center gap-2 mb-2">
                  <ShieldAlert className="h-4 w-4 text-slate-400" />
                  <h3 className="font-medium text-slate-700 dark:text-slate-300">Crime Intelligence</h3>
                </div>
                <p className="text-xs text-slate-500 mb-3">UK Police API Integration (Phase 1) will appear here.</p>
                <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded animate-pulse w-3/4"></div>
              </div>
            </div>
          </div>
        )}

        {/* ASSETS TAB */}
        {tab === "assets" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center bg-white dark:bg-slate-950 p-4 rounded-md border border-slate-200 dark:border-slate-800">
              <div>
                <h3 className="font-medium text-slate-900 dark:text-slate-100">Critical Assets</h3>
                <p className="text-sm text-slate-500">Track server rooms, medicine stores, and other critical areas.</p>
              </div>
              <button 
                type="button" 
                className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-sky-600 text-white hover:bg-sky-700 h-9 px-4"
                title="Add Asset form would open a modal here"
              >
                Add Asset
              </button>
            </div>
            
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {assets.length === 0 ? (
                <div className="col-span-full p-8 text-center text-slate-500 border border-dashed border-slate-300 dark:border-slate-700 rounded-lg">
                  <p>No assets tracked for this site.</p>
                </div>
              ) : (
                assets.map((asset) => (
                  <div key={asset.id} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-5 shadow-sm">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-slate-900 dark:text-slate-100">{asset.name}</h4>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold
                        ${asset.criticality_level >= 4 ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' : 
                          asset.criticality_level === 3 ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' : 
                          'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'}
                      `}>
                        L{asset.criticality_level}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">{asset.asset_type}</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">{asset.description}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* ASSESSMENTS TAB */}
        {tab === "assessments" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-slate-900 dark:text-slate-100">Assessment History</h3>
              <Link
                href={`/assessments/new?siteId=${site.id}`}
                className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-sky-600 text-white hover:bg-sky-700 h-9 px-4"
              >
                New Assessment
              </Link>
            </div>

            {siteAssessments.length === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 p-12 text-center">
                <ShieldAlert className="mx-auto h-10 w-10 text-slate-400 mb-3" />
                <p className="text-slate-500 mb-4">No assessments have been run for this site.</p>
                <Link
                  href={`/assessments/new?siteId=${site.id}`}
                  className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-sky-600 text-white hover:bg-sky-700 h-9 px-4"
                >
                  Run First Assessment
                </Link>
              </div>
            ) : (
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 overflow-hidden shadow-sm">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-500 dark:text-slate-400 uppercase bg-slate-50 dark:bg-slate-900/50">
                    <tr>
                      <th className="px-6 py-3 font-medium">Date</th>
                      <th className="px-6 py-3 font-medium">Template</th>
                      <th className="px-6 py-3 font-medium">Type</th>
                      <th className="px-6 py-3 font-medium">Status</th>
                      <th className="px-6 py-3 font-medium">Risk Band</th>
                      <th className="px-6 py-3 font-medium">Score</th>
                      <th className="px-6 py-3 text-right font-medium">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {siteAssessments.map((a: any) => {
                      const band = a.risk_band?.toLowerCase();
                      const bandClass = band === "critical"
                        ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
                        : band === "very high"
                        ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                        : band === "high"
                        ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400"
                        : band === "moderate"
                        ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
                        : band
                        ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                        : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400";

                      return (
                        <tr key={a.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-colors">
                          <td className="px-6 py-4 text-slate-700 dark:text-slate-300">
                            {a.assessed_at
                              ? new Date(a.assessed_at).toLocaleDateString()
                              : a.completed_at
                              ? new Date(a.completed_at).toLocaleDateString()
                              : new Date(a.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 text-slate-600 dark:text-slate-400">{a.template_name}</td>
                          <td className="px-6 py-4 capitalize text-slate-600 dark:text-slate-400">
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
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${bandClass}`}>
                                {a.risk_band}
                              </span>
                            ) : (
                              <span className="text-slate-400 text-xs">—</span>
                            )}
                          </td>
                          <td className="px-6 py-4 font-mono text-sm font-semibold text-slate-700 dark:text-slate-300">
                            {a.risk_score ? parseFloat(a.risk_score).toFixed(1) : "—"}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <Link
                              href={`/assessments/${a.id}${a.status === "completed" ? "/review" : ""}`}
                              className="inline-flex items-center text-sky-600 hover:text-sky-700 font-medium text-sm gap-1"
                            >
                              {a.status === "completed" ? "View" : "Resume"}
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ACTIONS TAB */}
        {tab === "actions" && (
          <div className="rounded-lg border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 p-12 text-center">
            <CheckSquare className="mx-auto h-12 w-12 text-slate-400 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">Action Tracking</h3>
            <p className="text-slate-500">Remediation actions linked to this site will appear here.</p>
          </div>
        )}

        {/* REPORTS TAB */}
        {tab === "reports" && (
          <div className="rounded-lg border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 p-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-slate-400 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">Reports Archive</h3>
            <p className="text-slate-500">Generated PDF/HTML reports for this site.</p>
          </div>
        )}

        {/* EVIDENCE TAB */}
        {tab === "evidence" && (
          <div className="rounded-lg border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 p-12 text-center">
            <Paperclip className="mx-auto h-12 w-12 text-slate-400 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">Evidence Repository</h3>
            <p className="text-slate-500">Collected photos and documents spanning all assessments.</p>
          </div>
        )}

      </div>
    </div>
  );
}
