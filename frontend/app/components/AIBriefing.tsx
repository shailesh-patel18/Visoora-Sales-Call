"use client";

import React from "react";
import { motion } from "framer-motion";
import { Activity, Mail, Search, Phone, CheckCircle2 } from "lucide-react";

interface AgentBriefing {
  id: string;
  name: string;
  role: string;
  avatar: string;
  status: string;
  summary: string;
}

interface AIBriefingProps {
  agents: AgentBriefing[];
}

export function AIBriefing({ agents }: AIBriefingProps) {
  if (!agents || agents.length === 0) return null;

  return (
    <div className="space-y-6 mb-8">
      <div className="flex items-center gap-3">
        <Activity className="w-6 h-6 text-[#00F0FF]" />
        <h2 className="text-2xl font-bold text-white tracking-tight">Morning Executive Briefing</h2>
      </div>
      <p className="text-[hsl(var(--text-secondary))] max-w-2xl text-sm">
        Good morning. Here is what your autonomous workforce accomplished in the last 24 hours.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {agents.map((agent, i) => (
          <motion.div 
            key={agent.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl p-5 relative overflow-hidden group shadow-lg hover:shadow-[0_0_20px_rgba(0,240,255,0.05)] transition-shadow"
          >
            {/* Agent Header */}
            <div className="flex items-start gap-4 mb-4">
              <img 
                src={agent.avatar} 
                alt={agent.name} 
                className="w-12 h-12 rounded-xl bg-white/5 object-cover"
              />
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-white font-bold text-lg">{agent.name}</h3>
                    <p className="text-[10px] font-semibold tracking-widest text-[#00F0FF] uppercase">{agent.role}</p>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="flex h-2 w-2 relative mb-1">
                      {agent.status === 'Active' && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10B981] opacity-75"></span>}
                      <span className={`relative inline-flex rounded-full h-2 w-2 ${agent.status === 'Active' ? 'bg-[#10B981]' : 'bg-yellow-500'}`}></span>
                    </span>
                    <span className="text-[10px] text-gray-500 font-medium">{agent.status}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Briefing Text */}
            <div className="bg-black/50 border border-white/5 rounded-xl p-4 min-h-[90px]">
              <p className="text-sm text-gray-300 leading-relaxed italic">
                "{agent.summary}"
              </p>
            </div>

            {/* Action Bar (Mock) */}
            <div className="mt-4 flex justify-end gap-2">
              <button className="px-3 py-1.5 bg-white/5 text-gray-400 hover:text-white rounded-md text-xs font-semibold transition-colors flex items-center gap-1.5">
                View Log <CheckCircle2 className="w-3 h-3" />
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
