import { useState, useEffect } from "react";
import { useAuth } from "./context/auth";
import { useNavigate } from "react-router";

const NAV_LINKS = ["Product", "Pricing", "Docs", "Blog"];

function useScrolled() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);
  return scrolled;
}

export default function Nav() {
    const [menuOpen, setMenuOpen] = useState(false);
    const scrolled = useScrolled();
    const { user, loading, setUser } = useAuth();
    const navigate = useNavigate();
    
    const handleLogout = async () => {
        await fetch("/auth/logout", { method: "POST", credentials: "include" });
        setUser(null);
        navigate("/");
    };

    return (
        <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? "bg-white/90 backdrop-blur-md border-b border-gray-100 shadow-sm" : "bg-transparent"}`}>
            <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
                {/* Logo */}
                <div className="flex items-center gap-2">
                    <div className="w-7 h-7 bg-black rounded-lg flex items-center justify-center">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
                            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                        </svg>
                    </div>
                    <span className="font-semibold text-[15px] tracking-tight">Volta</span>
                </div>

                {/* Desktop Links */}
                <div className="hidden md:flex items-center gap-8">
                    {NAV_LINKS.map((l) => (
                        <a key={l} href="#" className="text-sm text-gray-500 hover:text-gray-900 transition-colors">{l}</a>
                    ))}
                </div>

                {/* CTA */}
                <div className="hidden md:flex items-center gap-3">
                    {!loading && (
                        user ? (
                            <>
                            <a href="/dashboard" className="text-sm text-gray-500 hover:text-gray-900">Dashboard</a>
                            <button onClick={handleLogout} className="text-sm bg-black text-white px-4 py-2 rounded-lg cursor-pointer">
                                Logout
                            </button>
                            </>
                        ) : (
                            <>
                            <a href="/login" className="text-sm text-gray-500 hover:text-gray-900">Sign in</a>
                            <a href="/register" className="text-sm bg-black text-white px-4 py-2 rounded-lg">
                                Get started →
                            </a>
                            </>
                        )
                    )}
                </div>

                {/* Mobile burger */}
                <button className="md:hidden p-2" onClick={() => setMenuOpen(!menuOpen)}>
                    <div className={`w-5 h-0.5 bg-gray-900 mb-1.5 transition-all ${menuOpen ? "rotate-45 translate-y-2" : ""}`} />
                    <div className={`w-5 h-0.5 bg-gray-900 mb-1.5 transition-all ${menuOpen ? "opacity-0" : ""}`} />
                    <div className={`w-5 h-0.5 bg-gray-900 transition-all ${menuOpen ? "-rotate-45 -translate-y-2" : ""}`} />
                </button>
            </div>

            {/* Mobile menu */}
            {menuOpen && (
                <div className="md:hidden bg-white border-t border-gray-100 px-6 py-4 flex flex-col gap-4">
                    {NAV_LINKS.map((l) => (
                        <a key={l} href="#" className="text-sm text-gray-600">{l}</a>
                    ))}
                    <a href="/register" className="text-sm bg-black text-white px-4 py-2 rounded-lg text-center font-medium">Get started →</a>
                </div>
            )}
        </nav>
    );
}