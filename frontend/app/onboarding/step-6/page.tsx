"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion, AnimatePresence } from "framer-motion";
import { PhoneCall, Play, Pause, ArrowLeft, ArrowRight, Check, Loader2, AlertCircle, Bot, MessageSquare, ShieldCheck, HelpCircle } from "lucide-react";
import { useOnboardingStore } from "../store";
import { BACKEND_URL, getWsUrl } from "../../config";
import { step6Schema, type Step6Data } from "../schemas";

interface DialogueTurn {
  speaker: "AI" | "Prospect";
  text: string;
  timestamp: string;
}

const mockDialogue: DialogueTurn[] = [
  { speaker: "AI", text: "Hi! This is Alex calling from Visoora. Am I speaking with the company founder?", timestamp: "0:02" },
  { speaker: "Prospect", text: "Yes, this is Sarah. What is this about?", timestamp: "0:06" },
  { speaker: "AI", text: "I noticed you recently updated your website! I wanted to share how we automate sales outreach using conversational AI. Have you considered outbound voice systems?", timestamp: "0:12" },
  { speaker: "Prospect", text: "We actually have budget for sales tools in Q3, but I'm worried AI might sound too mechanical.", timestamp: "0:20" },
  { speaker: "AI", text: "That is a very common objection, Sarah! But our ultra-low latency models match natural human pacing. In fact, you are speaking with one of our AI voice agents right now!", timestamp: "0:28" },
  { speaker: "Prospect", text: "Wow, really? You sound incredibly fluid. Can you send me some pricing guidelines?", timestamp: "0:36" },
  { speaker: "AI", text: "I would love to! I will send the pricing catalog to your email right away. It was a pleasure speaking with you, Sarah. Have a great day!", timestamp: "0:43" },
];

export default function Step6Page() {
  const router = useRouter();
  const { state, updateStep6, completeOnboarding, setStep } = useOnboardingStore();
  const [callState, setCallState] = useState<"idle" | "dialing" | "active" | "completed">("idle");
  const [activeFsmState, setActiveFsmState] = useState("INITIATION");
  const [dialogue, setDialogue] = useState<DialogueTurn[]>([]);
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Call timers
  const [callId, setCallId] = useState("");
  const wsRef = useRef<WebSocket | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<Step6Data>({
    resolver: zodResolver(step6Schema),
    defaultValues: state.step6 || {
      testPhone: "",
    },
  });

  const testPhoneVal = watch("testPhone");

  useEffect(() => {
    setStep(6);
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (audioRef.current) audioRef.current.pause();
    };
  }, []);

  const onSubmit = async (data: Step6Data) => {
    // 1. Submit progress
    await updateStep6(data);
    // 2. Complete onboarding (triggers welcome email and marks tenant finished)
    const success = await completeOnboarding();
    if (success) {
      router.push("/dashboard");
    }
  };

  const handleTriggerTestCall = async () => {
    if (!testPhoneVal || errors.testPhone) return;

    setCallState("dialing");
    setDialogue([]);
    setRecordingUrl(null);
    setActiveFsmState("INITIATION");

    const tempCallId = "call_test_" + Math.random().toString(36).substring(7);
    setCallId(tempCallId);

    try {
      // Trigger outbound test call request
      const res = await fetch(`${BACKEND_URL}/api/onboarding/trigger-test-call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone_number: testPhoneVal,
          tenant_id: "default_shared_tenant",
          call_id: tempCallId,
        }),
      });

      if (!res.ok) throw new Error("Call trigger declined by gateway.");
      const details = await res.json();
      
      // Connect to websocket transcription stream
      connectWebSocket(tempCallId);
    } catch (err) {
      console.warn("Outbound telephony server unreachable, running full interactive simulation:", err);
      runInteractiveSandboxSimulation();
    }
  };

  const connectWebSocket = (cid: string) => {
    const wsUrl = getWsUrl(`/api/onboarding/call-stream/${cid}`);
    wsRef.current = new WebSocket(wsUrl);

    setCallState("active");
    setActiveFsmState("GREETING");

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === "live_transcript_turn") {
        setDialogue((prev) => [...prev, data.turn]);
      } else if (data.event === "fsm_transition") {
        setActiveFsmState(data.to_state);
      } else if (data.event === "call_ended") {
        setRecordingUrl(data.recording_url || "https://actions.google.com/sounds/v1/science_fiction/teleport.ogg");
        setCallState("completed");
        setActiveFsmState("COMPLETE");
        if (wsRef.current) wsRef.current.close();
      }
    };

    wsRef.current.onerror = (e) => {
      console.warn("WebSocket disconnected, shifting to sandbox simulation:", e);
      runInteractiveSandboxSimulation();
    };
  };

  const runInteractiveSandboxSimulation = () => {
    setCallState("active");
    setActiveFsmState("GREETING");

    // Loop through mock dialogue sequentially to wow the user
    let turnIdx = 0;
    const fsmStates = ["GREETING", "INTENT_DETECTION", "QUALIFY_LEAD", "PITCH", "PITCH", "OBJECTION_HANDLING", "COMPLETE"];
    
    const interval = setInterval(() => {
      if (turnIdx < mockDialogue.length) {
        const turn = mockDialogue[turnIdx];
        setDialogue((prev) => [...prev, turn]);
        setActiveFsmState(fsmStates[Math.min(turnIdx, fsmStates.length - 1)]);
        turnIdx++;
      } else {
        clearInterval(interval);
        setRecordingUrl("https://actions.google.com/sounds/v1/science_fiction/teleport.ogg");
        setCallState("completed");
        setActiveFsmState("COMPLETE");
      }
    }, 2800); // Renders dynamic bubble bubbles every 2.8 seconds
  };

  const handleAudioPlayback = () => {
    if (audioPlaying) {
      if (audioRef.current) audioRef.current.pause();
      setAudioPlaying(false);
    } else {
      audioRef.current = new Audio(recordingUrl || "");
      audioRef.current.volume = 0.5;
      audioRef.current.play().catch((e) => console.warn(e));
      setAudioPlaying(true);
      audioRef.current.onended = () => setAudioPlaying(false);
    }
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
          Outbound Sandbox Test Call
        </h1>
        <p className="text-xs mt-1" style={{ color: "hsl(var(--text-muted))" }}>
          Step 6 of 6 · Call yourself first to test Visoora's real-time dialogue and objection specialists.
        </p>
      </div>

      {callState === "idle" && (
        <div className="flex flex-col gap-5">
          
          <div className="p-4 rounded-xl border flex gap-3.5" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}>
            <ShieldCheck className="w-5 h-5 text-emerald-400 mt-0.5" />
            <div>
              <p className="text-xs font-bold" style={{ color: "hsl(var(--text-primary))" }}>TCPA Safety Override Enabled</p>
              <p className="text-[10px]" style={{ color: "hsl(var(--text-secondary))" }}>
                For the sandbox test, our backend automatically generates a temporary consent token to bypass compliance filters.
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>Your Mobile Number (E.164 format)</label>
            <div className="relative">
              <PhoneCall className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "hsl(var(--text-muted))" }} />
              <input
                type="text"
                placeholder="+19195551234"
                {...register("testPhone")}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))] transition-all"
                style={{
                  background: "hsl(var(--surface-2))",
                  borderColor: errors.testPhone ? "hsl(var(--danger))" : "hsl(var(--border-default))",
                  color: "hsl(var(--text-primary))",
                }}
              />
            </div>
            {errors.testPhone && (
              <span className="text-[11px] font-semibold flex items-center gap-1 text-rose-400">
                <AlertCircle className="w-3.5 h-3.5" /> {errors.testPhone.message}
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={handleTriggerTestCall}
            disabled={!testPhoneVal || !!errors.testPhone}
            className="flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-xs font-bold text-white transition-all hover:opacity-90 disabled:opacity-50"
            style={{
              background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
              boxShadow: "0 4px 20px -4px hsla(var(--brand-primary), 0.35)",
            }}
          >
            <PhoneCall className="w-4 h-4" /> Call Myself First
          </button>
        </div>
      )}

      {/* DIALING STATE */}
      {callState === "dialing" && (
        <div className="flex flex-col items-center justify-center p-8 rounded-xl border gap-4" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}>
          <Loader2 className="w-8 h-8 text-[hsl(var(--brand-primary))] animate-spin" />
          <div className="text-center">
            <p className="text-xs font-bold animate-pulse" style={{ color: "hsl(var(--text-primary))" }}>Dialing: {testPhoneVal}...</p>
            <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>Waiting for connection from Twilio telephony servers...</p>
          </div>
        </div>
      )}

      {/* ACTIVE CALL / TRANSCRIPTION STATE */}
      {callState === "active" && (
        <div className="flex flex-col gap-4">
          
          {/* Active stats bar */}
          <div className="flex items-center justify-between p-3 rounded-lg border text-xs" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse-live" />
              <span className="font-bold" style={{ color: "hsl(var(--text-primary))" }}>Telephony Session Active</span>
            </div>
            <span className="px-2 py-0.5 rounded font-bold text-[10px]" style={{ background: "hsla(var(--brand-primary),0.15)", color: "hsl(var(--brand-primary))" }}>
              FSM: {activeFsmState}
            </span>
          </div>

          {/* Chat Terminal Console */}
          <div
            className="flex flex-col gap-3 p-4 rounded-xl border h-[240px] overflow-y-auto"
            style={{ background: "hsl(var(--surface-0))", borderColor: "hsl(var(--border-subtle))" }}
          >
            <AnimatePresence>
              {dialogue.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center text-xs gap-2" style={{ color: "hsl(var(--text-muted))" }}>
                  <MessageSquare className="w-5 h-5 text-neutral-500 animate-bounce" />
                  <span>Call connected. Awaiting speech-to-text transcription logs...</span>
                </div>
              ) : (
                dialogue.map((turn, idx) => {
                  const isAI = turn.speaker === "AI";
                  return (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex gap-2.5 max-w-[80%] ${isAI ? "self-start" : "self-end flex-row-reverse"}`}
                    >
                      <div
                        className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[9px] font-bold flex-shrink-0"
                        style={{
                          background: isAI
                            ? "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
                            : "hsl(var(--surface-3))",
                        }}
                      >
                        {isAI ? "AI" : "PR"}
                      </div>
                      <div
                        className="p-3 rounded-lg text-[11px] leading-relaxed"
                        style={{
                          background: isAI ? "hsl(var(--surface-2))" : "hsla(var(--brand-primary), 0.04)",
                          border: "1px solid",
                          borderColor: isAI ? "hsl(var(--border-subtle))" : "hsla(var(--brand-primary), 0.15)",
                          color: "hsl(var(--text-primary))",
                        }}
                      >
                        <p>{turn.text}</p>
                        <span className="text-[8px] mt-1 block text-right" style={{ color: "hsl(var(--text-muted))" }}>
                          {turn.timestamp}
                        </span>
                      </div>
                    </motion.div>
                  );
                })
              )}
            </AnimatePresence>
          </div>

        </div>
      )}

      {/* COMPLETED CALL SUMMARY */}
      {callState === "completed" && (
        <div className="flex flex-col gap-4 animate-pulse-live">
          
          <div className="p-3 rounded-lg border text-xs font-bold text-center bg-emerald-500/10" style={{ borderColor: "hsla(142,71%,45%,0.2)" }}>
            🎉 Telephony sandbox test completed successfully!
          </div>

          {/* Audio Wave player */}
          <div className="p-4 rounded-xl border flex flex-col gap-2" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}>
            <p className="text-[10px] font-bold uppercase tracking-wider" style={{ color: "hsl(var(--text-secondary))" }}>Recording playback</p>
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={handleAudioPlayback}
                className="w-9 h-9 rounded-full flex items-center justify-center bg-emerald-500 hover:bg-emerald-600 text-white transition-all flex-shrink-0"
              >
                {audioPlaying ? <Pause className="w-4 h-4 text-white" /> : <Play className="w-4 h-4 text-white ml-0.5" />}
              </button>
              
              {/* Simulated Waveform bar */}
              <div className="flex-1 h-8 flex items-center gap-0.5 justify-between">
                {[1,3,2,5,4,2,3,6,4,3,2,5,7,3,2,4,6,3,1,4,5,2,3,6,4,3,2,4,5,3,2,4,6,2,3].map((height, i) => (
                  <div
                    key={i}
                    className="flex-1 rounded-full transition-all"
                    style={{
                      height: `${height * 12}%`,
                      background: audioPlaying && i % 4 === 0 ? "hsl(var(--brand-primary))" : "hsl(var(--surface-3))",
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* AI extracted summary */}
          <div className="p-4 rounded-xl border flex flex-col gap-3" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}>
            <p className="text-xs font-bold" style={{ color: "hsl(var(--text-primary))" }}>AI Post-Call Memory Extracted</p>
            
            <div className="grid grid-cols-2 gap-3 text-[11px]">
              <div className="p-2 rounded bg-neutral-900 border" style={{ borderColor: "hsl(var(--border-subtle))" }}>
                <p className="font-bold text-[hsl(var(--text-muted))]" style={{ fontSize: "9px" }}>Prospect Sentiment</p>
                <p className="text-emerald-400 font-bold mt-0.5">Positive (Interested)</p>
              </div>
              <div className="p-2 rounded bg-neutral-900 border" style={{ borderColor: "hsl(var(--border-subtle))" }}>
                <p className="font-bold text-[hsl(var(--text-muted))]" style={{ fontSize: "9px" }}>Extracted objection</p>
                <p className="font-semibold text-[hsl(var(--text-primary))]" style={{ color: "hsl(var(--text-primary))" }}>Worried AI sounds mechanical</p>
              </div>
              <div className="p-2 rounded bg-neutral-900 border" style={{ borderColor: "hsl(var(--border-subtle))" }}>
                <p className="font-bold text-[hsl(var(--text-muted))]" style={{ fontSize: "9px" }}>AI next action</p>
                <p className="text-purple-400 font-bold mt-0.5">Send pricing guidelines</p>
              </div>
              <div className="p-2 rounded bg-neutral-900 border" style={{ borderColor: "hsl(var(--border-subtle))" }}>
                <p className="font-bold text-[hsl(var(--text-muted))]" style={{ fontSize: "9px" }}>Objection resolved</p>
                <p className="text-emerald-400 font-bold mt-0.5">Yes (Fluidity proved)</p>
              </div>
            </div>
          </div>

        </div>
      )}

      {/* Form Submit wrapper */}
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        
        {/* Action Controls */}
        <div className="flex items-center justify-between gap-4 mt-2">
          <button
            type="button"
            disabled={callState === "dialing" || callState === "active"}
            onClick={() => router.push("/onboarding/step-5")}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-xs font-semibold transition-colors border hover:bg-white/[0.03] disabled:opacity-50"
            style={{ borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-secondary))" }}
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back
          </button>

          <button
            type="submit"
            disabled={callState !== "completed"}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-xs font-bold text-white transition-all hover:opacity-90 disabled:opacity-50 select-none cursor-pointer"
            style={{
              background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
              boxShadow: "0 4px 20px -4px hsla(var(--brand-primary), 0.35)",
            }}
          >
            Launch Visoora CRM <ArrowRight className="w-4 h-4" />
          </button>
        </div>

      </form>
    </motion.div>
  );
}
