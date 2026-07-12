"use client";

import { create } from "zustand";

// ====================================================
// TYPE DEFINITIONS
// ====================================================
export interface Contact {
  id: string;
  tenant_id: string;
  phone_e164: string;
  full_name: string;
  company_name: string;
  email?: string;
  lead_score: number;
  lead_source?: string;
  tags?: string[];
  custom_fields?: {
    lead_score_reason?: string;
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface Deal {
  id: string;
  tenant_id: string;
  contact_id: string;
  contact_name?: string;
  company_name?: string;
  stage_id: string;
  stage_name: string;
  title: string;
  value_usd: number;
  currency: string;
  close_date?: string;
  ai_sentiment: "positive" | "neutral" | "negative" | "unknown";
  ai_next_action?: string;
  last_activity_date?: string;
  created_at: string;
}

export interface PipelineStage {
  id: string;
  name: string;
  position: number;
  probability_pct: number;
  is_terminal: boolean;
  deals: Deal[];
}

export interface CallLog {
  id: string;
  name: string;
  company: string;
  phone: string;
  status: string;
  duration_seconds: number;
  recording_url?: string;
  transcript?: TranscriptTurn[];
  ai_summary?: AISummary;
  fsm_states?: string[];
  created_at: string;
}

export interface TranscriptTurn {
  speaker: "AI" | "Prospect";
  text: string;
  timestamp: string;
}

export interface AISummary {
  key_facts: string[];
  objections: string[];
  sentiment: string;
  next_action: string;
  outcome: string;
}

export interface LiveCall {
  stream_sid: string;
  phone: string;
  name: string;
  company: string;
  fsm_state: string;
  direction: "outbound" | "inbound";
  started_at: string;
}

export interface ActivityEvent {
  id: string;
  type: "call_completed" | "deal_stage_changed" | "booking_confirmed" | "contact_created" | "sms_sent";
  description: string;
  timestamp: string;
  metadata?: Record<string, string>;
}

export interface ComplianceSettings {
  recording_disclosure_enabled: boolean;
  recording_disclosure_text: string;
  ai_disclosure_enabled: boolean;
  ai_disclosure_text: string;
  calling_hours_start: string;
  calling_hours_end: string;
  calling_timezone: string;
}

// ====================================================
// ZUSTAND CRM STORE
// ====================================================
interface CRMStore {
  // Contacts
  contacts: Contact[];
  setContacts: (contacts: Contact[]) => void;
  addContact: (contact: Contact) => void;
  updateContact: (id: string, data: Partial<Contact>) => void;
  removeContact: (id: string) => void;

  // Pipeline
  stages: PipelineStage[];
  setStages: (stages: PipelineStage[]) => void;
  moveDeal: (dealId: string, fromStageId: string, toStageId: string) => void;
  addDeal: (deal: Deal) => void;
  removeDeal: (dealId: string) => void;

  // Live Calls
  liveCalls: LiveCall[];
  setLiveCalls: (calls: LiveCall[] | ((prev: LiveCall[]) => LiveCall[])) => void;

  // Activity Feed
  activities: ActivityEvent[];
  setActivities: (events: ActivityEvent[] | ((prev: ActivityEvent[]) => ActivityEvent[])) => void;

  // Call Logs
  callLogs: CallLog[];
  setCallLogs: (logs: CallLog[]) => void;

  // Compliance
  compliance: ComplianceSettings;
  setCompliance: (settings: ComplianceSettings) => void;

  // UI
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  mobileSidebarOpen: boolean;
  toggleMobileSidebar: () => void;
  setMobileSidebarOpen: (open: boolean) => void;
  // Workflow Tracking
  currentWorkflowStep: number;
  highestCompletedStep: number;
  setWorkflowStep: (step: number) => void;
  markStepComplete: (step: number) => void;
}

export const useCRMStore = create<CRMStore>((set) => ({
  // Workflow Tracking
  currentWorkflowStep: 1, // Start at step 1
  highestCompletedStep: 1, // Start with step 1 unlocked (Domain Analysis is technically done, but ICP is next)
  setWorkflowStep: (step) => set((s) => ({
    currentWorkflowStep: step <= s.highestCompletedStep + 1 ? step : s.currentWorkflowStep
  })),
  markStepComplete: (step) => set((s) => ({
    highestCompletedStep: Math.max(s.highestCompletedStep, step)
  })),

  // Contacts
  contacts: [],
  setContacts: (contacts) => set({ contacts }),
  addContact: (contact) => set((s) => ({ contacts: [contact, ...s.contacts] })),
  updateContact: (id, data) =>
    set((s) => ({
      contacts: s.contacts.map((c) => (c.id === id ? { ...c, ...data } : c)),
    })),
  removeContact: (id) =>
    set((s) => ({ contacts: s.contacts.filter((c) => c.id !== id) })),

  // Pipeline
  stages: [],
  setStages: (stages) => set({ stages }),
  moveDeal: (dealId, fromStageId, toStageId) =>
    set((s) => {
      const newStages = s.stages.map((stage) => {
        if (stage.id === fromStageId) {
          return { ...stage, deals: stage.deals.filter((d) => d.id !== dealId) };
        }
        if (stage.id === toStageId) {
          const fromStage = s.stages.find((st) => st.id === fromStageId);
          const deal = fromStage?.deals.find((d) => d.id === dealId);
          if (deal) {
            return {
              ...stage,
              deals: [...stage.deals, { ...deal, stage_id: toStageId, stage_name: stage.name }],
            };
          }
        }
        return stage;
      });
      return { stages: newStages };
    }),
  addDeal: (deal) =>
    set((s) => ({
      stages: s.stages.map((stage) =>
        stage.id === deal.stage_id
          ? { ...stage, deals: [...stage.deals, deal] }
          : stage
      ),
    })),
  removeDeal: (dealId) =>
    set((s) => ({
      stages: s.stages.map((stage) => ({
        ...stage,
        deals: stage.deals.filter((d) => d.id !== dealId),
      })),
    })),

  // Live Calls
  liveCalls: [],
  setLiveCalls: (calls) =>
    set((s) => ({
      liveCalls: typeof calls === "function" ? calls(s.liveCalls) : calls,
    })),

  // Activity Feed
  activities: [],
  setActivities: (events) =>
    set((s) => ({
      activities: typeof events === "function" ? events(s.activities) : events,
    })),

  // Call Logs
  callLogs: [],
  setCallLogs: (logs) => set({ callLogs: logs }),

  // Compliance
  compliance: {
    recording_disclosure_enabled: true,
    recording_disclosure_text: "This call may be recorded for quality and training purposes.",
    ai_disclosure_enabled: true,
    ai_disclosure_text: "You are speaking with an AI assistant from [Company].",
    calling_hours_start: "08:00",
    calling_hours_end: "21:00",
    calling_timezone: "America/New_York",
  },
  setCompliance: (settings) => set({ compliance: settings }),

  // UI
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  mobileSidebarOpen: false,
  toggleMobileSidebar: () => set((s) => ({ mobileSidebarOpen: !s.mobileSidebarOpen })),
  setMobileSidebarOpen: (open) => set({ mobileSidebarOpen: open }),
}));
