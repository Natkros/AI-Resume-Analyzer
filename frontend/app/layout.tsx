import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Resume Analyzer & Job Matcher",
  description: "Explainable resume-job compatibility analysis.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <nav className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <a href="/" className="font-semibold tracking-tight">
              AI Resume Analyzer
            </a>
            <div className="flex gap-6 text-sm text-slate-600">
              <a href="/resumes/upload" className="hover:text-brand-600">Upload Resume</a>
              <a href="/jobs" className="hover:text-brand-600">Add Job</a>
              <a href="/comparison" className="hover:text-brand-600">Compare Jobs</a>
              <a href="/dashboard" className="hover:text-brand-600">Dashboard</a>
              <a href="/settings" className="hover:text-brand-600">Settings</a>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
