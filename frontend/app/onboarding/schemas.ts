import { z } from "zod";

// Step 1: Business Context & URL
export const step1Schema = z.object({
  companyName: z.string().min(2, "Company name must be at least 2 characters"),
  website: z.string().url("Invalid website URL. Must start with http:// or https://"),
  companyDescription: z.string().min(20, "Please describe your company (at least 20 characters)"),
  valueProposition: z.string().min(10, "Please outline your value proposition (at least 10 characters)"),
});
export type Step1Data = z.infer<typeof step1Schema>;

// Step 2: Agent Identity
export const step2Schema = z.object({
  agentName: z.string().min(2, "Agent name must be at least 2 characters"),
});
export type Step2Data = z.infer<typeof step2Schema>;

// Step 3: ICP Industries
export const step3Schema = z.object({
  icpIndustries: z.array(z.string()).min(1, "Please select at least one industry"),
});
export type Step3Data = z.infer<typeof step3Schema>;

// Step 4: ICP Regions
export const step4Schema = z.object({
  icpRegions: z.array(z.string()).min(1, "Please select at least one target region"),
});
export type Step4Data = z.infer<typeof step4Schema>;

// Step 5: Decision Maker Titles
export const step5Schema = z.object({
  decisionMakerTitles: z.array(z.string()).min(1, "Please select or add at least one title"),
});
export type Step5Data = z.infer<typeof step5Schema>;

// Step 6: Competitors
export const step6Schema = z.object({
  competitors: z.array(z.string()).optional(),
});
export type Step6Data = z.infer<typeof step6Schema>;

// Step 7: Voice & Tone Selection
export const step7Schema = z.object({
  voice: z.string().min(1, "Please select a voice profile"),
  tone: z.string().min(1, "Please select a tone profile"),
  brandVoiceTone: z.string().min(5, "Please outline your brand voice rules in a brief instruction"),
});
export type Step7Data = z.infer<typeof step7Schema>;

// Step 8: Core Objections
export const step8Schema = z.object({
  objectionsList: z.array(z.object({
    objection: z.string().min(5, "Objection trigger must be at least 5 characters"),
    rebuttal: z.string().min(5, "Rebuttal response must be at least 5 characters")
  })).min(1, "Please define at least one common objection & rebuttal"),
});
export type Step8Data = z.infer<typeof step8Schema>;

// Step 9: Avoid-List
export const step9Schema = z.object({
  avoidList: z.array(z.string()).optional(),
});
export type Step9Data = z.infer<typeof step9Schema>;

// Step 10: Phone Number Selection
export const step10Schema = z.object({
  phoneOption: z.enum(["buy", "port"]),
  twilioNumber: z.string().optional(),
  portedNumber: z.string().optional(),
}).refine(
  (data) => {
    if (data.phoneOption === "buy") {
      return !!data.twilioNumber && data.twilioNumber.length >= 8;
    } else {
      return !!data.portedNumber && /^\+[1-9]\d{1,14}$/.test(data.portedNumber);
    }
  },
  {
    message: "Please specify a valid Twilio number or ported number in E.164 format (+1...)",
    path: ["portedNumber"],
  }
);
export type Step10Data = z.infer<typeof step10Schema>;

// Step 11: Launch Sandbox Call
export const step11Schema = z.object({
  testPhone: z.string().regex(/^\+[1-9]\d{1,14}$/, "Must be a valid E.164 phone number, e.g. +19195551234"),
});
export type Step11Data = z.infer<typeof step11Schema>;

export interface OnboardingWizardState {
  currentStep: number;
  step1: Step1Data | null;
  step2: Step2Data | null;
  step3: Step3Data | null;
  step4: Step4Data | null;
  step5: Step5Data | null;
  step6: Step6Data | null;
  step7: Step7Data | null;
  step8: Step8Data | null;
  step9: Step9Data | null;
  step10: Step10Data | null;
  step11: Step11Data | null;
  isCompleted: boolean;
  kbDescription?: string;
  kbFaqs?: Array<{ question: string; answer: string }>;
  playbookGreeting?: string;
  playbookBookingLink?: string;
  campaignGoal?: string;
}
