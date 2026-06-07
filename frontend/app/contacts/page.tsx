"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Search,
  Phone,
  ChevronDown,
  Download,
  UserPlus,
  ShieldBan,
  Filter,
  MoreHorizontal,
  ArrowUpDown,
  Mail,
  Building2,
  Clock,
  X,
} from "lucide-react";
import { useCRMStore, type Contact } from "../store";
import { BACKEND_URL } from "../config";

// ====================================================
// MOCK DATA
// ====================================================
function generateMockContacts(): Contact[] {
  const names = [
    "Sarah Connor", "Tony Stark", "Bruce Wayne", "Peter Parker", "Diana Prince",
    "Steve Rogers", "Natasha Romanoff", "Clark Kent", "Barry Allen", "Wanda Maximoff",
    "Hal Jordan", "Arthur Curry", "Oliver Queen", "Victor Stone", "John Constantine",
    "Selina Kyle", "Barbara Gordon", "Kara Danvers", "Jean Grey", "Scott Summers",
  ];
  const companies = [
    "Cyberdyne Systems", "Stark Industries", "Wayne Enterprises", "Daily Bugle", "Themyscira Inc",
    "Shield Corp", "Red Room LLC", "Daily Planet", "STAR Labs", "Westview Holdings",
    "Ferris Aircraft", "Atlantean Tech", "Queen Consolidated", "CyTech Global", "Hellblazer Co",
    "Catwoman Ltd", "Oracle Systems", "DEO Federal", "Xavier Institute", "Summers Optics",
  ];
  return names.map((name, i) => ({
    id: `contact_${i}`,
    tenant_id: "acme_tenant",
    phone_e164: `+1555${String(i).padStart(7, "0")}`,
    full_name: name,
    company_name: companies[i],
    email: `${name.toLowerCase().replace(" ", ".")}@${companies[i].toLowerCase().replace(/\s+/g, "")}.com`,
    lead_score: Math.floor(Math.random() * 100),
    lead_source: ["inbound", "outbound", "referral", "organic"][i % 4],
    tags: [["enterprise", "hot"][i % 2], ["tech", "finance", "healthcare"][i % 3]],
    created_at: new Date(Date.now() - i * 86400000).toISOString(),
    updated_at: new Date(Date.now() - i * 43200000).toISOString(),
  }));
}

// ====================================================
// SUB COMPONENTS
// ====================================================
function LeadScoreBadge({ score }: { score: number }) {
  let bg: string, text: string;
  if (score >= 80) {
    bg = "hsla(142, 71%, 45%, 0.12)";
    text = "#22c55e";
  } else if (score >= 50) {
    bg = "hsla(38, 92%, 50%, 0.12)";
    text = "#f59e0b";
  } else {
    bg = "hsla(0, 0%, 50%, 0.1)";
    text = "hsl(var(--text-muted))";
  }
  return (
    <span
      className="inline-flex items-center justify-center w-10 h-6 rounded-full text-[11px] font-bold"
      style={{ background: bg, color: text }}
    >
      {score}
    </span>
  );
}

// ====================================================
// CONTACTS PAGE
// ====================================================
const countries = [
  { code: "+91", flag: "🇮🇳", name: "India" },
  { code: "+1", flag: "🇺🇸", name: "United States" },
  { code: "+44", flag: "🇬🇧", name: "United Kingdom" },
  { code: "+971", flag: "🇦🇪", name: "United Arab Emirates" },
  { code: "+49", flag: "🇩🇪", name: "Germany" },
  { code: "+61", flag: "🇦🇺", name: "Australia" },
  { code: "+98", flag: "🇮🇷", name: "Iran" },
];

export default function ContactsPage() {
  const { contacts, setContacts, addContact } = useCRMStore();
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<"full_name" | "lead_score" | "created_at">("lead_score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [dialing, setDialing] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [mounted, setMounted] = useState(false);

  // New Contact Form State
  const [newName, setNewName] = useState("");
  const [newCompany, setNewCompany] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newScore, setNewScore] = useState("50");
  const [countryCode, setCountryCode] = useState("+91");

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newPhone.trim()) {
      alert("Name and Phone Number are required.");
      return;
    }
    
    // Format to E.164 compliance
    let trimmedPhone = newPhone.trim();
    let phoneFormatted = "";
    if (trimmedPhone.startsWith("+")) {
      phoneFormatted = trimmedPhone;
    } else {
      phoneFormatted = `${countryCode}${trimmedPhone.replace(/\D/g, "")}`;
    }

    const payload = {
      tenant_id: "acme_tenant",
      phone_e164: phoneFormatted,
      full_name: newName.trim(),
      company_name: newCompany.trim() || "Independent",
      email: newEmail.trim() || undefined,
      lead_score: parseInt(newScore) || 50,
      lead_source: "outbound",
      tags: ["manual"],
      custom_fields: {}
    };

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/crm/contacts`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Tenant-ID": "acme_tenant"
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const savedContact = await res.json();
        addContact(savedContact);
      } else {
        const errData = await res.json();
        console.error("Failed to save contact on backend:", errData);
        addContact({
          id: `contact_${Date.now()}`,
          ...payload,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
      }
    } catch (err) {
      console.warn("Failed to contact backend, saving locally:", err);
      addContact({
        id: `contact_${Date.now()}`,
        ...payload,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    }

    // Reset Form Fields
    setNewName("");
    setNewCompany("");
    setNewPhone("");
    setNewEmail("");
    setNewScore("50");
    setShowAddModal(false);
  };

  const fetchContacts = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/crm/contacts`, {
        headers: { "X-Tenant-ID": "acme_tenant" }
      });
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          setContacts(data);
        } else {
          setContacts(generateMockContacts());
        }
      } else {
        setContacts(generateMockContacts());
      }
    } catch (err) {
      console.warn("Failed to fetch contacts, using local mock:", err);
      setContacts(generateMockContacts());
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchContacts();
  }, [setContacts]);

  const filtered = useMemo(() => {
    let list = contacts.filter(
      (c) =>
        c.full_name.toLowerCase().includes(search.toLowerCase()) ||
        c.company_name.toLowerCase().includes(search.toLowerCase()) ||
        c.phone_e164.includes(search)
    );
    list.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av;
      }
      return sortDir === "asc"
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return list;
  }, [contacts, search, sortKey, sortDir]);

  const toggleSort = (key: typeof sortKey) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("desc"); }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedIds.size === filtered.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(filtered.map((c) => c.id)));
  };

  const handleDial = async (contact: Contact) => {
    setDialing(contact.id);
    try {
      await fetch(`${BACKEND_URL}/make-call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: contact.full_name,
          company: contact.company_name,
          phone: contact.phone_e164,
        }),
      });
    } catch (err) {
      console.error("Dial failed:", err);
    } finally {
      setTimeout(() => setDialing(null), 2000);
    }
  };

  const handleExportCSV = () => {
    const targets = selectedIds.size > 0
      ? contacts.filter((c) => selectedIds.has(c.id))
      : filtered;
    const header = "Name,Company,Phone,Email,Lead Score\n";
    const rows = targets
      .map((c) => `"${c.full_name}","${c.company_name}","${c.phone_e164}","${c.email || ""}",${c.lead_score}`)
      .join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "visoora_contacts.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!mounted) return null;

  return (
    <div className="p-6 lg:p-8 max-w-[1440px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>Contacts</h1>
          <p className="text-sm mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>
            {contacts.length} total contacts · {filtered.length} shown
          </p>
        </div>
        <div className="flex items-center gap-2">
          {selectedIds.size > 0 && (
            <>
              <button onClick={handleExportCSV} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition-colors" style={{ borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-secondary))", background: "hsl(var(--surface-2))" }}>
                <Download className="w-3.5 h-3.5" /> Export {selectedIds.size}
              </button>
              <button className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition-colors" style={{ borderColor: "hsl(var(--border-default))", color: "#ef4444", background: "hsla(0,84%,60%,0.05)" }}>
                <ShieldBan className="w-3.5 h-3.5" /> Add to DNC
              </button>
            </>
          )}
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white"
            style={{ background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))" }}
          >
            <UserPlus className="w-3.5 h-3.5" /> Add Contact
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "hsl(var(--text-muted))" }} />
        <input
          type="text"
          placeholder="Search contacts by name, company, or phone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm border outline-none transition-colors"
          style={{
            background: "hsl(var(--surface-2))",
            borderColor: "hsl(var(--border-subtle))",
            color: "hsl(var(--text-primary))",
          }}
        />
      </div>

      {/* Table */}
      <div className="rounded-xl border overflow-hidden" style={{ borderColor: "hsl(var(--border-subtle))" }}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: "hsl(var(--surface-2))" }}>
                <th className="px-4 py-3 text-left w-10">
                  <input type="checkbox" checked={selectedIds.size === filtered.length && filtered.length > 0} onChange={toggleAll} className="rounded accent-emerald-500" />
                </th>
                <th className="px-4 py-3 text-left">
                  <button onClick={() => toggleSort("full_name")} className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wider" style={{ color: "hsl(var(--text-muted))" }}>
                    Contact <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left hidden md:table-cell">
                  <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "hsl(var(--text-muted))" }}>Company</span>
                </th>
                <th className="px-4 py-3 text-center">
                  <button onClick={() => toggleSort("lead_score")} className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wider mx-auto" style={{ color: "hsl(var(--text-muted))" }}>
                    Score <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left hidden lg:table-cell">
                  <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "hsl(var(--text-muted))" }}>Source</span>
                </th>
                <th className="px-4 py-3 text-center">
                  <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "hsl(var(--text-muted))" }}>Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((contact) => (
                <tr
                  key={contact.id}
                  className="border-t transition-colors hover:bg-white/[0.02]"
                  style={{ borderColor: "hsl(var(--border-subtle))" }}
                >
                  <td className="px-4 py-3">
                    <input type="checkbox" checked={selectedIds.has(contact.id)} onChange={() => toggleSelect(contact.id)} className="rounded accent-emerald-500" />
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium text-[13px]" style={{ color: "hsl(var(--text-primary))" }}>{contact.full_name}</p>
                      <p className="text-[11px] mt-0.5 flex items-center gap-1" style={{ color: "hsl(var(--text-muted))" }}>
                        <Phone className="w-3 h-3" /> {contact.phone_e164}
                      </p>
                    </div>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <div className="flex items-center gap-1.5">
                      <Building2 className="w-3.5 h-3.5" style={{ color: "hsl(var(--text-muted))" }} />
                      <span className="text-[13px]" style={{ color: "hsl(var(--text-secondary))" }}>{contact.company_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <LeadScoreBadge score={contact.lead_score} />
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell">
                    <span className="text-[11px] px-2 py-0.5 rounded-full font-medium capitalize" style={{ background: "hsl(var(--surface-3))", color: "hsl(var(--text-secondary))" }}>
                      {contact.lead_source || "unknown"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button
                        onClick={() => handleDial(contact)}
                        disabled={dialing === contact.id}
                        className="p-2 rounded-lg transition-colors disabled:opacity-50"
                        style={{ background: "hsla(142, 71%, 45%, 0.1)", color: "#22c55e" }}
                        title="Call now"
                      >
                        <Phone className={`w-3.5 h-3.5 ${dialing === contact.id ? "animate-pulse" : ""}`} />
                      </button>
                      <button className="p-2 rounded-lg transition-colors" style={{ background: "hsl(var(--surface-3))", color: "hsl(var(--text-secondary))" }} title="More actions">
                        <MoreHorizontal className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Contact Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div
            className="w-full max-w-md rounded-xl border p-6 space-y-4 shadow-2xl relative"
            style={{
              background: "hsl(var(--surface-1))",
              borderColor: "hsl(var(--border-subtle))",
            }}
          >
            <button
              onClick={() => setShowAddModal(false)}
              className="absolute right-4 top-4 p-1.5 rounded-lg transition-colors hover:bg-white/5"
              style={{ color: "hsl(var(--text-muted))" }}
            >
              <X className="w-4 h-4" />
            </button>

            <div>
              <h2 className="text-lg font-bold" style={{ color: "hsl(var(--text-primary))" }}>Add New Contact</h2>
              <p className="text-xs" style={{ color: "hsl(var(--text-muted))" }}>Create a prospect to initiate or schedule calls.</p>
            </div>

            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Jane Doe"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm border outline-none transition-colors"
                  style={{
                    background: "hsl(var(--surface-2))",
                    borderColor: "hsl(var(--border-subtle))",
                    color: "hsl(var(--text-primary))",
                  }}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>Phone Number *</label>
                <div className="flex gap-2">
                  <div className="relative flex-shrink-0" style={{ width: "110px" }}>
                    <select
                      value={countryCode}
                      onChange={(e) => setCountryCode(e.target.value)}
                      className="w-full h-full pl-3 pr-8 py-2 rounded-lg text-sm border outline-none transition-colors cursor-pointer appearance-none"
                      style={{
                        background: "hsl(var(--surface-2))",
                        borderColor: "hsl(var(--border-subtle))",
                        color: "hsl(var(--text-primary))",
                      }}
                    >
                      {countries.map((c) => (
                        <option key={c.code} value={c.code}>
                          {c.flag} {c.code}
                        </option>
                      ))}
                    </select>
                    <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-xs flex items-center" style={{ color: "hsl(var(--text-muted))" }}>
                      <ChevronDown className="w-3.5 h-3.5" />
                    </div>
                  </div>
                  <input
                    type="text"
                    required
                    placeholder="9824457565"
                    value={newPhone}
                    onChange={(e) => setNewPhone(e.target.value)}
                    className="flex-1 px-3 py-2 rounded-lg text-sm border outline-none transition-colors"
                    style={{
                      background: "hsl(var(--surface-2))",
                      borderColor: "hsl(var(--border-subtle))",
                      color: "hsl(var(--text-primary))",
                    }}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>Company Name</label>
                <input
                  type="text"
                  placeholder="e.g. Acme Corp"
                  value={newCompany}
                  onChange={(e) => setNewCompany(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm border outline-none transition-colors"
                  style={{
                    background: "hsl(var(--surface-2))",
                    borderColor: "hsl(var(--border-subtle))",
                    color: "hsl(var(--text-primary))",
                  }}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>Email Address</label>
                <input
                  type="email"
                  placeholder="e.g. jane@company.com"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm border outline-none transition-colors"
                  style={{
                    background: "hsl(var(--surface-2))",
                    borderColor: "hsl(var(--border-subtle))",
                    color: "hsl(var(--text-primary))",
                  }}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>Lead Score (0-100)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={newScore}
                  onChange={(e) => setNewScore(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm border outline-none transition-colors text-center"
                  style={{
                    background: "hsl(var(--surface-2))",
                    borderColor: "hsl(var(--border-subtle))",
                    color: "hsl(var(--text-primary))",
                  }}
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-lg text-xs font-semibold border transition-colors"
                  style={{
                    borderColor: "hsl(var(--border-default))",
                    color: "hsl(var(--text-secondary))",
                    background: "transparent",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-white transition-colors"
                  style={{
                    background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
                  }}
                >
                  Save Contact
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
