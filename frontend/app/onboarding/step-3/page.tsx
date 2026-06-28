"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Bot, Play, Pause, ArrowLeft, ArrowRight, Check, 
  Volume2, Clock, Globe, FileText, AlertCircle, Plus, Trash2, 
  Package, HelpCircle, ShieldAlert, Sparkles 
} from "lucide-react";
import { useOnboardingStore } from "../store";
import { step3Schema, type Step3Data } from "../schemas";

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

export default function Step3Page() {
  const router = useRouter();
  const { state, updateStep3, setStep } = useOnboardingStore();
  const [activeTab, setActiveTab] = useState<"persona" | "product" | "kb" | "objections">("persona");
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const {
    register,
    control,
    handleSubmit,
    setValue,
    watch,
    trigger,
    formState: { errors },
  } = useForm<Step3Data>({
    resolver: zodResolver(step3Schema),
    defaultValues: state.step3 || {
      agentName: "Alex",
      companyDescription: "",
      valueProposition: "",
      voice: "rachel",
      tone: "consultative",
      timezone: "America/New_York",
      callingHoursStart: "08:00",
      callingHoursEnd: "17:00",
      productName: "",
      productPrice: "",
      productFeatures: "",
      targetAudience: "",
      kbDescription: "",
      kbFaqs: [
        { question: "What is your pricing model?", answer: "Pricing starts at $199/month for our growth plan, covering unlimited calling and direct CRM integrations." },
        { question: "How long does setup take?", answer: "Setup takes less than 10 minutes. You can claim a Twilio number and start dialing instantly." }
      ],
      objectionsList: [
        { objection: "Pricing is too expensive.", rebuttal: "I understand. Many clients start where you are but see immediate ROI through 40% higher bookings." },
        { objection: "AI sounds too mechanical.", rebuttal: "That's a fair point, but our agents match natural human speech patterns and pauses in real-time." }
      ]
    },
  });

  const selectedVoice = watch("voice");
  const selectedTone = watch("tone");

  const { fields: faqFields, append: appendFaq, remove: removeFaq } = useFieldArray({
    control,
    name: "kbFaqs"
  });

  const { fields: objectionFields, append: appendObjection, remove: removeObjection } = useFieldArray({
    control,
    name: "objectionsList"
  });

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
      setTimeout(() => setPlayingVoice(null), 2500);
    });

    audioRef.current.onended = () => {
      setPlayingVoice(null);
    };
  };

  const handleSelectVoice = (voiceId: string) => {
    setValue("voice", voiceId);
  };

  const handleSelectTone = (toneId: string) => {
    setValue("tone", toneId);
  };

  const validateAndNextTab = async (next: "persona" | "product" | "kb" | "objections") => {
    // Validate current tab fields before moving forward
    let fieldsToValidate: any[] = [];
    if (activeTab === "persona") {
      fieldsToValidate = ["agentName", "companyDescription", "valueProposition", "voice", "tone", "timezone", "callingHoursStart", "callingHoursEnd"];
    } else if (activeTab === "product") {
      fieldsToValidate = ["productName", "productPrice", "productFeatures", "targetAudience"];
    }
    
    if (fieldsToValidate.length > 0) {
      const isValid = await trigger(fieldsToValidate);
      if (!isValid) return; // Do not switch tab if validations fail
    }

    setActiveTab(next);
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
          Train your AI SDR Employee
        </h1>
        <p className="text-xs mt-1" style={{ color: "hsl(var(--text-muted))" }}>
          Step 3 of 6 · Configure persona, tone, product catalog details, custom FAQs, and objection handling rules.
        </p>
      </div>

      {/* Sub-Tabs Navigation */}
      <div className="flex border-b overflow-x-auto gap-2" style={{ borderColor: "hsl(var(--border-subtle))" }}>
        <button
          type="button"
          onClick={() => validateAndNextTab("persona")}
          className={`px-4 py-2 text-xs font-bold transition-all border-b-2 whitespace-nowrap flex items-center gap-1.5`}
          style={{
            borderColor: activeTab === "persona" ? "hsl(var(--brand-primary))" : "transparent",
            color: activeTab === "persona" ? "hsl(var(--text-primary))" : "hsl(var(--text-secondary))",
          }}
        >
          <Bot className="w-4 h-4" /> AI Persona
        </button>
        <button
          type="button"
          onClick={() => validateAndNextTab("product")}
          className={`px-4 py-2 text-xs font-bold transition-all border-b-2 whitespace-nowrap flex items-center gap-1.5`}
          style={{
            borderColor: activeTab === "product" ? "hsl(var(--brand-primary))" : "transparent",
            color: activeTab === "product" ? "hsl(var(--text-primary))" : "hsl(var(--text-secondary))",
          }}
        >
          <Package className="w-4 h-4" /> Product Details
        </button>
        <button
          type="button"
          onClick={() => validateAndNextTab("kb")}
          className={`px-4 py-2 text-xs font-bold transition-all border-b-2 whitespace-nowrap flex items-center gap-1.5`}
          style={{
            borderColor: activeTab === "kb" ? "hsl(var(--brand-primary))" : "transparent",
            color: activeTab === "kb" ? "hsl(var(--text-primary))" : "hsl(var(--text-secondary))",
          }}
        >
          <HelpCircle className="w-4 h-4" /> Knowledge Base
        </button>
        <button
          type="button"
          onClick={() => validateAndNextTab("objections")}
          className={`px-4 py-2 text-xs font-bold transition-all border-b-2 whitespace-nowrap flex items-center gap-1.5`}
          style={{
            borderColor: activeTab === "objections" ? "hsl(var(--brand-primary))" : "transparent",
            color: activeTab === "objections" ? "hsl(var(--text-primary))" : "hsl(var(--text-secondary))",
          }}
        >
          <ShieldAlert className="w-4 h-4" /> Objection Handling
        </button>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">
        
        {/* TAB 1: AI PERSONA */}
        {activeTab === "persona" && (
          <div className="flex flex-col gap-6">
            
            {/* Identity & Tone Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                  AI Employee Name
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
                  Core Value Hook
                </label>
                <div className="relative">
                  <FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "hsl(var(--text-muted))" }} />
                  <input
                    type="text"
                    placeholder="We automate sales prospecting by booking 40% more demos."
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

            {/* Company Description */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                Company Knowledge Summary (SDR context - 2-3 sentences)
              </label>
              <textarea
                rows={2}
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

            {/* Voices Grid */}
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
                      }}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handlePlayVoice(v.id, v.audio);
                          }}
                          className="w-7 h-7 rounded-full flex items-center justify-center bg-white/10 hover:bg-white/20 text-white flex-shrink-0"
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
                      {isSel && <Check className="w-4 h-4 text-[hsl(var(--brand-primary))]" />}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Tone Profiles Selection */}
            <div className="flex flex-col gap-2.5">
              <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                AI Conversational Tone
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {toneProfiles.map((t) => {
                  const isSel = selectedTone === t.id;
                  return (
                    <div
                      key={t.id}
                      onClick={() => handleSelectTone(t.id)}
                      className="p-3 rounded-lg border cursor-pointer transition-all flex gap-3 text-left items-start"
                      style={{
                        background: isSel ? "hsla(var(--brand-primary), 0.05)" : "hsl(var(--surface-2))",
                        borderColor: isSel ? "hsl(var(--brand-primary))" : "hsl(var(--border-default))",
                      }}
                    >
                      <div
                        className="w-4 h-4 rounded-full border flex items-center justify-center mt-0.5 flex-shrink-0"
                        style={{ borderColor: isSel ? "hsl(var(--brand-primary))" : "hsl(var(--border-default))" }}
                      >
                        {isSel && <div className="w-2 h-2 rounded-full bg-[hsl(var(--brand-primary))]" />}
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

            {/* Calling Hours & Timezone */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold flex items-center gap-1" style={{ color: "hsl(var(--text-secondary))" }}>
                  <Globe className="w-3.5 h-3.5" /> Calling Timezone
                </label>
                <select
                  {...register("timezone")}
                  className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}
                >
                  <option value="America/New_York">Eastern Time (ET)</option>
                  <option value="America/Chicago">Central Time (CT)</option>
                  <option value="America/Denver">Mountain Time (MT)</option>
                  <option value="America/Los_Angeles">Pacific Time (PT)</option>
                  <option value="UTC">Coordinated Universal Time (UTC)</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold flex items-center gap-1" style={{ color: "hsl(var(--text-secondary))" }}>
                  <Clock className="w-3.5 h-3.5" /> Hours Start
                </label>
                <select
                  {...register("callingHoursStart")}
                  className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}
                >
                  <option value="08:00">8:00 AM (Recommended)</option>
                  <option value="09:00">9:00 AM</option>
                  <option value="10:00">10:00 AM</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold flex items-center gap-1" style={{ color: "hsl(var(--text-secondary))" }}>
                  <Clock className="w-3.5 h-3.5" /> Hours End
                </label>
                <select
                  {...register("callingHoursEnd")}
                  className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}
                >
                  <option value="17:00">5:00 PM (Recommended)</option>
                  <option value="18:00">6:00 PM</option>
                  <option value="20:00">8:00 PM</option>
                  <option value="21:00">9:00 PM (Max Limit)</option>
                </select>
              </div>
            </div>

            <button
              type="button"
              onClick={() => validateAndNextTab("product")}
              className="flex items-center justify-center gap-1.5 mt-2 px-5 py-2.5 rounded-lg text-xs font-semibold text-white bg-[hsl(var(--brand-primary))] self-end"
            >
              Continue to Product Details <ArrowRight className="w-4 h-4" />
            </button>

          </div>
        )}

        {/* TAB 2: PRODUCT DETAILS */}
        {activeTab === "product" && (
          <div className="flex flex-col gap-5">
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                  Product/Service Name
                </label>
                <input
                  type="text"
                  placeholder="Starter Package / Consulting Plan"
                  {...register("productName")}
                  className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
                  style={{
                    background: "hsl(var(--surface-2))",
                    borderColor: errors.productName ? "hsl(var(--danger))" : "hsl(var(--border-default))",
                    color: "hsl(var(--text-primary))",
                  }}
                />
                {errors.productName && (
                  <span className="text-[11px] font-semibold flex items-center gap-1" style={{ color: "hsl(var(--danger))" }}>
                    <AlertCircle className="w-3.5 h-3.5" /> {errors.productName.message}
                  </span>
                )}
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                  Pricing Model (e.g. $49/mo, $500 one-time)
                </label>
                <input
                  type="text"
                  placeholder="$199/month billed annually"
                  {...register("productPrice")}
                  className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
                  style={{
                    background: "hsl(var(--surface-2))",
                    borderColor: errors.productPrice ? "hsl(var(--danger))" : "hsl(var(--border-default))",
                    color: "hsl(var(--text-primary))",
                  }}
                />
                {errors.productPrice && (
                  <span className="text-[11px] font-semibold flex items-center gap-1" style={{ color: "hsl(var(--danger))" }}>
                    <AlertCircle className="w-3.5 h-3.5" /> {errors.productPrice.message}
                  </span>
                )}
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                Core Features Description (TTS quote factual RAG source)
              </label>
              <textarea
                rows={2}
                placeholder="Includes 24/7 outbound dialing, HubSpot contact sync, pre-configured TCPA disclosures, and live call sentiment dashboards."
                {...register("productFeatures")}
                className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none resize-none"
                style={{
                  background: "hsl(var(--surface-2))",
                  borderColor: errors.productFeatures ? "hsl(var(--danger))" : "hsl(var(--border-default))",
                  color: "hsl(var(--text-primary))",
                }}
              />
              {errors.productFeatures && (
                <span className="text-[11px] font-semibold flex items-center gap-1" style={{ color: "hsl(var(--danger))" }}>
                  <AlertCircle className="w-3.5 h-3.5" /> {errors.productFeatures.message}
                </span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                Ideal Buyer Personas & Target Audience
              </label>
              <textarea
                rows={2}
                placeholder="Our ideal buyers are marketing agency founders, VP of sales at B2B startups, and outbound lead generation managers."
                {...register("targetAudience")}
                className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none resize-none"
                style={{
                  background: "hsl(var(--surface-2))",
                  borderColor: errors.targetAudience ? "hsl(var(--danger))" : "hsl(var(--border-default))",
                  color: "hsl(var(--text-primary))",
                }}
              />
              {errors.targetAudience && (
                <span className="text-[11px] font-semibold flex items-center gap-1" style={{ color: "hsl(var(--danger))" }}>
                  <AlertCircle className="w-3.5 h-3.5" /> {errors.targetAudience.message}
                </span>
              )}
            </div>

            <div className="flex items-center justify-between gap-4 mt-2">
              <button
                type="button"
                onClick={() => setActiveTab("persona")}
                className="flex items-center gap-1 px-4 py-2 rounded-lg text-xs font-semibold border"
                style={{ borderColor: "hsl(var(--border-default))" }}
              >
                Back to Persona
              </button>
              <button
                type="button"
                onClick={() => validateAndNextTab("kb")}
                className="flex items-center gap-1.5 px-5 py-2 rounded-lg text-xs font-semibold text-white bg-[hsl(var(--brand-primary))]"
              >
                Continue to Knowledge Base <ArrowRight className="w-4 h-4" />
              </button>
            </div>

          </div>
        )}

        {/* TAB 3: KNOWLEDGE BASE & FAQS */}
        {activeTab === "kb" && (
          <div className="flex flex-col gap-4">
            
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                Custom Knowledge Wiki Context (Optional RAG text)
              </label>
              <textarea
                rows={2}
                placeholder="Paste any corporate PDF, policy details, or company documentation here to enrich the AI employee's memory..."
                {...register("kbDescription")}
                className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none resize-none"
                style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}
              />
            </div>

            <div className="flex flex-col gap-2.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                  AI Grounding FAQs
                </label>
                <button
                  type="button"
                  onClick={() => appendFaq({ question: "", answer: "" })}
                  className="flex items-center gap-1 text-[10px] font-bold text-emerald-400 border border-dashed border-emerald-500/30 px-2.5 py-1 rounded"
                >
                  <Plus className="w-3 h-3" /> Add FAQ
                </button>
              </div>

              {faqFields.length === 0 ? (
                <div className="p-4 rounded-lg border border-dashed text-center text-xs" style={{ borderColor: "hsl(var(--border-default))" }}>
                  No custom FAQs defined. Add a question/answer to ground AI responses.
                </div>
              ) : (
                <div className="flex flex-col gap-3 max-h-[260px] overflow-y-auto pr-1">
                  {faqFields.map((field, idx) => (
                    <div key={field.id} className="p-3.5 rounded-lg border flex flex-col gap-2 relative" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}>
                      <button
                        type="button"
                        onClick={() => removeFaq(idx)}
                        className="absolute right-2 top-2 p-1 text-rose-400 hover:bg-white/5 rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                      
                      <div className="flex flex-col gap-1.5">
                        <span className="text-[9px] font-bold uppercase tracking-wider text-neutral-400">Question #{idx + 1}</span>
                        <input
                          type="text"
                          placeholder="e.g. Do you support native Salesforce sync?"
                          {...register(`kbFaqs.${idx}.question` as const)}
                          className="w-full px-2.5 py-1.5 rounded text-xs border outline-none"
                          style={{ background: "hsl(var(--surface-3))", borderColor: "hsl(var(--border-subtle))" }}
                        />
                      </div>
                      
                      <div className="flex flex-col gap-1.5">
                        <span className="text-[9px] font-bold uppercase tracking-wider text-neutral-400">Answer</span>
                        <textarea
                          rows={2}
                          placeholder="e.g. Yes, we support Salesforce out of the box."
                          {...register(`kbFaqs.${idx}.answer` as const)}
                          className="w-full px-2.5 py-1.5 rounded text-xs border outline-none resize-none"
                          style={{ background: "hsl(var(--surface-3))", borderColor: "hsl(var(--border-subtle))" }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between gap-4 mt-2">
              <button
                type="button"
                onClick={() => setActiveTab("product")}
                className="flex items-center gap-1 px-4 py-2 rounded-lg text-xs font-semibold border"
                style={{ borderColor: "hsl(var(--border-default))" }}
              >
                Back to Product
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("objections")}
                className="flex items-center gap-1.5 px-5 py-2 rounded-lg text-xs font-semibold text-white bg-[hsl(var(--brand-primary))]"
              >
                Continue to Objections <ArrowRight className="w-4 h-4" />
              </button>
            </div>

          </div>
        )}

        {/* TAB 4: OBJECTION HANDLING */}
        {activeTab === "objections" && (
          <div className="flex flex-col gap-4">
            
            <div className="flex flex-col gap-2.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                  AI Objection Handling Rebuttals
                </label>
                <button
                  type="button"
                  onClick={() => appendObjection({ objection: "", rebuttal: "" })}
                  className="flex items-center gap-1 text-[10px] font-bold text-emerald-400 border border-dashed border-emerald-500/30 px-2.5 py-1 rounded"
                >
                  <Plus className="w-3 h-3" /> Add Objection
                </button>
              </div>

              {objectionFields.length === 0 ? (
                <div className="p-4 rounded-lg border border-dashed text-center text-xs" style={{ borderColor: "hsl(var(--border-default))" }}>
                  No objections mapped.
                </div>
              ) : (
                <div className="flex flex-col gap-3 max-h-[280px] overflow-y-auto pr-1">
                  {objectionFields.map((field, idx) => (
                    <div key={field.id} className="p-3.5 rounded-lg border flex flex-col gap-2 relative" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}>
                      <button
                        type="button"
                        onClick={() => removeObjection(idx)}
                        className="absolute right-2 top-2 p-1 text-rose-400 hover:bg-white/5 rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                      
                      <div className="flex flex-col gap-1.5">
                        <span className="text-[9px] font-bold uppercase tracking-wider text-neutral-400">Trigger phrase (What the customer says)</span>
                        <input
                          type="text"
                          placeholder="e.g. We don't have budget."
                          {...register(`objectionsList.${idx}.objection` as const)}
                          className="w-full px-2.5 py-1.5 rounded text-xs border outline-none"
                          style={{ background: "hsl(var(--surface-3))", borderColor: "hsl(var(--border-subtle))" }}
                        />
                      </div>
                      
                      <div className="flex flex-col gap-1.5">
                        <span className="text-[9px] font-bold uppercase tracking-wider text-neutral-400">AI Rebuttal pivot response</span>
                        <textarea
                          rows={2}
                          placeholder="e.g. I hear you. The Growth Pack pays for itself by booking 40% more demos."
                          {...register(`objectionsList.${idx}.rebuttal` as const)}
                          className="w-full px-2.5 py-1.5 rounded text-xs border outline-none resize-none"
                          style={{ background: "hsl(var(--surface-3))", borderColor: "hsl(var(--border-subtle))" }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between gap-4 mt-2">
              <button
                type="button"
                onClick={() => setActiveTab("kb")}
                className="flex items-center gap-1 px-4 py-2 rounded-lg text-xs font-semibold border"
                style={{ borderColor: "hsl(var(--border-default))" }}
              >
                Back to KB
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

          </div>
        )}

      </form>
    </motion.div>
  );
}
