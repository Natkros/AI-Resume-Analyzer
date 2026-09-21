"use client";

import { useEffect, useState } from "react";
import { isLoggedIn, listMyResumes, listMyJobs, deleteResume, ResumeSummary, JobDetail, ApiError } from "@/lib/api";

export default function DashboardPage() {
  const [resumes, setResumes] = useState<ResumeSummary[]>([]);
  const [jobs, setJobs] = useState<JobDetail[]>([]);
  const [loggedIn, setLoggedIn] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoggedIn(isLoggedIn());
    if (!isLoggedIn()) return;
    Promise.all([listMyResumes(), listMyJobs()])
      .then(([r, j]) => {
        setResumes(r);
        setJobs(j);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load dashboard."));
  }, []);

  async function handleDelete(resumeId: string) {
    await deleteResume(resumeId);
    setResumes((prev) => prev.filter((r) => r.id !== resumeId));
  }

  if (!loggedIn) {
    return (
      <div className="mx-auto max-w-md text-center">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="mt-2 text-sm text-slate-600">
          Sign in to save resumes and jobs to your account and see them here.
        </p>
        <a
          href="/settings"
          className="mt-4 inline-block rounded-lg bg-brand-500 px-5 py-2.5 text-sm font-semibold text-white"
        >
          Go to Settings
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <section>
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Your resumes</h2>
          <a href="/resumes/upload" className="text-sm text-brand-600 underline">
            + Upload another
          </a>
        </div>
        <div className="mt-3 space-y-2">
          {resumes.length === 0 && <p className="text-sm text-slate-500">No resumes yet.</p>}
          {resumes.map((r) => (
            <div key={r.id} className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3 text-sm">
              <span>
                {r.filename} {r.used_ocr && <span className="text-xs text-slate-400">(OCR)</span>}
              </span>
              <div className="flex gap-3">
                <a href={`/comparison?resume_id=${r.id}`} className="text-brand-600 underline">
                  Compare against jobs
                </a>
                <button onClick={() => handleDelete(r.id)} className="text-red-600 underline">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Your jobs</h2>
          <a href="/jobs" className="text-sm text-brand-600 underline">
            + Add another
          </a>
        </div>
        <div className="mt-3 space-y-2">
          {jobs.length === 0 && <p className="text-sm text-slate-500">No jobs yet.</p>}
          {jobs.map((j) => (
            <div key={j.id} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
              {j.title || "Untitled role"} {j.company && <span className="text-slate-500">— {j.company}</span>}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
