"use client";

import { useEffect, useState } from "react";
import { getAnalysis, MatchResponse, ApiError } from "@/lib/api";

export default function AnalysisPage({ params }: { params: { id: string } }) {
  const [data, setData] = useState<MatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnalysis(params.id)
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load analysis."));
  }, [params.id]);

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!data) return <p className="text-sm text-slate-500">Loading analysis...</p>;

  const { compatibility, match, ats } = data;

  return (
    <div className="space-y-8">
      <section className="rounded-xl border border-slate-200 bg-white p-8 text-center">
        <p className="text-sm uppercase tracking-wide text-slate-500">{compatibility.label}</p>
        <p className="mt-2 text-6xl font-bold text-brand-600">{compatibility.overall}%</p>
        <p className="mx-auto mt-3 max-w-xl text-xs text-slate-500">{compatibility.disclaimer}</p>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="font-semibold">Score breakdown</h2>
        <div className="mt-4 space-y-3">
          {compatibility.components.map((c) => (
            <div key={c.name}>
              <div className="flex justify-between text-sm">
                <span className="font-medium capitalize">{c.name.replace(/_/g, " ")}</span>
                <span className="text-slate-500">{Math.round(c.raw_score * 100)}%</span>
              </div>
              <div className="mt-1 h-2 rounded-full bg-slate-100">
                <div
                  className="h-2 rounded-full bg-brand-500"
                  style={{ width: `${Math.round(c.raw_score * 100)}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-slate-500">{c.explanation}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-green-700">Matched Required Skills</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {match.required_skill_matches.map((m) => (
              <li key={m.skill}>
                <span className="font-medium">✓ {m.skill}</span>
                {m.evidence_snippet && (
                  <p className="text-xs text-slate-500">Evidence: {m.evidence_snippet}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-amber-700">Missing Required Skills</h2>
          <ul className="mt-3 space-y-1 text-sm">
            {match.missing_required_skills.length === 0 && (
              <li className="text-slate-500">None &mdash; all required skills matched.</li>
            )}
            {match.missing_required_skills.map((s) => (
              <li key={s}>△ {s}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="font-semibold">ATS Analysis &mdash; {ats.ats_score}/100</h2>
        <ul className="mt-3 space-y-1 text-sm">
          {ats.issues.map((i, idx) => (
            <li key={idx} className="text-red-600">⚠ {i.message}</li>
          ))}
          {ats.warnings.map((w, idx) => (
            <li key={idx} className="text-amber-600">△ {w.message}</li>
          ))}
        </ul>
        <h3 className="mt-4 text-sm font-semibold">Recommendations</h3>
        <ul className="mt-2 list-inside list-disc text-sm text-slate-600">
          {ats.recommendations.map((r, idx) => (
            <li key={idx}>{r}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
