import { useRef, useState } from "react";
import { useSearchParams, useNavigate } from "react-router";
import { useAuth } from "../context/auth";

type ApiError = {
  detail: string;
};

export default function LoginPage() {
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchParams] = useSearchParams();
  const justRegistered = searchParams.get("registered") === "true";
  const justActivated = searchParams.get("just-activated") === "true";
  const googleCancelled = searchParams.get("error") === "google_login_cancelled";
  const githubCancelled = searchParams.get("error") === "github_login_cancelled";
  const oauthLoginError = searchParams.get("login-error");
  const navigate = useNavigate();
  const { refetch } = useAuth();

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const email = emailRef.current?.value ?? "";
    const password = passwordRef.current?.value ?? "";

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        await refetch();
        navigate("/dashboard");
        return;
      }

      const data: ApiError = await response.json();

      if (response.status === 403) {
        setError("Account not verified. Please check your email.");
      } else if (response.status === 401) {
        setError("Invalid email or password.");
      } else {
        setError(data.detail ?? "Something went wrong. Please try again.");
      }
    } catch {
      setError("Could not reach the server. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-8 sm:px-6">
      {/* Card */}
      <div className="w-full max-w-md bg-white border border-gray-100 rounded-2xl shadow-xl shadow-gray-200/60 p-6 sm:p-8 mt-16">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-5 sm:mb-6 justify-center">
          <div className="w-7 h-7 sm:w-8 sm:h-8 bg-black rounded-lg flex items-center justify-center">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="white">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
          </div>
          <span className="font-semibold text-base sm:text-lg tracking-tight">Volta</span>
        </div>

        {/* Heading */}
        <div className="text-center mb-5 sm:mb-6">
          <h1 className="text-xl sm:text-2xl font-semibold text-gray-900">Welcome back</h1>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">Sign in to your account</p>
        </div>

        {/* Success banner */}
        {(justRegistered || justActivated) && (
          <div className="mb-4 px-3 py-2.5 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-sm text-green-700">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            Account {justRegistered ? (<>created</>) : (<>activated</>)} — please sign in.
          </div>
        )}

        {/* Warning banner */}
        {(googleCancelled || githubCancelled) && (
          <div className="mb-4 px-3 py-2.5 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2 text-sm text-amber-700">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            {googleCancelled ? "Google" : "GitHub"} sign-in was cancelled.
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="mb-4 px-3 py-2.5 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-700">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
          </div>
        )}
      
        {/* Login error banner */}
        {(oauthLoginError && !error) && (
          <div className="mb-4 px-3 py-2.5 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-700">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {oauthLoginError}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3 sm:space-y-4">
          <div>
            <label className="text-xs text-gray-500">Email</label>
            <input
              type="email"
              ref={emailRef}
              defaultValue=""
              required
              disabled={loading}
              className="mt-1 w-full px-3 py-2 sm:py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-black/80 focus:border-black transition disabled:opacity-50"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <div className="flex items-center justify-between">
              <label className="text-xs text-gray-500">Password</label>
              <a href="/forgot-password" className="text-xs text-gray-400 hover:text-gray-600">
                Forgot?
              </a>
            </div>
            <input
              type="password"
              ref={passwordRef}
              defaultValue=""
              required
              disabled={loading}
              className="mt-1 w-full px-3 py-2 sm:py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-black/80 focus:border-black transition disabled:opacity-50"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-black text-white text-sm font-medium py-2 sm:py-2.5 rounded-lg hover:bg-gray-800 transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        {/* Divider */}
        <div className="my-5 sm:my-6 flex items-center gap-3">
          <div className="flex-1 h-px bg-gray-100" />
          <span className="text-xs text-gray-300">or</span>
          <div className="flex-1 h-px bg-gray-100" />
        </div>

        {/* OAuth Buttons */}
        <div className="space-y-2 sm:space-y-3">
          <a href="/auth/login_via/google" className="w-full flex items-center justify-center gap-2 border border-gray-200 rounded-lg py-2 sm:py-2.5 text-sm hover:bg-gray-50 transition cursor-pointer">
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path fill="#EA4335" d="M12 10.2v3.6h5.1c-.2 1.2-1.4 3.5-5.1 3.5-3.1 0-5.6-2.6-5.6-5.8s2.5-5.8 5.6-5.8c1.8 0 3 .8 3.7 1.4l2.5-2.4C16.9 3.2 14.7 2.3 12 2.3 6.9 2.3 2.8 6.5 2.8 11.5S6.9 20.7 12 20.7c6.9 0 9.2-4.8 9.2-7.3 0-.5 0-.8-.1-1.2H12z" />
            </svg>
            Continue with Google
          </a>

          <a href="/auth/login_via/github" className="w-full flex items-center justify-center gap-2 border border-gray-200 rounded-lg py-2 sm:py-2.5 text-sm hover:bg-gray-50 transition cursor-pointer">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 .5C5.7.5.9 5.3.9 11.6c0 4.9 3.2 9 7.6 10.4.6.1.8-.3.8-.6v-2.3c-3.1.7-3.7-1.5-3.7-1.5-.5-1.3-1.2-1.6-1.2-1.6-1-.7.1-.7.1-.7 1.1.1 1.7 1.2 1.7 1.2 1 .1.7 2.3 2.9 1.6.1-.7.4-1.2.7-1.5-2.5-.3-5.1-1.3-5.1-5.8 0-1.3.5-2.3 1.2-3.2-.1-.3-.5-1.6.1-3.3 0 0 1-.3 3.3 1.2a11.4 11.4 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.7.2 3 .1 3.3.8.9 1.2 2 1.2 3.2 0 4.5-2.6 5.5-5.1 5.8.4.3.7.9.7 1.9v2.8c0 .3.2.7.8.6 4.4-1.4 7.6-5.5 7.6-10.4C23.1 5.3 18.3.5 12 .5z" />
            </svg>
            Continue with GitHub
          </a>
        </div>

        {/* Footer */}
        <p className="text-xs text-gray-400 text-center mt-5 sm:mt-6">
          Don't have an account?{" "}
          <a href="/register" className="text-gray-600 hover:text-gray-900">
            Sign up
          </a>
        </p>
      </div>
    </div>
  );
}