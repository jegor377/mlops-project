import { useState, useEffect } from "react";
import type { ReactNode, SVGProps } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

type PillVariant = "default" | "green" | "red" | "blue" | "yellow";
type FilterType = "all" | "active" | "expired";
type NavId = "overview" | "events" | "funnels" | "users" | "tokens" | "settings";
type ExpiryOption = "7 days" | "30 days" | "90 days" | "1 year" | "No expiration";

interface Token {
  id: number;
  name: string;
  prefix: string;
  scopes: string[];
  expiry: string | null;
  created: string;
  lastUsed: string;
  active: boolean;
}

interface NewTokenData {
  name: string;
  prefix: string;
  scopes: string[];
  expiry: string | null;
  created: string;
  lastUsed: string;
  active: boolean;
}

interface Scope {
  id: string;
  label: string;
  group: string;
}

interface NavItem {
  id: NavId;
  label: string;
  icon: keyof typeof icons;
}

// ── Icons ────────────────────────────────────────────────────────────────────

interface IconProps extends SVGProps<SVGSVGElement> {
  d: string;
  size?: number;
  stroke?: string;
  fill?: string;
}

const Icon = ({ d, size = 16, stroke = "currentColor", fill = "none", ...p }: IconProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={fill}
    stroke={stroke}
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...p}
  >
    <path d={d} />
  </svg>
);

const icons = {
  overview: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
  events: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
  tokens:
    "M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4",
  users: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2",
  settings:
    "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z",
  copy: "M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-4-4h-6M14 4v4h4M10 12h4M10 16h4",
  trash: "M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6",
  plus: "M12 5v14M5 12h14",
  check: "M20 6 9 17l-5-5",
  eye: "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
  eyeOff:
    "M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24 M1 1l22 22",
  close: "M18 6 6 18M6 6l12 12",
  warn: "M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01",
  shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
  funnels: "M3 4h18M7 8h10M11 12h2M10 16h4",
  chevron: "M9 18l6-6-6-6",
} as const;

// ── Helpers ──────────────────────────────────────────────────────────────────

function expiryDays(expiry: ExpiryOption): number | null {
  if (expiry === "No expiration") return null;
  if (expiry === "1 year") return 365;
  return parseInt(expiry);
}

const SCOPES: Scope[] = [
  { id: "read:events", label: "Read Events", group: "Events" },
  { id: "write:events", label: "Write Events", group: "Events" },
  { id: "read:users", label: "Read Users", group: "Users" },
  { id: "write:users", label: "Write Users", group: "Users" },
  { id: "read:analytics", label: "Read Analytics", group: "Analytics" },
  { id: "admin", label: "Full Access (Admin)", group: "Admin" },
];

const EXPIRY_OPTIONS: ExpiryOption[] = ["7 days", "30 days", "90 days", "1 year", "No expiration"];

const INITIAL_TOKENS: Token[] = [
  {
    id: 1,
    name: "CI/CD Pipeline",
    prefix: "vlt_K9mX",
    scopes: ["read:events", "write:events"],
    expiry: "2026-12-31",
    created: "2026-01-10",
    lastUsed: "2 hours ago",
    active: true,
  },
  {
    id: 2,
    name: "Analytics Dashboard",
    prefix: "vlt_Rp2Q",
    scopes: ["read:analytics", "read:events"],
    expiry: "2026-06-30",
    created: "2026-02-20",
    lastUsed: "Yesterday",
    active: true,
  },
  {
    id: 3,
    name: "Legacy Integration",
    prefix: "vlt_7fNL",
    scopes: ["read:users"],
    expiry: "2026-03-01",
    created: "2025-09-05",
    lastUsed: "3 months ago",
    active: false,
  },
];

const NAV: NavItem[] = [
  { id: "overview", label: "Overview", icon: "overview" },
  { id: "events", label: "Events", icon: "events" },
  { id: "funnels", label: "Funnels", icon: "funnels" },
  { id: "users", label: "Users", icon: "users" },
  { id: "tokens", label: "Access Tokens", icon: "tokens" },
  { id: "settings", label: "Settings", icon: "settings" },
];

// ── Sub-components ────────────────────────────────────────────────────────────

interface PillProps {
  children: ReactNode;
  variant?: PillVariant;
}

function Pill({ children, variant = "default" }: PillProps) {
  const styles: Record<PillVariant, string> = {
    default: "bg-gray-100 text-gray-500",
    green: "bg-emerald-50 text-emerald-600",
    red: "bg-red-50 text-red-500",
    blue: "bg-blue-50 text-blue-600",
    yellow: "bg-amber-50 text-amber-600",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium mono ${styles[variant]}`}>
      {children}
    </span>
  );
}

interface CopyButtonProps {
  value: string;
}

function CopyButton({ value }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);
  const handle = () => {
    navigator.clipboard?.writeText(value).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={handle}
      title="Copy to clipboard"
      className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all duration-200 mono font-medium ${
        copied
          ? "border-emerald-200 bg-emerald-50 text-emerald-600"
          : "border-gray-200 bg-white text-gray-500 hover:border-gray-300 hover:text-gray-700"
      }`}
    >
      <Icon d={copied ? icons.check : icons.copy} size={13} />
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

interface ModalProps {
  show: boolean;
  onClose: () => void;
  children: ReactNode;
}

function Modal({ show, onClose, children }: ModalProps) {
  useEffect(() => {
    document.body.style.overflow = show ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [show]);

  if (!show) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 bg-white rounded-2xl shadow-2xl shadow-gray-900/20 w-full max-w-lg border border-gray-100 animate-modal">
        {children}
      </div>
    </div>
  );
}

// ── Token row ─────────────────────────────────────────────────────────────────

interface TokenRowProps {
  token: Token;
  onRevoke: (id: number) => void;
}

function TokenRow({ token, onRevoke }: TokenRowProps) {
  const isExpired = !!token.expiry && new Date(token.expiry) < new Date();
  return (
    <div
      className={`group border rounded-2xl p-5 transition-all duration-200 ${
        isExpired || !token.active
          ? "border-gray-100 bg-gray-50/50 opacity-70"
          : "border-gray-100 bg-white hover:border-gray-200 hover:shadow-md hover:shadow-gray-100"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5 mb-2 flex-wrap">
            <span className="font-medium text-gray-950 text-sm">{token.name}</span>
            {!token.active || isExpired ? (
              <Pill variant="red">{isExpired ? "Expired" : "Revoked"}</Pill>
            ) : (
              <Pill variant="green">Active</Pill>
            )}
          </div>

          {/* Token preview */}
          <div className="flex items-center gap-2 mb-3">
            <code className="mono text-xs text-gray-500 bg-gray-50 border border-gray-100 rounded-lg px-3 py-1.5 tracking-wider">
              {token.prefix}••••••••••••••••••••••••••••••••••••
            </code>
          </div>

          {/* Meta */}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-400 mono mb-3">
            <span>Created {token.created}</span>
            <span className="text-gray-200">·</span>
            <span>Last used: {token.lastUsed}</span>
            <span className="text-gray-200">·</span>
            <span className={isExpired ? "text-red-400" : ""}>
              {token.expiry ? `Expires ${token.expiry}` : "No expiration"}
            </span>
          </div>

          {/* Scopes */}
          <div className="flex flex-wrap gap-1.5">
            {token.scopes.map((s) => (
              <Pill key={s} variant="blue">
                {s}
              </Pill>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          {token.active && !isExpired && (
            <button
              onClick={() => onRevoke(token.id)}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-400 hover:border-red-200 hover:bg-red-50 hover:text-red-500 transition-all duration-200 mono"
            >
              <Icon d={icons.trash} size={13} />
              Revoke
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Create Token Wizard ───────────────────────────────────────────────────────

interface CreateTokenModalProps {
  show: boolean;
  onClose: () => void;
  onCreate: (data: NewTokenData) => void;
}

function CreateTokenModal({ show, onClose, onCreate }: CreateTokenModalProps) {
  const [step, setStep] = useState<1 | 2>(1);
  const [name, setName] = useState("");
  const [selectedScopes, setSelectedScopes] = useState<string[]>([]);
  const [expiry, setExpiry] = useState<ExpiryOption>("90 days");
  const [generatedToken, setGeneratedToken] = useState("");
  const [showFull, setShowFull] = useState(false);

  const reset = () => {
    setStep(1);
    setName("");
    setSelectedScopes([]);
    setExpiry("90 days");
    setGeneratedToken("");
    setShowFull(false);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleCreate = async () => {
    const token = await fetch("/api/tokens", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        name,
        scopes: selectedScopes,
        expires_in_days: expiryDays(expiry)
      })
    }).then(res => res.json());
    setGeneratedToken(token);
    setStep(2);

    const days = expiryDays(expiry);
    let expiryDate: string | null = null;
    if (days !== null) {
      const d = new Date();
      d.setDate(d.getDate() + days);
      expiryDate = d.toISOString().split("T")[0];
    }

    onCreate({
      name,
      prefix: token.slice(0, 8),
      scopes: selectedScopes,
      expiry: expiryDate,
      created: new Date().toISOString().split("T")[0],
      lastUsed: "Never",
      active: true,
    });
  };

  const toggleScope = (id: string) => {
    setSelectedScopes((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]));
  };

  const grouped = SCOPES.reduce<Record<string, Scope[]>>((acc, s) => {
    (acc[s.group] = acc[s.group] ?? []).push(s);
    return acc;
  }, {});

  return (
    <Modal show={show} onClose={handleClose}>
      {step === 1 && (
        <>
          <div className="flex items-center justify-between px-6 pt-6 pb-5 border-b border-gray-100">
            <div>
              <h2 className="font-semibold text-gray-950 text-base">New access token</h2>
              <p className="text-xs text-gray-400 mt-0.5 mono">Tokens authenticate API requests on your behalf</p>
            </div>
            <button onClick={handleClose} className="text-gray-400 hover:text-gray-600 transition-colors">
              <Icon d={icons.close} size={18} />
            </button>
          </div>

          <div className="px-6 py-5 space-y-5 max-h-[60vh] overflow-y-auto">
            {/* Name */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mono mb-1.5 uppercase tracking-widest">
                Token name
              </label>
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. CI/CD Pipeline, Dev Environment"
                className="w-full text-sm border border-gray-200 rounded-xl px-4 py-2.5 text-gray-900 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400 transition-all mono"
              />
            </div>

            {/* Expiration */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mono mb-1.5 uppercase tracking-widest">
                Expiration
              </label>
              <div className="flex flex-wrap gap-2">
                {EXPIRY_OPTIONS.map((opt) => (
                  <button
                    key={opt}
                    onClick={() => setExpiry(opt)}
                    className={`text-xs px-3 py-1.5 rounded-lg border mono transition-all duration-150 ${
                      expiry === opt
                        ? "bg-gray-950 text-white border-gray-950"
                        : "bg-white text-gray-500 border-gray-200 hover:border-gray-400"
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>

            {/* Scopes */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mono mb-2 uppercase tracking-widest">
                Scopes
              </label>
              <div className="space-y-4">
                {Object.entries(grouped).map(([group, scopes]) => (
                  <div key={group}>
                    <p className="text-xs text-gray-400 mono mb-2">{group}</p>
                    <div className="space-y-1.5">
                      {scopes.map((scope) => {
                        const checked = selectedScopes.includes(scope.id);
                        return (
                          <label
                            key={scope.id}
                            className={`flex items-center gap-3 rounded-xl px-3.5 py-2.5 cursor-pointer border transition-all duration-150 ${
                              checked ? "border-gray-900 bg-gray-950/5" : "border-gray-100 hover:border-gray-200 bg-white"
                            }`}
                          >
                            <div
                              className={`w-4 h-4 rounded-md border flex items-center justify-center shrink-0 transition-all duration-150 ${
                                checked ? "bg-gray-950 border-gray-950" : "border-gray-300"
                              }`}
                            >
                              {checked && <Icon d={icons.check} size={10} stroke="white" strokeWidth={2.5} />}
                            </div>
                            <div>
                              <span className="text-sm text-gray-800 font-medium">{scope.label}</span>
                              <span className="text-xs text-gray-400 mono ml-2">{scope.id}</span>
                            </div>
                            <input
                              type="checkbox"
                              className="sr-only"
                              checked={checked}
                              onChange={() => toggleScope(scope.id)}
                            />
                          </label>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between gap-3">
            <button onClick={handleClose} className="text-sm text-gray-400 hover:text-gray-600 transition-colors">
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={!name.trim() || selectedScopes.length === 0}
              className="flex items-center gap-2 bg-gray-950 text-white text-sm font-medium px-5 py-2.5 rounded-xl hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              Generate token →
            </button>
          </div>
        </>
      )}

      {step === 2 && (
        <>
          <div className="flex items-center justify-between px-6 pt-6 pb-5 border-b border-gray-100">
            <div>
              <h2 className="font-semibold text-gray-950 text-base">Token created</h2>
              <p className="text-xs text-gray-400 mt-0.5 mono">{name}</p>
            </div>
          </div>

          <div className="px-6 py-6 space-y-5">
            {/* Warning */}
            <div className="flex gap-3 bg-amber-50 border border-amber-100 rounded-xl p-4">
              <Icon d={icons.warn} size={16} stroke="#d97706" className="shrink-0 mt-0.5" />
              <p className="text-xs text-amber-700 leading-relaxed">
                <strong>Make sure to copy your token now.</strong> You won't be able to see it again after closing this
                window.
              </p>
            </div>

            {/* Token display */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-medium text-gray-700 mono uppercase tracking-widest">
                  Your new token
                </label>
                <button
                  onClick={() => setShowFull((v) => !v)}
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors mono"
                >
                  <Icon d={showFull ? icons.eyeOff : icons.eye} size={13} />
                  {showFull ? "Hide" : "Reveal"}
                </button>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-950 rounded-xl px-4 py-3 border border-gray-800">
                  <code className="mono text-xs text-emerald-400 break-all tracking-wider">
                    {showFull ? generatedToken : generatedToken.slice(0, 12) + "•".repeat(32)}
                  </code>
                </div>
                <CopyButton value={generatedToken} />
              </div>
            </div>

            {/* Summary */}
            <div className="bg-gray-50 rounded-xl p-4 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-gray-400 mono">Expiration</span>
                <span className="text-gray-700 mono">{expiry}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-400 mono">Scopes</span>
                <span className="text-gray-700 mono">{selectedScopes.length} selected</span>
              </div>
            </div>
          </div>

          <div className="px-6 py-4 border-t border-gray-100">
            <button
              onClick={handleClose}
              className="w-full bg-gray-950 text-white text-sm font-medium py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
            >
              Done
            </button>
          </div>
        </>
      )}
    </Modal>
  );
}

// ── Revoke confirm ────────────────────────────────────────────────────────────

interface RevokeModalProps {
  show: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

function RevokeModal({ show, onClose, onConfirm }: RevokeModalProps) {
  return (
    <Modal show={show} onClose={onClose}>
      <div className="p-6">
        <div className="w-10 h-10 bg-red-50 rounded-xl flex items-center justify-center mb-4">
          <Icon d={icons.trash} size={18} stroke="#ef4444" />
        </div>
        <h2 className="font-semibold text-gray-950 mb-2">Revoke this token?</h2>
        <p className="text-sm text-gray-500 leading-relaxed mb-6">
          Any scripts or applications using this token will immediately lose access. This cannot be undone.
        </p>
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 border border-gray-200 text-gray-600 text-sm font-medium py-2.5 rounded-xl hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 bg-red-500 text-white text-sm font-medium py-2.5 rounded-xl hover:bg-red-600 transition-colors"
          >
            Revoke token
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

interface SidebarProps {
  active: NavId;
  setActive: (id: NavId) => void;
}

function Sidebar({ active, setActive }: SidebarProps) {
  return (
    <aside className="w-56 shrink-0 border-r border-gray-100 flex flex-col bg-white">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-100 flex items-center gap-2.5">
        <div className="w-7 h-7 bg-black rounded-lg flex items-center justify-center">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="white">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
          </svg>
        </div>
        <span className="font-semibold text-sm text-gray-950">Volta</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map((n) => (
          <button
            key={n.id}
            onClick={() => setActive(n.id)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all duration-150 text-left ${
              active === n.id ? "bg-gray-100 text-gray-900 font-medium" : "text-gray-400 hover:text-gray-700 hover:bg-gray-50"
            }`}
          >
            <Icon d={icons[n.icon]} size={15} />
            {n.label}
          </button>
        ))}
      </nav>

      {/* User */}
      <div className="px-3 pb-4 pt-3 border-t border-gray-100">
        <div className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors">
          <div className="w-7 h-7 rounded-full bg-gray-900 text-white text-xs font-medium flex items-center justify-center mono shrink-0">
            IK
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-gray-900 truncate">Igor K.</p>
            <p className="text-xs text-gray-400 truncate mono">igor@volta.io</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

// ── Tokens page ───────────────────────────────────────────────────────────────

function TokensPage() {
  const [tokens, setTokens] = useState<Token[]>(INITIAL_TOKENS);
  const [showCreate, setShowCreate] = useState(false);
  const [revokeId, setRevokeId] = useState<number | null>(null);
  const [filter, setFilter] = useState<FilterType>("all");

  const handleCreate = (data: NewTokenData) => {
    setTokens((prev) => [{ id: Date.now(), ...data }, ...prev]);
  };

  const handleRevoke = (id: number) => {
    setTokens((prev) => prev.map((t) => (t.id === id ? { ...t, active: false } : t)));
    setRevokeId(null);
  };

  const filtered = tokens.filter((t) => {
    const isExpired = !!t.expiry && new Date(t.expiry) < new Date();
    if (filter === "active") return t.active && !isExpired;
    if (filter === "expired") return !t.active || isExpired;
    return true;
  });

  const activeCount = tokens.filter((t) => t.active && !(t.expiry && new Date(t.expiry) < new Date())).length;

  const FILTERS: FilterType[] = ["all", "active", "expired"];

  return (
    <div className="max-w-3xl mx-auto py-10 px-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-950 mb-1">Access Tokens</h1>
          <p className="text-sm text-gray-400 font-light leading-relaxed max-w-md">
            Personal access tokens function like passwords — use them to authenticate with the Volta API or SDK from your
            scripts and applications.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="shrink-0 flex items-center gap-2 bg-gray-950 text-white text-sm font-medium px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors whitespace-nowrap"
        >
          <Icon d={icons.plus} size={14} stroke="white" />
          New token
        </button>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {(
          [
            { label: "Total tokens", value: tokens.length },
            { label: "Active", value: activeCount },
            { label: "Revoked / Expired", value: tokens.length - activeCount },
          ] as const
        ).map(({ label, value }) => (
          <div key={label} className="border border-gray-100 rounded-xl p-4 bg-white">
            <p className="text-xs text-gray-400 mono mb-1">{label}</p>
            <p className="text-2xl font-semibold tracking-tight text-gray-950">{value}</p>
          </div>
        ))}
      </div>

      {/* Security notice */}
      <div className="flex gap-3 bg-blue-50/60 border border-blue-100 rounded-xl p-4 mb-6">
        <Icon d={icons.shield} size={15} stroke="#3b82f6" className="shrink-0 mt-0.5" />
        <p className="text-xs text-blue-600 leading-relaxed">
          Treat your tokens like passwords. Never share them or check them into version control. Revoke any token you
          suspect has been compromised.
        </p>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 mb-5 bg-gray-50 rounded-xl p-1 w-fit border border-gray-100">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`text-xs px-3 py-1.5 rounded-lg mono capitalize transition-all duration-150 ${
              filter === f ? "bg-white text-gray-900 shadow-sm font-medium border border-gray-200" : "text-gray-400 hover:text-gray-600"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Token list */}
      <div className="space-y-3">
        {filtered.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <div className="w-12 h-12 rounded-2xl bg-gray-100 flex items-center justify-center mx-auto mb-3">
              <Icon d={icons.tokens} size={20} stroke="#d1d5db" />
            </div>
            <p className="text-sm font-medium text-gray-300 mono">No tokens</p>
          </div>
        )}
        {filtered.map((token) => (
          <TokenRow key={token.id} token={token} onRevoke={(id) => setRevokeId(id)} />
        ))}
      </div>

      <CreateTokenModal show={showCreate} onClose={() => setShowCreate(false)} onCreate={handleCreate} />
      <RevokeModal show={!!revokeId} onClose={() => setRevokeId(null)} onConfirm={() => revokeId !== null && handleRevoke(revokeId)} />
    </div>
  );
}

// ── Overview stub ─────────────────────────────────────────────────────────────

function OverviewPage() {
  const stats: [string, string, string][] = [
    ["Total events", "1.24M", "+18.2%"],
    ["Active users", "8,492", "+4.7%"],
    ["Conversion", "3.61%", "+0.4%"],
  ];
  const bars = [40, 55, 35, 70, 65, 80, 60, 90, 75, 85, 95, 88, 72, 100, 92, 78, 85, 95, 88, 100];

  return (
    <div className="max-w-5xl mx-auto py-10 px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-gray-950 mb-8">Overview</h1>
      <div className="grid grid-cols-3 gap-3 mb-6">
        {stats.map(([label, val, change]) => (
          <div key={label} className="border border-gray-100 rounded-2xl p-5 bg-white">
            <p className="text-xs text-gray-400 mb-1 mono">{label}</p>
            <p className="text-3xl font-semibold tracking-tight mb-1">{val}</p>
            <p className="text-xs text-emerald-500 mono">{change}</p>
          </div>
        ))}
      </div>
      <div className="border border-gray-100 rounded-2xl p-6 bg-white">
        <p className="text-xs text-gray-400 mb-4 mono">Events over time</p>
        <div className="flex items-end gap-1.5 h-32">
          {bars.map((h, i) => (
            <div
              key={i}
              className="flex-1 rounded-sm transition-all"
              style={{ height: `${h}%`, background: i === bars.length - 1 ? "#0f0f0f" : "#e5e7eb" }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface PlaceholderPageProps {
  name: string | undefined;
}

function PlaceholderPage({ name }: PlaceholderPageProps) {
  return (
    <div className="flex items-center justify-center h-full text-gray-300">
      <div className="text-center">
        <p className="text-4xl font-semibold tracking-tight mb-2 text-gray-100">{name}</p>
        <p className="text-sm mono">Coming soon</p>
      </div>
    </div>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [active, setActive] = useState<NavId>("tokens");

  const content: Partial<Record<NavId, ReactNode>> = {
    overview: <OverviewPage />,
    tokens: <TokensPage />,
  };

  const activeNav = NAV.find((n) => n.id === active);

  return (
    <>
      <style>{`
        @keyframes modalIn {
          from { opacity: 0; transform: scale(0.96) translateY(8px); }
          to   { opacity: 1; transform: scale(1)    translateY(0); }
        }
        .animate-modal { animation: modalIn 0.18s cubic-bezier(0.16,1,0.3,1) both; }
        * { box-sizing: border-box; }
      `}</style>

      <div className="flex h-screen bg-white overflow-hidden font-sans">
        <Sidebar active={active} setActive={setActive} />

        {/* Top bar */}
        <div className="flex-1 flex flex-col min-w-0">
          <header className="flex items-center justify-between px-8 py-4 border-b border-gray-100 bg-white shrink-0">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-400 mono">volta.io</span>
              <Icon d={icons.chevron} size={13} stroke="#d1d5db" />
              <span className="text-gray-700 font-medium mono capitalize">{active}</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-xs text-gray-400 mono">All systems operational</span>
            </div>
          </header>

          <main className="flex-1 overflow-y-auto bg-white">
            {content[active] ?? <PlaceholderPage name={activeNav?.label} />}
          </main>
        </div>
      </div>
    </>
  );
}