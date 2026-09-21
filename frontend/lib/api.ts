const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const TOKEN_STORAGE_KEY = "ara_access_token";

export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
  ) {
    super(message);
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (token) window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    else window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    // ignore storage errors (private browsing, disabled storage, etc.)
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = { ...(options.headers as Record<string, string> | undefined) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = body?.error;
    throw new ApiError(err?.message || res.statusText, err?.code || "UNKNOWN", res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export interface ResumeSummary {
  id: string;
  filename: string;
  used_ocr: boolean;
}

export interface ResumeDetail extends ResumeSummary {
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

export interface ComparisonResult {
  resume_id: string;
  comparisons: Array<{
    job_id: string;
    job_title: string | null;
    overall: number;
    required_skill_coverage: number;
    missing_required_skills: string[];
  }>;
}

export interface OptimizationResult {
  improved_summary: string;
  bullet_rewrites: Array<{ original: string; improved: string; reason: string }>;
  keyword_gaps_to_consider?: string[];
}

export interface InterviewResult {
  technical_questions: string[];
  project_questions: string[];
  behavioral_questions: string[];
  retrieved_sources?: Array<{ source: string; heading: string | null; similarity: number }>;
}

export interface RoadmapEntry {
  skill: string;
  why_it_matters: string;
  prerequisites?: string[];
  learning_sequence: string[];
  practical_project?: string;
  validation_task?: string;
}

export interface RoadmapResult {
  roadmap: RoadmapEntry[];
  retrieved_sources?: Array<{ source: string; heading: string | null; similarity: number }>;
}

// --- Auth ---

export async function register(email: string, password: string): Promise<string> {
  const res = await request<{ access_token: string }>("/api/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  setToken(res.access_token);
  return res.access_token;
}

export async function login(email: string, password: string): Promise<string> {
  const res = await request<{ access_token: string }>("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  setToken(res.access_token);
  return res.access_token;
}

export function logout() {
  setToken(null);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

// --- Resumes ---

export async function uploadResume(file: File): Promise<ResumeDetail> {
  const formData = new FormData();
  formData.append("file", file);
  return request<ResumeDetail>("/api/v1/resumes/upload", { method: "POST", body: formData });
}

export async function listMyResumes(): Promise<ResumeSummary[]> {
  return request<ResumeSummary[]>("/api/v1/resumes");
}

export async function deleteResume(resumeId: string): Promise<void> {
  return request<void>(`/api/v1/resumes/${resumeId}`, { method: "DELETE" });
}

// --- Jobs ---

export async function analyzeJob(text: string, company?: string): Promise<JobDetail> {
  return request<JobDetail>("/api/v1/jobs/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, company }),
  });
}

export async function listMyJobs(): Promise<JobDetail[]> {
  return request<JobDetail[]>("/api/v1/jobs");
}

// --- Matching ---

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

export async function compareJobs(resumeId: string, jobIds: string[]): Promise<ComparisonResult> {
  const params = new URLSearchParams({ resume_id: resumeId });
  return request<ComparisonResult>(`/api/v1/matching/compare?${params.toString()}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(jobIds),
  });
}

// --- LLM-backed recommendations (require ANTHROPIC_API_KEY/OPENAI_API_KEY configured server-side) ---

export async function optimizeResume(analysisId: string): Promise<OptimizationResult> {
  return request<OptimizationResult>(`/api/v1/resumes/${analysisId}/optimize`, { method: "POST" });
}

export async function generateInterviewQuestions(analysisId: string): Promise<InterviewResult> {
  return request<InterviewResult>("/api/v1/interview/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analysis_id: analysisId }),
  });
}

export async function generateRoadmap(analysisId: string): Promise<RoadmapResult> {
  return request<RoadmapResult>("/api/v1/roadmap/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analysis_id: analysisId }),
  });
}
