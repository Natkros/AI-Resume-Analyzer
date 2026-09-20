"use client";

import { useState } from "react";
import { uploadResume, ApiError } from "@/lib/api";

export default function UploadResumePage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setStatus("uploading");
    setError(null);
    try {
      const result = await uploadResume(file);
      setResumeId(result.id);
      setStatus("done");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
      setStatus("error");
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="text-2xl font-semibold">Upload your resume</h1>
      <p className="mt-1 text-sm text-slate-600">Supported formats: PDF, DOCX, TXT.</p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full rounded-lg border border-slate-300 p-2 text-sm"
        />
        <button
          type="submit"
          disabled={!file || status === "uploading"}
          className="rounded-lg bg-brand-500 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
        >
          {status === "uploading" ? "Parsing..." : "Upload & Parse"}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      {status === "done" && resumeId && (
        <div className="mt-6 rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800">
          Resume parsed successfully. Resume ID: <code>{resumeId}</code>
          <div className="mt-2">
            <a href="/jobs" className="font-semibold underline">
              Next: add a job description &rarr;
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
