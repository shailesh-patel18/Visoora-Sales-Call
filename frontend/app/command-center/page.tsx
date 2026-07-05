"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  Activity,
  CheckCircle,
  XCircle,
  Edit3,
  Clock,
  Play,
  MessageSquare,
  Zap,
  Server,
  Shield,
  Send,
  Loader2,
  ListTodo
} from "lucide-react";
import Link from "next/link";
import { BACKEND_URL, getWsUrl } from "../config";
import { getAuthHeaders } from "../auth/store";

export default function CommandCenterPage() {
  const [inboxTasks, setInboxTasks] = useState<any[]>([]);
  const [selectedTask, setSelectedTask] = useState<any | null>(null);
  const [editingContent, setEditingContent] = useState<string>("");
  const [rejectFeedback, setRejectFeedback] = useState<string>("");
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [liveEvents, setLiveEvents] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const fetchInbox = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/missions/inbox`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setInboxTasks(data);
      }
    } catch (e) {
      console.error("Failed to fetch inbox", e);
    }
  }, []);

  useEffect(() => {
    fetchInbox();
    
    // Connect WebSocket
    const wsUrl = getWsUrl("/ws/missions/default_shared_tenant"); // In prod, get tenant_id dynamically
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.category === "mission_update") {
          setLiveEvents((prev) => [data, ...prev].slice(0, 50));
        }
      } catch (err) {
        console.error("WS Parse Error", err);
      }
    };

    return () => {
      ws.close();
    };
  }, [fetchInbox]);

  const selectTask = (task: any) => {
    setSelectedTask(task);
    setShowRejectForm(false);
    if (task.mission_artifacts && task.mission_artifacts.length > 0) {
      const art = task.mission_artifacts[0];
      setEditingContent(JSON.stringify(art.content, null, 2));
    } else {
      setEditingContent("{}");
    }
  };

  const handleApprove = async () => {
    if (!selectedTask) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/missions/tasks/${selectedTask.id}/approve`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        setSelectedTask(null);
        fetchInbox();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveEdits = async () => {
    if (!selectedTask) return;
    try {
      let parsed = {};
      try {
        parsed = JSON.parse(editingContent);
      } catch {
        alert("Invalid JSON format");
        return;
      }
      
      const res = await fetch(`${BACKEND_URL}/api/missions/tasks/${selectedTask.id}/artifact`, {
        method: "PUT",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ content: parsed }),
      });
      
      if (res.ok) {
        alert("Artifact edits saved!");
        fetchInbox();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleReject = async () => {
    if (!selectedTask || !rejectFeedback) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/missions/tasks/${selectedTask.id}/reject`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ feedback: rejectFeedback, feedback_categories: ["General"] }),
      });
      if (res.ok) {
        setSelectedTask(null);
        setShowRejectForm(false);
        setRejectFeedback("");
        fetchInbox();
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8 text-neutral-200" style={{ background: "hsl(var(--background))" }}>
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-6" style={{ borderColor: "hsl(var(--border-subtle))" }}>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
              <Zap className="w-8 h-8 text-[hsl(var(--brand-primary))]" />
              AI Command Center
            </h1>
            <p className="mt-2 text-sm text-neutral-400">
              Manage your AI workforce, review artifacts, and monitor real-time execution.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Event Bus Connected
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Column 1: Approval Queue (Agent Inbox) */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <ListTodo className="w-5 h-5 text-[hsl(var(--brand-primary))]" />
                Approval Queue
              </h2>
              <span className="text-xs bg-neutral-800 px-2 py-0.5 rounded-full font-bold">{inboxTasks.length} Pending</span>
            </div>
            
            <div className="space-y-3">
              {inboxTasks.length === 0 ? (
                <div className="text-sm text-neutral-500 text-center py-8 bg-neutral-900/30 rounded-xl border border-neutral-800/50">
                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-neutral-700" />
                  Inbox Zero. AI Workforce is fully unblocked.
                </div>
              ) : (
                inboxTasks.map((task) => (
                  <div
                    key={task.id}
                    onClick={() => selectTask(task)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      selectedTask?.id === task.id ? 'border-[hsl(var(--brand-primary))] bg-[hsl(var(--brand-primary))]/5' : 'border-neutral-800 bg-neutral-900/50 hover:border-neutral-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-[hsl(var(--brand-primary))]">
                        {task.agent_type.replace("_", " ")}
                      </span>
                      <span className="text-[10px] text-neutral-500">{new Date(task.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-sm font-semibold text-white mb-1 line-clamp-1">{task.name || "Review Drafted Artifact"}</p>
                    <p className="text-xs text-neutral-400 line-clamp-2">Goal: {task.missions?.goal}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Column 2: Artifact Editor (Main Panel) */}
          <div className="lg:col-span-2 flex flex-col gap-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Edit3 className="w-5 h-5 text-purple-400" />
              Artifact Editor
            </h2>
            
            <div className="flex-1 min-h-[500px] rounded-xl border border-neutral-800 bg-neutral-900/30 flex flex-col overflow-hidden relative">
              {!selectedTask ? (
                <div className="flex-1 flex flex-col items-center justify-center text-neutral-500 p-8 text-center">
                  <MessageSquare className="w-12 h-12 mb-4 text-neutral-700" />
                  <p className="font-semibold text-white">No task selected</p>
                  <p className="text-sm mt-1">Select a task from the Approval Queue to review the AI's drafted work.</p>
                </div>
              ) : (
                <div className="flex flex-col h-full">
                  <div className="p-4 border-b border-neutral-800 bg-neutral-900/80 flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-white text-sm">Reviewing: {selectedTask.agent_type}</h3>
                      <p className="text-xs text-neutral-400 mt-0.5">Please review the content below before approving execution.</p>
                    </div>
                  </div>
                  
                  <div className="flex-1 p-4 bg-neutral-950 overflow-y-auto">
                    <textarea 
                      className="w-full h-full min-h-[300px] bg-transparent text-sm font-mono text-neutral-300 focus:outline-none resize-none"
                      value={editingContent}
                      onChange={(e) => setEditingContent(e.target.value)}
                      spellCheck={false}
                    />
                  </div>
                  
                  <div className="p-4 border-t border-neutral-800 bg-neutral-900/80">
                    {showRejectForm ? (
                      <div className="flex flex-col gap-3">
                        <textarea 
                          placeholder="Provide feedback to the agent on why this was rejected..."
                          className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-red-500/50"
                          rows={3}
                          value={rejectFeedback}
                          onChange={(e) => setRejectFeedback(e.target.value)}
                        />
                        <div className="flex justify-end gap-2">
                          <button onClick={() => setShowRejectForm(false)} className="px-4 py-2 rounded-lg text-xs font-bold text-neutral-400 hover:bg-neutral-800">
                            Cancel
                          </button>
                          <button onClick={handleReject} className="px-4 py-2 rounded-lg text-xs font-bold bg-red-500/20 text-red-400 hover:bg-red-500/30">
                            Submit Feedback & Reject
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-wrap items-center justify-between gap-4">
                        <button 
                          onClick={handleSaveEdits}
                          className="px-4 py-2 rounded-lg text-xs font-bold bg-neutral-800 text-white hover:bg-neutral-700 transition-colors"
                        >
                          Save Edits
                        </button>
                        
                        <div className="flex items-center gap-3">
                          <button 
                            onClick={() => setShowRejectForm(true)}
                            className="px-4 py-2 rounded-lg text-xs font-bold border border-red-500/20 text-red-400 hover:bg-red-500/10 transition-colors"
                          >
                            Reject & Give Feedback
                          </button>
                          <button 
                            onClick={handleApprove}
                            className="flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-bold bg-[hsl(var(--brand-primary))] text-white hover:opacity-90 transition-opacity"
                          >
                            <Play className="w-4 h-4 fill-current" />
                            Approve & Execute
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Real-time Telemetry Bottom Bar */}
        <div className="mt-8">
          <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-emerald-400" />
            Live Mission Telemetry
          </h2>
          <div className="bg-neutral-900/30 border border-neutral-800 rounded-xl p-4 overflow-hidden h-[250px] relative">
            <div className="absolute inset-0 overflow-y-auto p-4 space-y-2 font-mono text-xs">
              {liveEvents.length === 0 ? (
                <div className="text-neutral-500 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" /> Waiting for mission events...
                </div>
              ) : (
                liveEvents.map((evt, idx) => (
                  <div key={idx} className="flex gap-4 items-start pb-2 border-b border-neutral-800/50 last:border-0">
                    <span className="text-neutral-500 flex-shrink-0">{new Date(evt.timestamp).toLocaleTimeString()}</span>
                    <span className="text-[hsl(var(--brand-primary))] font-bold w-32 flex-shrink-0 truncate">
                      {evt.payload.event_type}
                    </span>
                    <span className="text-neutral-300">
                      {JSON.stringify(evt.payload.details)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
