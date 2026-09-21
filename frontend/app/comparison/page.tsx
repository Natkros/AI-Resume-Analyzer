"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { compareJobs, analyzeJob, ComparisonResult, ApiError } from "@/lib/api";

export default function ComparisonPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Loading...</p>}>
      <ComparisonForm />
    </Suspense>
  );
}

function ComparisonForm() {
  const searchParams = useSearchParams();
  const [resumeId, setResumeId] = useState(searchParams.get("resume_id") || "");
  const [jdTexts, setJdTexts] = useState(["", ""]);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function updateJdText(idx: number, value: string) {
    setJdTexts((prev) => prev.map((t, i) => (i === idx ? value : t)));
  }

  function addJobField() {
    setJdTexts((prev) => [...prev, ""]);
  }

  async function handleCompare(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const nonEmpty = jdTexts.filter((t) => t.trim());
      const jobs = await Promise.all(nonEmpty.map((text) => analyzeJob(text)));
      const jobIds = jobs.map((j) => j.id);
      const comparison = await compareJobs(resumeId.trim(), jobIds);
      setResult(comparison);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Comparison failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Compare one resume against multiple jobs</h1>
        <p className="mt-1 text-sm text-slate-600">
          Every job below is scored with the same transparent criteria — required skill coverage
          and missing skills are always shown alongside the ranking, never hidden behind a single number.
        </p>
      </div>

      <form onSubmit={handleCompare} className="space-y-4">
        <input
          type="text"
          placeholder="Resume ID"
          value={resumeId}
          onChange={(e) => setResumeId(e.target.value)}
          className="block w-full rounded-lg border border-slate-300 p-2 text-sm"
          required
        />
        {jdTexts.map((text, idx) => (
          <textarea
            key={idx}
            rows={6}
            placeholder={`Job description #${idx + 1}`}
            value={text}
            onChange={(e) => updateJdText(idx, e.target.value)}
            className="block w-full rounded-lg border border-slate-300 p-3 text-sm"
          />
        ))}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={addJobField}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-100"
          >
            + Add another job
          </button>
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-brand-500 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
          >
            {loading ? "Comparing..." : "Compare"}
          </button>
        </div>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="space-y-3">
          {result.comparisons.map((c, idx) => (
            <div key={c.job_id} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex items-center justify-between">
                <span className="font-semibold">
                  #{idx + 1} {c.job_title || "Untitled role"}
                </span>
                <span className="text-lg font-bold text-brand-600">{c.overall}%</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Required skill coverage: {Math.round(c.required_skill_coverage * 100)}%
              </p>
              {c.missing_required_skills.length > 0 && (
                <p className="mt-1 text-xs text-amber-700">
                  Missing: {c.missing_required_skills.join(", ")}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
