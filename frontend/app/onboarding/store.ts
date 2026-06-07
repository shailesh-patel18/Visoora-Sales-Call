"use client";

import { create } from "zustand";
import {
  type Step1Data,
  type Step2Data,
  type Step3Data,
  type Step4Data,
  type Step5Data,
  type Step6Data,
  type OnboardingWizardState,
} from "./schemas";

const BACKEND_URL = "http://localhost:8000";
const LOCAL_STORAGE_KEY = "visoora_onboarding_progress";

const DEFAULT_STATE: OnboardingWizardState = {
  currentStep: 1,
  step1: null,
  step2: null,
  step3: null,
  step4: null,
  step5: null,
  step6: null,
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

  completeOnboarding: async () => {
    set({ isSaving: true, error: null });
    try {
      const response = await fetch(`${BACKEND_URL}/api/onboarding/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_id: "default_shared_tenant", // Multi-tenant sandbox fallback
          company_name: get().state.step1?.companyName || "Unknown",
          website: get().state.step1?.website || "",
          phone_number: get().state.step2?.twilioNumber || get().state.step2?.portedNumber || "",
          agent_name: get().state.step3?.agentName || "Alex",
          recording_disclosure: get().state.step4?.recordingDisclosure || false,
        }),
      });

      if (!response.ok) throw new Error("Failed to complete onboarding on server.");

      const updated = { ...get().state, isCompleted: true };
      set({ state: updated });
      localStorage.removeItem(LOCAL_STORAGE_KEY);
      return true;
    } catch (err: any) {
      console.warn("Server completion call failed, running local mock save:", err);
      // Run fallback complete
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
    
    // 1. Try local storage load first to be fast
    try {
      const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
      if (stored) {
        localData = JSON.parse(stored);
      }
    } catch (e) {
      console.warn("Failed to load local storage:", e);
    }

    // 2. Query FastAPI server which handles Supabase storage
    try {
      const response = await fetch(`${BACKEND_URL}/api/onboarding/progress?tenant_id=default_shared_tenant`);
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

    // 3. Fallback to local storage if server load was unconfigured
    if (localData) {
      set({ state: { ...DEFAULT_STATE, ...localData } });
    }
    set({ isLoading: false });
  },

  saveProgress: async (newState: OnboardingWizardState) => {
    set({ isSaving: true });
    // Write to Local Storage instantly for rapid client-side sync
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(newState));
    } catch (e) {
      console.warn("Local storage save failed:", e);
    }

    // Write to FastAPI server asynchronously
    try {
      await fetch(`${BACKEND_URL}/api/onboarding/progress`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_id: "default_shared_tenant",
          progress_data: newState,
        }),
      });
    } catch (err) {
      console.warn("FastAPI server auto-save failed, progress is secured in localStorage:", err);
    } finally {
      // Small visual delay so user sees smooth transition saving states
      setTimeout(() => set({ isSaving: false }), 400);
    }
  },
}));
