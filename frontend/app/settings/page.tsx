"use client";

import { useState } from "react";
import { login, register, logout, isLoggedIn, ApiError } from "@/lib/api";

export default function SettingsPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState<string | null>(null);
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password);
      setLoggedIn(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Authentication failed.");
    }
  }

  function handleLogout() {
    logout();
    setLoggedIn(false);
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-semibold">Settings</h1>

      {loggedIn ? (
        <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6">
          <p className="text-sm text-slate-600">
            You&apos;re signed in. Resumes and jobs you create while signed in are private to your
            account — see the <a href="/dashboard" className="underline">dashboard</a>.
          </p>
          <button
            onClick={handleLogout}
            className="mt-4 rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-100"
          >
            Log out
          </button>
        </div>
      ) : (
        <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6">
          <div className="mb-4 flex gap-2 text-sm">
            <button
              className={`rounded-md px-3 py-1.5 ${mode === "login" ? "bg-brand-500 text-white" : "bg-slate-100"}`}
              onClick={() => setMode("login")}
            >
              Log in
            </button>
            <button
              className={`rounded-md px-3 py-1.5 ${mode === "register" ? "bg-brand-500 text-white" : "bg-slate-100"}`}
              onClick={() => setMode("register")}
            >
              Register
            </button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="block w-full rounded-lg border border-slate-300 p-2 text-sm"
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="block w-full rounded-lg border border-slate-300 p-2 text-sm"
              required
            />
            <button
              type="submit"
              className="w-full rounded-lg bg-brand-500 px-4 py-2 text-sm font-semibold text-white"
            >
              {mode === "login" ? "Log in" : "Create account"}
            </button>
          </form>
          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        </div>
      )}

      <p className="mt-6 text-xs text-slate-500">
        Resumes uploaded without signing in are still analyzed normally but are not tied to an
        account and won&apos;t appear on your dashboard.
      </p>
    </div>
  );
}
