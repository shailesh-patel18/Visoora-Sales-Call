"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, CheckCircle2, ChevronRight, BrainCircuit, Globe, Users, Target, ShieldCheck } from "lucide-react";

const extractionPhases = [
  { id: "read", text: "Research Agent is reading your site...", icon: Globe },
  { id: "icp", text: "Identifying Ideal Customer Profile (ICP)...", icon: Users },
  { id: "comp", text: "Mapping Competitors & Market Position...", icon: Target },
  { id: "brain", text: "Building your Business Brain...", icon: BrainCircuit },
  { id: "done", text: "Analysis Complete.", icon: ShieldCheck }
];

interface SkeletonAnalyzerProps {
  onComplete: () => void;
  isFinished?: boolean;
  error?: string | null;
}

export function SkeletonAnalyzer({ onComplete, isFinished = false, error = null }: SkeletonAnalyzerProps) {
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);

  useEffect(() => {
    // If the API finishes early or errors out, stop the timer
    if (isFinished || error) {
      setCurrentPhaseIndex(extractionPhases.length - 1);
      if (isFinished && !error) {
        setTimeout(() => onComplete(), 1000);
      }
      return;
    }

    if (currentPhaseIndex >= extractionPhases.length - 1) {
      return; // Do nothing, wait for isFinished
    }

    const timer = setTimeout(() => {
      setCurrentPhaseIndex((prev) => prev + 1);
    }, 2000); // 2 seconds per phase

    return () => clearTimeout(timer);
  }, [currentPhaseIndex, isFinished, error, onComplete]);

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-md mx-auto p-8 bg-[#111] rounded-2xl border border-[hsl(var(--border-subtle))] shadow-2xl relative overflow-hidden">
      {/* Background Glow */}
      <div className={`absolute inset-0 bg-gradient-to-b ${error ? 'from-red-500/10' : 'from-[rgba(0,240,255,0.03)]'} to-transparent pointer-events-none`} />
      
      <div className="relative z-10 w-full space-y-6">
        <div className="flex items-center justify-center mb-8">
          <motion.div
            animate={{ rotate: (isFinished || error) ? 0 : 360 }}
            transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
            className={`w-16 h-16 rounded-full border-t-2 border-r-2 ${error ? 'border-red-500' : 'border-[#00F0FF]'} flex items-center justify-center bg-[#1A1A1A]`}
          >
            <Sparkles className={`w-6 h-6 ${error ? 'text-red-500' : 'text-[#00F0FF]'}`} />
          </motion.div>
        </div>

        <div className="space-y-4">
          <AnimatePresence mode="popLayout">
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm text-center text-red-400 font-medium bg-red-500/10 border border-red-500/20 p-3 rounded-lg"
              >
                {error}
              </motion.div>
            )}

            {!error && extractionPhases.map((phase, index) => {
              if (index > currentPhaseIndex) return null;
              
              const isCurrent = index === currentPhaseIndex && !isFinished;
              const isDone = index < currentPhaseIndex || isFinished;
              const Icon = phase.icon;

              return (
                <motion.div
                  key={phase.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: isCurrent ? 1 : 0.5, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="flex items-center gap-3 text-sm"
                >
                  {isDone ? (
                    <CheckCircle2 className="w-5 h-5 text-[#10B981]" />
                  ) : isCurrent ? (
                    <Icon className="w-5 h-5 text-[#00F0FF] animate-pulse" />
                  ) : (
                     <div className="w-5 h-5" />
                  )}
                  <span className={`font-medium ${isCurrent ? "text-white" : "text-gray-400"}`}>
                    {phase.text}
                  </span>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
