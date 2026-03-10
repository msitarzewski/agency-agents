"use client";

import { useState } from "react";
import { saveResponsesAction, completeAssessmentAction } from "./actions";
import { Save, Check, AlertTriangle, UploadCloud } from "lucide-react";

export function AssessmentForm({ assessmentId, domains, initialResponses }: any) {
  const [activeDomainIdx, setActiveDomainIdx] = useState(0);
  const [responses, setResponses] = useState<Record<string, any>>(initialResponses);
  const [saving, setSaving] = useState(false);

  const activeDomain = domains[activeDomainIdx];

  const handleResponseChange = (questionId: string, score: number) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: { ...(prev[questionId] || {}), score, na: false }
    }));
  };

  const handleCommentChange = (questionId: string, txt: string) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: { ...(prev[questionId] || {}), comment: txt }
    }));
  };

  const saveForm = async () => {
    setSaving(true);
    await saveResponsesAction(assessmentId, responses);
    setSaving(false);
  };

  const completeForm = async () => {
    if (confirm("Are you sure you want to complete this assessment? Missing responses will lower confidence score.")) {
      setSaving(true);
      await saveResponsesAction(assessmentId, responses);
      await completeAssessmentAction(assessmentId);
      // Redirection happening inside action
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div className="md:col-span-1 space-y-2">
        <div className="sticky top-6">
          <h3 className="font-semibold mb-4">Domains</h3>
          <nav className="flex flex-col gap-1">
            {domains.map((d: any, i: number) => {
              const answered = d.questions.filter((q:any) => responses[q.id]?.score).length;
              const total = d.questions.length;
              return (
                <button
                  key={d.id}
                  onClick={() => setActiveDomainIdx(i)}
                  className={`text-left px-3 py-2 rounded-md text-sm transition-colors ${
                    i === activeDomainIdx 
                      ? "bg-primary text-primary-foreground font-medium" 
                      : "hover:bg-muted font-normal text-muted-foreground"
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="truncate">{d.domain_number}. {d.name}</span>
                    <span className="text-xs opacity-75">{answered}/{total}</span>
                  </div>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="md:col-span-3 space-y-6">
        <div className="border rounded-xl bg-card text-card-foreground shadow-sm p-6 mb-6">
          <h2 className="text-2xl font-bold">{activeDomain.domain_number}. {activeDomain.name}</h2>
          <p className="text-muted-foreground">{activeDomain.description}</p>
        </div>

        <div className="space-y-6">
          {activeDomain.questions.map((q: any) => {
            const val = responses[q.id]?.score || null;
            const isHighRisk = val === 5;
            
            return (
              <div key={q.id} className="border rounded-xl bg-card shadow-sm p-4 md:p-6 space-y-4">
                <div className="font-medium text-lg">
                  <span className="text-muted-foreground mr-2">{q.number}.</span>
                  {q.text}
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {q.options.map((opt: any) => (
                    <button
                      key={opt.score}
                      onClick={() => handleResponseChange(q.id, opt.score)}
                      className={`px-4 py-3 rounded-lg border text-sm font-medium transition-all text-left flex justify-between ${
                        val === opt.score 
                          ? 'border-primary bg-primary/10 ring-1 ring-primary' 
                          : 'border-input hover:border-primary/50 hover:bg-muted/50'
                      }`}
                    >
                      {opt.label}
                      {val === opt.score && <Check className="h-4 w-4 text-primary" />}
                    </button>
                  ))}
                </div>

                {isHighRisk && (
                  <div className="p-3 bg-red-50 dark:bg-red-950/30 text-red-800 dark:text-red-400 rounded-md text-sm flex items-start gap-2 border border-red-200 dark:border-red-900 border-l-4">
                    <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                    <div>
                      <p className="font-medium">High Risk Identified</p>
                      <p className="text-xs mt-1">Please provide a comment or upload evidence.</p>
                    </div>
                  </div>
                )}

                <div className="pt-2">
                  <textarea 
                    value={responses[q.id]?.comment || ""}
                    onChange={(e) => handleCommentChange(q.id, e.target.value)}
                    placeholder="Add optional notes or observations..."
                    className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </div>
                
                <div className="flex justify-end pt-2">
                  <button className="text-xs text-muted-foreground inline-flex items-center hover:text-foreground">
                    <UploadCloud className="h-3 w-3 mr-1" />
                    Attach Evidence
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex justify-between items-center py-6 border-t mt-8">
          <div className="flex gap-2">
            <button 
              onClick={() => setActiveDomainIdx(Math.max(0, activeDomainIdx - 1))}
              disabled={activeDomainIdx === 0}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 py-2 px-4 disabled:opacity-50"
            >
              Previous Domain
            </button>
            <button 
              onClick={() => setActiveDomainIdx(Math.min(domains.length - 1, activeDomainIdx + 1))}
              disabled={activeDomainIdx === domains.length - 1}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 py-2 px-4 disabled:opacity-50"
            >
              Next Domain
            </button>
          </div>
          
          <div className="flex gap-2">
            <button 
              onClick={saveForm}
              disabled={saving}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 py-2 px-4"
            >
              <Save className="mr-2 h-4 w-4" /> Save Draft
            </button>
            <button 
              onClick={completeForm}
              disabled={saving}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-primary text-primary-foreground hover:bg-primary/90 h-10 py-2 px-4 shadow"
            >
              <Check className="mr-2 h-4 w-4" /> Complete Assessment
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
