"use client";

import React, { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { 
  Zap, 
  Search, 
  Calendar, 
  Clock, 
  ArrowRight,
  ShieldCheck,
  Cpu,
  TrendingUp
} from "lucide-react";
import { PublicNavbar } from "../components/public-navbar";
import { PublicFooter } from "../components/public-footer";

export default function Blog() {
  const [selectedCluster, setSelectedCluster] = useState<string>("All");

  const clusters = ["All", "Compliance & Safety", "Telephony Stack", "Campaign Automation"];

  const articles = [
    {
      id: "tcpa-compliance-guide",
      title: "The Complete Guide to TCPA Compliance for Outbound Sales in 2026",
      summary: "Understand calling hour restrictions, quiet hour rules, and how automated timezone gating mitigates risk for voice-agent campaigns.",
      cluster: "Compliance & Safety",
      date: "June 25, 2026",
      readTime: "7 min read",
      icon: ShieldCheck,
      iconColor: "text-emerald-400"
    },
    {
      id: "conversational-latency",
      title: "Understanding Conversational Latency in Real-Time Voice AI",
      summary: "How raw G.711 μ-law PCM transcoding over WebSockets eliminates delay and awkward silences for outbound call platforms.",
      cluster: "Telephony Stack",
      date: "June 20, 2026",
      readTime: "9 min read",
      icon: Cpu,
      iconColor: "text-indigo-400"
    },
    {
      id: "national-dnc-violations",
      title: "How to Avoid National DNC Violations with Outbound Voice Agents",
      summary: "Rules of the National Do-Not-Call registry, setting up CRM scrubs, and validating compliance database architecture.",
      cluster: "Compliance & Safety",
      date: "June 18, 2026",
      readTime: "5 min read",
      icon: ShieldCheck,
      iconColor: "text-emerald-400"
    },
    {
      id: "scaling-appointment-setting",
      title: "Scaling Outbound Appointment Setting with Autonomous Voice Agents",
      summary: "Structuring scheduling playbooks, managing calendar objections, and measuring appointment-to-meeting conversions.",
      cluster: "Campaign Automation",
      date: "June 12, 2026",
      readTime: "6 min read",
      icon: TrendingUp,
      iconColor: "text-amber-400"
    },
    {
      id: "optimize-vad-voip",
      title: "How to Optimize Voice Activity Detection (VAD) for Outbound Dialers",
      summary: "Fine-tuning silence thresholds, handling mobile background noise, and preventing premature model interruptions.",
      cluster: "Telephony Stack",
      date: "June 08, 2026",
      readTime: "8 min read",
      icon: Cpu,
      iconColor: "text-indigo-400"
    },
    {
      id: "hubspot-transcript-automation",
      title: "How to Synchronize Outbound Call Transcripts and Audio to HubSpot",
      summary: "Synchronizing call status, stereo WAV recordings, and structured transcripts directly to contact timelines via REST endpoints.",
      cluster: "Campaign Automation",
      date: "June 03, 2026",
      readTime: "6 min read",
      icon: TrendingUp,
      iconColor: "text-amber-400"
    }
  ];

  const filteredArticles = selectedCluster === "All" 
    ? articles 
    : articles.filter(a => a.cluster === selectedCluster);

  return (
    <div className="min-h-screen bg-[hsl(var(--surface-0))] text-white selection:bg-[hsl(var(--brand-primary))]/30 relative overflow-hidden">
      <PublicNavbar />

      {/* Decorative background gradients */}
      <div className="absolute top-0 right-1/4 w-[500px] h-[500px] bg-[hsl(var(--brand-primary))]/5 rounded-full blur-[120px] pointer-events-none -z-10" />

      {/* HERO SECTION */}
      <section className="pt-32 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white via-zinc-200 to-zinc-500">
          Resources & Technical Insights
        </h1>
        <p className="mt-4 text-base sm:text-lg text-[hsl(var(--text-secondary))] max-w-2xl mx-auto leading-relaxed">
          Learn how to engineer high-performance real-time VoIP systems, manage calling compliance, and scale outbound sales workflows.
        </p>
      </section>

      {/* SEARCH & FILTERS BAR */}
      <section className="py-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-y border-zinc-900 bg-zinc-950/20">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Cluster Filter Buttons */}
          <div className="flex flex-wrap gap-2.5">
            {clusters.map((cluster) => (
              <button
                key={cluster}
                onClick={() => setSelectedCluster(cluster)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold border transition-all ${
                  selectedCluster === cluster 
                    ? "border-[hsl(var(--brand-primary))] text-white bg-[hsl(var(--brand-primary))]/10" 
                    : "border-zinc-900 text-[hsl(var(--text-secondary))] hover:text-white hover:border-zinc-800"
                }`}
              >
                {cluster}
              </button>
            ))}
          </div>

          {/* Search bar mockup */}
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-[hsl(var(--text-muted))]" />
            <input
              type="text"
              placeholder="Search articles..."
              className="w-full pl-10 pr-4 py-2.5 bg-zinc-900/40 border border-zinc-800 rounded-xl text-xs focus:outline-none focus:border-[hsl(var(--brand-primary))]"
              disabled
            />
          </div>
        </div>
      </section>

      {/* ARTICLES GRID */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {filteredArticles.map((article, index) => {
            const Icon = article.icon;
            return (
              <motion.article
                key={article.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                className="group p-6 rounded-2xl border border-zinc-900 hover:border-zinc-800/80 bg-zinc-900/10 hover:bg-zinc-900/20 flex flex-col justify-between gap-6 transition-all duration-300"
              >
                <div className="flex flex-col gap-4">
                  <div className="flex justify-between items-center text-xs text-[hsl(var(--text-muted))]">
                    <span className="font-semibold text-[hsl(var(--brand-primary))] uppercase">{article.cluster}</span>
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {article.date}</span>
                      <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {article.readTime}</span>
                    </div>
                  </div>

                  <h2 className="text-lg font-bold text-white group-hover:text-[hsl(var(--brand-primary))] transition-colors leading-snug">
                    {article.title}
                  </h2>

                  <p className="text-xs text-[hsl(var(--text-secondary))] leading-relaxed">
                    {article.summary}
                  </p>
                </div>

                <div className="flex items-center gap-2 text-xs font-bold text-white border-t border-zinc-900 pt-4 cursor-pointer group-hover:gap-3 transition-all duration-200">
                  <span>Read Article</span>
                  <ArrowRight className="w-4 h-4 text-[hsl(var(--brand-primary))]" />
                </div>
              </motion.article>
            );
          })}
        </div>
      </section>

      {/* CALL TO ACTION */}
      <section className="py-20 px-4 text-center border-t border-zinc-900 bg-zinc-950/20">
        <div className="max-w-4xl mx-auto flex flex-col items-center">
          <h2 className="text-2xl font-extrabold tracking-tight">Need custom playbook assistance?</h2>
          <p className="mt-4 text-sm text-[hsl(var(--text-secondary))] max-w-sm">
            Read our telemetry API documentation or schedule a walkthrough with our design engineers.
          </p>
          <div className="mt-8 flex gap-4">
            <Link
              href="/contact"
              className="px-6 py-3 rounded-xl font-bold text-white transition-all shadow-md text-xs"
              style={{
                background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
              }}
            >
              Book a Live Demo
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
