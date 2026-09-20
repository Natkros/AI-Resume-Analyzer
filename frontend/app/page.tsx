export default function LandingPage() {
  return (
    <div className="space-y-16">
      <section className="text-center">
        <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Understand How Your Resume Matches the Job.
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          AI-powered resume intelligence for skills, ATS compatibility, semantic matching, and
          personalized improvement &mdash; every score backed by evidence, never a black box.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <a
            href="/resumes/upload"
            className="rounded-lg bg-brand-500 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-600"
          >
            Upload your resume
          </a>
          <a
            href="/jobs"
            className="rounded-lg border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Add a job description
          </a>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        {[
          { title: "Structured extraction", body: "Skills, experience, education, and projects parsed from PDF/DOCX/TXT, section-aware." },
          { title: "Explainable matching", body: "Every matched or missing skill is backed by a resume excerpt or a stated absence." },
          { title: "Grounded recommendations", body: "AI suggestions only ever cite what's actually in your resume — never fabricated experience." },
        ].map((f) => (
          <div key={f.title} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="font-semibold text-slate-900">{f.title}</h3>
            <p className="mt-2 text-sm text-slate-600">{f.body}</p>
          </div>
        ))}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-8">
        <h2 className="text-xl font-semibold">How it works</h2>
        <ol className="mt-4 space-y-2 text-sm text-slate-600">
          <li>1. Upload a resume (PDF, DOCX, or TXT).</li>
          <li>2. Paste or upload a job description.</li>
          <li>3. Get an explainable Resume-Job Compatibility Score with evidence for every subscore.</li>
          <li>4. Review ATS issues, skill gaps, and optional grounded recommendations.</li>
        </ol>
      </section>
    </div>
  );
}
