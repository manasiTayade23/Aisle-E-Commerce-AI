"use client";

import { useState } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name: name || undefined }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError((data as { detail?: string }).detail || "Registration failed");
        return;
      }
      setDone(true);
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <div className="min-h-dvh flex items-center justify-center bg-gradient-to-br from-peach-50/50 to-rose-50/50 px-4">
        <div className="w-full max-w-sm rounded-2xl border border-peach-100/50 bg-white/90 p-6 shadow-lg shadow-peach-200/20 text-center">
          <p className="text-gray-800 font-semibold">Account created. Sign in to continue.</p>
          <Link href="/signin" className="mt-4 inline-block btn-gradient rounded-xl px-4 py-2 text-sm font-bold">
            Sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-dvh flex items-center justify-center bg-gradient-to-br from-peach-50/50 to-rose-50/50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-peach-100/50 bg-white/90 p-6 shadow-lg shadow-peach-200/20">
        <h1 className="text-xl font-extrabold text-gray-900 mb-1">Create account</h1>
        <p className="text-sm font-medium text-gray-600 mb-6">Cart is saved when you sign in.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-xl border border-peach-200/50 px-3 py-2.5 text-gray-900 focus:border-peach-400 focus:ring-2 focus:ring-peach-100"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full rounded-xl border border-peach-200/50 px-3 py-2.5 text-gray-900 focus:border-peach-400 focus:ring-2 focus:ring-peach-100"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Name (optional)</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-xl border border-peach-200/50 px-3 py-2.5 text-gray-900 focus:border-peach-400 focus:ring-2 focus:ring-peach-100"
              placeholder="Your name"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full btn-gradient rounded-xl py-2.5 text-sm font-bold disabled:opacity-50"
          >
            {loading ? "Creating…" : "Register"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm font-semibold text-gray-600">
          Already have an account? <Link href="/signin" className="text-peach-600 font-bold underline underline-offset-2">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
