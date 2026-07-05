"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import DemoReport from "./components/DemoReport";
import { motion, useInView } from "framer-motion";
import {
  Zap,
  ArrowRight,
  ChevronDown,
  Globe,
  Brain,
  Target,
  Search,
  Mail,
  Phone,
  TrendingUp,
  Shield,
  Eye,
  CheckCircle2,
  BarChart3,
  Users,
  Lightbulb,
  Clock,
  FileText,
  Layers,
  Sparkles,
  Database,
  GitBranch,
  MessageSquare,
  Award,
  Compass,
  BookOpen,
  Activity,
  ArrowDown,
  Star,
  ChevronRight,
} from "lucide-react";
import { PublicNavbar } from "./components/public-navbar";
import { PublicFooter } from "./components/public-footer";

/* ======================================================
   SECTION WRAPPER — scroll-triggered fade-in
   ====================================================== */
function Section({
  children,
  className = "",
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <motion.section
      id={id}
      ref={ref}
      initial={{ opacity: 0, y: 32 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.section>
  );
}

/* ======================================================
   ANIMATED WORKFLOW STEP
   ====================================================== */
function WorkflowStep({
  icon: Icon,
  label,
  delay,
  isActive,
}: {
  icon: React.ElementType;
  label: string;
  delay: number;
  isActive: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.5 }}
      className={`flex flex-col items-center gap-2 transition-all duration-500 ${
        isActive ? "scale-110" : "opacity-60"
      }`}
    >
      <div
        className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-500 ${
          isActive
            ? "bg-gradient-to-br from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))] shadow-[0_0_24px_hsla(var(--brand-primary),0.4)]"
            : "bg-[hsl(var(--surface-2))] border border-zinc-800"
        }`}
      >
        <Icon className={`w-5 h-5 ${isActive ? "text-white" : "text-[hsl(var(--text-muted))]"}`} />
      </div>
      <span
        className={`text-sm font-semibold text-center leading-tight ${
          isActive ? "text-white" : "text-[hsl(var(--text-muted))]"
        }`}
      >
        {label}
      </span>
    </motion.div>
  );
}

/* ======================================================
   MAIN LANDING PAGE
   ====================================================== */
export default function Home() {
  const [activeFaq, setActiveFaq] = useState<number | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [demoUrl, setDemoUrl] = useState("");
  const [demoActive, setDemoActive] = useState(false);
  const [demoPhase, setDemoPhase] = useState(0);
  const [demoError, setDemoError] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [pricingPeriod, setPricingPeriod] = useState<"monthly" | "yearly">("monthly");

  // Auto-cycle hero workflow steps
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % 6);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const toggleFaq = (index: number) => {
    setActiveFaq(activeFaq === index ? null : index);
  };

  // "Analyze My Website" demo handler
  const handleDemoAnalyze = async () => {
    if (!demoUrl) return;
    setDemoActive(true);
    setDemoPhase(1);
    setDemoError(null);
    setAnalysisData(null);

    // Simulate progressive loading while waiting for the long API call (up to 10 phases)
    const progressInterval = setInterval(() => {
      setDemoPhase(prev => {
        if (prev < 10) return prev + 1;
        return prev;
      });
    }, 4500);

    try {
      const res = await fetch("http://localhost:8000/api/public/analyze-website", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: demoUrl, captcha_token: "test-bypass" })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || "Failed to analyze website.");
      }

      const data = await res.json();
      clearInterval(progressInterval);
      
      if (data.cached && data.result_id) {
          // It's cached! Fetch the report directly.
          const reportRes = await fetch(`http://localhost:8000/api/public/report/${data.result_id}`);
          if (reportRes.ok) {
              const reportData = await reportRes.json();
              setAnalysisData(reportData);
              setDemoPhase(11);
              return;
          }
      }
      
      if (!data.job_id) {
          throw new Error("Invalid response from server.");
      }
      
      // Connect to SSE stream for progressive loading
      const eventSource = new EventSource(`http://localhost:8000/api/public/workflow/${data.job_id}/stream`);
      
      eventSource.onmessage = (event) => {
          const payload = JSON.parse(event.data);
          
          if (payload.event_type === "step_success") {
              setDemoPhase((prev) => prev < 10 ? prev + 1 : prev);
          } else if (payload.event_type === "workflow_completed") {
              setAnalysisData(payload.payload.result);
              setDemoPhase(11); // Complete
              eventSource.close();
          } else if (payload.event_type === "workflow_failed") {
              setDemoError(payload.payload.error || "Analysis Failed");
              setDemoPhase(11);
              eventSource.close();
          }
      };
      
      eventSource.onerror = (err) => {
          console.error("SSE Connection Error", err);
          eventSource.close();
          // If we fail, try to fetch the result manually after a delay or just show error
          if (demoPhase < 11) {
              setDemoError("Lost connection to the analysis stream. Please try again.");
              setDemoPhase(11);
          }
      };
      
    } catch (err: any) {
      clearInterval(progressInterval);
      setDemoError(err.message);
      setDemoPhase(11);
    }
  };

  const heroSteps = [
    { icon: Globe, label: "Business\nUnderstanding" },
    { icon: Search, label: "Market\nResearch" },
    { icon: Target, label: "ICP\nDiscovery" },
    { icon: BarChart3, label: "Lead\nScoring" },
    { icon: Mail, label: "Strategic\nOutreach" },
    { icon: TrendingUp, label: "Revenue\nGrowth" },
  ];

  const problems = [
    {
      icon: Clock,
      title: "Manual Prospecting",
      desc: "20+ hours every week researching companies that never convert. Your team burns out before finding the right buyers.",
      color: "text-rose-400",
      bg: "bg-rose-500/10",
    },
    {
      icon: Layers,
      title: "Too Many Disconnected Tools",
      desc: "Apollo + Clay + CRM + ChatGPT + Email = chaos. Context is lost between tools, and nothing talks to each other.",
      color: "text-amber-400",
      bg: "bg-amber-500/10",
    },
    {
      icon: Brain,
      title: "Generic AI That Doesn't Know You",
      desc: "AI tools generate outreach without understanding your business. The result: generic messages prospects ignore.",
      color: "text-violet-400",
      bg: "bg-violet-500/10",
    },
  ];

  const features = [
    {
      icon: MessageSquare,
      title: "AI Business Consultant",
      desc: "Analyzes your website, understands your value proposition, and designs your go-to-market strategy before prospecting begins.",
    },
    {
      icon: Brain,
      title: "AI Business Brain",
      desc: "Builds a deep knowledge graph of your business — ICP segments, buyer personas, competitive advantages, and objection handling playbooks.",
    },
    {
      icon: Search,
      title: "AI Market Research",
      desc: "Researches every prospect's company using public data. Every fact is sourced. Every inference shows confidence level.",
    },
    {
      icon: Target,
      title: "Explainable Lead Scoring",
      desc: "Scores every lead against your ICP with transparent reasoning — matching factors, confidence scores, and data sources. Not a black box.",
    },
    {
      icon: Phone,
      title: "AI Voice Agent",
      desc: "Natural-sounding AI calls with sub-1.2s conversational latency and full TCPA compliance built into every call.",
    },
    {
      icon: Mail,
      title: "AI Email Strategist",
      desc: "Generates personalized outreach grounded in company research and business context, not generic templates.",
    },
  ];

  const journeySteps = [
    { icon: Globe, label: "Business Understanding", desc: "AI analyzes your website and products" },
    { icon: Database, label: "Knowledge Graph", desc: "Builds a structured model of your business" },
    { icon: Target, label: "ICP Definition", desc: "Identifies your ideal customer segments" },
    { icon: Users, label: "Buyer Personas", desc: "Maps decision-maker profiles and pain points" },
    { icon: Search, label: "Market Research", desc: "Researches prospects with sourced data" },
    { icon: Compass, label: "Lead Discovery", desc: "Imports and enriches prospect lists" },
    { icon: BarChart3, label: "Qualification", desc: "Scores and ranks by fit with reasoning" },
    { icon: Mail, label: "Outreach", desc: "Generates personalized emails and call scripts" },
    { icon: Phone, label: "Meetings", desc: "AI voice agent books qualified meetings" },
    { icon: TrendingUp, label: "Growth", desc: "Learns from results, refines strategy" },
  ];

  const faqs = [
    {
      q: "Can AI replace my SDR team?",
      a: "Visoora doesn't replace your team — it amplifies them. The AI handles research, scoring, and initial outreach so your people focus on closing deals and building relationships. Think of it as giving every rep a senior research analyst.",
    },
    {
      q: "How secure is my data?",
      a: "All data is tenant-isolated with Postgres Row-Level Security. We enforce per-account LLM token budgets, never share data between accounts, and all API traffic is encrypted. Your business intelligence stays yours.",
    },
    {
      q: "Can I use my own email for outreach?",
      a: "Yes. Visoora generates draft emails grounded in your business context and prospect research. You review, edit, and send from your own email. Nothing goes out without your explicit approval.",
    },
    {
      q: "How does the AI find prospects?",
      a: "Visoora does not autonomously discover prospects. You upload prospect lists (CSV/XLSX), and Visoora researches each company using publicly available data, then scores them against your ICP with explainable reasoning.",
    },
    {
      q: "How accurate is lead scoring?",
      a: "Every score shows its reasoning: which ICP criteria matched, which buying signals were detected, data sources used, and confidence level. You can inspect, adjust, and override any score. Confirmed facts are visually separated from AI estimates.",
    },
    {
      q: "Can I review everything before outreach goes out?",
      a: "Absolutely. Visoora operates on a human-in-the-loop model. Every email draft, call script, and lead score is presented for your review and approval before any action is taken.",
    },
  ];

  const metrics = [
    { value: "20+", unit: "hrs/week", label: "Research Time Saved", icon: Clock },
    { value: "85%", unit: "", label: "Faster Prospect Qualification", icon: Zap },
    { value: "3x", unit: "", label: "More Qualified Leads Identified", icon: Target },
    { value: "100%", unit: "", label: "Explainable AI Decisions", icon: Eye },
  ];

  const roadmapItems = [
    { label: "AI Business Consultant", status: "live", icon: MessageSquare },
    { label: "AI Business Brain", status: "live", icon: Brain },
    { label: "Prospect Intelligence", status: "live", icon: Search },
    { label: "AI Voice Calls", status: "live", icon: Phone },
    { label: "Meeting Intelligence", status: "coming", icon: Activity },
    { label: "CRM Intelligence", status: "coming", icon: GitBranch },
  ];

  return (
    <div className="min-h-screen bg-[hsl(var(--surface-0))] text-white selection:bg-[hsl(var(--brand-primary))]/30 relative overflow-hidden">
      <PublicNavbar />

      {/* Background Decorative Gradients */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-[hsl(var(--brand-accent))]/8 rounded-full blur-[140px] pointer-events-none -z-10 animate-float-slow" />
      <div className="absolute top-[800px] right-1/4 w-[600px] h-[600px] bg-[hsl(var(--brand-primary))]/5 rounded-full blur-[160px] pointer-events-none -z-10 animate-float-delayed" />
      <div className="absolute top-[2000px] left-1/3 w-[400px] h-[400px] bg-[hsl(var(--brand-accent))]/6 rounded-full blur-[120px] pointer-events-none -z-10" />

      {/* ============================================================
          HERO SECTION
          ============================================================ */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col items-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-zinc-800 bg-zinc-900/60 text-sm font-medium text-[hsl(var(--brand-primary))] mb-8 hover:border-zinc-700 transition-colors cursor-default"
        >
          <Sparkles className="w-4 h-4" />
          <span>AI Growth Strategist for B2B Sales</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight max-w-4xl leading-[1.1] bg-clip-text text-transparent bg-gradient-to-b from-white via-zinc-100 to-zinc-400"
        >
          Your AI Growth Strategist That Understands Your Business First
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-6 text-lg sm:text-xl text-[hsl(var(--text-secondary))] max-w-2xl leading-relaxed"
        >
          Visoora doesn&apos;t just automate sales — it first understands your
          business, then continuously identifies where and how you should grow.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-10 flex flex-col sm:flex-row items-center gap-4"
        >
          <Link
            href="/signup"
            className="w-full sm:w-auto px-8 py-4 rounded-xl font-bold text-white transition-all duration-300 hover:scale-[1.03] active:scale-[0.97] shadow-lg hover:shadow-[0_8px_32px_hsla(var(--brand-primary),0.3)] flex items-center justify-center gap-2 group"
            style={{
              background:
                "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
            }}
          >
            Start Free
            <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
          </Link>
          <Link
            href="/contact"
            className="w-full sm:w-auto px-8 py-4 rounded-xl font-semibold border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900 hover:border-zinc-700 transition-all flex items-center justify-center gap-2"
          >
            <span>Watch Demo</span>
          </Link>
        </motion.div>

        {/* Hero Animated Workflow */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="w-full max-w-3xl mt-20 rounded-2xl border border-zinc-800/60 bg-zinc-950/40 p-8 shadow-2xl relative overflow-hidden"
        >
          {/* Glow behind active step */}
          <div className="absolute inset-0 bg-gradient-to-b from-[hsla(var(--brand-primary),0.03)] to-transparent pointer-events-none" />

          <div className="flex items-center justify-between gap-2 sm:gap-4 relative z-10">
            {heroSteps.map((step, i) => (
              <React.Fragment key={step.label}>
                <WorkflowStep
                  icon={step.icon}
                  label={step.label}
                  delay={0.6 + i * 0.1}
                  isActive={i === activeStep}
                />
                {i < heroSteps.length - 1 && (
                  <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ delay: 0.7 + i * 0.1, duration: 0.4 }}
                    className={`hidden sm:block h-px flex-1 transition-colors duration-500 ${
                      i < activeStep
                        ? "bg-[hsl(var(--brand-primary))]"
                        : "bg-zinc-800"
                    }`}
                  />
                )}
              </React.Fragment>
            ))}
          </div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="text-center text-sm text-[hsl(var(--text-muted))] mt-6"
          >
            Visoora follows a strategic process — understand first, act second
          </motion.p>
        </motion.div>
      </section>

      {/* ============================================================
          SOCIAL PROOF BAR
          ============================================================ */}
      <section className="py-10 border-y border-zinc-900/60 bg-zinc-950/20 text-center">
        <div className="max-w-7xl mx-auto px-4">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--text-muted))] mb-6">
            Trusted by growth teams building smarter outbound
          </p>
          <div className="flex flex-wrap items-center justify-center gap-12 sm:gap-20 opacity-40">
            <span className="text-sm font-bold tracking-tight text-white select-none">VERTEX SOLUTIONS</span>
            <span className="text-sm font-bold tracking-tight text-white select-none">PULSE RECRUITING</span>
            <span className="text-sm font-bold tracking-tight text-white select-none">SKYLINE AGENCIES</span>
            <span className="text-sm font-bold tracking-tight text-white select-none">CLAYMORE B2B</span>
          </div>
        </div>
      </section>

      {/* ============================================================
          BUSINESS METRICS — OUTCOMES EXECUTIVES CARE ABOUT
          ============================================================ */}
      <Section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {metrics.map((m, i) => (
            <motion.div
              key={m.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass-card rounded-2xl p-6 text-center card-hover"
            >
              <div className="flex justify-center mb-3">
                <m.icon className="w-5 h-5 text-[hsl(var(--brand-primary))]" />
              </div>
              <div className="text-3xl sm:text-4xl font-extrabold text-gradient mb-1">
                {m.value}
                <span className="text-lg">{m.unit}</span>
              </div>
              <p className="text-sm text-[hsl(var(--text-secondary))] font-medium">
                {m.label}
              </p>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* ============================================================
          PROBLEM SECTION — "Why Traditional Outbound Fails"
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto" id="problems">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-primary))] mb-4">
            The Problem
          </h2>
          <p className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Why Traditional Outbound Fails
          </p>
          <p className="mt-4 text-lg text-[hsl(var(--text-secondary))] max-w-xl mx-auto">
            Most sales teams are stuck in a cycle of manual research, disconnected tools, and
            generic AI that doesn&apos;t understand their business.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {problems.map((p, i) => (
            <motion.div
              key={p.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15 }}
              className="glass-card rounded-2xl p-7 flex flex-col gap-4 card-hover"
            >
              <div className={`w-11 h-11 rounded-xl ${p.bg} flex items-center justify-center`}>
                <p.icon className={`w-5 h-5 ${p.color}`} />
              </div>
              <h3 className="text-lg font-bold">{p.title}</h3>
              <p className="text-base text-[hsl(var(--text-secondary))] leading-relaxed">
                {p.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* ============================================================
          SOLUTION — "How Visoora Thinks"
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900" id="how-it-works">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-accent))] mb-4">
            How It Works
          </h2>
          <p className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            An AI That Understands Before It Acts
          </p>
          <p className="mt-4 text-lg text-[hsl(var(--text-secondary))] max-w-xl mx-auto">
            Unlike generic AI tools, Visoora starts by building deep understanding of your business,
            then uses that context for every decision it makes.
          </p>
        </div>

        {/* Animated Solution Flow */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 max-w-5xl mx-auto">
          {[
            { icon: Globe, label: "Analyze Business", color: "from-emerald-500/20 to-emerald-500/5" },
            { icon: Brain, label: "Build Knowledge", color: "from-violet-500/20 to-violet-500/5" },
            { icon: Target, label: "Define ICP", color: "from-blue-500/20 to-blue-500/5" },
            { icon: Search, label: "Research Prospects", color: "from-amber-500/20 to-amber-500/5" },
            { icon: BarChart3, label: "Score & Rank", color: "from-rose-500/20 to-rose-500/5" },
            { icon: Mail, label: "Personalized Outreach", color: "from-[hsla(var(--brand-primary),0.2)] to-[hsla(var(--brand-primary),0.05)]" },
          ].map((step, i) => (
            <motion.div
              key={step.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="flex flex-col items-center gap-3 text-center"
            >
              <div className={`w-14 h-14 rounded-2xl bg-gradient-to-b ${step.color} border border-zinc-800/60 flex items-center justify-center`}>
                <step.icon className="w-6 h-6 text-white" />
              </div>
              <span className="text-sm font-semibold text-[hsl(var(--text-secondary))]">
                {step.label}
              </span>
              {i < 5 && (
                <ChevronRight className="w-4 h-4 text-zinc-700 hidden lg:block absolute" style={{ display: "none" }} />
              )}
            </motion.div>
          ))}
        </div>
      </Section>

      {/* ============================================================
          "ANALYZE MY WEBSITE" — INTERACTIVE DEMO (Reviewer #1)
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-primary))] mb-4">
            See It In Action
          </h2>
          <p className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Watch Visoora Analyze a Business
          </p>
          <p className="mt-4 text-lg text-[hsl(var(--text-secondary))] max-w-xl mx-auto">
            Enter any website URL and see how Visoora builds business intelligence in seconds.
          </p>
        </div>

        <div className="max-w-5xl mx-auto">
          {/* URL Input */}
          <div className="flex gap-3 mb-8 max-w-3xl mx-auto print:hidden">
            <div className="flex-1 relative">
              <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[hsl(var(--text-muted))]" />
              <input
                type="text"
                value={demoUrl}
                onChange={(e) => setDemoUrl(e.target.value)}
                placeholder="https://your-company.com"
                className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-xl py-3.5 pl-11 pr-4 text-[14px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))]"
                onKeyDown={(e) => e.key === "Enter" && handleDemoAnalyze()}
              />
            </div>
            <button
              onClick={handleDemoAnalyze}
              className="px-6 py-3.5 rounded-xl font-semibold text-white text-[14px] hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg"
              style={{
                background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
              }}
            >
              Analyze
            </button>
          </div>

          {/* Analysis Results */}
          <div id="printable-report" className="rounded-2xl border border-zinc-800/60 bg-zinc-950/60 overflow-hidden shadow-2xl">
            <DemoReport 
              analysisData={analysisData} 
              demoPhase={demoPhase} 
              demoError={demoError} 
            />
          </div>
        </div>
      </Section>

      {/* ============================================================
          AI CONVERSATION "WOW" MOMENT (Reviewer #2)
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-accent))] mb-4">
              The "Wow" Moment
            </h2>
            <p className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-6">
              AI That Proves It Understands
            </p>
            <p className="text-base text-[hsl(var(--text-secondary))] leading-relaxed mb-6">
              Most AI tools ask you questions. Visoora makes educated assumptions,
              explains its reasoning, and only asks for what it can&apos;t figure out itself.
            </p>
            <p className="text-sm text-[hsl(var(--text-muted))] italic">
              &quot;This AI is helping me make better business decisions.&quot;
            </p>
          </div>

          {/* Chat Mockup */}
          <div className="rounded-2xl border border-zinc-800/60 bg-zinc-950/60 overflow-hidden shadow-2xl">
            <div className="flex items-center gap-2 px-5 py-3 border-b border-zinc-900">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
              <span className="text-sm text-[hsl(var(--text-muted))] ml-2 font-mono">Visoora AI Consultant</span>
            </div>
            <div className="p-5 space-y-4 text-sm">
              {/* AI Message */}
              <div className="flex gap-3">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))] flex items-center justify-center flex-shrink-0">
                  <Zap className="w-3.5 h-3.5 text-white" />
                </div>
                <div className="glass-card rounded-xl rounded-tl-sm px-4 py-3 max-w-[85%]">
                  <p className="text-[hsl(var(--text-secondary))] leading-relaxed">
                    Hi! I analyzed your website. I believe you&apos;re a <strong className="text-white">software agency focused on startups and SMBs</strong>.
                    I also noticed you&apos;ve built healthcare and fintech projects. Is healthcare a target industry?
                  </p>
                </div>
              </div>
              {/* User Reply */}
              <div className="flex gap-3 justify-end">
                <div className="bg-[hsl(var(--surface-3))] rounded-xl rounded-tr-sm px-4 py-3 max-w-[70%]">
                  <p className="text-white">We want more healthcare clients.</p>
                </div>
              </div>
              {/* AI Follow-up */}
              <div className="flex gap-3">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))] flex items-center justify-center flex-shrink-0">
                  <Zap className="w-3.5 h-3.5 text-white" />
                </div>
                <div className="glass-card rounded-xl rounded-tl-sm px-4 py-3 max-w-[85%]">
                  <p className="text-[hsl(var(--text-secondary))] leading-relaxed mb-2">
                    Excellent choice. Healthcare companies have <strong className="text-white">longer sales cycles but higher contract values</strong>. I&apos;d recommend targeting:
                  </p>
                  <div className="flex flex-col gap-1.5">
                    {["HealthTech startups (50-200 employees)", "Multi-location clinics", "Healthcare SaaS companies"].map((rec) => (
                      <div key={rec} className="flex items-center gap-2 text-sm">
                        <CheckCircle2 className="w-3.5 h-3.5 text-[hsl(var(--brand-primary))]" />
                        <span className="text-[hsl(var(--text-secondary))]">{rec}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-[hsl(var(--brand-primary))] font-medium mt-3">
                    Confidence: 93% · Based on 1,200+ similar agencies
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Section>

      {/* ============================================================
          FEATURES — BUSINESS CAPABILITIES
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900" id="features">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-primary))] mb-4">
            Capabilities
          </h2>
          <p className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Business Intelligence, Not Just Features
          </p>
          <p className="mt-4 text-lg text-[hsl(var(--text-secondary))] max-w-xl mx-auto">
            Every capability is designed to help you make better business decisions, not just automate tasks.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass-card rounded-2xl p-7 flex flex-col gap-4 card-hover group"
            >
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[hsla(var(--brand-primary),0.15)] to-[hsla(var(--brand-accent),0.05)] border border-zinc-800/60 flex items-center justify-center group-hover:border-[hsla(var(--brand-primary),0.3)] transition-colors">
                <f.icon className="w-5 h-5 text-[hsl(var(--brand-primary))]" />
              </div>
              <h3 className="text-lg font-bold">{f.title}</h3>
              <p className="text-base text-[hsl(var(--text-secondary))] leading-relaxed">
                {f.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* ============================================================
          TRUST — VISUAL EVIDENCE WITH LEAD SCORE CARD (Reviewer #3)
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-accent))] mb-4">
              Transparent AI
            </h2>
            <p className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-6">
              Why You Can Trust AI Recommendations
            </p>
            <p className="text-base text-[hsl(var(--text-secondary))] leading-relaxed mb-8">
              Every AI decision shows its work. Confidence scores, data sources, and human-in-the-loop approval
              mean you always understand why a lead was scored, recommended, or flagged.
            </p>
            <div className="flex flex-col gap-4">
              {[
                { icon: Eye, label: "Inspect AI reasoning for every recommendation" },
                { icon: Shield, label: "Confirmed facts vs. AI estimates are visually distinct" },
                { icon: CheckCircle2, label: "Nothing goes out without your explicit approval" },
                { icon: FileText, label: "Full data sources and citations for every insight" },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-3">
                  <item.icon className="w-4.5 h-4.5 text-[hsl(var(--brand-primary))] flex-shrink-0" />
                  <span className="text-sm text-[hsl(var(--text-secondary))]">{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Lead Score Card Mockup */}
          <div className="rounded-2xl border border-zinc-800/60 bg-zinc-950/60 p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <h4 className="text-sm font-bold text-white">Lead Score Analysis</h4>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                HIGH CONFIDENCE
              </span>
            </div>

            {/* Score Circle */}
            <div className="flex items-center gap-6 mb-6">
              <div className="relative w-20 h-20">
                <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                  <circle cx="40" cy="40" r="35" fill="none" stroke="hsl(var(--surface-3))" strokeWidth="6" />
                  <circle cx="40" cy="40" r="35" fill="none" stroke="hsl(var(--brand-primary))" strokeWidth="6" strokeDasharray={`${94 * 2.2} 220`} strokeLinecap="round" />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-2xl font-extrabold text-white">94</span>
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Acme HealthTech</p>
                <p className="text-xs text-[hsl(var(--text-muted))]">Series B · 180 employees · San Francisco</p>
              </div>
            </div>

            {/* Matching Factors */}
            <div className="space-y-2.5 mb-5">
              <p className="text-sm font-bold text-[hsl(var(--text-muted))] uppercase tracking-wider">Matching Factors</p>
              {[
                { label: "Matches Healthcare ICP", icon: "✓", type: "confirmed" },
                { label: "Raised Series B ($18M)", icon: "✓", type: "confirmed" },
                { label: "Hiring 3 SDR positions", icon: "✓", type: "confirmed" },
                { label: "Uses HubSpot CRM", icon: "~", type: "estimated" },
              ].map((factor) => (
                <div key={factor.label} className="flex items-center gap-2.5">
                  <span className={`w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold ${
                    factor.type === "confirmed"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  }`}>
                    {factor.icon}
                  </span>
                  <span className="text-sm text-[hsl(var(--text-secondary))]">{factor.label}</span>
                  {factor.type === "estimated" && (
                    <span className="text-[10px] text-amber-400/80 font-medium ml-auto">AI Estimate</span>
                  )}
                </div>
              ))}
            </div>

            {/* Sources */}
            <div className="pt-4 border-t border-zinc-900">
              <p className="text-sm font-bold text-[hsl(var(--text-muted))] uppercase tracking-wider mb-2">Sources</p>
              <div className="flex flex-wrap gap-2">
                {["Website", "Crunchbase", "Job Boards"].map((src) => (
                  <span key={src} className="px-2 py-1 rounded-md text-[10px] font-medium bg-[hsl(var(--surface-3))] text-[hsl(var(--text-secondary))] border border-zinc-800">
                    {src}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </Section>

      {/* ============================================================
          AI BUSINESS BRAIN VISUALIZATION (Reviewer #4)
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-primary))] mb-4">
            AI Business Brain
          </h2>
          <p className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            A Living Map of Your Business Intelligence
          </p>
          <p className="mt-4 text-lg text-[hsl(var(--text-secondary))] max-w-xl mx-auto">
            Visoora builds a structured knowledge graph from your website, products, customers, and market data.
            Every AI decision is grounded in this deep business understanding.
          </p>
        </div>

        {/* Business Brain Visual */}
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { icon: Globe, label: "Website & Products", desc: "Value proposition, services, pricing", color: "from-emerald-500/20 to-emerald-500/5", border: "border-emerald-500/20" },
            { icon: Users, label: "Customers", desc: "Industries, sizes, decision makers", color: "from-blue-500/20 to-blue-500/5", border: "border-blue-500/20" },
            { icon: Compass, label: "Competitors", desc: "Positioning, differentiators, gaps", color: "from-rose-500/20 to-rose-500/5", border: "border-rose-500/20" },
            { icon: Target, label: "ICP Segments", desc: "Ideal profiles with confidence", color: "from-violet-500/20 to-violet-500/5", border: "border-violet-500/20" },
            { icon: Users, label: "Buyer Personas", desc: "Titles, pain points, motivations", color: "from-amber-500/20 to-amber-500/5", border: "border-amber-500/20" },
            { icon: Lightbulb, label: "Objections", desc: "Common pushbacks and responses", color: "from-cyan-500/20 to-cyan-500/5", border: "border-cyan-500/20" },
            { icon: Search, label: "Market Intel", desc: "Trends, signals, opportunities", color: "from-pink-500/20 to-pink-500/5", border: "border-pink-500/20" },
            { icon: TrendingUp, label: "Growth Strategy", desc: "Prioritized action plan", color: "from-[hsla(var(--brand-primary),0.2)] to-[hsla(var(--brand-primary),0.05)]", border: "border-[hsla(var(--brand-primary),0.3)]" },
          ].map((node, i) => (
            <motion.div
              key={node.label}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className={`glass-card rounded-xl p-5 card-hover border ${node.border}`}
            >
              <div className={`w-9 h-9 rounded-lg bg-gradient-to-b ${node.color} flex items-center justify-center mb-3`}>
                <node.icon className="w-4 h-4 text-white" />
              </div>
              <h4 className="text-sm font-bold text-white mb-1">{node.label}</h4>
              <p className="text-sm text-[hsl(var(--text-muted))] leading-relaxed">{node.desc}</p>
            </motion.div>
          ))}
        </div>

        <p className="text-center text-sm text-[hsl(var(--text-muted))] mt-8">
          Every data point connects to form your complete business intelligence profile
        </p>
      </Section>

      {/* ============================================================
          "WHY VISOORA" — PHILOSOPHY COMPARISON (Reviewer #5)
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-accent))] mb-4">
            Why Visoora
          </h2>
          <p className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            A Different Philosophy, Not Just Different Features
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Traditional Approach */}
          <div className="rounded-2xl border border-zinc-800/60 bg-zinc-950/40 p-8">
            <h3 className="text-sm font-bold text-[hsl(var(--text-muted))] uppercase tracking-wider mb-6">
              Traditional Outbound
            </h3>
            <div className="flex flex-col gap-3">
              {["Guess", "Research manually", "Build spreadsheets", "Write generic emails", "Send and hope", "Repeat"].map((step, i) => (
                <div key={step} className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-md bg-zinc-800 flex items-center justify-center text-[10px] font-mono text-[hsl(var(--text-muted))]">
                    {i + 1}
                  </span>
                  <span className="text-sm text-[hsl(var(--text-muted))] line-through decoration-zinc-700">{step}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Visoora Approach */}
          <div className="rounded-2xl border border-[hsla(var(--brand-primary),0.2)] bg-[hsla(var(--brand-primary),0.03)] p-8 gradient-border">
            <h3 className="text-sm font-bold text-[hsl(var(--brand-primary))] uppercase tracking-wider mb-6">
              Visoora Approach
            </h3>
            <div className="flex flex-col gap-3">
              {[
                { label: "Understand", desc: "Deep business analysis" },
                { label: "Analyze", desc: "Market & competitor research" },
                { label: "Strategize", desc: "ICP & persona design" },
                { label: "Prioritize", desc: "Scored & ranked leads" },
                { label: "Execute", desc: "Personalized outreach" },
                { label: "Learn", desc: "Continuous improvement" },
              ].map((step, i) => (
                <div key={step.label} className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-md bg-gradient-to-br from-[hsla(var(--brand-primary),0.2)] to-[hsla(var(--brand-accent),0.1)] border border-[hsla(var(--brand-primary),0.3)] flex items-center justify-center text-[10px] font-mono text-[hsl(var(--brand-primary))]">
                    {i + 1}
                  </span>
                  <div>
                    <span className="text-sm font-semibold text-white">{step.label}</span>
                    <span className="text-sm text-[hsl(var(--text-muted))] ml-2">{step.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* One vs Five comparison */}
        <div className="mt-12 text-center max-w-2xl mx-auto">
          <p className="text-sm text-[hsl(var(--text-secondary))]">
            Replace <span className="text-[hsl(var(--text-muted))] line-through">Apollo + Clay + CRM + ChatGPT + Email Tool</span> with
          </p>
          <p className="text-lg font-bold text-gradient mt-2">One AI Growth Strategist</p>
        </div>
      </Section>

      {/* ============================================================
          AI MEMORY — LONG-TERM PARTNER (Reviewer #6)
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Memory Visual */}
          <div className="order-2 lg:order-1 grid grid-cols-2 gap-3">
            {[
              { icon: Database, label: "Business Context", desc: "Your products, values, and positioning" },
              { icon: Activity, label: "Campaign History", desc: "What worked, what didn't, and why" },
              { icon: Award, label: "Winning Industries", desc: "Verticals where you close fastest" },
              { icon: GitBranch, label: "ICP Evolution", desc: "How your ideal customer profile grows" },
              { icon: Star, label: "Top Performers", desc: "Patterns from your best-converting leads" },
              { icon: BookOpen, label: "Objection Playbook", desc: "Refined responses from real conversations" },
            ].map((item, i) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="glass-card rounded-xl p-4 card-hover"
              >
                <item.icon className="w-4 h-4 text-[hsl(var(--brand-primary))] mb-2" />
                <h4 className="text-sm font-bold text-white mb-0.5">{item.label}</h4>
                <p className="text-[10px] text-[hsl(var(--text-muted))] leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>

          <div className="order-1 lg:order-2">
            <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-primary))] mb-4">
              AI Memory
            </h2>
            <p className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-6">
              An AI That Learns and Remembers
            </p>
            <p className="text-base text-[hsl(var(--text-secondary))] leading-relaxed mb-4">
              Visoora isn&apos;t a stateless chatbot. It remembers your business context,
              previous campaigns, winning industries, lost deals, and customer feedback.
            </p>
            <p className="text-base text-[hsl(var(--text-secondary))] leading-relaxed">
              Over time, it becomes a <strong className="text-white">long-term strategic partner</strong> that
              gets smarter with every interaction.
            </p>
          </div>
        </div>
      </Section>

      {/* ============================================================
          CUSTOMER JOURNEY
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto border-t border-zinc-900">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-accent))] mb-4">
            Your Journey
          </h2>
          <p className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            From Understanding to Growth
          </p>
        </div>

        <div className="relative">
          {/* Connecting Line */}
          <div className="absolute left-[22px] md:left-1/2 md:-translate-x-px top-0 bottom-0 w-px bg-gradient-to-b from-[hsl(var(--brand-primary))] via-[hsl(var(--brand-accent))] to-[hsl(var(--brand-primary))] opacity-20" />

          <div className="space-y-6">
            {journeySteps.map((step, i) => (
              <motion.div
                key={step.label}
                initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className={`flex items-center gap-4 ${
                  i % 2 === 0 ? "md:flex-row" : "md:flex-row-reverse"
                }`}
              >
                <div className={`flex-1 ${i % 2 === 0 ? "md:text-right" : "md:text-left"} hidden md:block`}>
                  <h4 className="text-sm font-bold text-white">{step.label}</h4>
                  <p className="text-sm text-[hsl(var(--text-muted))]">{step.desc}</p>
                </div>

                <div className="w-11 h-11 rounded-xl bg-[hsl(var(--surface-2))] border border-zinc-800 flex items-center justify-center flex-shrink-0 z-10 relative">
                  <step.icon className="w-5 h-5 text-[hsl(var(--brand-primary))]" />
                </div>

                <div className="flex-1 md:hidden">
                  <h4 className="text-sm font-bold text-white">{step.label}</h4>
                  <p className="text-sm text-[hsl(var(--text-muted))]">{step.desc}</p>
                </div>

                <div className={`flex-1 hidden md:block ${i % 2 === 0 ? "" : "text-right"}`} />
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* ============================================================
          PRICING + ROADMAP (Reviewer #7)
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-zinc-900" id="pricing">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-primary))] mb-4">
            Pricing
          </h2>
          <p className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Simple, Transparent Pricing
          </p>
          <p className="mt-4 text-lg text-[hsl(var(--text-secondary))] max-w-xl mx-auto">
            Start free. Scale as you grow. No hidden fees.
          </p>

          {/* Period Toggle */}
          <div className="flex items-center justify-center gap-3 mt-8">
            <button
              onClick={() => setPricingPeriod("monthly")}
              className={`text-sm font-medium px-4 py-2 rounded-lg transition-all ${
                pricingPeriod === "monthly" ? "text-white bg-[hsl(var(--surface-3))]" : "text-[hsl(var(--text-muted))]"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setPricingPeriod("yearly")}
              className={`text-sm font-medium px-4 py-2 rounded-lg transition-all ${
                pricingPeriod === "yearly" ? "text-white bg-[hsl(var(--surface-3))]" : "text-[hsl(var(--text-muted))]"
              }`}
            >
              Yearly
              <span className="ml-1.5 text-[10px] text-[hsl(var(--brand-primary))] font-bold">Save 20%</span>
            </button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mb-20">
          {[
            {
              name: "Starter",
              price: pricingPeriod === "monthly" ? "$99" : "$79",
              period: "/mo",
              desc: "For solo founders and small teams getting started",
              features: ["AI Business Brain", "500 prospect imports/mo", "Lead scoring", "Email draft generation", "1 user"],
              cta: "Join Waitlist",
              highlight: false,
            },
            {
              name: "Growth",
              price: pricingPeriod === "monthly" ? "$299" : "$239",
              period: "/mo",
              desc: "For growth teams ready to scale outbound",
              features: ["Everything in Starter", "5,000 prospect imports/mo", "AI Voice Agent", "Company research", "5 users", "Priority support"],
              cta: "Join Waitlist",
              highlight: true,
            },
            {
              name: "Enterprise",
              price: "Custom",
              period: "",
              desc: "For organizations that need full control",
              features: ["Everything in Growth", "Unlimited imports", "Custom integrations", "SSO & SAML", "Dedicated CSM", "SLA guarantee"],
              cta: "Contact Sales",
              highlight: false,
            },
          ].map((plan) => (
            <div
              key={plan.name}
              className={`rounded-2xl p-7 flex flex-col ${
                plan.highlight
                  ? "border-2 border-[hsla(var(--brand-primary),0.4)] bg-[hsla(var(--brand-primary),0.03)] relative"
                  : "border border-zinc-800/60 bg-zinc-950/40"
              }`}
            >
              {plan.highlight && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-[10px] font-bold bg-gradient-to-r from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))] text-white uppercase tracking-wider">
                  Most Popular
                </span>
              )}
              <h3 className="text-lg font-bold text-white mb-1">{plan.name}</h3>
              <p className="text-sm text-[hsl(var(--text-muted))] mb-4">{plan.desc}</p>
              <div className="mb-6">
                <span className="text-3xl font-extrabold text-white">{plan.price}</span>
                <span className="text-sm text-[hsl(var(--text-muted))]">{plan.period}</span>
              </div>
              <div className="flex flex-col gap-2.5 mb-8 flex-1">
                {plan.features.map((f) => (
                  <div key={f} className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[hsl(var(--brand-primary))]" />
                    <span className="text-sm text-[hsl(var(--text-secondary))]">{f}</span>
                  </div>
                ))}
              </div>
              <Link
                href="/signup"
                className={`w-full text-center py-2.5 rounded-xl text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] ${
                  plan.highlight
                    ? "text-white shadow-lg"
                    : "text-white border border-zinc-800 hover:border-zinc-700 bg-[hsl(var(--surface-2))]"
                }`}
                style={plan.highlight ? {
                  background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
                } : {}}
              >
                {plan.cta}
              </Link>
              <p className="text-center text-[10px] text-[hsl(var(--text-muted))] mt-2">Coming Soon</p>
            </div>
          ))}
        </div>

        {/* Roadmap */}
        <div className="max-w-3xl mx-auto" id="roadmap">
          <div className="text-center mb-8">
            <h3 className="text-xl font-bold text-white mb-2">Product Roadmap</h3>
            <p className="text-sm text-[hsl(var(--text-muted))]">Where we are and where we&apos;re headed</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {roadmapItems.map((item) => (
              <div key={item.label} className="glass-card rounded-xl p-4 flex items-center gap-3">
                <item.icon className={`w-4 h-4 flex-shrink-0 ${
                  item.status === "live" ? "text-emerald-400" : "text-[hsl(var(--text-muted))]"
                }`} />
                <div>
                  <p className="text-sm font-semibold text-white">{item.label}</p>
                  <span className={`text-[10px] font-bold uppercase tracking-wider ${
                    item.status === "live" ? "text-emerald-400" : "text-[hsl(var(--text-muted))]"
                  }`}>
                    {item.status === "live" ? "● Live" : "○ Coming Soon"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* ============================================================
          FAQ SECTION
          ============================================================ */}
      <Section className="py-24 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto border-t border-zinc-900">
        <div className="text-center mb-16">
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-[hsl(var(--brand-primary))] mb-4">
            FAQ
          </h2>
          <p className="text-3xl font-extrabold tracking-tight">
            Questions &amp; Answers
          </p>
        </div>

        <div className="flex flex-col gap-3">
          {faqs.map((item, index) => (
            <div
              key={index}
              className="rounded-xl border border-zinc-800/60 bg-zinc-950/40 overflow-hidden transition-colors"
            >
              <button
                onClick={() => toggleFaq(index)}
                className="w-full px-6 py-5 flex items-center justify-between text-left font-semibold text-[14px] hover:bg-zinc-900/30 transition-colors"
              >
                <span>{item.q}</span>
                <ChevronDown
                  className={`w-4 h-4 text-[hsl(var(--text-muted))] transition-transform duration-200 flex-shrink-0 ml-4 ${
                    activeFaq === index ? "rotate-180" : ""
                  }`}
                />
              </button>
              {activeFaq === index && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="px-6 pb-5 text-base text-[hsl(var(--text-secondary))] leading-relaxed border-t border-zinc-900 pt-4"
                >
                  {item.a}
                </motion.div>
              )}
            </div>
          ))}
        </div>
      </Section>

      {/* ============================================================
          FINAL CTA
          ============================================================ */}
      <section className="py-24 px-4 text-center border-t border-zinc-900 bg-gradient-to-b from-zinc-950/20 to-zinc-950 relative overflow-hidden">
        <div className="absolute inset-0 bg-[hsl(var(--brand-primary))]/2 opacity-5 blur-[100px] pointer-events-none" />
        <div className="max-w-3xl mx-auto flex flex-col items-center relative z-10">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl sm:text-4xl font-extrabold tracking-tight"
          >
            Ready to Grow Smarter?
          </motion.h2>
          <p className="mt-4 text-base text-[hsl(var(--text-secondary))] max-w-lg">
            Join the next generation of B2B growth teams using AI strategy, not AI spam.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center gap-4">
            <Link
              href="/signup"
              className="w-full sm:w-auto px-8 py-4 rounded-xl font-bold text-white transition-all duration-300 hover:scale-[1.03] active:scale-[0.97] shadow-lg hover:shadow-[0_8px_32px_hsla(var(--brand-primary),0.3)] flex items-center justify-center gap-2 group"
              style={{
                background:
                  "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
              }}
            >
              Start Free
              <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              href="/contact"
              className="w-full sm:w-auto px-8 py-4 rounded-xl font-semibold border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900 hover:border-zinc-700 transition-all flex items-center justify-center"
            >
              Book a Demo
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
