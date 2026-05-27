import { useState } from "react";
import { useNavigate } from "react-router";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const handleSubmit = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      setIsLoading(false);
      return;
    }
    try {
      const response = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, confirmPassword }),
      });
      if (response.ok) {
        navigate("/login?registered=true");
      } else {
        const data = await response.json().catch(() => ({}));
        if (response.status === 409) {
          setError("An account with this email already exists.");
        } else if (response.status === 500) {
          setError("Something went wrong on our end. Please try again later.");
        } else {
          setError(data.message ?? "Registration failed. Please try again.");
        }
      }
    } catch {
      setError("Network error. Please check your connection.");
    } finally {
      setIsLoading(false);
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
          <h1 className="text-xl sm:text-2xl font-semibold text-gray-900">Create an account</h1>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">Get started for free</p>
        </div>

        {/* Form */}
        <div className="space-y-3 sm:space-y-4">
          {/* Email */}
          <div>
            <label className="text-xs text-gray-500">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full px-3 py-2 sm:py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-black/80 focus:border-black transition"
              placeholder="you@example.com"
            />
          </div>

          {/* Password */}
          <div>
            <label className="text-xs text-gray-500">Password</label>
            <div className="relative mt-1">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 sm:py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-black/80 focus:border-black transition pr-10"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-300 hover:text-gray-500 transition"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
            {/* Password strength indicator */}
            {password.length > 0 && (
              <div className="mt-2 flex gap-1">
                {[1, 2, 3, 4].map((i) => {
                  const strength =
                    (password.length >= 8 ? 1 : 0) +
                    (/[A-Z]/.test(password) ? 1 : 0) +
                    (/[0-9]/.test(password) ? 1 : 0) +
                    (/[^A-Za-z0-9]/.test(password) ? 1 : 0);
                  return (
                    <div
                      key={i}
                      className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                        i <= strength
                          ? strength <= 1
                            ? "bg-red-400"
                            : strength <= 2
                            ? "bg-yellow-400"
                            : strength <= 3
                            ? "bg-blue-400"
                            : "bg-green-400"
                          : "bg-gray-100"
                      }`}
                    />
                  );
                })}
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label className="text-xs text-gray-500">Confirm password</label>
            <div className="relative mt-1">
              <input
                type={showPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={`w-full px-3 py-2 sm:py-2.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-black/80 focus:border-black transition pr-10 ${
                  confirmPassword.length > 0 && confirmPassword !== password
                    ? "border-red-300 bg-red-50/40"
                    : "border-gray-200"
                }`}
                placeholder="••••••••"
              />
              {confirmPassword.length > 0 && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  {confirmPassword === password ? (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#4ade80" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  ) : (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  )}
                </div>
              )}
            </div>
            {confirmPassword.length > 0 && confirmPassword !== password && (
              <p className="text-xs text-red-400 mt-1">Passwords don't match</p>
            )}
          </div>

          {/* Terms */}
          <label className="flex items-start gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={agreedToTerms}
            onChange={(e) => setAgreedToTerms(e.target.checked)}
            className="peer w-5 h-5 rounded-full border-2 border-gray-300 appearance-none cursor-pointer
              checked:bg-black checked:border-black
              hover:border-gray-400
              focus:outline-none focus:ring-2 focus:ring-black/20 focus:ring-offset-1
              transition-all duration-200"
          />
          <span className="text-xs text-gray-400 leading-relaxed">
            I agree to the{" "}
            <a href="#" className="text-gray-600 hover:text-gray-900 underline underline-offset-2">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="#" className="text-gray-600 hover:text-gray-900 underline underline-offset-2">
              Privacy Policy
            </a>
          </span>
        </label>

          {/* Error banner */}
          {error && (
            <div className="px-3 py-2.5 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-600">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              {error}
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={isLoading || !agreedToTerms}
            className="w-full bg-black text-white text-sm font-medium py-2 sm:py-2.5 rounded-lg hover:bg-gray-800 transition disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
          >
            {isLoading ? (
              <>
                <svg
                  className="animate-spin h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Creating account...
              </>
            ) : (
              "Create account"
            )}
          </button>
        </div>

        {/* Divider */}
        <div className="my-5 sm:my-6 flex items-center gap-3">
          <div className="flex-1 h-px bg-gray-100" />
          <span className="text-xs text-gray-300">or</span>
          <div className="flex-1 h-px bg-gray-100" />
        </div>

        {/* OAuth Buttons */}
        <div className="space-y-2 sm:space-y-3">
          <a href="/auth/login_via_google" className="w-full flex items-center justify-center gap-2 border border-gray-200 rounded-lg py-2 sm:py-2.5 text-sm hover:bg-gray-50 transition cursor-pointer">
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path fill="#EA4335" d="M12 10.2v3.6h5.1c-.2 1.2-1.4 3.5-5.1 3.5-3.1 0-5.6-2.6-5.6-5.8s2.5-5.8 5.6-5.8c1.8 0 3 .8 3.7 1.4l2.5-2.4C16.9 3.2 14.7 2.3 12 2.3 6.9 2.3 2.8 6.5 2.8 11.5S6.9 20.7 12 20.7c6.9 0 9.2-4.8 9.2-7.3 0-.5 0-.8-.1-1.2H12z" />
            </svg>
            Continue with Google
          </a>

          <button className="w-full flex items-center justify-center gap-2 border border-gray-200 rounded-lg py-2 sm:py-2.5 text-sm hover:bg-gray-50 transition cursor-pointer">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 .5C5.7.5.9 5.3.9 11.6c0 4.9 3.2 9 7.6 10.4.6.1.8-.3.8-.6v-2.3c-3.1.7-3.7-1.5-3.7-1.5-.5-1.3-1.2-1.6-1.2-1.6-1-.7.1-.7.1-.7 1.1.1 1.7 1.2 1.7 1.2 1 .1.7 2.3 2.9 1.6.1-.7.4-1.2.7-1.5-2.5-.3-5.1-1.3-5.1-5.8 0-1.3.5-2.3 1.2-3.2-.1-.3-.5-1.6.1-3.3 0 0 1-.3 3.3 1.2a11.4 11.4 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.7.2 3 .1 3.3.8.9 1.2 2 1.2 3.2 0 4.5-2.6 5.5-5.1 5.8.4.3.7.9.7 1.9v2.8c0 .3.2.7.8.6 4.4-1.4 7.6-5.5 7.6-10.4C23.1 5.3 18.3.5 12 .5z" />
            </svg>
            Continue with GitHub
          </button>
        </div>

        {/* Footer */}
        <p className="text-xs text-gray-400 text-center mt-5 sm:mt-6">
          Already have an account?{" "}
          <a href="/login" className="text-gray-600 hover:text-gray-900">
            Sign in
          </a>
        </p>
      </div>
    </div>
  );
}