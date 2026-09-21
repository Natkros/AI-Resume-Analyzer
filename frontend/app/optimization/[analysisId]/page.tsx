"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { optimizeResume, OptimizationResult, ApiError } from "@/lib/api";

export default function OptimizationPage() {
  const params = useParams<{ analysisId: string }>();
  const [data, setData] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    optimizeResume(params.analysisId)
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to optimize resume."))
      .finally(() => setLoading(false));
  }, [params.analysisId]);

  if (loading) return <p className="text-sm text-slate-500">Generating grounded suggestions...</p>;
  if (error)
    return (
      <div className="mx-auto max-w-xl rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        {error}
        {error.toLowerCase().includes("llm") && (
          <p className="mt-2">This feature requires an LLM API key configured on the backend (ANTHROPIC_API_KEY or OPENAI_API_KEY).</p>
        )}
      </div>
    );
  if (!data) return null;

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Resume optimization</h1>
        <p className="mt-1 text-sm text-slate-600">
          Suggestions are grounded only in your original resume text — nothing here adds a
          technology, employer, or metric you didn&apos;t already write.
        </p>
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="font-semibold">Improved summary</h2>
        <p className="mt-2 text-sm text-slate-700">{data.improved_summary}</p>
      </section>

      <section className="space-y-4">
        <h2 className="font-semibold">Before / after bullets</h2>
        {data.bullet_rewrites.map((b, idx) => (
          <div key={idx} className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-slate-400">Original</p>
            <p className="text-sm text-slate-500 line-through">{b.original}</p>
            <p className="mt-2 text-xs uppercase tracking-wide text-green-600">Optimized</p>
            <p className="text-sm font-medium text-slate-900">{b.improved}</p>
            <p className="mt-1 text-xs text-slate-500">{b.reason}</p>
          </div>
        ))}
      </section>

      {data.keyword_gaps_to_consider && data.keyword_gaps_to_consider.length > 0 && (
        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="font-semibold">Keyword gaps to consider</h2>
          <p className="mt-2 text-xs text-slate-500">
            Only add these if genuinely true of your experience.
          </p>
          <ul className="mt-2 list-inside list-disc text-sm text-slate-700">
            {data.keyword_gaps_to_consider.map((k) => (
              <li key={k}>{k}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
