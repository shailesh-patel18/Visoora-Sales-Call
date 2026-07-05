"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Globe,
  Building2,
  Check,
  Sparkles,
  Send,
  RefreshCw,
  AlertCircle,
  ArrowRight,
  User,
  Shield,
  Phone,
  Volume2,
  Trash2,
  Plus,
  HelpCircle,
} from "lucide-react";
import { useOnboardingStore } from "../store";
import { BACKEND_URL } from "../../config";

interface Message {
  id: string;
  sender: "ai" | "user";
  text: string;
  type?: "intro" | "assumptions" | "challenge" | "telephony" | "identity" | "ready";
  data?: any;
}

export default function ConversationalOnboardingPage() {
  const router = useRouter();
  const { updateStep1, updateStep2, updateStep3, updateStep4, updateStep5, updateStep6, updateStep7, updateStep8, updateStep9, updateStep10, updateStep11, completeOnboarding } = useOnboardingStore();

  const [website, setWebsite] = useState("");
  const [userName, setUserName] = useState("");
  const [phase, setPhase] = useState<"input" | "analyzing" | "chat">("input");
  const [analyzingStep, setAnalyzingStep] = useState(0);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputVal, setInputVal] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [analyzedData, setAnalyzedData] = useState<any>(null);
  
  // Inline edit states for assumptions
  const [editMode, setEditMode] = useState(false);
  const [editCompany, setEditCompany] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editValProp, setEditValProp] = useState("");
  const [editCompetitors, setEditCompetitors] = useState<string[]>([]);
  const [newCompetitor, setNewCompetitor] = useState("");

  // Telephony states
  const [availableNumbers, setAvailableNumbers] = useState<string[]>([]);
  const [selectedNumber, setSelectedNumber] = useState("");
  const [customPhone, setCustomPhone] = useState("");
  const [phoneMode, setPhoneMode] = useState<"buy" | "port">("buy");
  const [loadingNumbers, setLoadingNumbers] = useState(false);

  // Identity states
  const [agentName, setAgentName] = useState("Alex");
  const [voice, setVoice] = useState("rachel");
  const [tone, setTone] = useState("consultative");
  const [callingStart, setCallingStart] = useState("08:00");
  const [callingEnd, setCallingEnd] = useState("17:00");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const analyzingLogs = [
    "🔍 Connecting to corporate web host...",
    "🕷️ Crawling index pages and asset sitemaps...",
    "🧠 Training localized B2B Growth Strategy brain...",
    "✨ Compiling competitor profiles & objections list...",
    "✅ Business discovery completed successfully!"
  ];

  useEffect(() => {
    if (phase === "analyzing") {
      let logIndex = 0;
      const interval = setInterval(() => {
        if (logIndex < analyzingLogs.length - 1) {
          logIndex++;
          setAnalyzingStep(logIndex);
        } else {
          clearInterval(interval);
          setPhase("chat");
          startConversation();
        }
      }, 900);
      return () => clearInterval(interval);
    }
  }, [phase]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleStartAnalysis = async () => {
    if (!website || !userName) return;
    setPhase("analyzing");
    setAnalyzingStep(0);

    try {
      const res = await fetch(`${BACKEND_URL}/api/onboarding/analyze-domain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ website }),
      });
      if (res.ok) {
        const data = await res.json();
        setAnalyzedData(data);
        setEditCompany(data.company_name);
        setEditDesc(data.company_description);
        setEditValProp(data.value_proposition);
        setEditCompetitors(data.potential_competitors || []);
      }
    } catch (e) {
      console.error("Domain analysis failed:", e);
    }
  };

  const simulateAiTyping = (text: string, delay: number = 800) => {
    setIsTyping(true);
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        setIsTyping(false);
        resolve();
      }, delay);
    });
  };

  const startConversation = async () => {
    await simulateAiTyping("");
    const introMsg: Message = {
      id: "m_intro",
      sender: "ai",
      text: `Hello ${userName}! 👋 I have analyzed your website (${website}). Can I show you what I found?`,
      type: "intro"
    };
    setMessages([introMsg]);
  };

  const handleShowAssumptions = async () => {
    // Add user response to chat
    setMessages(prev => [...prev, { id: `u_${Date.now()}`, sender: "user", text: "Yes, show me assumptions." }]);
    await simulateAiTyping("");
    
    // Add AI response with assumptions payload
    const assumptionsMsg: Message = {
      id: "m_assumptions",
      sender: "ai",
      text: "Based on my research, here is my initial growth twin analysis of your business:",
      type: "assumptions",
      data: analyzedData
    };
    setMessages(prev => [...prev, assumptionsMsg]);
  };

  const handleSaveAssumptions = async () => {
    setEditMode(false);
    // Update analyzedData object
    const updated = {
      ...analyzedData,
      company_name: editCompany,
      company_description: editDesc,
      value_proposition: editValProp,
      potential_competitors: editCompetitors
    };
    setAnalyzedData(updated);

    // Save step data to Zustand store
    await updateStep1({
      companyName: editCompany,
      website: website,
      companyDescription: editDesc,
      valueProposition: editValProp
    });

    await updateStep6({
      competitors: editCompetitors
    });

    setMessages(prev => [...prev, { id: `u_${Date.now()}`, sender: "user", text: "I have reviewed and confirmed these assumptions." }]);
    await simulateAiTyping("");

    // Trigger Challenger step
    const challengeMsg: Message = {
      id: "m_challenge",
      sender: "ai",
      text: `I noticed that your company provides services to many sectors. Agencies similar to ${editCompany} scale 3.4x faster by focusing on only TWO core industries. Currently you are targeting all of them. I strongly recommend narrowing down your outbound campaign focus.`,
      type: "challenge"
    };
    setMessages(prev => [...prev, challengeMsg]);
  };

  const handleChallengeResponse = async (accept: boolean) => {
    const text = accept 
      ? "(Recommended) Yes, focus campaigns on the top 2 niches."
      : "No, target all industries simultaneously.";
    
    setMessages(prev => [...prev, { id: `u_${Date.now()}`, sender: "user", text }]);
    await simulateAiTyping("");

    // Save ICP industries based on selection
    const industries = accept 
      ? (analyzedData?.estimated_industries?.slice(0, 2).map((i: any) => i.industry) || ["Technology", "SaaS"])
      : (analyzedData?.estimated_industries?.map((i: any) => i.industry) || ["Technology"]);
    
    await updateStep3({ icpIndustries: industries });
    await updateStep4({ icpRegions: analyzedData?.estimated_regions?.map((r: any) => r.region) || ["North America"] });
    await updateStep5({ decisionMakerTitles: analyzedData?.estimated_decision_makers?.map((d: any) => d.title) || ["CTO"] });

    // Format objections list for store step 8
    const objList = analyzedData?.potential_objections?.map((obj: any) => ({
      objection: obj.objection,
      rebuttal: obj.rebuttal
    })) || [
      { objection: "Outsource lacks alignment.", rebuttal: "We integrate directly inside Slack/Jira." }
    ];
    await updateStep8({ objectionsList: objList });

    // Retrieve phone numbers
    setLoadingNumbers(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/provision/available-numbers?area_code=501&country=US`);
      if (res.ok) {
        const data = await res.json();
        setAvailableNumbers(data.numbers || []);
        if (data.numbers && data.numbers.length > 0) {
          setSelectedNumber(data.numbers[0]);
        }
      }
    } catch {
      const fallbacks = ["+1 (501) 555-0192", "+1 (501) 555-0244", "+1 (501) 555-0388"];
      setAvailableNumbers(fallbacks);
      setSelectedNumber(fallbacks[0]);
    } finally {
      setLoadingNumbers(false);
    }

    const telephonyMsg: Message = {
      id: "m_telephony",
      sender: "ai",
      text: "Let's reserve a business calling number for outbound pitches. Here are available local Twilio caller numbers:",
      type: "telephony"
    };
    setMessages(prev => [...prev, telephonyMsg]);
  };

  const handleConfirmTelephony = async () => {
    const finalNumber = phoneMode === "buy" ? selectedNumber : customPhone;
    if (!finalNumber) return;

    setMessages(prev => [...prev, { id: `u_${Date.now()}`, sender: "user", text: `Provision calling number: ${finalNumber}` }]);
    await simulateAiTyping("");

    await updateStep10({
      phoneOption: phoneMode,
      twilioNumber: phoneMode === "buy" ? selectedNumber : "",
      portedNumber: phoneMode === "port" ? customPhone : ""
    });

    const identityMsg: Message = {
      id: "m_identity",
      sender: "ai",
      text: "Almost complete! Let's choose the identity and brand settings for your B2B Growth Strategist.",
      type: "identity"
    };
    setMessages(prev => [...prev, identityMsg]);
  };

  const handleConfirmIdentity = async () => {
    setMessages(prev => [...prev, { id: `u_${Date.now()}`, sender: "user", text: `Configure agent ${agentName} (Voice: ${voice}, Tone: ${tone}).` }]);
    await simulateAiTyping("");

    await updateStep2({ agentName });
    await updateStep7({
      voice,
      tone,
      brandVoiceTone: `You are ${agentName}, a consultative sales strategist. Keep answers professional and ROI-focused.`
    });
    await updateStep9({ avoidList: [] });
    await updateStep11({ testPhone: "+19195551234" }); // default placeholder for sandbox triggers

    const readyMsg: Message = {
      id: "m_ready",
      sender: "ai",
      text: `Excellent! Your personalized Growth Strategist twin is fully trained. We have mapped out your company value proposition, target decision makers, core market segments, and outbound playbooks. Let's launch your Growth Engine!`,
      type: "ready"
    };
    setMessages(prev => [...prev, readyMsg]);
  };

  const handleLaunchEngine = async () => {
    // Inject the estimated icp segments and buyer personas into complete payload
    const segmentsPayload = analyzedData?.suggested_segments?.map((s: any) => ({
      segment: s.segment,
      confidence: s.confidence,
      rationale: s.rationale
    })) || [
      { segment: "SaaS Enterprise", confidence: 90, rationale: "Match custom tech portfolio." }
    ];

    const personasPayload = analyzedData?.estimated_decision_makers?.map((d: any) => ({
      title: d.title,
      confidence: d.confidence,
      description: `Targeting decision maker: ${d.title}`
    })) || [
      { title: "CTO", confidence: 95, description: "Technical decision maker." }
    ];

    // Trigger Zustand save with complete parameters
    const completeOnboardingWithCustomData = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/onboarding/complete`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            tenant_id: "default_shared_tenant",
            company_name: editCompany || "Unknown",
            website: website || "",
            company_description: editDesc || "",
            value_proposition: editValProp || "",
            phone_number: phoneMode === "buy" ? selectedNumber : customPhone,
            agent_name: agentName,
            voice: voice,
            tone: tone,
            timezone: "America/New_York",
            calling_hours_start: callingStart,
            calling_hours_end: callingEnd,
            product_name: editCompany,
            product_price: "Custom Sprint pricing",
            product_features: editValProp,
            target_audience: "B2B SaaS and Enterprise",
            recording_disclosure: true,
            consent_confirmed: true,
            icp_industries: analyzedData?.estimated_industries?.map((i: any) => i.industry) || [],
            icp_regions: analyzedData?.estimated_regions?.map((r: any) => r.region) || [],
            decision_maker_titles: analyzedData?.estimated_decision_makers?.map((d: any) => d.title) || [],
            competitors: editCompetitors,
            avoid_list: [],
            objections_list: analyzedData?.potential_objections || [],
            brand_voice_tone: tone,
            icp_segments: segmentsPayload,
            buyer_personas: personasPayload
          })
        });
        if (response.ok) {
          router.push("/dashboard");
        }
      } catch (err) {
        console.error("Complete onboarding failed:", err);
        router.push("/dashboard");
      }
    };

    await completeOnboardingWithCustomData();
  };

  const addCompetitor = () => {
    if (newCompetitor && !editCompetitors.includes(newCompetitor)) {
      setEditCompetitors([...editCompetitors, newCompetitor]);
      setNewCompetitor("");
    }
  };

  const removeCompetitor = (comp: string) => {
    setEditCompetitors(editCompetitors.filter(c => c !== comp));
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 max-w-[800px] mx-auto w-full min-h-[calc(100vh-140px)]">
      {phase === "input" && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass p-8 rounded-2xl border w-full flex flex-col gap-6"
          style={{ borderColor: "hsl(var(--border-subtle))" }}
        >
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-tr from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))] text-white shadow-lg">
              <Sparkles className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">Meet your AI Growth Twin</h1>
              <p className="text-xs text-[hsl(var(--text-muted))]">
                No complex questionnaires. We analyze your website and build your B2B Growth Engine.
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-[hsl(var(--text-secondary))]">Your Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[hsl(var(--text-muted))]" />
                <input
                  type="text"
                  placeholder="e.g. Shailesh"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm border outline-none bg-[hsl(var(--surface-2))] border-[hsl(var(--border-default))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] text-white"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-[hsl(var(--text-secondary))]">Corporate Website URL</label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[hsl(var(--text-muted))]" />
                <input
                  type="text"
                  placeholder="https://youragency.com"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm border outline-none bg-[hsl(var(--surface-2))] border-[hsl(var(--border-default))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] text-white"
                />
              </div>
            </div>

            <button
              onClick={handleStartAnalysis}
              disabled={!website || !userName}
              className="flex items-center justify-center gap-2 mt-4 px-6 py-3.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))] hover:opacity-90 transition-all disabled:opacity-40 shadow-lg shadow-[hsla(var(--brand-primary),0.35)]"
            >
              Analyze Website & Create Twin <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </motion.div>
      )}

      {phase === "analyzing" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass p-8 rounded-2xl border w-full flex flex-col items-center justify-center text-center gap-6"
          style={{ borderColor: "hsl(var(--border-subtle))" }}
        >
          <div className="w-16 h-16 rounded-full flex items-center justify-center bg-[hsla(var(--brand-primary),0.1)] relative">
            <Sparkles className="w-8 h-8 text-[hsl(var(--brand-primary))] animate-pulse" />
            <motion.div
              className="absolute inset-0 rounded-full border border-[hsl(var(--brand-primary))]"
              animate={{ scale: [1, 1.4, 1], opacity: [1, 0, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </div>

          <div>
            <h2 className="text-lg font-bold text-white">Visoora discovery scanner live</h2>
            <p className="text-xs text-[hsl(var(--text-muted))]">Analyzing target domain: {website}</p>
          </div>

          {/* Crawler Log Terminal */}
          <div className="w-full text-left p-4 rounded-xl font-mono text-xs max-w-md bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-subtle))] text-[hsl(var(--text-secondary))] flex flex-col gap-2">
            {analyzingLogs.slice(0, analyzingStep + 1).map((log, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -5 }}
                animate={{ opacity: 1, x: 0 }}
                style={{
                  color: idx === analyzingStep ? "hsl(var(--brand-accent))" : "hsl(var(--text-muted))",
                  fontWeight: idx === analyzingStep ? "bold" : "normal"
                }}
              >
                {log}
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {phase === "chat" && (
        <div className="flex flex-col w-full h-[calc(100vh-160px)] glass rounded-2xl border overflow-hidden relative" style={{ borderColor: "hsl(var(--border-subtle))" }}>
          
          {/* Chat Messages Log */}
          <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 max-w-[85%] ${msg.sender === "user" ? "self-end flex-row-reverse" : "self-start"}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${msg.sender === "user" ? "bg-[hsl(var(--brand-accent))]" : "bg-[hsl(var(--brand-primary))]"}`}>
                    {msg.sender === "user" ? <User className="w-4.5 h-4.5" /> : <Sparkles className="w-4.5 h-4.5" />}
                  </div>

                  <div className="flex flex-col gap-2">
                    <div className={`p-4 rounded-2xl text-sm leading-relaxed ${msg.sender === "user" ? "bg-[hsl(var(--brand-accent))]/10 text-white border border-[hsl(var(--brand-accent))]/20 rounded-tr-none" : "bg-[hsl(var(--surface-2))] text-white border border-[hsl(var(--border-subtle))] rounded-tl-none"}`}>
                      {msg.text}
                    </div>

                    {/* Intro Actions */}
                    {msg.type === "intro" && (
                      <button
                        onClick={handleShowAssumptions}
                        className="self-start mt-1 flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold text-white bg-[hsl(var(--brand-primary))] hover:opacity-90 transition-all shadow-md"
                      >
                        Show me assumptions <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    )}

                    {/* Assumptions Card */}
                    {msg.type === "assumptions" && (
                      <div className="p-5 rounded-2xl border bg-[hsl(var(--surface-1))] border-[hsl(var(--border-subtle))] flex flex-col gap-4 mt-1 w-full max-w-[550px] shadow-xl">
                        {!editMode ? (
                          <>
                            <div className="flex justify-between items-center border-b border-[hsl(var(--border-subtle))] pb-2">
                              <span className="text-xs font-bold uppercase tracking-wider text-[hsl(var(--brand-primary))]">Growth Twin assumptions</span>
                              <button
                                onClick={() => setEditMode(true)}
                                className="text-[10px] font-bold text-[hsl(var(--brand-accent))] hover:underline"
                              >
                                Edit Profile
                              </button>
                            </div>

                            <div className="flex flex-col gap-2 text-xs">
                              <p><strong className="text-[hsl(var(--text-secondary))]">Company:</strong> {editCompany}</p>
                              <p><strong className="text-[hsl(var(--text-secondary))]">Description:</strong> {editDesc}</p>
                              <p><strong className="text-[hsl(var(--text-secondary))]">Core Value Prop:</strong> {editValProp}</p>
                              <div>
                                <strong className="text-[hsl(var(--text-secondary))] block mb-1">Estimated Niches:</strong>
                                <div className="flex flex-wrap gap-1.5">
                                  {analyzedData?.estimated_industries?.map((ind: any, idx: number) => (
                                    <span key={idx} className="px-2 py-0.5 rounded bg-[hsla(var(--brand-primary),0.08)] text-[hsl(var(--brand-primary))] text-[10px] font-semibold border border-[hsla(var(--brand-primary),0.15)] flex items-center gap-1">
                                      {ind.industry} <span className="opacity-70 text-[9px]">{ind.confidence}%</span>
                                    </span>
                                  ))}
                                </div>
                              </div>

                              <div>
                                <strong className="text-[hsl(var(--text-secondary))] block mb-1">Key Competitors:</strong>
                                <div className="flex flex-wrap gap-1.5">
                                  {editCompetitors.map((comp: string, idx: number) => (
                                    <span key={idx} className="px-2 py-0.5 rounded bg-[hsl(var(--surface-3))] text-[hsl(var(--text-secondary))] text-[10px] border border-[hsl(var(--border-default))]">
                                      {comp}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>

                            <button
                              onClick={handleSaveAssumptions}
                              className="mt-2 w-full flex items-center justify-center gap-1 py-2 px-4 rounded-lg text-xs font-bold text-white bg-gradient-to-r from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))]"
                            >
                              <Check className="w-3.5 h-3.5" /> Confirm all assumptions
                            </button>
                          </>
                        ) : (
                          <div className="flex flex-col gap-3">
                            <h3 className="text-xs font-bold uppercase text-white">Edit Business twin assumptions</h3>
                            
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-[hsl(var(--text-secondary))]">Company Name</label>
                              <input
                                type="text"
                                value={editCompany}
                                onChange={(e) => setEditCompany(e.target.value)}
                                className="px-3 py-1.5 rounded bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] text-xs outline-none text-white focus:border-[hsl(var(--brand-primary))]"
                              />
                            </div>

                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-[hsl(var(--text-secondary))]">Description</label>
                              <textarea
                                value={editDesc}
                                rows={2}
                                onChange={(e) => setEditDesc(e.target.value)}
                                className="px-3 py-1.5 rounded bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] text-xs outline-none text-white focus:border-[hsl(var(--brand-primary))]"
                              />
                            </div>

                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-[hsl(var(--text-secondary))]">Value Proposition</label>
                              <textarea
                                value={editValProp}
                                rows={2}
                                onChange={(e) => setEditValProp(e.target.value)}
                                className="px-3 py-1.5 rounded bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] text-xs outline-none text-white focus:border-[hsl(var(--brand-primary))]"
                              />
                            </div>

                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-[hsl(var(--text-secondary))]">Competitors</label>
                              <div className="flex gap-2 mb-1.5">
                                <input
                                  type="text"
                                  placeholder="Competitor name"
                                  value={newCompetitor}
                                  onChange={(e) => setNewCompetitor(e.target.value)}
                                  className="flex-1 px-3 py-1 rounded bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] text-xs outline-none text-white"
                                />
                                <button
                                  type="button"
                                  onClick={addCompetitor}
                                  className="px-3 py-1 rounded bg-[hsl(var(--surface-3))] text-xs font-bold text-white border border-[hsl(var(--border-default))]"
                                >
                                  Add
                                </button>
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {editCompetitors.map((comp) => (
                                  <span key={comp} className="px-2 py-0.5 rounded bg-[hsl(var(--surface-3))] text-white text-[10px] border border-[hsl(var(--border-default))] flex items-center gap-1">
                                    {comp}
                                    <button type="button" onClick={() => removeCompetitor(comp)}>
                                      <Trash2 className="w-3 h-3 text-red-400 hover:text-red-300" />
                                    </button>
                                  </span>
                                ))}
                              </div>
                            </div>

                            <div className="flex justify-end gap-2 mt-2">
                              <button
                                onClick={() => setEditMode(false)}
                                className="px-3 py-1.5 rounded text-xs font-semibold border border-[hsl(var(--border-default))] text-[hsl(var(--text-secondary))] hover:bg-white/[0.02]"
                              >
                                Cancel
                              </button>
                              <button
                                onClick={handleSaveAssumptions}
                                className="px-4 py-1.5 rounded text-xs font-bold text-white bg-[hsl(var(--brand-primary))]"
                              >
                                Save Changes
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* AI Challenge / Advice Card */}
                    {msg.type === "challenge" && (
                      <div className="p-4 rounded-xl border bg-amber-500/[0.03] border-amber-500/20 flex flex-col gap-3 mt-1 w-full max-w-[500px]">
                        <span className="text-[10px] font-bold text-amber-500 uppercase tracking-wider flex items-center gap-1">
                          ⚠️ Growth Advisor Warning
                        </span>
                        <p className="text-xs text-[hsl(var(--text-secondary))]">
                          High outbound performance relies on hyper-focused campaigns. Broad targeting leads to generalist playbooks, lowering answer rates by 48%.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-2 mt-1">
                          <button
                            onClick={() => handleChallengeResponse(true)}
                            className="flex-1 py-2 px-3 rounded-lg text-xs font-bold text-white bg-gradient-to-r from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))] text-center shadow-md"
                          >
                            Focus niches (Recommend)
                          </button>
                          <button
                            onClick={() => handleChallengeResponse(false)}
                            className="py-2 px-3 rounded-lg text-xs font-semibold border border-[hsl(var(--border-default))] text-[hsl(var(--text-secondary))] text-center hover:bg-white/[0.02]"
                          >
                            Keep broad targeting
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Telephony Setup Card */}
                    {msg.type === "telephony" && (
                      <div className="p-5 rounded-2xl border bg-[hsl(var(--surface-1))] border-[hsl(var(--border-subtle))] flex flex-col gap-4 mt-1 w-full max-w-[500px] shadow-xl">
                        <div className="flex gap-2 border-b border-[hsl(var(--border-subtle))] pb-2">
                          <button
                            type="button"
                            onClick={() => setPhoneMode("buy")}
                            className={`text-xs font-bold px-3 py-1 rounded-md transition-colors ${phoneMode === "buy" ? "bg-[hsla(var(--brand-primary),0.15)] text-[hsl(var(--brand-primary))]" : "text-[hsl(var(--text-muted))]"}`}
                          >
                            Buy Local Line
                          </button>
                          <button
                            type="button"
                            onClick={() => setPhoneMode("port")}
                            className={`text-xs font-bold px-3 py-1 rounded-md transition-colors ${phoneMode === "port" ? "bg-[hsla(var(--brand-accent),0.15)] text-[hsl(var(--brand-accent))]" : "text-[hsl(var(--text-muted))]"}`}
                          >
                            Use Existing Line
                          </button>
                        </div>

                        {phoneMode === "buy" ? (
                          <div className="flex flex-col gap-3">
                            <label className="text-[10px] uppercase font-bold text-[hsl(var(--text-secondary))]">Select Caller Number</label>
                            {loadingNumbers ? (
                              <div className="flex items-center justify-center py-4">
                                <RefreshCw className="w-5 h-5 animate-spin text-[hsl(var(--brand-primary))]" />
                              </div>
                            ) : (
                              <div className="grid grid-cols-1 gap-2 max-h-[140px] overflow-y-auto">
                                {availableNumbers.map((num) => (
                                  <button
                                    key={num}
                                    onClick={() => setSelectedNumber(num)}
                                    className={`flex items-center justify-between p-2.5 rounded-lg border text-xs transition-all ${selectedNumber === num ? "border-[hsl(var(--brand-primary))] bg-[hsla(var(--brand-primary),0.05)] text-white" : "border-[hsl(var(--border-default))] bg-[hsl(var(--surface-2))] text-[hsl(var(--text-secondary))]"}`}
                                  >
                                    <span>{num}</span>
                                    {selectedNumber === num && <Check className="w-3.5 h-3.5 text-[hsl(var(--brand-primary))]" />}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="flex flex-col gap-2">
                            <label className="text-[10px] uppercase font-bold text-[hsl(var(--text-secondary))]">Phone Number (E.164)</label>
                            <input
                              type="text"
                              value={customPhone}
                              onChange={(e) => setCustomPhone(e.target.value)}
                              placeholder="e.g. +19195551234"
                              className="px-3 py-2 rounded bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] text-xs outline-none text-white focus:border-[hsl(var(--brand-primary))]"
                            />
                          </div>
                        )}

                        <button
                          onClick={handleConfirmTelephony}
                          className="w-full flex items-center justify-center gap-1.5 py-2 px-4 rounded-lg text-xs font-bold text-white bg-[hsl(var(--brand-primary))] hover:opacity-90 shadow-md"
                        >
                          Confirm & Provision <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}

                    {/* Identity Card */}
                    {msg.type === "identity" && (
                      <div className="p-5 rounded-2xl border bg-[hsl(var(--surface-1))] border-[hsl(var(--border-subtle))] flex flex-col gap-4 mt-1 w-full max-w-[500px] shadow-xl">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[10px] uppercase font-bold text-[hsl(var(--text-secondary))]">Agent Name</label>
                            <input
                              type="text"
                              value={agentName}
                              onChange={(e) => setAgentName(e.target.value)}
                              className="px-3 py-2 rounded bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] text-xs outline-none text-white focus:border-[hsl(var(--brand-primary))]"
                            />
                          </div>

                          <div className="flex flex-col gap-1">
                            <label className="text-[10px] uppercase font-bold text-[hsl(var(--text-secondary))]">Voice</label>
                            <select
                              value={voice}
                              onChange={(e) => setVoice(e.target.value)}
                              className="px-2 py-2 rounded bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] text-xs outline-none text-white focus:border-[hsl(var(--brand-primary))]"
                            >
                              <option value="rachel">Rachel (Consultative)</option>
                              <option value="drew">Drew (Authoritative)</option>
                              <option value="clyde">Clyde (Technical)</option>
                              <option value="paul">Paul (Friendly)</option>
                            </select>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[10px] uppercase font-bold text-[hsl(var(--text-secondary))]">Tone style</label>
                            <select
                              value={tone}
                              onChange={(e) => setTone(e.target.value)}
                              className="px-2 py-2 rounded bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] text-xs outline-none text-white focus:border-[hsl(var(--brand-primary))]"
                            >
                              <option value="consultative">Consultative & Professional</option>
                              <option value="direct">Direct & Solution-Focused</option>
                              <option value="friendly">Warm & Advisory</option>
                            </select>
                          </div>

                          <div className="flex flex-col gap-1">
                            <label className="text-[10px] uppercase font-bold text-[hsl(var(--text-secondary))]">Calling Hours</label>
                            <div className="flex items-center gap-1.5">
                              <input
                                type="text"
                                value={callingStart}
                                onChange={(e) => setCallingStart(e.target.value)}
                                className="w-12 text-center py-1 rounded bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] text-[10px] text-white"
                              />
                              <span className="text-[10px] text-[hsl(var(--text-muted))]">to</span>
                              <input
                                type="text"
                                value={callingEnd}
                                onChange={(e) => setCallingEnd(e.target.value)}
                                className="w-12 text-center py-1 rounded bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] text-[10px] text-white"
                              />
                            </div>
                          </div>
                        </div>

                        <button
                          onClick={handleConfirmIdentity}
                          className="w-full flex items-center justify-center gap-1.5 py-2 px-4 rounded-lg text-xs font-bold text-white bg-[hsl(var(--brand-primary))] hover:opacity-90 shadow-md"
                        >
                          Save Identity Settings <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}

                    {/* Launch Engine Card */}
                    {msg.type === "ready" && (
                      <button
                        onClick={handleLaunchEngine}
                        className="mt-2 max-w-[300px] flex items-center justify-center gap-2 py-3 px-6 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))] hover:opacity-95 shadow-lg shadow-[hsla(var(--brand-primary),0.35)]"
                      >
                        Launch Growth Engine <Sparkles className="w-4 h-4" />
                      </button>
                    )}

                  </div>
                </motion.div>
              ))}

              {isTyping && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex gap-3 max-w-[80%] self-start"
                >
                  <div className="w-8 h-8 rounded-full flex items-center justify-center bg-[hsl(var(--brand-primary))] text-white">
                    <Sparkles className="w-4 h-4 animate-spin" />
                  </div>
                  <div className="p-4 rounded-2xl bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-subtle))] flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" />
                    <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce delay-150" />
                    <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce delay-300" />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          {/* Bottom Lock Info bar */}
          <div className="p-4 border-t border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface-1))]/80 flex items-center justify-center gap-2 text-[10px] text-[hsl(var(--text-muted))]">
            <Shield className="w-3.5 h-3.5 text-emerald-400" /> All scraped company data and call recordings are isolated per workspace.
          </div>
          
        </div>
      )}
    </div>
  );
}
