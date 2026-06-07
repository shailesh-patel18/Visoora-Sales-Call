"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Bot, Play, Pause, ArrowLeft, ArrowRight, Check, Volume2, Clock, Globe, FileText, AlertCircle } from "lucide-react";
import { useOnboardingStore } from "../store";
import { step3Schema, type Step3Data } from "../schemas";

const voiceProfiles = [
  { id: "rachel", name: "Rachel", gender: "Female", accent: "US", desc: "Warm & Professional", audio: "https://actions.google.com/sounds/v1/science_fiction/teleport.ogg" },
  { id: "drew", name: "Drew", gender: "Male", accent: "US", desc: "Friendly & Casual", audio: "https://actions.google.com/sounds/v1/impacts/crash.ogg" },
  { id: "clyde", name: "Clyde", gender: "Male", accent: "UK", desc: "Energetic & Assertive", audio: "https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg" },
  { id: "paul", name: "Paul", gender: "Male", accent: "US", desc: "Corporate & Technical", audio: "https://actions.google.com/sounds/v1/science_fiction/alien_beacon.ogg" },
  { id: "charlotte", name: "Charlotte", gender: "Female", accent: "AU", desc: "Helpful & Direct", audio: "https://actions.google.com/sounds/v1/ambiences/morning_birds.ogg" },
];

export default function Step3Page() {
  const router = useRouter();
  const { state, updateStep3, setStep } = useOnboardingStore();
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);
  const [activeCatalogTab, setActiveCatalogTab] = useState<"manual" | "csv">("manual");
  const [productsCatalog, setProductsCatalog] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<Step3Data>({
    resolver: zodResolver(step3Schema),
    defaultValues: state.step3 || {
      agentName: "Alex",
      companyDescription: "",
      valueProposition: "",
      voice: "rachel",
      timezone: "America/New_York",
      callingHoursStart: "08:00",
      callingHoursEnd: "17:00",
    },
  });

  const selectedVoice = watch("voice");

  useEffect(() => {
    setStep(3);
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  const handlePlayVoice = (voiceId: string, audioUrl: string) => {
    if (playingVoice === voiceId) {
      if (audioRef.current) audioRef.current.pause();
      setPlayingVoice(null);
      return;
    }

    if (audioRef.current) {
      audioRef.current.pause();
    }

    setPlayingVoice(voiceId);
    audioRef.current = new Audio(audioUrl);
    audioRef.current.volume = 0.5;
    audioRef.current.play().catch((err) => {
      console.warn("Audio play failed:", err);
      // Fail gracefully: mock audio playback visual state and stop after 2s
      setTimeout(() => setPlayingVoice(null), 2500);
    });

    audioRef.current.onended = () => {
      setPlayingVoice(null);
    };
  };

  const handleSelectVoice = (voiceId: string) => {
    setValue("voice", voiceId);
  };

  const onSubmit = async (data: Step3Data) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    await updateStep3(data);
    router.push("/onboarding/step-4");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.3 }}
      className="glass p-6 md:p-8 rounded-xl border flex flex-col gap-6"
      style={{ borderColor: "hsl(var(--border-subtle))" }}
    >
      <div>
        <h1 className="text-xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
          Configure your AI Sales Agent persona
        </h1>
        <p className="text-xs mt-1" style={{ color: "hsl(var(--text-muted))" }}>
          Step 3 of 6 · Give your agent a personality, pitch parameters, and a conversational voice.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">
        
        {/* Agent Name & Identity */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
              Agent Identity Name
            </label>
            <div className="relative">
              <Bot className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "hsl(var(--text-muted))" }} />
              <input
                type="text"
                placeholder="Alex"
                {...register("agentName")}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))] transition-all"
                style={{
                  background: "hsl(var(--surface-2))",
                  borderColor: errors.agentName ? "hsl(var(--danger))" : "hsl(var(--border-default))",
                  color: "hsl(var(--text-primary))",
                }}
              />
            </div>
            {errors.agentName && (
              <span className="text-[11px] font-semibold flex items-center gap-1" style={{ color: "hsl(var(--danger))" }}>
                <AlertCircle className="w-3.5 h-3.5" /> {errors.agentName.message}
              </span>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
              Value Proposition (AI Pitch Hook)
            </label>
            <div className="relative">
              <FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "hsl(var(--text-muted))" }} />
              <input
                type="text"
                placeholder="We automate sales prospecting by 90% using outbound voice calls."
                {...register("valueProposition")}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))] transition-all"
                style={{
                  background: "hsl(var(--surface-2))",
                  borderColor: errors.valueProposition ? "hsl(var(--danger))" : "hsl(var(--border-default))",
                  color: "hsl(var(--text-primary))",
                }}
              />
            </div>
            {errors.valueProposition && (
              <span className="text-[11px] font-semibold flex items-center gap-1" style={{ color: "hsl(var(--danger))" }}>
                <AlertCircle className="w-3.5 h-3.5" /> {errors.valueProposition.message}
              </span>
            )}
          </div>
        </div>

        {/* Company Prompt Context */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
            Company Knowledge Summary (Prompt context — 2-3 sentences)
          </label>
          <textarea
            rows={3}
            placeholder="Visoora is a modern software platform that helps businesses schedule calls and automate lead generation. We target busy marketing agencies and offer a 14-day free trial."
            {...register("companyDescription")}
            className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))] transition-all resize-none"
            style={{
              background: "hsl(var(--surface-2))",
              borderColor: errors.companyDescription ? "hsl(var(--danger))" : "hsl(var(--border-default))",
              color: "hsl(var(--text-primary))",
            }}
          />
          {errors.companyDescription && (
            <span className="text-[11px] font-semibold flex items-center gap-1" style={{ color: "hsl(var(--danger))" }}>
              <AlertCircle className="w-3.5 h-3.5" /> {errors.companyDescription.message}
            </span>
          )}
        </div>

        {/* Voices Profile Grid */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
            Conversational Voice Profile
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {voiceProfiles.map((v) => {
              const isSel = selectedVoice === v.id;
              const isPlaying = playingVoice === v.id;
              
              return (
                <div
                  key={v.id}
                  onClick={() => handleSelectVoice(v.id)}
                  className="flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all hover:bg-white/[0.01]"
                  style={{
                    background: isSel ? "hsla(var(--brand-primary), 0.05)" : "hsl(var(--surface-2))",
                    borderColor: isSel ? "hsl(var(--brand-primary))" : "hsl(var(--border-default))",
                    boxShadow: isSel ? "0 0 10px -2px hsla(var(--brand-primary), 0.15)" : "none",
                  }}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePlayVoice(v.id, v.audio);
                      }}
                      className="w-7 h-7 rounded-full flex items-center justify-center transition-all bg-white/10 hover:bg-white/20 text-white flex-shrink-0"
                    >
                      {isPlaying ? (
                        <Pause className="w-3 h-3 text-[hsl(var(--brand-primary))] animate-pulse" />
                      ) : (
                        <Play className="w-3 h-3 text-white ml-0.5" />
                      )}
                    </button>
                    <div className="min-w-0">
                      <p className="text-xs font-bold truncate" style={{ color: "hsl(var(--text-primary))" }}>{v.name}</p>
                      <p className="text-[10px] truncate" style={{ color: "hsl(var(--text-muted))" }}>{v.desc}</p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <span className="text-[9px] px-1.5 py-0.5 rounded font-bold" style={{ background: "hsl(var(--surface-3))", color: "hsl(var(--text-secondary))" }}>
                      {v.accent} · {v.gender[0]}
                    </span>
                    {isSel && <Check className="w-3.5 h-3.5" style={{ color: "hsl(var(--brand-primary))" }} />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Products Catalog Uploader */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between pb-1 border-b" style={{ borderColor: "hsl(var(--border-subtle))" }}>
            <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
              Products & Services List (Used in AI objection handling)
            </label>
            <div className="flex gap-1.5">
              <button
                type="button"
                onClick={() => setActiveCatalogTab("manual")}
                className="text-[10px] font-bold px-2 py-0.5 rounded transition-all"
                style={{
                  background: activeCatalogTab === "manual" ? "hsl(var(--surface-3))" : "transparent",
                  color: activeCatalogTab === "manual" ? "hsl(var(--text-primary))" : "hsl(var(--text-secondary))",
                }}
              >
                Manual Entry
              </button>
              <button
                type="button"
                onClick={() => setActiveCatalogTab("csv")}
                className="text-[10px] font-bold px-2 py-0.5 rounded transition-all"
                style={{
                  background: activeCatalogTab === "csv" ? "hsl(var(--surface-3))" : "transparent",
                  color: activeCatalogTab === "csv" ? "hsl(var(--text-primary))" : "hsl(var(--text-secondary))",
                }}
              >
                CSV Upload
              </button>
            </div>
          </div>
          
          {activeCatalogTab === "manual" ? (
            <textarea
              rows={2}
              value={productsCatalog}
              onChange={(e) => setProductsCatalog(e.target.value)}
              placeholder="e.g. Starter Pack ($49/mo) — covers 10 campaigns; Agency Growth Pack ($199/mo) — covers unlimited campaigns."
              className="w-full px-3 py-2.5 rounded-lg text-xs border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))] transition-all resize-none"
              style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}
            />
          ) : (
            <div className="flex flex-col items-center justify-center p-6 border border-dashed rounded-lg text-center gap-2" style={{ borderColor: "hsl(var(--border-default))", background: "hsl(var(--surface-2))" }}>
              <Volume2 className="w-6 h-6 text-emerald-400 animate-pulse-live" />
              <div>
                <p className="text-xs font-bold" style={{ color: "hsl(var(--text-primary))" }}>Drag & drop products CSV file here</p>
                <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>Support .csv files up to 2MB (Manual fallback is active)</p>
              </div>
            </div>
          )}
        </div>

        {/* Calling Hours & Timezone */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          
          {/* Timezone */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold flex items-center gap-1" style={{ color: "hsl(var(--text-secondary))" }}>
              <Globe className="w-3.5 h-3.5" /> Calling Timezone
            </label>
            <select
              {...register("timezone")}
              className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))] transition-all"
              style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}
            >
              <option value="America/New_York">Eastern Time (ET)</option>
              <option value="America/Chicago">Central Time (CT)</option>
              <option value="America/Denver">Mountain Time (MT)</option>
              <option value="America/Los_Angeles">Pacific Time (PT)</option>
              <option value="UTC">Coordinated Universal Time (UTC)</option>
            </select>
          </div>

          {/* Calling Start */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold flex items-center gap-1" style={{ color: "hsl(var(--text-secondary))" }}>
              <Clock className="w-3.5 h-3.5" /> Allowed Hours Start
            </label>
            <select
              {...register("callingHoursStart")}
              className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))] transition-all"
              style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}
            >
              <option value="08:00">8:00 AM (Recommended)</option>
              <option value="09:00">9:00 AM</option>
              <option value="10:00">10:00 AM</option>
            </select>
          </div>

          {/* Calling End */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold flex items-center gap-1" style={{ color: "hsl(var(--text-secondary))" }}>
              <Clock className="w-3.5 h-3.5" /> Allowed Hours End
            </label>
            <select
              {...register("callingHoursEnd")}
              className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))] transition-all"
              style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}
            >
              <option value="17:00">5:00 PM (Recommended)</option>
              <option value="18:00">6:00 PM</option>
              <option value="20:00">8:00 PM</option>
              <option value="21:00">9:00 PM (Max Limit)</option>
            </select>
          </div>

        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-between gap-4 mt-2">
          <button
            type="button"
            onClick={() => router.push("/onboarding/step-2")}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-xs font-semibold transition-colors border hover:bg-white/[0.03]"
            style={{ borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-secondary))" }}
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back
          </button>

          <button
            type="submit"
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-semibold text-white transition-all hover:opacity-90"
            style={{
              background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
              boxShadow: "0 4px 20px -4px hsla(var(--brand-primary), 0.35)",
            }}
          >
            Verify Compliance <ArrowRight className="w-4 h-4" />
          </button>
        </div>

      </form>
    </motion.div>
  );
}
