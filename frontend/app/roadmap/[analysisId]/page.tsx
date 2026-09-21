"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { generateRoadmap, RoadmapResult, ApiError } from "@/lib/api";

export default function RoadmapPage() {
  const params = useParams<{ analysisId: string }>();
  const [data, setData] = useState<RoadmapResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    generateRoadmap(params.analysisId)
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to generate roadmap."))
      .finally(() => setLoading(false));
  }, [params.analysisId]);

  if (loading) return <p className="text-sm text-slate-500">Building your learning roadmap...</p>;
  if (error)
    return (
      <div className="mx-auto max-w-xl rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        {error}
      </div>
    );
  if (!data) return null;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Skill gap roadmap</h1>
        <p className="mt-1 text-sm text-slate-600">One entry per missing required skill.</p>
      </div>

      {data.roadmap.length === 0 && (
        <p className="text-sm text-slate-500">No missing required skills — nothing to roadmap.</p>
      )}

      {data.roadmap.map((entry) => (
        <section key={entry.skill} className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-brand-600">{entry.skill}</h2>
          <p className="mt-2 text-sm text-slate-700">{entry.why_it_matters}</p>

          {entry.prerequisites && entry.prerequisites.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-semibold uppercase text-slate-400">Prerequisites</p>
              <p className="text-sm text-slate-600">{entry.prerequisites.join(", ")}</p>
            </div>
          )}

          <div className="mt-3">
            <p className="text-xs font-semibold uppercase text-slate-400">Learning sequence</p>
            <ol className="mt-1 list-inside list-decimal text-sm text-slate-700">
              {entry.learning_sequence.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
          </div>

          {entry.practical_project && (
            <div className="mt-3">
              <p className="text-xs font-semibold uppercase text-slate-400">Practical project</p>
              <p className="text-sm text-slate-700">{entry.practical_project}</p>
            </div>
          )}

          {entry.validation_task && (
            <div className="mt-3">
              <p className="text-xs font-semibold uppercase text-slate-400">How to validate</p>
              <p className="text-sm text-slate-700">{entry.validation_task}</p>
            </div>
          )}
        </section>
      ))}
    </div>
  );
}
