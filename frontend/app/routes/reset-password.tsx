import { useState } from "react";
import { useSearchParams, Link } from "react-router";

type ApiError = {
  detail: string;
};

type Stage = "form" | "done";

function PasswordStrengthBar({ password }: { password: string }) {
  const score =
    (password.length >= 8 ? 1 : 0) +
    (/[A-Z]/.test(password) ? 1 : 0) +
    (/[0-9]/.test(password) ? 1 : 0) +
    (/[^A-Za-z0-9]/.test(password) ? 1 : 0);

  if (!password) return null;

  return (
    <div className="mt-2 flex gap-1">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
            i <= score
              ? score <= 1
                ? "bg-red-400"
                : score <= 2
                ? "bg-yellow-400"
                : score <= 3
                ? "bg-blue-400"
                : "bg-green-400"
              : "bg-gray-100"
          }`}
        />
      ))}
    </div>
  );
}

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState<Stage>("form");

  const mismatch = confirm.length > 0 && password !== confirm;

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const response = await fetch("/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });

      if (response.ok) {
        setStage("done");
        return;
      }

      const data: ApiError = await response.json();

      if (response.status === 400) {
        setError("This reset link is invalid or has expired.");
      } else {
        setError(data.detail ?? "Something went wrong. Please try again.");
      }
    } catch {
      setError("Could not reach the server. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const missingToken = !token;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-8 sm:px-6">
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

        {/* Missing token state */}
        {missingToken ? (
          <>
            <div className="text-center mb-5 sm:mb-6">
              <h1 className="text-xl sm:text-2xl font-semibold text-gray-900">Invalid link</h1>
              <p className="text-xs sm:text-sm text-gray-400 mt-1">
                This password reset link is missing or malformed.
              </p>
            </div>
            <div className="px-3 py-2.5 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-700 mb-5 sm:mb-6">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              Please use the link from your reset email.
            </div>
            <Link
              to="/forgot-password"
              className="w-full flex items-center justify-center bg-black text-white text-sm font-medium py-2 sm:py-2.5 rounded-lg hover:bg-gray-800 transition"
            >
              Request a new link
            </Link>
          </>
        ) : stage === "form" ? (
          <>
            {/* Heading */}
            <div className="text-center mb-5 sm:mb-6">
              <h1 className="text-xl sm:text-2xl font-semibold text-gray-900">Set new password</h1>
              <p className="text-xs sm:text-sm text-gray-400 mt-1">
                Choose a strong password for your account.
              </p>
            </div>

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

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3 sm:space-y-4">
              <div>
                <label className="text-xs text-gray-500">New password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  disabled={loading}
                  className="mt-1 w-full px-3 py-2 sm:py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-black/80 focus:border-black transition disabled:opacity-50"
                  placeholder="••••••••"
                />
                <PasswordStrengthBar password={password} />
              </div>

              <div>
                <label className="text-xs text-gray-500">Confirm password</label>
                <input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
                  disabled={loading}
                  className={`mt-1 w-full px-3 py-2 sm:py-2.5 text-sm border rounded-lg focus:outline-none focus:ring-2 transition disabled:opacity-50 ${
                    mismatch
                      ? "border-red-300 focus:ring-red-400/40 focus:border-red-400"
                      : "border-gray-200 focus:ring-black/80 focus:border-black"
                  }`}
                  placeholder="••••••••"
                />
                {mismatch && (
                  <p className="mt-1 text-xs text-red-500">Passwords do not match.</p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading || mismatch}
                className="w-full bg-black text-white text-sm font-medium py-2 sm:py-2.5 rounded-lg hover:bg-gray-800 transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Saving…" : "Set new password"}
              </button>
            </form>
          </>
        ) : (
          <>
            {/* Success state */}
            <div className="text-center mb-5 sm:mb-6">
              <div className="flex justify-center mb-4">
                <div className="w-12 h-12 bg-gray-50 border border-gray-100 rounded-xl flex items-center justify-center">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="text-gray-600">
                    <rect x="3" y="11" width="18" height="11" rx="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </div>
              </div>
              <h1 className="text-xl sm:text-2xl font-semibold text-gray-900">Password updated</h1>
              <p className="text-xs sm:text-sm text-gray-400 mt-1">
                Your password has been changed successfully.
              </p>
            </div>

            <div className="px-3 py-2.5 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-sm text-green-700 mb-5 sm:mb-6">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              You can now sign in with your new password.
            </div>

            <Link
              to="/login"
              className="w-full flex items-center justify-center bg-black text-white text-sm font-medium py-2 sm:py-2.5 rounded-lg hover:bg-gray-800 transition"
            >
              Go to sign in
            </Link>
          </>
        )}

        {/* Footer */}
        {!missingToken && stage === "form" && (
          <p className="text-xs text-gray-400 text-center mt-5 sm:mt-6">
            Remember your password?{" "}
            <Link to="/login" className="text-gray-600 hover:text-gray-900">
              Sign in
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}