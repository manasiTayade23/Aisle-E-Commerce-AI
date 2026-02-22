"use client";

import { useState } from "react";
import Link from "next/link";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });
      if (res?.error) {
        setError(res.error === "CredentialsSignin" ? "Invalid email or password" : res.error);
        return;
      }
      router.push(callbackUrl);
      router.refresh();
    } catch {
      setError("Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-dvh flex items-center justify-center bg-gradient-to-br from-peach-50/50 to-rose-50/50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-peach-100/50 bg-white/90 p-6 shadow-lg shadow-peach-200/20">
        <h1 className="text-xl font-extrabold text-gray-900 mb-1">Sign in to Aisle</h1>
        <p className="text-sm font-medium text-gray-600 mb-6">Use your account to sync cart across devices.</p>
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
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full btn-gradient rounded-xl py-2.5 text-sm font-bold disabled:opacity-50"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm font-semibold text-gray-600">
          No account? <Link href="/register" className="text-peach-600 font-bold underline underline-offset-2">Register</Link>
        </p>
      </div>
    </div>
  );
}
