import type { Route } from "./+types/home";
import { useState, useEffect } from "react";

const FEATURES = [
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M15 7h3a5 5 0 0 1 5 5 5 5 0 0 1-5 5h-3m-6 0H6a5 5 0 0 1-5-5 5 5 0 0 1 5-5h3" />
        <line x1="8" y1="12" x2="16" y2="12" />
      </svg>
    ),
    title: "Private access tokens",
    desc: "Generate scoped API keys in seconds. Revoke, rotate, and audit them from your dashboard — no downtime required.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
      </svg>
    ),
    title: "Rate limiting built in",
    desc: "Every plan ships with request quotas enforced at the gateway. Transparent headers tell you exactly where you stand.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <path d="M9 9h6M9 12h6M9 15h4" />
      </svg>
    ),
    title: "Usage analytics",
    desc: "Track requests, token consumption, latency, and error rates. Understand how your integration performs over time.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
    title: "OAuth 2.0 login",
    desc: "Sign in with Google or GitHub. No new passwords to manage. Session cookies, not JWTs — secure by default.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    ),
    title: "OpenAPI documentation",
    desc: "Every endpoint is documented and explorable via Swagger UI. Copy a curl command and you're making real requests in under a minute.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M9 12l2 2 4-4" />
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" />
      </svg>
    ),
    title: "Audit log",
    desc: "Every key creation, revocation, and authentication event is recorded. Know exactly what happened and when.",
  },
];

const LOGOS = ["Stripe", "Notion", "Linear", "Vercel", "Figma", "Raycast"];

const TESTIMONIALS = [
  {
    quote: "Integrated in 15 minutes. The OpenAPI docs made it trivial to wire up our pipeline.",
    name: "Sara Chen",
    role: "ML Engineer, Cortex",
    avatar: "SC",
  },
  {
    quote: "Rate limit headers in every response. Finally an API that tells you how close you are to the wall.",
    name: "Marcus Webb",
    role: "CTO, Baseflow",
    avatar: "MW",
  },
  {
    quote: "We run classification on every user submission. The latency is consistently under 300 ms.",
    name: "Priya Nair",
    role: "Founder, Petal",
    avatar: "PN",
  },
];

const PLANS = [
  {
    name: "Free",
    price: "$0",
    per: "forever free",
    features: ["1,000 requests / day", "1 API key", "7-day request history", "Community support"],
    cta: "Get started",
    highlight: false,
    link: "/register",
  },
  {
    name: "Pro",
    price: "$29",
    per: "per seat / month",
    features: ["50,000 requests / day", "10 API keys", "90-day history", "Priority support", "Webhook notifications", "Higher rate limits"],
    cta: "Start free trial",
    highlight: true,
    link: "/register",
  },
  {
    name: "Enterprise",
    price: "Custom",
    per: "talk to us",
    features: ["Unlimited requests", "Unlimited API keys", "Custom SLA", "Dedicated support", "On-prem option", "Custom contracts"],
    cta: "Contact sales",
    highlight: false,
    link: "/register",
  },
];

export default function Home() {
  return (
    <>
      {/* HERO */}
      <section className="relative min-h-screen flex-col md:flex-row flex items-center justify-center grid-bg overflow-hidden">
        {/* Radial fade overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-white via-white/60 to-white pointer-events-none" />

        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center pt-24 pb-16">
          <div className="fade-in inline-flex items-center gap-2 tag-pill rounded-full px-3 py-1.5 text-xs text-gray-500 mb-8 mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
            REST API · GraphQL coming soon · MCP planned
          </div>

          <h1 className="fade-in-2 text-5xl md:text-7xl font-semibold tracking-tight leading-[1.05] text-gray-950 mb-6">
            ML inference,<br />
            <span className="text-gray-400 font-light italic">without the ops.</span>
          </h1>

          <p className="fade-in-3 text-lg md:text-xl text-gray-500 max-w-xl mx-auto mb-10 leading-relaxed font-light">
            Call our API with a single token. Sentiment analysis, classification, and LLM completions — all behind one endpoint, with usage you can actually see.
          </p>

          <div className="fade-in-4 flex flex-col sm:flex-row items-center justify-center gap-3">
            <a href="/register" className="w-full sm:w-auto bg-black text-white text-sm font-medium px-6 py-3 rounded-xl hover:bg-gray-800 transition-colors">
              Get your API key →
            </a>
            <a href="/docs" className="w-full sm:w-auto border border-gray-200 text-gray-700 text-sm font-medium px-6 py-3 rounded-xl hover:border-gray-300 hover:bg-gray-50 transition-all">
              View API docs ↗
            </a>
          </div>

          <p className="fade-in-4 mt-5 text-xs text-gray-400 mono">No credit card required · Free plan includes 1,000 req/day</p>
        </div>

        {/* Hero dashboard mockup */}
        <div className="relative z-10 max-w-5xl mx-auto px-6 pb-24 fade-in-4">
          <div className="rounded-2xl border border-gray-200 shadow-2xl shadow-gray-200/80 overflow-hidden bg-white">
            {/* Toolbar */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 bg-gray-50/70">
              <div className="w-3 h-3 rounded-full bg-red-300" />
              <div className="w-3 h-3 rounded-full bg-yellow-300" />
              <div className="w-3 h-3 rounded-full bg-green-300" />
              <div className="flex-1 mx-4 bg-white border border-gray-200 rounded-md px-3 py-1 text-xs text-gray-400 mono">app.volta.io/dashboard</div>
            </div>
            {/* Fake dashboard */}
            <div className="grid grid-cols-4 gap-0 bg-white">
              {/* Sidebar */}
              <div className="col-span-1 border-r border-gray-100 p-4 min-h-[300px] hidden sm:block">
                <div className="space-y-1">
                  {["Overview", "API Keys", "Requests", "Billing", "Settings"].map((item, i) => (
                    <div key={item} className={`text-xs px-3 py-2 rounded-lg ${i === 0 ? "bg-gray-100 text-gray-900 font-medium" : "text-gray-400"}`}>{item}</div>
                  ))}
                </div>
              </div>
              {/* Main */}
              <div className="col-span-4 sm:col-span-3 p-5">
                <div className="grid grid-cols-3 gap-3 mb-4">
                  {[["Requests today", "8,492", "742 remaining"], ["Tokens used", "2.1M", "this month"], ["Avg latency", "241 ms", "↓ 12 ms vs last week"]].map(([label, val, sub]) => (
                    <div key={label} className="border border-gray-100 rounded-xl p-3">
                      <p className="text-xs text-gray-400 mb-1">{label}</p>
                      <p className="text-xl font-semibold tracking-tight">{val}</p>
                      <p className="text-xs text-gray-400 mono mt-0.5">{sub}</p>
                    </div>
                  ))}
                </div>
                {/* Recent requests table */}
                <div className="border border-gray-100 rounded-xl p-4">
                  <p className="text-xs text-gray-400 mb-3">Recent requests</p>
                  <div className="space-y-2">
                    {[
                      ["POST /v1/classify", "200", "118 ms", "2 min ago"],
                      ["POST /v1/classify", "200", "241 ms", "5 min ago"],
                      ["POST /v1/classify", "429", "8 ms",  "11 min ago"],
                    ].map(([path, status, latency, time], i) => (
                      <div key={i} className="flex items-center gap-3 text-xs mono">
                        <span className="text-gray-500 flex-1">{path}</span>
                        <span className={`font-medium ${status === "200" ? "text-emerald-500" : "text-red-400"}`}>{status}</span>
                        <span className="text-gray-400 w-14 text-right">{latency}</span>
                        <span className="text-gray-300 w-16 text-right">{time}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* LOGO STRIP */}
      <section className="border-y border-gray-100 py-10 bg-gray-50/50">
        <div className="max-w-5xl mx-auto px-6">
          <p className="text-center text-xs text-gray-400 mono mb-7 tracking-widest uppercase">Trusted by teams at</p>
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-12">
            {LOGOS.map((l) => (
              <span key={l} className="text-gray-300 font-semibold text-lg tracking-tight hover:text-gray-500 transition-colors cursor-default">{l}</span>
            ))}
          </div>
        </div>
      </section>

      {/* QUICK START */}
      <section className="py-24 max-w-6xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
          <div>
            <p className="mono text-xs text-gray-400 mb-3 tracking-widest uppercase">Get started in seconds</p>
            <h2 className="text-4xl font-semibold tracking-tight text-gray-950 mb-4">One token.<br />One endpoint.</h2>
            <p className="text-gray-400 font-light leading-relaxed mb-6">
              Register, grab your API key from the dashboard, and start making requests. No SDKs required — just HTTP.
            </p>
            <a href="/register" className="inline-flex items-center gap-2 bg-gray-950 text-white text-sm font-medium px-5 py-2.5 rounded-xl hover:bg-gray-800 transition-colors">
              Create free account →
            </a>
          </div>
          <div className="bg-gray-950 rounded-2xl p-6 font-mono text-sm leading-relaxed overflow-x-auto">
            <p className="text-gray-500 mb-3 text-xs">// classify a piece of text</p>
            <p><span className="text-violet-400">curl</span> <span className="text-gray-300">-X POST</span> \</p>
            <p className="pl-4 text-gray-300">https://api.volta.io/v1/classify \</p>
            <p className="pl-4"><span className="text-yellow-300">-H</span> <span className="text-emerald-300">"Authorization: Bearer YOUR_PAT"</span> \</p>
            <p className="pl-4"><span className="text-yellow-300">-H</span> <span className="text-emerald-300">"Content-Type: application/json"</span> \</p>
            <p className="pl-4"><span className="text-yellow-300">-d</span> <span className="text-emerald-300">{'\'{"text": "I love this product!"}\''}</span></p>
            <div className="mt-4 pt-4 border-t border-gray-800">
              <p className="text-gray-500 text-xs mb-2">// response</p>
              <p><span className="text-gray-400">{"{"}</span></p>
              <p className="pl-4"><span className="text-blue-300">"label"</span><span className="text-gray-400">: </span><span className="text-emerald-300">"positive"</span><span className="text-gray-400">,</span></p>
              <p className="pl-4"><span className="text-blue-300">"score"</span><span className="text-gray-400">: </span><span className="text-orange-300">0.97</span><span className="text-gray-400">,</span></p>
              <p className="pl-4"><span className="text-blue-300">"latency_ms"</span><span className="text-gray-400">: </span><span className="text-orange-300">118</span></p>
              <p><span className="text-gray-400">{"}"}</span></p>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-800 text-xs">
              <p><span className="text-gray-500">X-RateLimit-Limit:</span> <span className="text-gray-300">1000</span></p>
              <p><span className="text-gray-500">X-RateLimit-Remaining:</span> <span className="text-gray-300">742</span></p>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="py-28 max-w-6xl mx-auto px-6">
        <div className="max-w-xl mb-16">
          <p className="mono text-xs text-gray-400 mb-3 tracking-widest uppercase">Features</p>
          <h2 className="text-4xl font-semibold tracking-tight text-gray-950 mb-4">Everything an API<br />platform needs.</h2>
          <p className="text-gray-400 font-light leading-relaxed">Authentication, rate limiting, usage visibility, and docs — without stitching together five separate tools.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((f) => (
            <div key={f.title} className="group border border-gray-100 rounded-2xl p-6 hover:border-gray-200 hover:shadow-lg hover:shadow-gray-100 transition-all duration-300">
              <div className="w-9 h-9 rounded-xl bg-gray-100 flex items-center justify-center mb-4 text-gray-600 group-hover:bg-black group-hover:text-white transition-colors duration-300">
                {f.icon}
              </div>
              <h3 className="font-medium text-gray-950 mb-2">{f.title}</h3>
              <p className="text-sm text-gray-400 leading-relaxed font-light">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="py-24 bg-gray-50/60 border-y border-gray-100">
        <div className="max-w-6xl mx-auto px-6">
          <p className="mono text-xs text-gray-400 mb-12 tracking-widest uppercase text-center">What developers say</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((t) => (
              <div key={t.name} className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
                <p className="text-gray-700 leading-relaxed mb-6 font-light">"{t.quote}"</p>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-gray-900 text-white text-xs font-medium flex items-center justify-center mono">{t.avatar}</div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t.name}</p>
                    <p className="text-xs text-gray-400">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="py-28 max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <p className="mono text-xs text-gray-400 mb-3 tracking-widest uppercase">Pricing</p>
          <h2 className="text-4xl font-semibold tracking-tight text-gray-950 mb-4">Pay for what you use.</h2>
          <p className="text-gray-400 font-light">Start free. Scale when you need to. No surprises on your bill.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 items-center">
          {PLANS.map((p) => (
            <div key={p.name} className={`rounded-2xl p-7 ${p.highlight ? "highlight-card text-white shadow-2xl shadow-gray-900/20 scale-105" : "border border-gray-100 bg-white"}`}>
              <p className={`mono text-xs mb-4 tracking-widest uppercase ${p.highlight ? "text-gray-400" : "text-gray-400"}`}>{p.name}</p>
              <div className="mb-1">
                <span className="text-4xl font-semibold tracking-tight">{p.price}</span>
              </div>
              <p className={`text-xs mb-7 ${p.highlight ? "text-gray-500" : "text-gray-400"} mono`}>{p.per}</p>
              <ul className="space-y-2.5 mb-8">
                {p.features.map((f) => (
                  <li key={f} className="flex items-center gap-2.5 text-sm font-light">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={p.highlight ? "#6ee7b7" : "#9ca3af"} strokeWidth="2.5">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    <span className={p.highlight ? "text-gray-300" : "text-gray-600"}>{f}</span>
                  </li>
                ))}
              </ul>
              <a href={p.link} className={`block text-center text-sm font-medium py-2.5 rounded-xl transition-all ${
                p.highlight
                  ? "bg-white text-gray-900 hover:bg-gray-100"
                  : "bg-gray-950 text-white hover:bg-gray-800"
              }`}>
                {p.cta}
              </a>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-28 max-w-6xl mx-auto px-6">
        <div className="bg-gray-950 rounded-3xl p-12 md:p-20 text-center relative overflow-hidden">
          <div className="absolute inset-0 grid-bg opacity-20" />
          <div className="relative z-10">
            <h2 className="text-4xl md:text-5xl font-semibold text-white tracking-tight mb-4">Your first request<br />is one token away.</h2>
            <p className="text-gray-400 font-light mb-10 max-w-md mx-auto">Register, generate a PAT, and hit the endpoint. The free plan gives you 1,000 requests a day — no card required.</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <a href="/register" className="w-full sm:w-auto bg-white text-gray-900 text-sm font-medium px-7 py-3 rounded-xl hover:bg-gray-100 transition-colors">
                Create free account →
              </a>
              <a href="/docs" className="w-full sm:w-auto border border-gray-700 text-gray-300 text-sm font-medium px-7 py-3 rounded-xl hover:border-gray-500 transition-colors">
                Read the docs
              </a>
            </div>
            <p className="text-xs text-gray-600 mono mt-6">No credit card · OAuth via Google & GitHub · Cancel anytime</p>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-gray-100 py-12">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-start justify-between gap-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 bg-black rounded-md flex items-center justify-center">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="white">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
              </div>
              <span className="font-semibold text-sm">Volta</span>
            </div>
            <p className="text-xs text-gray-400 font-light max-w-xs leading-relaxed">ML inference and LLM completions behind a clean REST API. Built for developers, ready for production.</p>
          </div>
          <div className="grid grid-cols-3 gap-12 text-sm">
            {[
              {
                heading: "Product", links: [
                  {
                    name: "API Docs",
                    link: "/docs",
                  },
                  {
                    name: "Changelog",
                    link: "#",
                  },
                  {
                    name: "Roadmap",
                    link: "#",
                  },
                  {
                    name: "Status",
                    link: "#",
                  }
                ]
              },
              {
                heading: "Company", links: [
                  {
                    name: "About",
                    link: "#",
                  },
                  {
                    name: "Careers",
                    link: "#",
                  },
                  {
                    name: "Press",
                    link: "#",
                  }
                ]
              },
              { heading: "Legal", links: [
                {
                  name: "Privacy",
                  link: "#",
                },
                {
                  name: "Terms",
                  link: "#",
                },
                {
                  name: "Security",
                  link: "#",
                },
                {
                  name: "Cookies",
                  link: "#",
                }
              ]},
            ].map((col) => (
              <div key={col.heading}>
                <p className="font-medium text-gray-900 mb-3 text-xs mono uppercase tracking-widest">{col.heading}</p>
                <ul className="space-y-2">
                  {col.links.map(({name, link}) => (
                    <li key={name}><a href={link} className="text-gray-400 hover:text-gray-700 text-xs transition-colors font-light">{name}</a></li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
        <div className="max-w-6xl mx-auto px-6 mt-10 pt-6 border-t border-gray-100 flex flex-col sm:flex-row justify-between items-center gap-2">
          <p className="text-xs text-gray-300 mono">© 2026 Volta Technologies, Inc.</p>
          <p className="text-xs text-gray-300 mono">Made with care · Poland</p>
        </div>
      </footer>
    </>
  );
}