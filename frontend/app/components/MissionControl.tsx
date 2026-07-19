"use client";

import React, { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, CircleDashed, AlertCircle, Activity } from "lucide-react";

export type MissionStepStatus = "pending" | "active" | "done" | "error";

export interface MissionStep {
  id: string;
  label: string;
  status: MissionStepStatus;
  message?: string;
}

interface MissionControlProps {
  title?: string;
  steps: MissionStep[];
  className?: string;
}

export function MissionControl({ title = "AI Mission Control", steps, className = "" }: MissionControlProps) {
  const timelineRef = useRef<HTMLDivElement>(null);

  // Auto-scroll timeline when steps change
  useEffect(() => {
    if (timelineRef.current) {
      timelineRef.current.scrollTop = timelineRef.current.scrollHeight;
    }
  }, [steps]);

  return (
    <div className={`w-full max-w-lg space-y-6 ${className}`}>
      <h2 className="text-2xl font-bold text-white text-center flex items-center justify-center gap-3">
        <Activity className="w-6 h-6 text-[#00F0FF] animate-pulse" /> {title}
      </h2>
      <div 
        ref={timelineRef}
        className="bg-[#111] border border-white/10 rounded-2xl p-6 h-[400px] overflow-y-auto space-y-4 relative shadow-[0_0_40px_rgba(0,240,255,0.05)]"
      >
        {steps.map((step, idx) => {
          let Icon = CircleDashed;
          let iconColor = "text-gray-500";
          let iconClass = "";
          
          if (step.status === "done") {
            Icon = CheckCircle2;
            iconColor = "text-[#10B981]";
          } else if (step.status === "active") {
            iconColor = "text-[#00F0FF]";
            iconClass = "animate-spin";
          } else if (step.status === "error") {
            Icon = AlertCircle;
            iconColor = "text-rose-500";
          }

          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`flex items-center gap-4 ${step.status === "pending" ? 'opacity-50' : ''}`}
            >
              {step.status === "active" ? (
                <div className={`w-5 h-5 border-2 border-[#00F0FF] border-t-transparent rounded-full ${iconClass} shrink-0`}/>
              ) : (
                <Icon className={`w-5 h-5 ${iconColor} shrink-0`} />
              )}
              <div className="flex flex-col">
                <span className={`font-medium font-mono text-sm tracking-wide ${step.status === "done" ? "text-white" : "text-gray-300"}`}>
                  {step.label}
                </span>
                {step.message && (
                  <span className={`text-xs mt-1 ${step.status === "error" ? "text-rose-400" : "text-gray-400"}`}>
                    {step.message}
                  </span>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
