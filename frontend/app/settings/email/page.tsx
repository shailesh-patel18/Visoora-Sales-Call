"use client";

import React, { useState, useEffect } from "react";
import {
  Mail,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Key,
  Globe,
  RefreshCw,
  Chrome,
  Settings,
  Shield,
  Loader2,
  ArrowRight,
} from "lucide-react";
import { BACKEND_URL } from "../../config";
import { getAuthHeaders } from "../../auth/store";
import { useCRMStore } from "../../store";
import { useRouter } from "next/navigation";

interface Mailbox {
  id: string;
  email: string;
  provider: string;
  is_default: boolean;
  verification_status: string;
  created_at: string;
}

export default function EmailAccountsPage() {
  const [mounted, setMounted] = useState(false);
  const [mailboxes, setMailboxes] = useState<Mailbox[]>([]);
  const [loading, setLoading] = useState(true);
  const [connectingProvider, setConnectingProvider] = useState<string | null>(null);
  const { markStepComplete } = useCRMStore();
  const router = useRouter();

  // Form states for manual configurations (SMTP, SendGrid, etc.)
  const [showAddForm, setShowAddForm] = useState(false);
  const [provider, setProvider] = useState("smtp");
  const [email, setEmail] = useState("");
  
  // SMTP settings
  const [smtpHost, setSmtpHost] = useState("");
  const [smtpPort, setSmtpPort] = useState("587");
  const [smtpUsername, setSmtpUsername] = useState("");
  const [smtpPassword, setSmtpPassword] = useState("");
  const [useSsl, setUseSsl] = useState(false);

  // API settings (SendGrid, Resend, Postmark)
  const [apiKey, setApiKey] = useState("");

  const fetchMailboxes = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/mailboxes`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setMailboxes(data);
      }
    } catch (err) {
      console.error("Failed to fetch mailboxes:", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    setMounted(true);
    fetchMailboxes();
  }, []);

  const handleOAuthConnect = async (prov: string) => {
    setConnectingProvider(prov);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/v1/sales-employee/mailboxes/oauth/authorize?provider=${prov}`,
        {
          headers: getAuthHeaders(),
        }
      );
      if (res.ok) {
        const data = await res.json();
        // In local/mock mode, this will authorize instantly and redirect back
        window.location.href = data.url;
      }
    } catch (err) {
      console.error(err);
      alert("OAuth integration failed to initialize.");
    }
    setConnectingProvider(null);
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      alert("Sender Email is required.");
      return;
    }

    let config: any = {};
    if (provider === "smtp") {
      if (!smtpHost || !smtpPassword) {
        alert("SMTP Host and Password are required.");
        return;
      }
      config = {
        host: smtpHost,
        port: parseInt(smtpPort),
        username: smtpUsername || email,
        password: smtpPassword,
        use_ssl: useSsl,
      };
    } else {
      if (!apiKey) {
        alert("API Key is required.");
        return;
      }
      config = { api_key: apiKey };
    }

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/mailboxes`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          provider,
          connection_config: config,
          is_default: mailboxes.length === 0,
        }),
      });

      if (res.ok) {
        setShowAddForm(false);
        // Reset states
        setEmail("");
        setSmtpHost("");
        setSmtpPassword("");
        setApiKey("");
        fetchMailboxes();
      } else {
        const data = await res.json();
        alert(`Connection failed: ${data.detail || "Check configurations."}`);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to connect mailbox.");
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/mailboxes/${id}/default`, {
        method: "PUT",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        fetchMailboxes();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDisconnect = async (id: string) => {
    if (!confirm("Are you sure you want to disconnect this mailbox account?")) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/mailboxes/${id}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        fetchMailboxes();
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (!mounted) return null;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-4xl mx-auto text-white">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Email Connected Accounts</h1>
        <p className="text-sm mt-0.5 text-neutral-400">
          Connect your custom business mailboxes. The AI outreach agent will automatically send emails using your verified sender profile.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main List */}
        <div className="md:col-span-2 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center p-12 bg-neutral-900 border border-neutral-800 rounded-xl">
              <Loader2 className="w-6 h-6 animate-spin text-neutral-500" />
            </div>
          ) : mailboxes.length === 0 ? (
            <div className="rounded-xl border border-neutral-800 p-8 text-center bg-neutral-900/60">
              <Mail className="w-8 h-8 mx-auto text-neutral-600 mb-2" />
              <p className="text-xs text-neutral-400">No custom mailboxes connected yet. Visoora fallback sender is active for testing.</p>
            </div>
          ) : (
            mailboxes.map((m) => (
              <div
                key={m.id}
                className="p-5 rounded-xl border flex items-center justify-between transition-all"
                style={{
                  background: m.is_default ? "hsl(var(--surface-2))" : "hsl(var(--surface-1))",
                  borderColor: m.is_default ? "hsl(var(--brand-primary))" : "hsl(var(--border-subtle))",
                }}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-lg bg-white/[0.03] flex items-center justify-center">
                    <Mail className="w-4 h-4 text-neutral-300" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-white flex items-center gap-2">
                      {m.email}
                      {m.is_default && (
                        <span
                          className="text-[9px] font-bold px-1.5 py-0.5 rounded-full"
                          style={{ background: "hsla(var(--brand-primary), 0.1)", color: "hsl(var(--brand-primary))" }}
                        >
                          Default Sender
                        </span>
                      )}
                    </h3>
                    <p className="text-[10px] text-neutral-400 capitalize mt-0.5">Provider: {m.provider}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {!m.is_default && (
                    <button
                      onClick={() => handleSetDefault(m.id)}
                      className="text-[11px] font-semibold px-2.5 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] transition-all"
                    >
                      Make Default
                    </button>
                  )}
                  <button
                    onClick={() => handleDisconnect(m.id)}
                    className="p-2 rounded-lg text-red-400 hover:bg-red-400/10 transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Action Panel */}
        <div className="md:col-span-1 space-y-4">
          <div className="p-5 rounded-xl border border-neutral-800 bg-neutral-900/60 flex flex-col gap-3">
            <h2 className="text-xs font-bold text-neutral-400 uppercase tracking-wider">Connect Mailbox</h2>
            
            <button
              onClick={() => handleOAuthConnect("gmail")}
              disabled={connectingProvider !== null}
              className="w-full py-2.5 rounded-lg text-xs font-semibold bg-neutral-800 hover:bg-neutral-700 transition-all flex items-center justify-center gap-2"
            >
              <Chrome className="w-3.5 h-3.5 text-blue-400" />
              Connect Gmail Account
            </button>

            <button
              onClick={() => handleOAuthConnect("outlook")}
              disabled={connectingProvider !== null}
              className="w-full py-2.5 rounded-lg text-xs font-semibold bg-neutral-800 hover:bg-neutral-700 transition-all flex items-center justify-center gap-2"
            >
              <Settings className="w-3.5 h-3.5 text-blue-300" />
              Connect Outlook / Office 365
            </button>

            <button
              onClick={() => {
                setProvider("smtp");
                setShowAddForm(true);
              }}
              className="w-full py-2.5 rounded-lg text-xs font-semibold text-white transition-all flex items-center justify-center gap-2"
              style={{ background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))" }}
            >
              <Plus className="w-3.5 h-3.5" />
              Connect Other (SMTP/API)
            </button>

            {/* Skip / Continue button — always visible so user is never stuck */}
            <div className="pt-2 border-t border-neutral-800">
              <button
                onClick={() => {
                  markStepComplete(4);
                  router.push("/contacts");
                }}
                className="w-full py-2.5 rounded-lg text-xs font-semibold text-teal-400 hover:text-white hover:bg-teal-500/10 border border-teal-500/30 hover:border-teal-500/60 transition-all flex items-center justify-center gap-2"
              >
                Continue to Audience <ArrowRight className="w-3.5 h-3.5" />
              </button>
              <p className="text-[10px] text-neutral-600 text-center mt-1.5">You can connect a mailbox later from Settings</p>
            </div>
          </div>
        </div>
      </div>

      {/* Manual Configuration Modal */}
      {showAddForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-[480px] rounded-2xl border p-6 shadow-2xl bg-neutral-950 border-neutral-800 text-xs">
            <h2 className="text-sm font-bold text-white mb-4">Manual Mailbox Configuration</h2>
            
            <form onSubmit={handleManualSubmit} className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <span className="text-neutral-400">Connection Provider</span>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full bg-neutral-900 border border-neutral-800 rounded py-2 px-3 outline-none text-white"
                >
                  <option value="smtp">SMTP Relay (Any Provider)</option>
                  <option value="sendgrid">SendGrid API</option>
                  <option value="resend">Resend API</option>
                  <option value="postmark">Postmark API</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <span className="text-neutral-400">Sender Email Address</span>
                <input
                  type="email"
                  required
                  placeholder="e.g. outreach@acme.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded border border-neutral-800 bg-neutral-900 text-white outline-none"
                />
              </div>

              {provider === "smtp" ? (
                <>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="col-span-2 flex flex-col gap-1.5">
                      <span className="text-neutral-400">SMTP Host</span>
                      <input
                        type="text"
                        required
                        placeholder="e.g. smtp.gmail.com"
                        value={smtpHost}
                        onChange={(e) => setSmtpHost(e.target.value)}
                        className="w-full px-3 py-2 rounded border border-neutral-800 bg-neutral-900 text-white outline-none"
                      />
                    </div>
                    <div className="col-span-1 flex flex-col gap-1.5">
                      <span className="text-neutral-400">SMTP Port</span>
                      <input
                        type="text"
                        required
                        value={smtpPort}
                        onChange={(e) => setSmtpPort(e.target.value)}
                        className="w-full px-3 py-2 rounded border border-neutral-800 bg-neutral-900 text-white outline-none"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex flex-col gap-1.5">
                      <span className="text-neutral-400">SMTP Username</span>
                      <input
                        type="text"
                        placeholder="Optional (defaults to email)"
                        value={smtpUsername}
                        onChange={(e) => setSmtpUsername(e.target.value)}
                        className="w-full px-3 py-2 rounded border border-neutral-800 bg-neutral-900 text-white outline-none"
                      />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <span className="text-neutral-400">SMTP Password</span>
                      <input
                        type="password"
                        required
                        placeholder="••••••••••••"
                        value={smtpPassword}
                        onChange={(e) => setSmtpPassword(e.target.value)}
                        className="w-full px-3 py-2 rounded border border-neutral-800 bg-neutral-900 text-white outline-none"
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-1.5">
                    <input
                      type="checkbox"
                      id="useSsl"
                      checked={useSsl}
                      onChange={(e) => setUseSsl(e.target.checked)}
                      className="w-4 h-4 rounded border-neutral-800 bg-neutral-900 text-emerald-400 outline-none"
                    />
                    <label htmlFor="useSsl" className="text-neutral-400 cursor-pointer">
                      Use SSL/TLS Connection (Encrypted transport)
                    </label>
                  </div>
                </>
              ) : (
                <div className="flex flex-col gap-1.5">
                  <span className="text-neutral-400">API Key</span>
                  <input
                    type="password"
                    required
                    placeholder="e.g. re_xxxxxx or SG.xxxxxx"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full px-3 py-2 rounded border border-neutral-800 bg-neutral-900 text-white outline-none"
                  />
                </div>
              )}

              <div className="flex gap-3 justify-end pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 rounded border border-neutral-800 hover:bg-neutral-900 text-neutral-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded text-white font-semibold transition-all flex items-center gap-1.5"
                  style={{ background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))" }}
                >
                  <Key className="w-3.5 h-3.5" />
                  Connect Mailbox
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
