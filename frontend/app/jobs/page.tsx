"use client";

import { useState } from "react";
import { analyzeJob, runMatch, ApiError } from "@/lib/api";

export default function AddJobPage() {
  const [text, setText] = useState("");
  const [resumeId, setResumeId] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim() || !resumeId.trim()) return;
    setStatus("loading");
    setError(null);
    try {
      const job = await analyzeJob(text);
      const match = await runMatch(resumeId.trim(), job.id);
      window.location.href = `/analysis/${match.id}`;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to analyze job.");
      setStatus("error");
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-semibold">Add a job description</h1>
      <p className="mt-1 text-sm text-slate-600">
        Paste the job description text and the resume ID from your upload step.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <input
          type="text"
          placeholder="Resume ID"
          value={resumeId}
          onChange={(e) => setResumeId(e.target.value)}
          className="block w-full rounded-lg border border-slate-300 p-2 text-sm"
        />
        <textarea
          rows={12}
          placeholder="Paste job description here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="block w-full rounded-lg border border-slate-300 p-3 text-sm"
        />
        <button
          type="submit"
          disabled={status === "loading"}
          className="rounded-lg bg-brand-500 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
        >
          {status === "loading" ? "Analyzing..." : "Analyze Match"}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
    </div>
  );
}
