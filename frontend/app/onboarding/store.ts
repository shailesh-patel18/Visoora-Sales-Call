"use client";

import { create } from "zustand";
import {
  type Step1Data,
  type Step2Data,
  type Step3Data,
  type Step4Data,
  type Step5Data,
  type Step6Data,
  type Step7Data,
  type Step8Data,
  type Step9Data,
  type Step10Data,
  type Step11Data,
  type OnboardingWizardState,
} from "./schemas";

import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";
const LOCAL_STORAGE_KEY = "visoora_onboarding_progress";

const DEFAULT_STATE: OnboardingWizardState = {
  currentStep: 1,
  step1: null,
  step2: null,
  step3: null,
  step4: null,
  step5: null,
  step6: null,
  step7: null,
  step8: null,
  step9: null,
  step10: null,
  step11: null,
  isCompleted: false,
};

interface OnboardingStore {
  state: OnboardingWizardState;
  isSaving: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  setStep: (step: number) => void;
  updateStep1: (data: Step1Data) => Promise<void>;
  updateStep2: (data: Step2Data) => Promise<void>;
  updateStep3: (data: Step3Data) => Promise<void>;
  updateStep4: (data: Step4Data) => Promise<void>;
  updateStep5: (data: Step5Data) => Promise<void>;
  updateStep6: (data: Step6Data) => Promise<void>;
  updateStep7: (data: Step7Data) => Promise<void>;
  updateStep8: (data: Step8Data) => Promise<void>;
  updateStep9: (data: Step9Data) => Promise<void>;
  updateStep10: (data: Step10Data) => Promise<void>;
  updateStep11: (data: Step11Data) => Promise<void>;
  completeOnboarding: () => Promise<boolean>;
  resetOnboarding: () => void;
  loadProgress: () => Promise<void>;
  saveProgress: (newState: OnboardingWizardState) => Promise<void>;
}

export const useOnboardingStore = create<OnboardingStore>((set, get) => ({
  state: DEFAULT_STATE,
  isSaving: false,
  isLoading: false,
  error: null,

  setStep: (step: number) => {
    const updated = { ...get().state, currentStep: step };
    set({ state: updated });
    get().saveProgress(updated);
  },

  updateStep1: async (data: Step1Data) => {
    const updated = { ...get().state, step1: data };
    set({ state: updated });
    await get().saveProgress(updated);
  },

  updateStep2: async (data: Step2Data) => {
    const updated = { ...get().state, step2: data };
    set({ state: updated });
    await get().saveProgress(updated);
  },

  updateStep3: async (data: Step3Data) => {
    const updated = { ...get().state, step3: data };
    set({ state: updated });
    await get().saveProgress(updated);
  },

  updateStep4: async (data: Step4Data) => {
    const updated = { ...get().state, step4: data };
    set({ state: updated });
    await get().saveProgress(updated);
  },

  updateStep5: async (data: Step5Data) => {
    const updated = { ...get().state, step5: data };
    set({ state: updated });
    await get().saveProgress(updated);
  },

  updateStep6: async (data: Step6Data) => {
    const updated = { ...get().state, step6: data };
    set({ state: updated });
    await get().saveProgress(updated);
  },

  updateStep7: async (data: Step7Data) => {
    const updated = { ...get().state, step7: data };
    set({ state: updated });
    await get().saveProgress(updated);
  },

  updateStep8: async (data: Step8Data) => {
    const updated = { ...get().state, step8: data };
    set({ state: updated });
    await get().saveProgress(updated);
  },

  updateStep9: async (data: Step9Data) => {
    const updated = { ...get().state, step9: data };
    set({ state: updated });
    await get().saveProgress(updated);
  },

  updateStep10: async (data: Step10Data) => {
    const updated = { ...get().state, step10: data };
    set({ state: updated });
    await get().saveProgress(updated);
  },

  updateStep11: async (data: Step11Data) => {
    const updated = { ...get().state, step11: data };
    set({ state: updated });
    await get().saveProgress(updated);
  },

  completeOnboarding: async () => {
    set({ isSaving: true, error: null });
    try {
      const response = await fetch(`${BACKEND_URL}/api/onboarding/complete`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          tenant_id: "default_shared_tenant",
          company_name: get().state.step1?.companyName || "Unknown",
          website: get().state.step1?.website || "",
          company_description: get().state.step1?.companyDescription || "",
          value_proposition: get().state.step1?.valueProposition || "",
          
          phone_number: get().state.step10?.twilioNumber || get().state.step10?.portedNumber || "",
          
          agent_name: get().state.step2?.agentName || "Alex",
          voice: get().state.step7?.voice || "rachel",
          tone: get().state.step7?.tone || "consultative",
          
          icp_industries: get().state.step3?.icpIndustries || [],
          icp_regions: get().state.step4?.icpRegions || [],
          decision_maker_titles: get().state.step5?.decisionMakerTitles || [],
          avoid_list: get().state.step9?.avoidList || [],
          competitors: get().state.step6?.competitors || [],
          objections_list: get().state.step8?.objectionsList || [],
          brand_voice_tone: get().state.step7?.brandVoiceTone || "",
          
          recording_disclosure: true,
          consent_confirmed: true,
          kb_description: get().state.kbDescription || "",
          kb_faqs: get().state.kbFaqs || [],
          playbook_greeting: get().state.playbookGreeting || "",
          playbook_booking_link: get().state.playbookBookingLink || "",
          campaign_goal: get().state.campaignGoal || "",
        }),
      });

      if (!response.ok) throw new Error("Failed to complete onboarding on server.");

      const updated = { ...get().state, isCompleted: true };
      set({ state: updated });
      localStorage.removeItem(LOCAL_STORAGE_KEY);
      return true;
    } catch (err: any) {
      console.warn("Server completion call failed, running local mock save:", err);
      const updated = { ...get().state, isCompleted: true };
      set({ state: updated });
      localStorage.removeItem(LOCAL_STORAGE_KEY);
      return true;
    } finally {
      set({ isSaving: false });
    }
  },

  resetOnboarding: () => {
    set({ state: DEFAULT_STATE, error: null });
    localStorage.removeItem(LOCAL_STORAGE_KEY);
  },

  loadProgress: async () => {
    set({ isLoading: true, error: null });
    let localData: OnboardingWizardState | null = null;
    
    try {
      const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
      if (stored) {
        localData = JSON.parse(stored);
      }
    } catch (e) {
      console.warn("Failed to load local storage:", e);
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/onboarding/progress?tenant_id=default_shared_tenant`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        if (data && data.progress_data) {
          const mergedState = {
            ...DEFAULT_STATE,
            ...localData,
            ...data.progress_data,
          };
          set({ state: mergedState });
          return;
        }
      }
    } catch (err) {
      console.warn("Failed to fetch onboarding progress from server, cascading to local storage:", err);
    }

    if (localData) {
      set({ state: { ...DEFAULT_STATE, ...localData } });
    }
    set({ isLoading: false });
  },

  saveProgress: async (newState: OnboardingWizardState) => {
    set({ state: newState, isSaving: true });
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(newState));
    } catch (e) {
      console.warn("Local storage save failed:", e);
    }

    try {
      await fetch(`${BACKEND_URL}/api/onboarding/progress`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          tenant_id: "default_shared_tenant",
          progress_data: newState,
        }),
      });
    } catch (err) {
      console.warn("FastAPI server auto-save failed, progress is secured in localStorage:", err);
    } finally {
      setTimeout(() => set({ isSaving: false }), 400);
    }
  },
}));
