const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { ...(options.headers || {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = body?.error;
    throw new ApiError(err?.message || res.statusText, err?.code || "UNKNOWN", res.status);
  }
  return res.json() as Promise<T>;
}

export interface ResumeDetail {
  id: string;
  filename: string;
  used_ocr: boolean;
  parsed: Record<string, unknown>;
}

export interface JobDetail {
  id: string;
  title: string | null;
  company: string | null;
  parsed: Record<string, unknown>;
}

export interface ScoreComponent {
  name: string;
  weight: number;
  raw_score: number;
  weighted_points: number;
  explanation: string;
}

export interface MatchResponse {
  id: string;
  resume_id: string;
  job_id: string;
  compatibility: {
    label: string;
    overall: number;
    components: ScoreComponent[];
    disclaimer: string;
  };
  match: {
    required_skill_matches: Array<{ skill: string; evidence_snippet: string | null; confidence: string }>;
    preferred_skill_matches: Array<{ skill: string; evidence_snippet: string | null; confidence: string }>;
    missing_required_skills: string[];
    missing_preferred_skills: string[];
    required_skill_coverage: number;
    preferred_skill_coverage: number;
  };
  ats: {
    ats_score: number;
    issues: Array<{ severity: string; area: string; message: string }>;
    warnings: Array<{ severity: string; area: string; message: string }>;
    recommendations: string[];
  };
}

export async function uploadResume(file: File): Promise<ResumeDetail> {
  const formData = new FormData();
  formData.append("file", file);
  return request<ResumeDetail>("/api/v1/resumes/upload", { method: "POST", body: formData });
}

export async function analyzeJob(text: string, company?: string): Promise<JobDetail> {
  return request<JobDetail>("/api/v1/jobs/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, company }),
  });
}

export async function runMatch(resumeId: string, jobId: string): Promise<MatchResponse> {
  return request<MatchResponse>("/api/v1/matching/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_id: resumeId, job_id: jobId }),
  });
}

export async function getAnalysis(analysisId: string): Promise<MatchResponse> {
  return request<MatchResponse>(`/api/v1/matching/${analysisId}`);
}
