"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  Phone,
  Clock,
  AlertTriangle,
  Plus,
  Trash2,
  ToggleLeft,
  ToggleRight,
  MessageSquare,
  Bot,
  Save,
  CheckCircle2,
} from "lucide-react";
import { useCRMStore } from "../../store";

// ====================================================
// DNC MANAGEMENT
// ====================================================
function DNCManager() {
  const [dncNumbers, setDncNumbers] = useState<string[]>([
    "+15551234567",
    "+14155559999",
    "+12125553333",
  ]);
  const [newNumber, setNewNumber] = useState("");
  const [adding, setAdding] = useState(false);

  const handleAdd = async () => {
    if (!newNumber.match(/^\+\d{10,15}$/)) return;
    setAdding(true);
    // Simulate API call
    await new Promise((r) => setTimeout(r, 500));
    setDncNumbers((prev) => [newNumber, ...prev]);
    setNewNumber("");
    setAdding(false);
  };

  const handleRemove = async (number: string) => {
    setDncNumbers((prev) => prev.filter((n) => n !== number));
  };

  return (
    <div
      className="rounded-xl border p-5"
      style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
    >
      <div className="flex items-center gap-2 mb-4">
        <Phone className="w-4 h-4 text-red-400" />
        <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
          Do Not Call (DNC) Registry
        </h2>
        <span
          className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full"
          style={{ background: "hsla(0, 84%, 60%, 0.1)", color: "#ef4444" }}
        >
          {dncNumbers.length} blocked
        </span>
      </div>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="+1XXXXXXXXXX"
          value={newNumber}
          onChange={(e) => setNewNumber(e.target.value)}
          className="flex-1 px-3 py-2 rounded-lg text-sm border outline-none"
          style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))", color: "hsl(var(--text-primary))" }}
        />
        <button
          onClick={handleAdd}
          disabled={adding || !newNumber.match(/^\+\d{10,15}$/)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white disabled:opacity-50"
          style={{ background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))" }}
        >
          <Plus className="w-3.5 h-3.5" /> Add
        </button>
      </div>
      <div className="space-y-1 max-h-[200px] overflow-y-auto">
        {dncNumbers.map((num) => (
          <div
            key={num}
            className="flex items-center justify-between py-2 px-3 rounded-lg transition-colors hover:bg-white/[0.02]"
          >
            <span className="text-[13px] font-mono" style={{ color: "hsl(var(--text-secondary))" }}>
              {num}
            </span>
            <button
              onClick={() => handleRemove(num)}
              className="p-1.5 rounded-lg transition-colors"
              style={{ color: "#ef4444" }}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ====================================================
// CALLING HOURS
// ====================================================
function CallingHoursEditor() {
  const { compliance, setCompliance } = useCRMStore();

  return (
    <div
      className="rounded-xl border p-5"
      style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
    >
      <div className="flex items-center gap-2 mb-4">
        <Clock className="w-4 h-4 text-amber-400" />
        <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
          Calling Hours
        </h2>
      </div>
      <p className="text-[12px] mb-4" style={{ color: "hsl(var(--text-muted))" }}>
        Calls will be blocked outside these hours in the recipient's local timezone.
      </p>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1" style={{ color: "hsl(var(--text-muted))" }}>
            Start Time
          </label>
          <input
            type="time"
            value={compliance.calling_hours_start}
            onChange={(e) => setCompliance({ ...compliance, calling_hours_start: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm border outline-none"
            style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))", color: "hsl(var(--text-primary))" }}
          />
        </div>
        <div>
          <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1" style={{ color: "hsl(var(--text-muted))" }}>
            End Time
          </label>
          <input
            type="time"
            value={compliance.calling_hours_end}
            onChange={(e) => setCompliance({ ...compliance, calling_hours_end: e.target.value })}
            className="w-full px-3 py-2 rounded-lg text-sm border outline-none"
            style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))", color: "hsl(var(--text-primary))" }}
          />
        </div>
      </div>
      <div>
        <label className="text-[11px] font-semibold uppercase tracking-wider block mb-1" style={{ color: "hsl(var(--text-muted))" }}>
          Default Timezone
        </label>
        <select
          value={compliance.calling_timezone}
          onChange={(e) => setCompliance({ ...compliance, calling_timezone: e.target.value })}
          className="w-full px-3 py-2 rounded-lg text-sm border outline-none"
          style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))", color: "hsl(var(--text-primary))" }}
        >
          <option value="America/New_York">Eastern (ET)</option>
          <option value="America/Chicago">Central (CT)</option>
          <option value="America/Denver">Mountain (MT)</option>
          <option value="America/Los_Angeles">Pacific (PT)</option>
          <option value="Asia/Kolkata">India (IST)</option>
          <option value="Europe/London">UK (GMT)</option>
        </select>
      </div>
    </div>
  );
}

// ====================================================
// DISCLOSURE TOGGLES
// ====================================================
function DisclosureToggles() {
  const { compliance, setCompliance } = useCRMStore();

  return (
    <div
      className="rounded-xl border p-5"
      style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
    >
      <div className="flex items-center gap-2 mb-4">
        <MessageSquare className="w-4 h-4 text-blue-400" />
        <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
          Disclosures
        </h2>
      </div>
      <div className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[13px] font-medium" style={{ color: "hsl(var(--text-primary))" }}>
              Recording Disclosure
            </span>
            <button
              onClick={() =>
                setCompliance({ ...compliance, recording_disclosure_enabled: !compliance.recording_disclosure_enabled })
              }
            >
              {compliance.recording_disclosure_enabled ? (
                <ToggleRight className="w-8 h-5 text-emerald-400" />
              ) : (
                <ToggleLeft className="w-8 h-5" style={{ color: "hsl(var(--text-muted))" }} />
              )}
            </button>
          </div>
          <textarea
            value={compliance.recording_disclosure_text}
            onChange={(e) => setCompliance({ ...compliance, recording_disclosure_text: e.target.value })}
            rows={2}
            className="w-full px-3 py-2 rounded-lg text-[12px] border outline-none resize-none"
            style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))", color: "hsl(var(--text-primary))" }}
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-purple-400" />
              <span className="text-[13px] font-medium" style={{ color: "hsl(var(--text-primary))" }}>
                AI Disclosure
              </span>
            </div>
            <button
              onClick={() =>
                setCompliance({ ...compliance, ai_disclosure_enabled: !compliance.ai_disclosure_enabled })
              }
            >
              {compliance.ai_disclosure_enabled ? (
                <ToggleRight className="w-8 h-5 text-emerald-400" />
              ) : (
                <ToggleLeft className="w-8 h-5" style={{ color: "hsl(var(--text-muted))" }} />
              )}
            </button>
          </div>
          <textarea
            value={compliance.ai_disclosure_text}
            onChange={(e) => setCompliance({ ...compliance, ai_disclosure_text: e.target.value })}
            rows={2}
            className="w-full px-3 py-2 rounded-lg text-[12px] border outline-none resize-none"
            style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))", color: "hsl(var(--text-primary))" }}
          />
        </div>
      </div>
    </div>
  );
}

// ====================================================
// CONSENT LOG
// ====================================================
function ConsentLog() {
  const mockConsents = [
    { id: "cs1", phone: "+15551234567", type: "explicit_verbal", obtained_at: new Date(Date.now() - 86400000).toISOString(), method: "IVR press-1" },
    { id: "cs2", phone: "+14155552671", type: "written_form", obtained_at: new Date(Date.now() - 172800000).toISOString(), method: "Web form" },
    { id: "cs3", phone: "+919824457565", type: "inbound_implied", obtained_at: new Date(Date.now() - 259200000).toISOString(), method: "Caller initiated" },
  ];

  return (
    <div
      className="rounded-xl border p-5"
      style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
    >
      <div className="flex items-center gap-2 mb-4">
        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
          Consent Log
        </h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: "1px solid hsl(var(--border-subtle))" }}>
              <th className="text-left py-2 px-2 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "hsl(var(--text-muted))" }}>Phone</th>
              <th className="text-left py-2 px-2 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "hsl(var(--text-muted))" }}>Type</th>
              <th className="text-left py-2 px-2 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "hsl(var(--text-muted))" }}>Method</th>
              <th className="text-left py-2 px-2 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "hsl(var(--text-muted))" }}>Date</th>
            </tr>
          </thead>
          <tbody>
            {mockConsents.map((c) => (
              <tr key={c.id} className="border-t" style={{ borderColor: "hsl(var(--border-subtle))" }}>
                <td className="py-2.5 px-2 text-[13px] font-mono" style={{ color: "hsl(var(--text-secondary))" }}>{c.phone}</td>
                <td className="py-2.5 px-2">
                  <span className="text-[11px] px-2 py-0.5 rounded-full font-medium" style={{ background: "hsl(var(--surface-3))", color: "hsl(var(--text-secondary))" }}>
                    {c.type.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="py-2.5 px-2 text-[13px]" style={{ color: "hsl(var(--text-secondary))" }}>{c.method}</td>
                <td className="py-2.5 px-2 text-[12px]" style={{ color: "hsl(var(--text-muted))" }}>
                  {new Date(c.obtained_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ====================================================
// COMPLIANCE PAGE
// ====================================================
export default function CompliancePage() {
  const [mounted, setMounted] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (!mounted) return null;

  return (
    <div className="p-6 lg:p-8 max-w-[1200px] mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            Compliance Settings
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>
            TCPA, GDPR, and AI disclosure management
          </p>
        </div>
        <button
          onClick={handleSave}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white transition-all"
          style={{
            background: saved
              ? "hsl(var(--success))"
              : "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
          }}
        >
          {saved ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
          {saved ? "Saved!" : "Save Changes"}
        </button>
      </div>

      {/* Warning Banner */}
      <div
        className="rounded-xl p-4 border flex items-start gap-3"
        style={{ background: "hsla(38, 92%, 50%, 0.05)", borderColor: "hsla(38, 92%, 50%, 0.2)" }}
      >
        <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-[13px] font-medium text-amber-400">Compliance Warning</p>
          <p className="text-[12px] mt-0.5" style={{ color: "hsl(var(--text-secondary))" }}>
            Ensure all disclosure settings comply with your jurisdiction's TCPA, FCC, and GDPR regulations. Visoora blocks calls outside configured hours automatically.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DNCManager />
        <CallingHoursEditor />
        <DisclosureToggles />
        <ConsentLog />
      </div>
    </div>
  );
}
