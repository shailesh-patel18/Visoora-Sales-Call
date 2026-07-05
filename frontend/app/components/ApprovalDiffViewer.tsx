"use client";

import React, { useState } from "react";
import { Check, X, Edit3, MessageSquare, ArrowRight, Bot } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ApprovalDiffViewerProps {
  originalContent: string;
  suggestedContent: string;
  onApprove: () => void;
  onReject: (feedback: string) => void;
  onEdit: (newContent: string) => void;
}

export function ApprovalDiffViewer({ 
  originalContent, 
  suggestedContent, 
  onApprove, 
  onReject,
  onEdit 
}: ApprovalDiffViewerProps) {
  const [mode, setMode] = useState<"diff" | "edit" | "feedback">("diff");
  const [editedContent, setEditedContent] = useState(suggestedContent);
  const [feedbackText, setFeedbackText] = useState("");

  const handleRejectSubmit = () => {
    onReject(feedbackText);
    setMode("diff");
  };

  const handleEditSubmit = () => {
    onEdit(editedContent);
    setMode("diff");
  };

  return (
    <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl overflow-hidden shadow-2xl">
      <div className="flex border-b border-[hsl(var(--border-subtle))]">
        <div className="flex-1 p-4 bg-white/5 border-r border-[hsl(var(--border-subtle))]">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Original Template</h4>
          <p className="text-sm text-gray-400 whitespace-pre-wrap font-mono leading-relaxed">{originalContent}</p>
        </div>
        <div className="flex-1 p-4 bg-[#1a1a1a]">
          <h4 className="text-xs font-semibold text-[#00F0FF] uppercase tracking-wider mb-4 flex items-center gap-2">
            <Bot className="w-4 h-4" /> AI Generated
          </h4>
          
          <AnimatePresence mode="wait">
            {mode === "diff" && (
              <motion.div 
                key="diff"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-sm text-gray-200 whitespace-pre-wrap font-mono leading-relaxed"
              >
                {suggestedContent}
              </motion.div>
            )}

            {mode === "edit" && (
              <motion.div 
                key="edit"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
              >
                <textarea 
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="w-full h-48 bg-black text-white p-3 font-mono text-sm border border-[hsl(var(--border-subtle))] rounded-lg focus:outline-none focus:border-[#00F0FF] resize-none"
                />
                <div className="flex justify-end gap-2 mt-3">
                  <button onClick={() => setMode("diff")} className="text-xs text-gray-400 hover:text-white px-3 py-1.5">Cancel</button>
                  <button onClick={handleEditSubmit} className="text-xs font-semibold bg-white text-black px-4 py-1.5 rounded hover:bg-gray-200">Save Edit</button>
                </div>
              </motion.div>
            )}

            {mode === "feedback" && (
              <motion.div 
                key="feedback"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
              >
                <h5 className="text-sm text-white mb-2 font-medium">Why are you rejecting this?</h5>
                <p className="text-xs text-gray-500 mb-3">Your feedback trains the Learning Engine to improve the Business Brain.</p>
                <textarea 
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="e.g., Don't mention pricing in the first email."
                  className="w-full h-24 bg-black text-white p-3 text-sm border border-red-500/50 rounded-lg focus:outline-none focus:border-red-500 resize-none"
                />
                <div className="flex justify-end gap-2 mt-3">
                  <button onClick={() => setMode("diff")} className="text-xs text-gray-400 hover:text-white px-3 py-1.5">Cancel</button>
                  <button 
                    onClick={handleRejectSubmit} 
                    disabled={!feedbackText.trim()}
                    className="text-xs font-semibold bg-red-500 text-white px-4 py-1.5 rounded hover:bg-red-600 disabled:opacity-50"
                  >
                    Submit Feedback
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {mode === "diff" && (
        <div className="p-3 bg-black flex items-center justify-between border-t border-[hsl(var(--border-subtle))]">
          <div className="flex gap-2">
            <button 
              onClick={() => setMode("edit")}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              <Edit3 className="w-3.5 h-3.5" /> Edit
            </button>
            <button 
              onClick={() => setMode("feedback")}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" /> Reject w/ Feedback
            </button>
          </div>
          
          <button 
            onClick={onApprove}
            className="flex items-center gap-2 text-xs font-bold px-6 py-2 bg-gradient-to-r from-[#10B981] to-[#059669] text-white rounded-lg hover:shadow-[0_0_15px_rgba(16,185,129,0.4)] transition-all"
          >
            <Check className="w-4 h-4" /> Approve
          </button>
        </div>
      )}
    </div>
  );
}
