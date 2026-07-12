import React, { useState } from "react";
import { Info, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface EvidenceField {
  value: string | string[];
  confidence: number;
  snippet: string;
  source_url: string;
}

export default function EvidenceCard({ title, field, renderValue }: { title: string, field?: EvidenceField, renderValue?: (val: any) => React.ReactNode }) {
  const [expanded, setExpanded] = useState(false);

  if (!field) {
    return (
      <div className="py-2 border-b border-white/5 last:border-0">
        <label className="text-xs font-semibold text-gray-500 uppercase">{title}</label>
        <p className="text-gray-400 mt-1 italic">N/A</p>
      </div>
    );
  }

  const { value, confidence, snippet, source_url } = field;

  // Determine color based on confidence
  let confColor = "text-red-500";
  let confBg = "bg-red-500/10";
  if (confidence >= 90) {
    confColor = "text-[#10B981]";
    confBg = "bg-[#10B981]/10";
  } else if (confidence >= 60) {
    confColor = "text-yellow-500";
    confBg = "bg-yellow-500/10";
  }

  return (
    <div className="py-3 border-b border-white/5 last:border-0">
      <div className="flex justify-between items-start mb-1">
        <label className="text-xs font-semibold text-gray-500 uppercase flex items-center gap-2">
          {title}
          {confidence > 0 && (
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${confBg} ${confColor}`}>
              {confidence}% CONF
            </span>
          )}
        </label>
        <button 
          onClick={() => setExpanded(!expanded)}
          className="text-gray-500 hover:text-white transition-colors p-1"
          title="View extraction evidence"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <Info className="w-3 h-3" />}
        </button>
      </div>
      
      <div className="mt-1">
        {renderValue ? renderValue(value) : (
          <p className="text-gray-200 text-sm">
            {typeof value === 'string' ? value : JSON.stringify(value)}
          </p>
        )}
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden mt-3"
          >
            <div className="p-3 bg-black/40 rounded-lg border border-[hsl(var(--border-subtle))] text-xs text-gray-400">
              <div className="font-semibold text-gray-300 mb-1">Source Snippet:</div>
              <blockquote className="border-l-2 border-[#00F0FF]/30 pl-2 italic mb-2">
                "{snippet}"
              </blockquote>
              {source_url && source_url !== "N/A" && (
                <a href={source_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-[#00F0FF] hover:underline">
                  <ExternalLink className="w-3 h-3" /> Source URL
                </a>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
