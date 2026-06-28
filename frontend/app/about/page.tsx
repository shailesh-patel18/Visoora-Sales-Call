"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { 
  Zap, 
  Cpu, 
  ShieldCheck, 
  Terminal, 
  ArrowRight,
  Database,
  PhoneCall,
  Activity
} from "lucide-react";
import { PublicNavbar } from "../components/public-navbar";
import { PublicFooter } from "../components/public-footer";

export default function About() {
  return (
    <div className="min-h-screen bg-[hsl(var(--surface-0))] text-white selection:bg-[hsl(var(--brand-primary))]/30 relative overflow-hidden">
      <PublicNavbar />

      {/* Background Decorative Gradients */}
      <div className="absolute top-0 right-1/4 w-[500px] h-[500px] bg-[hsl(var(--brand-accent))]/5 rounded-full blur-[120px] pointer-events-none -z-10" />
      <div className="absolute top-[600px] left-1/4 w-[600px] h-[600px] bg-[hsl(var(--brand-primary))]/5 rounded-full blur-[150px] pointer-events-none -z-10" />

      {/* HEADER HERO */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col items-center text-center">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-4xl sm:text-5xl font-extrabold tracking-tight max-w-3xl leading-tight bg-clip-text text-transparent bg-gradient-to-b from-white via-zinc-200 to-zinc-500"
        >
          Bridging AI Reasoning and Telephony.
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mt-6 text-lg text-[hsl(var(--text-secondary))] max-w-2xl leading-relaxed"
        >
          Visoora was founded with a single mission: to allow businesses to deploy natural, human-grade voice agents that maintain strict regulatory compliance and enterprise security.
        </motion.p>
      </section>

      {/* MISSION & VISION */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900/60">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <div className="flex flex-col gap-4">
            <h2 className="text-sm font-bold uppercase tracking-widest text-[hsl(var(--brand-primary))]">Our Mission</h2>
            <h3 className="text-2xl font-bold">Safe, Scalable Conversations</h3>
            <p className="text-sm sm:text-base text-[hsl(var(--text-secondary))] leading-relaxed">
              We build systems that automate high-volume outbound dialing while ensuring consumer rights are respected. By enforcing automated timezone restrictions and checking regional DNC registries before dialing, Visoora makes voice-agent campaigns compliant by default.
            </p>
          </div>
          <div className="flex flex-col gap-4">
            <h2 className="text-sm font-bold uppercase tracking-widest text-[hsl(var(--brand-accent))]">Our Philosophy</h2>
            <h3 className="text-2xl font-bold">Deterministic Dialogue Controls</h3>
            <p className="text-sm sm:text-base text-[hsl(var(--text-secondary))] leading-relaxed">
              We do not deploy black-box autonomous agents that are prone to hallucinating pricing details or competitors. Visoora uses a Finite State Machine (FSM) configuration engine, ensuring that conversational agents always stay on-script and preserve brand integrity.
            </p>
          </div>
        </div>
      </section>

      {/* TECHNOLOGY STACK */}
      <section id="technology" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900/60">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-bold uppercase tracking-widest text-[hsl(var(--brand-primary))]">The Tech Stack</h2>
          <p className="mt-3 text-3xl font-extrabold tracking-tight">Engineered for Low Latency</p>
          <p className="mt-4 text-sm text-[hsl(var(--text-secondary))] leading-relaxed">
            Every step in Visoora's media processing pipeline is optimized for latency reduction, ensuring the conversation flows naturally.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="p-6 rounded-2xl border border-zinc-900 bg-zinc-900/10 flex flex-col gap-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400">
              <PhoneCall className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold">VoIP Streaming</h3>
            <p className="text-xs text-[hsl(var(--text-secondary))] leading-relaxed">
              Asynchronous event loop handler built on FastAPI. Transcodes raw G.711 $\mu$-law PCM binary payloads over WebSockets directly to Twilio.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-zinc-900 bg-zinc-900/10 flex flex-col gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold">STT Engine</h3>
            <p className="text-xs text-[hsl(var(--text-secondary))] leading-relaxed">
              Deepgram Nova-2 handles real-time audio chunk transcripts with built-in voice activity detection (VAD) energy monitoring.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-zinc-900 bg-zinc-900/10 flex flex-col gap-4">
            <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center text-violet-400">
              <Terminal className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold">FSM Reasoning</h3>
            <p className="text-xs text-[hsl(var(--text-secondary))] leading-relaxed">
              Google Gemini 2.0/2.5 Flash acts as the primary reasoning state-machine provider with OpenAI fallback handling objection flows.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-zinc-900 bg-zinc-900/10 flex flex-col gap-4">
            <div className="w-10 h-10 rounded-xl bg-zinc-500/10 flex items-center justify-center text-zinc-400">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold">Data Isolation</h3>
            <p className="text-xs text-[hsl(var(--text-secondary))] leading-relaxed">
              Multi-tenant security isolation enforced via Supabase Row Level Security (RLS) with resilient local JSON storage backups.
            </p>
          </div>
        </div>
      </section>

      {/* COMPLIANCE & SECURITY ROADMAP */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900/60">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-5 flex flex-col gap-4">
            <h2 className="text-sm font-bold uppercase tracking-widest text-[hsl(var(--brand-accent))]">Roadmap</h2>
            <h3 className="text-3xl font-extrabold tracking-tight">Security & Compliance Outlook</h3>
            <p className="text-sm text-[hsl(var(--text-secondary))] leading-relaxed">
              While our system contains implemented compliance parameters like timezone gating, we are planning security validations to extend enterprise trust.
            </p>
          </div>

          <div className="lg:col-span-7 p-6 rounded-2xl border border-zinc-900 bg-zinc-900/20 font-mono text-xs flex flex-col gap-4">
            <div className="flex items-center justify-between p-3 rounded-xl border border-zinc-800 bg-zinc-950/40">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span>TCPA Gating & Area Code Check</span>
              </div>
              <span className="text-[10px] text-emerald-400">FULLY IMPLEMENTED</span>
            </div>
            
            <div className="flex items-center justify-between p-3 rounded-xl border border-zinc-800 bg-zinc-950/40">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span>Local Do-Not-Call (DNC) Scrubber</span>
              </div>
              <span className="text-[10px] text-emerald-400">FULLY IMPLEMENTED</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl border border-zinc-800 bg-zinc-950/40 border-l-[hsl(var(--brand-primary))]">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[hsl(var(--brand-primary))] animate-pulse-live" />
                <span>SOC 2 Type II Validation Audit</span>
              </div>
              <span className="text-[10px] text-[hsl(var(--brand-primary))]">PLANNED (Q3 2026)</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl border border-zinc-800 bg-zinc-950/40 border-l-[hsl(var(--brand-primary))]">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[hsl(var(--brand-primary))] animate-pulse-live" />
                <span>HIPAA & HITECH Business Associate Compliance</span>
              </div>
              <span className="text-[10px] text-[hsl(var(--brand-primary))]">PLANNED (Q4 2026)</span>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CALL TO ACTION */}
      <section className="py-20 px-4 text-center border-t border-zinc-900 bg-zinc-950/20">
        <div className="max-w-4xl mx-auto flex flex-col items-center">
          <h2 className="text-3xl font-extrabold tracking-tight">Build compliance-ready campaigns</h2>
          <p className="mt-4 text-sm text-[hsl(var(--text-secondary))] max-w-md">
            Schedule a technical walkthrough and see how the sandbox dialer enforces outbound calling regulations.
          </p>
          <div className="mt-8">
            <Link
              href="/contact"
              className="px-8 py-4 rounded-xl font-bold text-white transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] shadow-lg flex items-center justify-center gap-2 group w-max mx-auto"
              style={{
                background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
              }}
            >
              Request Live Sandbox Demo
              <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
