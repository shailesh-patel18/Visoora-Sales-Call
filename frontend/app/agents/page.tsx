"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Bot, ShieldAlert, Sparkles, Volume2, Clock, Globe, 
  Play, Pause, Plus, Trash2, CheckCircle2, UserCheck, Settings, Award 
} from "lucide-react";
import { useOnboardingStore } from "../onboarding/store";
import { BACKEND_URL } from "../config";

interface AgentProfile {
  id: string;
  name: string;
  role: string;
  voice: string;
  tone: string;
  timezone: string;
  callingHoursStart: string;
  callingHoursEnd: string;
  isActive: boolean;
}

const voiceProfiles = [
  { id: "rachel", name: "Rachel", gender: "Female", accent: "US", desc: "Warm & Professional", audio: "https://actions.google.com/sounds/v1/science_fiction/teleport.ogg" },
  { id: "drew", name: "Drew", gender: "Male", accent: "US", desc: "Friendly & Casual", audio: "https://actions.google.com/sounds/v1/impacts/crash.ogg" },
  { id: "clyde", name: "Clyde", gender: "Male", accent: "UK", desc: "Energetic & Assertive", audio: "https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg" },
  { id: "paul", name: "Paul", gender: "Male", accent: "US", desc: "Corporate & Technical", audio: "https://actions.google.com/sounds/v1/science_fiction/alien_beacon.ogg" },
  { id: "charlotte", name: "Charlotte", gender: "Female", accent: "AU", desc: "Helpful & Direct", audio: "https://actions.google.com/sounds/v1/ambiences/morning_birds.ogg" },
];

const toneProfiles = [
  { id: "consultative", label: "Consultative", desc: "Empathic, asks clarifying questions, focuses on solving issues" },
  { id: "direct", label: "Direct", desc: "Clear, concise, professional, doesn't waste words" },
  { id: "friendly", label: "Friendly", desc: "Casual, warm, matches high-energy prospects" },
  { id: "professional", label: "Professional", desc: "Formal, respectful, perfect for enterprise buyers" },
];

const roleTemplates = [
  { id: "SDR", label: "Sales Development Rep (SDR)", desc: "Outbound cold calling, booking meetings and qualifying leads." },
  { id: "Recruiter", label: "Recruiting Consultant", desc: "Screening candidates, qualifying expertise, and scheduling deep interviews." },
  { id: "Support", label: "Customer Support Agent", desc: "Handling inbound inquiries, resolving FAQ questions, troubleshooting." },
  { id: "Collections", label: "Billing & Collections Agent", desc: "Friendly reminders, handling invoices, and confirming payments." },
];

export default function AgentsPage() {
  const { state, loadProgress, saveProgress } = useOnboardingStore();
  const [mounted, setMounted] = useState(false);
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Roster of profiles
  const [roster, setRoster] = useState<AgentProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form states
  const [nameInput, setNameInput] = useState("");
  const [roleInput, setRoleInput] = useState("SDR");
  const [voiceInput, setVoiceInput] = useState("rachel");
  const [toneInput, setToneInput] = useState("consultative");
  const [timezoneInput, setTimezoneInput] = useState("America/New_York");
  const [hoursStartInput, setHoursStartInput] = useState("08:00");
  const [hoursEndInput, setHoursEndInput] = useState("17:00");

  const fetchRoster = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/agents`, {
        headers: { "X-Tenant-ID": "acme_tenant" }
      });
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          const mapped = data.map((agent: any) => ({
            id: agent.id,
            name: agent.name,
            role: agent.persona_config?.role || "SDR",
            voice: agent.persona_config?.voice || "rachel",
            tone: agent.persona_config?.tone || "consultative",
            timezone: agent.persona_config?.timezone || "America/New_York",
            callingHoursStart: agent.persona_config?.calling_hours_start || "08:00",
            callingHoursEnd: agent.persona_config?.calling_hours_end || "17:00",
            isActive: agent.persona_config?.is_active ?? true,
          }));
          setRoster(mapped);
          if (mapped.length > 0) {
            const first = mapped[0];
            setSelectedProfileId(first.id);
            setNameInput(first.name);
            setRoleInput(first.role);
            setVoiceInput(first.voice);
            setToneInput(first.tone);
            setTimezoneInput(first.timezone);
            setHoursStartInput(first.callingHoursStart);
            setHoursEndInput(first.callingHoursEnd);
          }
          return true;
        }
      }
    } catch (err) {
      console.warn("Failed to fetch backend agents, using local state fallback:", err);
    }
    return false;
  };

  useEffect(() => {
    setMounted(true);
    loadProgress();
    fetchRoster();
    return () => {
      if (audioRef.current) audioRef.current.pause();
    };
  }, []);

  // Initialize roster from state.step3 onboarding config (fallback)
  useEffect(() => {
    if (state.step3 && roster.length === 0) {
      const activeName = state.step3.agentName || "Alex";
      const activeVoice = state.step3.voice || "rachel";
      const activeTone = state.step3.tone || "consultative";
      const activeTimezone = state.step3.timezone || "America/New_York";
      const activeStart = state.step3.callingHoursStart || "08:00";
      const activeEnd = state.step3.callingHoursEnd || "17:00";
      
      const initialActiveProfile: AgentProfile = {
        id: "active_profile",
        name: activeName,
        role: "SDR", // Default template role
        voice: activeVoice,
        tone: activeTone,
        timezone: activeTimezone,
        callingHoursStart: activeStart,
        callingHoursEnd: activeEnd,
        isActive: true,
      };

      // Load additional templates as draft profiles
      const recProfile: AgentProfile = {
        id: "rec_profile",
        name: "Charlotte",
        role: "Recruiter",
        voice: "charlotte",
        tone: "professional",
        timezone: "America/New_York",
        callingHoursStart: "09:00",
        callingHoursEnd: "17:00",
        isActive: false,
      };

      const collProfile: AgentProfile = {
        id: "coll_profile",
        name: "Clyde",
        role: "Collections",
        voice: "clyde",
        tone: "direct",
        timezone: "America/New_York",
        callingHoursStart: "08:00",
        callingHoursEnd: "18:00",
        isActive: false,
      };

      setRoster([initialActiveProfile, recProfile, collProfile]);
      setSelectedProfileId("active_profile");

      // Set input values
      setNameInput(activeName);
      setRoleInput("SDR");
      setVoiceInput(activeVoice);
      setToneInput(activeTone);
      setTimezoneInput(activeTimezone);
      setHoursStartInput(activeStart);
      setHoursEndInput(activeEnd);
    }
  }, [state.step3, roster.length]);


  const handlePlayVoice = (voiceId: string, audioUrl: string) => {
    if (playingVoice === voiceId) {
      if (audioRef.current) audioRef.current.pause();
      setPlayingVoice(null);
      return;
    }
    if (audioRef.current) audioRef.current.pause();
    setPlayingVoice(voiceId);
    audioRef.current = new Audio(audioUrl);
    audioRef.current.volume = 0.5;
    audioRef.current.play().catch((err) => {
      console.warn("Audio play failed:", err);
      setTimeout(() => setPlayingVoice(null), 2000);
    });
    audioRef.current.onended = () => {
      setPlayingVoice(null);
    };
  };

  const handleSelectProfile = (id: string) => {
    setSelectedProfileId(id);
    const profile = roster.find((p) => p.id === id);
    if (profile) {
      setNameInput(profile.name);
      setRoleInput(profile.role);
      setVoiceInput(profile.voice);
      setToneInput(profile.tone);
      setTimezoneInput(profile.timezone);
      setHoursStartInput(profile.callingHoursStart);
      setHoursEndInput(profile.callingHoursEnd);
    }
  };

  const handleAddNewDraft = () => {
    const newId = `draft_${Date.now()}`;
    const newDraft: AgentProfile = {
      id: newId,
      name: "New Recruit",
      role: "SDR",
      voice: "rachel",
      tone: "consultative",
      timezone: "America/New_York",
      callingHoursStart: "09:00",
      callingHoursEnd: "17:00",
      isActive: false,
    };
    setRoster([...roster, newDraft]);
    handleSelectProfile(newId);
  };

  const handleActivateProfile = async (id: string) => {
    const updatedRoster = roster.map((p) => ({
      ...p,
      isActive: p.id === id,
    }));
    setRoster(updatedRoster);

    const activeProfile = updatedRoster.find((p) => p.isActive);
    if (activeProfile && state.step3) {
      setIsSaving(true);
      const updatedStep3 = {
        ...state.step3,
        agentName: activeProfile.name,
        voice: activeProfile.voice,
        tone: activeProfile.tone,
        timezone: activeProfile.timezone,
        callingHoursStart: activeProfile.callingHoursStart,
        callingHoursEnd: activeProfile.callingHoursEnd,
      };

      const mergedState = {
        ...state,
        step3: updatedStep3,
      };

      await saveProgress(mergedState);
      
      // Call onboarding/complete endpoint to trigger server config DB sync
      try {
        await fetch(`${BACKEND_URL}/api/onboarding/complete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tenant_id: "default_shared_tenant",
            company_name: state.step1?.companyName || "Unknown",
            website: state.step1?.website || "",
            industry: state.step1?.industry || "",
            team_size: state.step1?.teamSize || "",
            annual_revenue: state.step1?.annualRevenue || "",
            target_region: state.step1?.targetRegion || "",
            phone_number: state.step2?.twilioNumber || "",
            agent_name: updatedStep3.agentName,
            company_description: updatedStep3.companyDescription,
            value_proposition: updatedStep3.valueProposition,
            voice: updatedStep3.voice,
            tone: updatedStep3.tone,
            timezone: updatedStep3.timezone,
            calling_hours_start: updatedStep3.callingHoursStart,
            calling_hours_end: updatedStep3.callingHoursEnd,
            product_name: updatedStep3.productName,
            product_price: updatedStep3.productPrice,
            product_features: updatedStep3.productFeatures,
            target_audience: updatedStep3.targetAudience,
            kb_description: updatedStep3.kbDescription,
            kb_faqs: updatedStep3.kbFaqs,
            objections_list: updatedStep3.objectionsList,
            recording_disclosure: state.step4?.recordingDisclosure || false,
            consent_confirmed: state.step4?.consentConfirmed || false,
            country: state.step4?.country || "US",
            import_source: state.step5?.importSource || "csv",
            campaign_goal: state.step5?.campaignGoal || "",
            playbook_greeting: state.step5?.playbookGreeting || "",
            playbook_booking_link: state.step5?.playbookBookingLink || "",
          }),
        });
      } catch (err) {
        console.warn("DB update failed: ", err);
      }

      setIsSaving(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    }
  };

  const handleSaveProfileSettings = async () => {
    if (!selectedProfileId) return;
    setIsSaving(true);

    const updatedRoster = roster.map((p) => {
      if (p.id === selectedProfileId) {
        return {
          ...p,
          name: nameInput,
          role: roleInput,
          voice: voiceInput,
          tone: toneInput,
          timezone: timezoneInput,
          callingHoursStart: hoursStartInput,
          callingHoursEnd: hoursEndInput,
        };
      }
      return p;
    });

    setRoster(updatedRoster);

    // Save agent details to backend
    const payload = {
      name: nameInput,
      persona_config: {
        agent_name: nameInput,
        role: roleInput,
        voice: voiceInput,
        tone: toneInput,
        timezone: timezoneInput,
        calling_hours_start: hoursStartInput,
        calling_hours_end: hoursEndInput,
        is_active: true,
        company_name: "Visoora"
      }
    };

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/agents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": "acme_tenant"
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        await fetchRoster();
      }
    } catch (err) {
      console.error("Failed to save agent to backend API:", err);
    }

    // If saving the active profile, trigger saveProgress & completeOnboarding sync
    const active = updatedRoster.find((p) => p.isActive);
    if (active && state.step3) {
      const updatedStep3 = {
        ...state.step3,
        agentName: active.name,
        voice: active.voice,
        tone: active.tone,
        timezone: active.timezone,
        callingHoursStart: active.callingHoursStart,
        callingHoursEnd: active.callingHoursEnd,
      };

      const mergedState = {
        ...state,
        step3: updatedStep3,
      };

      await saveProgress(mergedState);

      // Trigger sync completion
      try {
        await fetch(`${BACKEND_URL}/api/onboarding/complete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tenant_id: "default_shared_tenant",
            company_name: state.step1?.companyName || "Unknown",
            website: state.step1?.website || "",
            industry: state.step1?.industry || "",
            team_size: state.step1?.teamSize || "",
            annual_revenue: state.step1?.annualRevenue || "",
            target_region: state.step1?.targetRegion || "",
            phone_number: state.step2?.twilioNumber || "",
            agent_name: updatedStep3.agentName,
            company_description: updatedStep3.companyDescription,
            value_proposition: updatedStep3.valueProposition,
            voice: updatedStep3.voice,
            tone: updatedStep3.tone,
            timezone: updatedStep3.timezone,
            calling_hours_start: updatedStep3.callingHoursStart,
            calling_hours_end: updatedStep3.callingHoursEnd,
            product_name: updatedStep3.productName,
            product_price: updatedStep3.productPrice,
            product_features: updatedStep3.productFeatures,
            target_audience: updatedStep3.targetAudience,
            kb_description: updatedStep3.kbDescription,
            kb_faqs: updatedStep3.kbFaqs,
            objections_list: updatedStep3.objectionsList,
            recording_disclosure: state.step4?.recordingDisclosure || false,
            consent_confirmed: state.step4?.consentConfirmed || false,
            country: state.step4?.country || "US",
            import_source: state.step5?.importSource || "csv",
            campaign_goal: state.step5?.campaignGoal || "",
            playbook_greeting: state.step5?.playbookGreeting || "",
            playbook_booking_link: state.step5?.playbookBookingLink || "",
          }),
        });
      } catch (err) {
        console.warn("DB update failed: ", err);
      }
    }

    setIsSaving(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };


  const handleDeleteProfile = (id: string) => {
    const deleted = roster.find((p) => p.id === id);
    if (deleted?.isActive) return; // Cannot delete deployed agent
    setRoster(roster.filter((p) => p.id !== id));
    if (selectedProfileId === id) {
      handleSelectProfile("active_profile");
    }
  };

  if (!mounted) return null;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            AI Employee Center
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>
            Identify, train, and schedule your digital personnel roster.
          </p>
        </div>
        <button
          onClick={handleAddNewDraft}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white"
          style={{ background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))" }}
        >
          <Plus className="w-3.5 h-3.5" /> Recruit New AI Employee
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Roster List (Left Column) */}
        <div className="flex flex-col gap-4">
          <div className="rounded-xl border p-5 flex flex-col gap-4" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
            <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
              Digital Roster
            </h2>
            <div className="space-y-3">
              {roster.map((p) => (
                <div
                  key={p.id}
                  onClick={() => handleSelectProfile(p.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all flex items-start gap-3 relative hover:bg-white/[0.01] ${
                    selectedProfileId === p.id ? "ring-1" : ""
                  }`}
                  style={{
                    background: selectedProfileId === p.id ? "hsl(var(--surface-2))" : "hsl(var(--surface-2))",
                    borderColor: selectedProfileId === p.id ? "hsl(var(--brand-primary))" : "hsl(var(--border-subtle))",
                  }}
                >
                  <div className="w-10 h-10 rounded-full flex items-center justify-center bg-white/5 border text-white flex-shrink-0" style={{ borderColor: "hsl(var(--border-default))" }}>
                    <Bot className="w-5 h-5 text-[hsl(var(--brand-primary))]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold truncate" style={{ color: "hsl(var(--text-primary))" }}>{p.name}</p>
                    <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>{p.role} · {p.tone}</p>
                    <div className="mt-2 flex items-center gap-1.5">
                      {p.isActive ? (
                        <span className="text-[9px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded flex items-center gap-1">
                          <UserCheck className="w-3 h-3" /> Deployed
                        </span>
                      ) : (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleActivateProfile(p.id);
                          }}
                          className="text-[9px] font-bold uppercase tracking-wider text-amber-400 hover:text-white bg-amber-500/15 hover:bg-amber-500 px-1.5 py-0.5 rounded transition-all"
                        >
                          Deploy
                        </button>
                      )}
                    </div>
                  </div>
                  {!p.isActive && p.id !== "active_profile" && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteProfile(p.id);
                      }}
                      className="absolute top-2 right-2 text-red-400 opacity-60 hover:opacity-100 transition-opacity"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Configuration Panel (Right 2 Columns) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="rounded-xl border p-6 flex flex-col gap-6" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
            <div className="flex items-center justify-between pb-4 border-b" style={{ borderColor: "hsl(var(--border-subtle))" }}>
              <div>
                <h3 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
                  Employee Config: {roster.find((p) => p.id === selectedProfileId)?.name || "Alex"}
                </h3>
                <p className="text-[11px]" style={{ color: "hsl(var(--text-muted))" }}>
                  Configure voice details, behavioral profile templates, and shift hours.
                </p>
              </div>
              <button
                onClick={handleSaveProfileSettings}
                disabled={isSaving}
                className="flex items-center gap-1 px-4 py-2 rounded-lg text-xs font-semibold text-white transition-all"
                style={{
                  background: saveSuccess
                    ? "hsl(var(--success))"
                    : "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
                }}
              >
                {saveSuccess ? <Award className="w-3.5 h-3.5" /> : <Settings className="w-3.5 h-3.5 animate-spin-slow" />}
                {saveSuccess ? "Changes Saved!" : "Save Profile"}
              </button>
            </div>

            {/* Profile fields form */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                  AI Employee Name
                </label>
                <input
                  type="text"
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))]"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                  Call Center Role
                </label>
                <select
                  value={roleInput}
                  onChange={(e) => setRoleInput(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm border outline-none"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                >
                  {roleTemplates.map((t) => (
                    <option key={t.id} value={t.id}>{t.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Role Template Details Banner */}
            <div className="p-3.5 rounded-lg border text-xs leading-relaxed" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}>
              <span className="font-semibold text-emerald-400 block mb-1">Role Description:</span>
              <span style={{ color: "hsl(var(--text-secondary))" }}>
                {roleTemplates.find((t) => t.id === roleInput)?.desc}
              </span>
            </div>

            {/* Voice Profile Picker */}
            <div className="flex flex-col gap-2.5">
              <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                Conversational Voice
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {voiceProfiles.map((v) => {
                  const isSel = voiceInput === v.id;
                  const isPlaying = playingVoice === v.id;
                  return (
                    <div
                      key={v.id}
                      onClick={() => setVoiceInput(v.id)}
                      className="p-3 border rounded-lg cursor-pointer transition-all flex items-center justify-between hover:bg-white/[0.01]"
                      style={{
                        background: isSel ? "hsla(var(--brand-primary), 0.05)" : "hsl(var(--surface-2))",
                        borderColor: isSel ? "hsl(var(--brand-primary))" : "hsl(var(--border-default))",
                      }}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handlePlayVoice(v.id, v.audio);
                          }}
                          className="w-6 h-6 rounded-full flex items-center justify-center bg-white/10 hover:bg-white/20 text-white flex-shrink-0"
                        >
                          {isPlaying ? (
                            <Pause className="w-2.5 h-2.5 text-[hsl(var(--brand-primary))]" />
                          ) : (
                            <Play className="w-2.5 h-2.5 text-white ml-0.5" />
                          )}
                        </button>
                        <div className="min-w-0">
                          <p className="text-[11px] font-bold truncate" style={{ color: "hsl(var(--text-primary))" }}>{v.name}</p>
                          <p className="text-[9px] truncate" style={{ color: "hsl(var(--text-muted))" }}>{v.desc}</p>
                        </div>
                      </div>
                      {isSel && <CheckCircle2 className="w-3.5 h-3.5 text-[hsl(var(--brand-primary))]" />}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Tone picker */}
            <div className="flex flex-col gap-2.5">
              <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                AI Behavioral Tone
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {toneProfiles.map((t) => {
                  const isSel = toneInput === t.id;
                  return (
                    <div
                      key={t.id}
                      onClick={() => setToneInput(t.id)}
                      className="p-3 border rounded-lg cursor-pointer transition-all flex items-start gap-2.5 text-left"
                      style={{
                        background: isSel ? "hsla(var(--brand-primary), 0.05)" : "hsl(var(--surface-2))",
                        borderColor: isSel ? "hsl(var(--brand-primary))" : "hsl(var(--border-default))",
                      }}
                    >
                      <div className="w-4 h-4 rounded-full border flex items-center justify-center mt-0.5 flex-shrink-0" style={{ borderColor: isSel ? "hsl(var(--brand-primary))" : "hsl(var(--border-default))" }}>
                        {isSel && <div className="w-2.5 h-2.5 rounded-full bg-[hsl(var(--brand-primary))]" />}
                      </div>
                      <div>
                        <p className="text-xs font-bold" style={{ color: "hsl(var(--text-primary))" }}>{t.label}</p>
                        <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>{t.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Scheduled shifts calling hours */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold flex items-center gap-1" style={{ color: "hsl(var(--text-secondary))" }}>
                  <Globe className="w-3.5 h-3.5" /> Shift Timezone
                </label>
                <select
                  value={timezoneInput}
                  onChange={(e) => setTimezoneInput(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm border outline-none"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                >
                  <option value="America/New_York">Eastern Time (ET)</option>
                  <option value="America/Chicago">Central Time (CT)</option>
                  <option value="America/Denver">Mountain Time (MT)</option>
                  <option value="America/Los_Angeles">Pacific Time (PT)</option>
                  <option value="UTC">Universal Coordinated (UTC)</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold flex items-center gap-1" style={{ color: "hsl(var(--text-secondary))" }}>
                  <Clock className="w-3.5 h-3.5" /> Shift Start Hour
                </label>
                <input
                  type="time"
                  value={hoursStartInput}
                  onChange={(e) => setHoursStartInput(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm border outline-none"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold flex items-center gap-1" style={{ color: "hsl(var(--text-secondary))" }}>
                  <Clock className="w-3.5 h-3.5" /> Shift End Hour
                </label>
                <input
                  type="time"
                  value={hoursEndInput}
                  onChange={(e) => setHoursEndInput(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm border outline-none"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
