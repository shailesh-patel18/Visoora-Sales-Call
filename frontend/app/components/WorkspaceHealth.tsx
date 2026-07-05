"use client";

import React from "react";
import { CheckCircle2, AlertCircle, HelpCircle, Info } from "lucide-react";
import { motion } from "framer-motion";

export function WorkspaceHealth() {
  const readinessScore = 82;

  const checklist = [
    { label: "Business Brain", status: "ready", value: "Ready" },
    { label: "Email Integration", status: "ready", value: "Connected" },
    { label: "Calendar", status: "ready", value: "Connected" },
    { label: "Voice", status: "missing", value: "Not Configured" },
    { label: "CRM", status: "warning", value: "Optional" }
  ];

  return (
    <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl p-6 shadow-lg">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Workspace Readiness</h3>
          <p className="text-sm text-[hsl(var(--text-secondary))] mt-1">Core AI configuration</p>
        </div>
        <div className="text-right">
          <span className="text-3xl font-bold text-white">{readinessScore}%</span>
        </div>
      </div>

      <div className="space-y-4">
        {checklist.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {item.status === "ready" && <CheckCircle2 className="w-5 h-5 text-[#10B981]" />}
              {item.status === "missing" && <AlertCircle className="w-5 h-5 text-gray-500" />}
              {item.status === "warning" && <HelpCircle className="w-5 h-5 text-gray-500" />}
              <span className="text-gray-300 text-sm">{item.label}</span>
            </div>
            <span className={`text-sm font-medium ${
              item.status === "ready" ? "text-gray-400" : 
              "text-gray-500"
            }`}>
              {item.value}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-[hsl(var(--border-subtle))] flex items-start gap-2">
        <Info className="w-4 h-4 text-[#00F0FF] mt-0.5" />
        <p className="text-sm text-gray-300">
          <strong className="text-white">Voice can be connected later.</strong> Your agents have enough context to begin email outreach immediately.
        </p>
      </div>
    </div>
  );
}
