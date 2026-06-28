"use client";

import React, { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { 
  Zap, 
  ShieldCheck, 
  TrendingUp, 
  ArrowRight, 
  Play, 
  CheckCircle2, 
  ChevronDown, 
  Globe, 
  Smartphone, 
  Database,
  RefreshCw,
  Clock,
  Sparkles,
  Server
} from "lucide-react";
import { PublicNavbar } from "./components/public-navbar";
import { PublicFooter } from "./components/public-footer";

export default function Home() {
  // ROI Slider state
  const [leadVolume, setLeadVolume] = useState(15000);
  const [activeFaq, setActiveFaq] = useState<number | null>(null);

  // ROI calculations
  const avgSdrCostPerLead = 4.50; // SDR labor, telephone bills, CRM seats
  const visooraCostPerLead = 0.65; // Twilio + API usage
  const manualSdrTotal = leadVolume * avgSdrCostPerLead;
  const visooraTotal = leadVolume * visooraCostPerLead;
  const moneySaved = manualSdrTotal - visooraTotal;

  const toggleFaq = (index: number) => {
    setActiveFaq(activeFaq === index ? null : index);
  };

  return (
    <div className="min-h-screen bg-[hsl(var(--surface-0))] text-white selection:bg-[hsl(var(--brand-primary))]/30 relative overflow-hidden">
      <PublicNavbar />

      {/* Background Decorative Gradients */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-[hsl(var(--brand-accent))]/10 rounded-full blur-[120px] pointer-events-none -z-10" />
      <div className="absolute top-[800px] right-1/4 w-[600px] h-[600px] bg-[hsl(var(--brand-primary))]/5 rounded-full blur-[150px] pointer-events-none -z-10" />

      {/* HERO SECTION */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col items-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border border-zinc-800 bg-zinc-900/60 text-sm font-medium text-[hsl(var(--brand-primary))] mb-6 hover:border-zinc-700 transition-colors cursor-pointer"
        >
          <Sparkles className="w-4 h-4" />
          <span>Compliant, Low-Latency Outbound calling</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-4xl sm:text-6xl font-extrabold tracking-tight max-w-4xl leading-tight bg-clip-text text-transparent bg-gradient-to-b from-white via-zinc-200 to-zinc-500"
        >
          Enterprise AI Outbound Sales Calls, Built Compliantly.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-6 text-lg sm:text-xl text-[hsl(var(--text-secondary))] max-w-2xl leading-relaxed"
        >
          Qualify cold leads, book calendar meetings, and update CRM records automatically. Achieve sub-1.2-second response latency with a built-in compliance engine that enforces local TCPA timezone rules.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-10 flex flex-col sm:flex-row items-center gap-4"
        >
          <Link
            href="/contact"
            className="w-full sm:w-auto px-8 py-4 rounded-xl font-bold text-white transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] shadow-lg flex items-center justify-center gap-2 group"
            style={{
              background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
            }}
          >
            Book a Demo 
            <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
          </Link>
          <Link
            href="/about#technology"
            className="w-full sm:w-auto px-8 py-4 rounded-xl font-semibold border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900 hover:border-zinc-700 transition-colors flex items-center justify-center"
          >
            Read the Specs
          </Link>
        </motion.div>

        {/* Hero Interactive Telemetry Mockup */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="w-full mt-16 rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-4 shadow-2xl relative overflow-hidden"
        >
          {/* Header Controls */}
          <div className="flex items-center justify-between pb-3 border-b border-zinc-900 mb-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-500/80" />
              <span className="w-3 h-3 rounded-full bg-amber-500/80" />
              <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
              <span className="text-xs text-[hsl(var(--text-muted))] font-mono ml-2">visoora-telemetry-engine</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-[hsl(var(--brand-primary))] font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-[hsl(var(--brand-primary))] animate-pulse-live" />
              LIVE TELEPHONY CONNECTED
            </div>
          </div>
          
          {/* Screen Content Mockup */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left font-mono">
            <div className="p-4 rounded-xl border border-zinc-900 bg-zinc-900/30">
              <div className="text-xs text-[hsl(var(--text-secondary))] mb-1">CURRENT ACTIVE CALLS</div>
              <div className="text-2xl font-bold text-white">8 / 10 concurrent</div>
              <div className="w-full bg-zinc-800 h-1.5 rounded-full mt-2 overflow-hidden">
                <div className="bg-[hsl(var(--brand-primary))] h-full rounded-full" style={{ width: "80%" }} />
              </div>
            </div>
            <div className="p-4 rounded-xl border border-zinc-900 bg-zinc-900/30">
              <div className="text-xs text-[hsl(var(--text-secondary))] mb-1">CONVERSATIONAL LATENCY</div>
              <div className="text-2xl font-bold text-emerald-400">920ms (P95)</div>
              <span className="text-[10px] text-[hsl(var(--text-muted))]">Deepgram STT + Gemini FSM Response</span>
            </div>
            <div className="p-4 rounded-xl border border-zinc-900 bg-zinc-900/30">
              <div className="text-xs text-[hsl(var(--text-secondary))] mb-1">TCPA COMPLIANCE STATUS</div>
              <div className="text-2xl font-bold text-emerald-400">100% Gated</div>
              <span className="text-[10px] text-[hsl(var(--text-muted))]">Active timezone area code enforcement</span>
            </div>
          </div>

          {/* Code Execution Fallback Logger View */}
          <div className="mt-4 p-4 rounded-xl border border-zinc-900 bg-zinc-950/80 text-left font-mono text-xs overflow-x-auto text-[hsl(var(--text-secondary))] h-32 flex flex-col justify-end">
            <p className="text-[hsl(var(--text-muted))]">{"[2026-06-27T23:19:30] outbound_dialer.py -> Initializing campaign queue \"SaaS Q3 Outreach\""}</p>
            <p className="text-[hsl(var(--text-muted))]">{"[2026-06-27T23:19:31] compliance_engine.py -> Checking timezone gate for +1 (415) 555-0199 (California)"}</p>
            <p className="text-emerald-400">{"[2026-06-27T23:19:31] compliance_engine.py -> COMPLIANT (Calling hour is 10:49 AM local time)"}</p>
            <p className="text-indigo-400">{"[2026-06-27T23:19:32] fsm_dialog.py -> FSM State transition [START] -> [INTRO] -> Outbound Audio Stream Active"}</p>
            <p className="text-white">{"[2026-06-27T23:19:33] websocket_stream.py -> Deepgram STT Event: \"Hey, who's this?\" | latency: 240ms"}</p>
            <p className="text-emerald-400">{"[2026-06-27T23:19:34] gemini_fsm.py -> FSM output generated: \"Hi, I'm calling from Acme Corp...\" | reasoning: 680ms"}</p>
          </div>
        </motion.div>
      </section>

      {/* SOCIAL PROOF BAR */}
      <section className="py-10 border-y border-zinc-900/60 bg-zinc-950/20 text-center">
        <div className="max-w-7xl mx-auto px-4">
          <p className="text-xs font-bold uppercase tracking-wider text-[hsl(var(--text-muted))] mb-6">
            Trusted by high-growth sales & recruitment teams
          </p>
          <div className="flex flex-wrap items-center justify-center gap-12 sm:gap-20 opacity-40">
            <span className="text-sm font-bold tracking-tight text-white select-none">VERTEX SOLUTIONS</span>
            <span className="text-sm font-bold tracking-tight text-white select-none">PULSE RECRUITING</span>
            <span className="text-sm font-bold tracking-tight text-white select-none">SKYLINE AGENCIES</span>
            <span className="text-sm font-bold tracking-tight text-white select-none">CLAYMORE B2B</span>
          </div>
        </div>
      </section>

      {/* THE PROBLEM SECTION */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-bold uppercase tracking-widest text-[hsl(var(--brand-primary))]">The Cold Calling Bottleneck</h2>
          <p className="mt-3 text-3xl sm:text-4xl font-extrabold tracking-tight">Outbound Outreach is Complex and Risky.</p>
          <p className="mt-4 text-base text-[hsl(var(--text-secondary))]">
            Relying entirely on manual SDR dialing limits scale and increases labor costs. However, generic robotic voice bots pose severe regulatory risks and damage brand reputation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-6 rounded-2xl border border-zinc-900 bg-zinc-900/20 flex flex-col gap-4">
            <div className="w-10 h-10 rounded-xl bg-rose-500/10 flex items-center justify-center text-rose-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold">TCPA Compliance Fines</h3>
            <p className="text-sm text-[hsl(var(--text-secondary))] leading-relaxed">
              Dialing numbers outside scheduled hours or calling active Do-Not-Call (DNC) numbers violates federal compliance guidelines, resulting in structural fines of up to $1,500 per call.
            </p>
          </div>
          <div className="p-6 rounded-2xl border border-zinc-900 bg-zinc-900/20 flex flex-col gap-4">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400">
              <Clock className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold">High Conversational Latency</h3>
            <p className="text-sm text-[hsl(var(--text-secondary))] leading-relaxed">
              Robotic voice delays (pauses &gt; 2 seconds) result in awkward, broken conversations that prompt buyers to hang up immediately before key value propositions are delivered.
            </p>
          </div>
          <div className="p-6 rounded-2xl border border-zinc-900 bg-zinc-900/20 flex flex-col gap-4">
            <div className="w-10 h-10 rounded-xl bg-zinc-500/10 flex items-center justify-center text-zinc-400">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold">Low Representative Retention</h3>
            <p className="text-sm text-[hsl(var(--text-secondary))] leading-relaxed">
              SDR teams face high annual turnover. Representatives spend over 60% of their workday dialing busy tones, answering machines, and manually typing notes instead of booking deals.
            </p>
          </div>
        </div>
      </section>

      {/* THE SOLUTION SECTION */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-5 flex flex-col gap-5">
            <h2 className="text-sm font-bold uppercase tracking-widest text-[hsl(var(--brand-accent))]">The Solution</h2>
            <h3 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Built for Speed. Designed for Compliance.</h3>
            <p className="text-base text-[hsl(var(--text-secondary))] leading-relaxed">
              Visoora resolves outbound calling challenges by replacing manual scripts with low-latency conversational agents. Enforce timezone regulations and synchronize call logs dynamically.
            </p>
            <div className="flex flex-col gap-4 mt-2">
              <div className="flex gap-3">
                <CheckCircle2 className="w-5 h-5 text-[hsl(var(--brand-primary))] flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-bold">Deterministic FSM Dialog Trees</h4>
                  <p className="text-xs text-[hsl(var(--text-secondary))] mt-0.5">Control the conversation path and keep AI agents on-script with explicit state controls.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <CheckCircle2 className="w-5 h-5 text-[hsl(var(--brand-primary))] flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-bold">Automated Timezone Gating</h4>
                  <p className="text-xs text-[hsl(var(--text-secondary))] mt-0.5">Verify coordinates and local timezone windows before outbound campaigns place calls.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <CheckCircle2 className="w-5 h-5 text-[hsl(var(--brand-primary))] flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-bold">Sub-1.2s Conversational Response</h4>
                  <p className="text-xs text-[hsl(var(--text-secondary))] mt-0.5">Direct PCM Base64 transcoding over WebSockets eliminates delay and awkward silences.</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="lg:col-span-7 p-6 rounded-2xl border border-zinc-900 bg-zinc-900/10 relative overflow-hidden">
            {/* Visual illustration of FSM logic pipeline */}
            <div className="flex flex-col gap-5 relative font-mono text-xs">
              <div className="flex items-center justify-between p-3 rounded-xl border border-zinc-800/80 bg-zinc-950/40">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-[hsl(var(--brand-primary))]" />
                  <span>Lead Database (CSV Upload)</span>
                </div>
                <span className="text-[10px] text-emerald-400">Import complete</span>
              </div>
              <div className="w-max mx-auto text-[hsl(var(--text-muted))]">|</div>
              <div className="flex items-center justify-between p-3 rounded-xl border border-zinc-800/80 bg-zinc-950/40 border-l-[hsl(var(--brand-primary))]">
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-[hsl(var(--brand-primary))]" />
                  <span>Compliance Filter</span>
                </div>
                <span className="text-[10px] text-emerald-400">Timezone OK (8:00 AM - 9:00 PM)</span>
              </div>
              <div className="w-max mx-auto text-[hsl(var(--text-muted))]">|</div>
              <div className="flex items-center justify-between p-3 rounded-xl border border-zinc-800/80 bg-zinc-950/40 border-l-[hsl(var(--brand-accent))]">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-[hsl(var(--brand-accent))]" />
                  <span>Gemini FSM State Machine</span>
                </div>
                <span className="text-[10px] text-indigo-400">Reasoning State: Objection Handling</span>
              </div>
              <div className="w-max mx-auto text-[hsl(var(--text-muted))]">|</div>
              <div className="flex items-center justify-between p-3 rounded-xl border border-zinc-800/80 bg-zinc-950/40">
                <div className="flex items-center gap-2">
                  <Smartphone className="w-4 h-4 text-[hsl(var(--brand-primary))]" />
                  <span>Twilio Outbound VoIP Gateway</span>
                </div>
                <span className="text-[10px] text-emerald-400">Call Connected</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CRM INTEGRATIONS SECTION */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900 bg-zinc-950/10">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-sm font-bold uppercase tracking-widest text-[hsl(var(--brand-primary))]">CRM Sync & Integrations</h2>
          <p className="mt-3 text-3xl font-extrabold tracking-tight">Sync call logs dynamically</p>
          <p className="mt-4 text-sm text-[hsl(var(--text-secondary))] leading-relaxed">
            Visoora communicates directly with your sales tech stack. Feed call transcriptions, customer sentiments, and compiled stereo WAV recordings directly to HubSpot, Salesforce, and other tools automatically.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-8 md:gap-16">
          <div className="px-6 py-4 rounded-xl border border-zinc-900 bg-zinc-900/30 text-sm font-bold tracking-tight text-white">
            HUBSPOT INTEGRATION
          </div>
          <div className="w-12 h-0.5 bg-gradient-to-r from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))]" />
          <div className="flex items-center gap-2 px-6 py-4 rounded-xl border border-zinc-800 bg-zinc-900/60 font-mono text-xs">
            <RefreshCw className="w-4 h-4 text-[hsl(var(--brand-primary))] animate-spin-slow" />
            <span>VISOORA TELEMETRY BRIDGE</span>
          </div>
          <div className="w-12 h-0.5 bg-gradient-to-r from-[hsl(var(--brand-accent))] to-[hsl(var(--brand-primary))]" />
          <div className="px-6 py-4 rounded-xl border border-zinc-900 bg-zinc-900/30 text-sm font-bold tracking-tight text-white">
            SALESFORCE CONNECTOR
          </div>
        </div>
      </section>

      {/* DYNAMIC ROI CALCULATOR */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-5 flex flex-col gap-4">
            <h2 className="text-sm font-bold uppercase tracking-widest text-[hsl(var(--brand-accent))]">Return on Investment</h2>
            <h3 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Optimize Outbound Outreach Budgets</h3>
            <p className="text-base text-[hsl(var(--text-secondary))] leading-relaxed">
              Review outbound operational costs. Slider controls show manual outbound SDR costs versus Visoora's autonomous calling platform pricing.
            </p>
          </div>

          <div className="lg:col-span-7 p-8 rounded-2xl border border-zinc-900 bg-zinc-900/20 flex flex-col gap-6">
            <div>
              <div className="flex justify-between text-sm font-medium mb-2">
                <span>Monthly Outbound Leads</span>
                <span className="text-[hsl(var(--brand-primary))] font-bold">{leadVolume.toLocaleString()} leads</span>
              </div>
              <input 
                type="range" 
                min="5000" 
                max="100000" 
                step="5000"
                value={leadVolume} 
                onChange={(e) => setLeadVolume(Number(e.target.value))}
                className="w-full h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-[hsl(var(--brand-primary))]"
              />
              <div className="flex justify-between text-xs text-[hsl(var(--text-muted))] mt-1 font-mono">
                <span>5,000</span>
                <span>100,000</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-zinc-900">
              <div>
                <span className="text-xs text-[hsl(var(--text-secondary))] uppercase">Manual SDR Outreach Cost</span>
                <div className="text-xl font-bold mt-1 text-zinc-300">${manualSdrTotal.toLocaleString()}</div>
                <span className="text-[10px] text-[hsl(var(--text-muted))]">Labor, dialer seats & CRM</span>
              </div>
              <div>
                <span className="text-xs text-[hsl(var(--text-secondary))] uppercase">Visoora Campaign Cost</span>
                <div className="text-xl font-extrabold mt-1 text-[hsl(var(--brand-primary))]">${visooraTotal.toLocaleString()}</div>
                <span className="text-[10px] text-[hsl(var(--text-muted))]">Outbound VoIP + FSM logic</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[hsl(var(--brand-primary))]/5 border border-[hsl(var(--brand-primary))]/20 flex items-center justify-between mt-2">
              <div>
                <span className="text-xs text-[hsl(var(--brand-primary))] font-bold uppercase tracking-wider">Estimated Monthly Savings</span>
                <div className="text-2xl font-extrabold text-white mt-1">${moneySaved.toLocaleString()}</div>
              </div>
              <Link 
                href="/contact" 
                className="px-4 py-2.5 rounded-lg text-xs font-bold text-white shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all"
                style={{
                  background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
                }}
              >
                Claim Savings
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ SECTION */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto border-t border-zinc-900">
        <div className="text-center mb-16">
          <h2 className="text-sm font-bold uppercase tracking-widest text-[hsl(var(--brand-primary))]">Frequently Asked Questions</h2>
          <p className="mt-3 text-3xl font-extrabold tracking-tight">Compliance, Latency, and Architecture</p>
        </div>

        <div className="flex flex-col gap-4">
          {[
            {
              q: "How does Visoora handle TCPA calling hours and compliance?",
              a: "Visoora maps lead phone numbers to regional area codes and coordinates to enforce TCPA compliant window restrictions (8:00 AM – 9:00 PM local time). If a call is scheduled outside this window, the system automatically gates the dialer until the compliant window opens."
            },
            {
              q: "What is the conversational latency of the AI voice agent?",
              a: "Visoora's media engine transcodes G.711 u-law raw PCM binary payloads over WebSockets, using Deepgram Nova-2 for STT and Google Gemini for reasoning. The system delivers a P95 response latency of under 1.2 seconds, avoiding awkward silences."
            },
            {
              q: "Does Visoora disclose that it is an AI voice agent?",
              a: "Yes. While our agents are designed to sound highly natural, transparency is critical for compliance and trust. In the event of safety or grounding validation failures (such as off-topic questions or competitor queries), the agent is configured to redirect the call using human-sounding fallback phrases, maintaining brand safety."
            },
            {
              q: "How does the system sync with our existing CRM?",
              a: "Visoora provides bi-directional API endpoints that sync lead status, live transcripts, customer sentiment analysis, and compiled stereo WAV recordings directly to HubSpot, Salesforce, and other platforms using webhook events."
            }
          ].map((item, index) => (
            <div 
              key={index} 
              className="rounded-2xl border border-zinc-900 bg-zinc-900/10 overflow-hidden transition-colors"
            >
              <button
                onClick={() => toggleFaq(index)}
                className="w-full px-6 py-5 flex items-center justify-between text-left font-bold text-sm sm:text-base hover:bg-zinc-900/20"
              >
                <span>{item.q}</span>
                <ChevronDown className={`w-5 h-5 text-[hsl(var(--text-secondary))] transition-transform duration-200 ${activeFaq === index ? "rotate-180" : ""}`} />
              </button>
              {activeFaq === index && (
                <div className="px-6 pb-6 text-sm text-[hsl(var(--text-secondary))] leading-relaxed border-t border-zinc-950 pt-4 bg-zinc-950/20">
                  {item.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* FINAL CTA SECTION */}
      <section className="py-20 px-4 text-center border-t border-zinc-900 bg-gradient-to-b from-zinc-950/20 to-zinc-950 relative overflow-hidden">
        <div className="absolute inset-0 bg-[hsl(var(--brand-primary))]/2 opacity-5 blur-3xl pointer-events-none" />
        <div className="max-w-4xl mx-auto flex flex-col items-center">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Ready to scale your outreach?</h2>
          <p className="mt-4 text-base text-[hsl(var(--text-secondary))] max-w-xl">
            Configure a compliant sandbox voice agent, build custom playbooks, and run test outbound campaigns locally.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center gap-4">
            <Link
              href="/contact"
              className="w-full sm:w-auto px-8 py-4 rounded-xl font-bold text-white transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] shadow-lg flex items-center justify-center gap-2"
              style={{
                background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
              }}
            >
              Book a Live Demo
            </Link>
            <Link
              href="/login"
              className="w-full sm:w-auto px-8 py-4 rounded-xl font-semibold border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900 hover:border-zinc-700 transition-colors flex items-center justify-center"
            >
              Access Developer Dashboard
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
