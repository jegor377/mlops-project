import { useState } from "react";
import { Link } from "react-router";

type ApiError = {
  detail: string;
};

type Stage = "form" | "sent";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState<Stage>("form");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await fetch("/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setStage("sent");
        return;
      }

      const data: ApiError = await response.json();
      setError(data.detail ?? "Something went wrong. Please try again.");
    } catch {
      setError("Could not reach the server. Please try again.");
    } finally {
      setLoading(false);
    }
  };

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

        {stage === "form" ? (
          <>
            {/* Heading */}
            <div className="text-center mb-5 sm:mb-6">
              <h1 className="text-xl sm:text-2xl font-semibold text-gray-900">Forgot password?</h1>
              <p className="text-xs sm:text-sm text-gray-400 mt-1">
                Enter your email and we'll send you a reset link.
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
                <label className="text-xs text-gray-500">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={loading}
                  className="mt-1 w-full px-3 py-2 sm:py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-black/80 focus:border-black transition disabled:opacity-50"
                  placeholder="you@example.com"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-black text-white text-sm font-medium py-2 sm:py-2.5 rounded-lg hover:bg-gray-800 transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Sending…" : "Send reset link"}
              </button>
            </form>
          </>
        ) : (
          <>
            {/* Success state */}
            <div className="text-center mb-5 sm:mb-6">
              {/* Mail icon */}
              <div className="flex justify-center mb-4">
                <div className="w-12 h-12 bg-gray-50 border border-gray-100 rounded-xl flex items-center justify-center">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="text-gray-600">
                    <rect x="2" y="4" width="20" height="16" rx="2" />
                    <path d="m2 7 10 7 10-7" />
                  </svg>
                </div>
              </div>
              <h1 className="text-xl sm:text-2xl font-semibold text-gray-900">Check your inbox</h1>
              <p className="text-xs sm:text-sm text-gray-400 mt-1 leading-relaxed">
                If <span className="text-gray-600 font-medium">{email}</span> is registered,
                you'll receive a reset link shortly.
              </p>
            </div>

            <div className="px-3 py-2.5 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-sm text-green-700 mb-5 sm:mb-6">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Reset link sent — check your spam folder too.
            </div>

            <button
              onClick={() => { setStage("form"); setEmail(""); setError(null); }}
              className="w-full border border-gray-200 text-gray-600 text-sm font-medium py-2 sm:py-2.5 rounded-lg hover:bg-gray-50 transition cursor-pointer"
            >
              Try a different email
            </button>
          </>
        )}

        {/* Footer */}
        <p className="text-xs text-gray-400 text-center mt-5 sm:mt-6">
          Remember your password?{" "}
          <Link to="/login" className="text-gray-600 hover:text-gray-900">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}