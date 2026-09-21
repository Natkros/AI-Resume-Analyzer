"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { generateInterviewQuestions, InterviewResult, ApiError } from "@/lib/api";

function QuestionList({ title, questions }: { title: string; questions: string[] }) {
  if (!questions?.length) return null;
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6">
      <h2 className="font-semibold">{title}</h2>
      <ul className="mt-3 space-y-2 text-sm text-slate-700">
        {questions.map((q, idx) => (
          <li key={idx} className="rounded-lg bg-slate-50 p-3">
            {q}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function InterviewPage() {
  const params = useParams<{ analysisId: string }>();
  const [data, setData] = useState<InterviewResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    generateInterviewQuestions(params.analysisId)
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to generate interview questions."))
      .finally(() => setLoading(false));
  }, [params.analysisId]);

  if (loading) return <p className="text-sm text-slate-500">Generating interview questions...</p>;
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
        <h1 className="text-2xl font-semibold">Interview preparation</h1>
        <p className="mt-1 text-sm text-slate-600">
          Technical questions are scoped to skills your resume already demonstrates; project
          questions are based on the projects you actually described.
        </p>
      </div>
      <QuestionList title="Technical questions" questions={data.technical_questions} />
      <QuestionList title="Project questions" questions={data.project_questions} />
      <QuestionList title="Behavioral questions" questions={data.behavioral_questions} />
    </div>
  );
}
