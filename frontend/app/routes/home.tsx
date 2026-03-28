import type { Route } from "./+types/home";
import { useState, useEffect } from "react";

const FEATURES = [
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
      </svg>
    ),
    title: "Instant setup",
    desc: "Go from zero to production in under five minutes. No infrastructure knowledge required.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <path d="M9 9h6M9 12h6M9 15h4" />
      </svg>
    ),
    title: "Readable analytics",
    desc: "Dashboards built for humans, not data scientists. Understand your product at a glance.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8v4l3 3" />
      </svg>
    ),
    title: "Always on",
    desc: "99.99% uptime SLA backed by redundant global infrastructure. Sleep soundly.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
    title: "Enterprise security",
    desc: "SOC 2 Type II certified. End-to-end encryption. GDPR and CCPA compliant.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
    title: "Team collaboration",
    desc: "Roles, permissions, shared workspaces. Built for teams of any size.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    ),
    title: "API-first",
    desc: "Every feature is accessible via our REST and GraphQL APIs. Build anything.",
  },
];

const LOGOS = ["Stripe", "Notion", "Linear", "Vercel", "Figma", "Raycast"];

const TESTIMONIALS = [
  {
    quote: "We replaced three tools with this. Our team hasn't looked back.",
    name: "Sara Chen",
    role: "Head of Product, Cortex",
    avatar: "SC",
  },
  {
    quote: "The DX is exceptional. Onboarding took 20 minutes end-to-end.",
    name: "Marcus Webb",
    role: "CTO, Baseflow",
    avatar: "MW",
  },
  {
    quote: "Finally, analytics that don't require a PhD to interpret.",
    name: "Priya Nair",
    role: "Founder, Petal",
    avatar: "PN",
  },
];

const PLANS = [
  {
    name: "Starter",
    price: "$0",
    per: "forever free",
    features: ["Up to 3 projects", "10k events/mo", "7-day data retention", "Community support"],
    cta: "Get started",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$29",
    per: "per seat / month",
    features: ["Unlimited projects", "1M events/mo", "90-day retention", "Priority support", "Custom domains", "SSO"],
    cta: "Start free trial",
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    per: "talk to us",
    features: ["Unlimited everything", "SLA guarantee", "Dedicated support", "Custom contracts", "On-prem option"],
    cta: "Contact sales",
    highlight: false,
  },
];

export default function Home() {
  return (
    <>
      {/* HERO */}
      <section className="relative min-h-screen flex items-center justify-center grid-bg overflow-hidden">
        {/* Radial fade overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-white via-white/60 to-white pointer-events-none" />

        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center pt-24 pb-16">
          <div className="fade-in inline-flex items-center gap-2 tag-pill rounded-full px-3 py-1.5 text-xs text-gray-500 mb-8 mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
            v2.4 just shipped — changelog ↗
          </div>

          <h1 className="fade-in-2 text-5xl md:text-7xl font-semibold tracking-tight leading-[1.05] text-gray-950 mb-6">
            The platform<br />
            <span className="text-gray-400 font-light italic">your team</span><br />
            actually ships with.
          </h1>

          <p className="fade-in-3 text-lg md:text-xl text-gray-500 max-w-xl mx-auto mb-10 leading-relaxed font-light">
            Volta unifies your infrastructure, analytics, and collaboration into one lean workspace. Less context-switching. More building.
          </p>

          <div className="fade-in-4 flex flex-col sm:flex-row items-center justify-center gap-3">
            <a href="#" className="w-full sm:w-auto bg-black text-white text-sm font-medium px-6 py-3 rounded-xl hover:bg-gray-800 transition-colors">
              Start for free →
            </a>
            <a href="#" className="w-full sm:w-auto border border-gray-200 text-gray-700 text-sm font-medium px-6 py-3 rounded-xl hover:border-gray-300 hover:bg-gray-50 transition-all">
              Watch demo  ▶
            </a>
          </div>

          <p className="fade-in-4 mt-5 text-xs text-gray-400 mono">No credit card required · Free forever plan</p>
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
                  {["Overview", "Events", "Funnels", "Users", "Settings"].map((item, i) => (
                    <div key={item} className={`text-xs px-3 py-2 rounded-lg ${i === 0 ? "bg-gray-100 text-gray-900 font-medium" : "text-gray-400"}`}>{item}</div>
                  ))}
                </div>
              </div>
              {/* Main */}
              <div className="col-span-4 sm:col-span-3 p-5">
                <div className="grid grid-cols-3 gap-3 mb-4">
                  {[["Total events", "1.24M", "+18.2%"], ["Active users", "8,492", "+4.7%"], ["Conversion", "3.61%", "+0.4%"]].map(([label, val, change]) => (
                    <div key={label} className="border border-gray-100 rounded-xl p-3">
                      <p className="text-xs text-gray-400 mb-1">{label}</p>
                      <p className="text-xl font-semibold tracking-tight">{val}</p>
                      <p className="text-xs text-emerald-500 mono mt-0.5">{change}</p>
                    </div>
                  ))}
                </div>
                {/* Chart placeholder */}
                <div className="border border-gray-100 rounded-xl p-4">
                  <p className="text-xs text-gray-400 mb-3">Events over time</p>
                  <div className="flex items-end gap-1.5 h-20">
                    {[40,55,35,70,65,80,60,90,75,85,95,88,72,100,92,78,85,95,88,100].map((h, i) => (
                      <div key={i} className="flex-1 rounded-sm" style={{height:`${h}%`, background: i === 19 ? "#0f0f0f" : "#e5e7eb"}} />
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

      {/* FEATURES */}
      <section className="py-28 max-w-6xl mx-auto px-6">
        <div className="max-w-xl mb-16">
          <p className="mono text-xs text-gray-400 mb-3 tracking-widest uppercase">Features</p>
          <h2 className="text-4xl font-semibold tracking-tight text-gray-950 mb-4">Built for speed.<br />Designed to last.</h2>
          <p className="text-gray-400 font-light leading-relaxed">Everything you need to run a modern software product — in one place, without the bloat.</p>
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
          <p className="mono text-xs text-gray-400 mb-12 tracking-widest uppercase text-center">What teams say</p>
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
      <section className="py-28 max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <p className="mono text-xs text-gray-400 mb-3 tracking-widest uppercase">Pricing</p>
          <h2 className="text-4xl font-semibold tracking-tight text-gray-950 mb-4">Simple, honest pricing.</h2>
          <p className="text-gray-400 font-light">No usage surprises. No hidden tiers. Just value.</p>
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
              <a href="#" className={`block text-center text-sm font-medium py-2.5 rounded-xl transition-all ${
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
            <h2 className="text-4xl md:text-5xl font-semibold text-white tracking-tight mb-4">Ready to move fast?</h2>
            <p className="text-gray-400 font-light mb-10 max-w-md mx-auto">Join thousands of teams building with Volta. Free to start, scales with you.</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <a href="#" className="w-full sm:w-auto bg-white text-gray-900 text-sm font-medium px-7 py-3 rounded-xl hover:bg-gray-100 transition-colors">
                Get started for free →
              </a>
              <a href="#" className="w-full sm:w-auto border border-gray-700 text-gray-300 text-sm font-medium px-7 py-3 rounded-xl hover:border-gray-500 transition-colors">
                Talk to sales
              </a>
            </div>
            <p className="text-xs text-gray-600 mono mt-6">No credit card · SOC 2 certified · Cancel anytime</p>
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
            <p className="text-xs text-gray-400 font-light max-w-xs leading-relaxed">The platform your team actually ships with. Built for modern software teams.</p>
          </div>
          <div className="grid grid-cols-3 gap-12 text-sm">
            {[
              { heading: "Product", links: ["Features", "Changelog", "Roadmap", "Status"] },
              { heading: "Company", links: ["About", "Blog", "Careers", "Press"] },
              { heading: "Legal", links: ["Privacy", "Terms", "Security", "Cookies"] },
            ].map((col) => (
              <div key={col.heading}>
                <p className="font-medium text-gray-900 mb-3 text-xs mono uppercase tracking-widest">{col.heading}</p>
                <ul className="space-y-2">
                  {col.links.map((l) => (
                    <li key={l}><a href="#" className="text-gray-400 hover:text-gray-700 text-xs transition-colors font-light">{l}</a></li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
        <div className="max-w-6xl mx-auto px-6 mt-10 pt-6 border-t border-gray-100 flex flex-col sm:flex-row justify-between items-center gap-2">
          <p className="text-xs text-gray-300 mono">© 2026 Volta Technologies, Inc.</p>
          <p className="text-xs text-gray-300 mono">Made with care ·  San Francisco</p>
        </div>
      </footer>
    </>
  );
}
