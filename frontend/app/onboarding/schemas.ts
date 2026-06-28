import { z } from "zod";

// ====================================================
// STEP 1: COMPANY SETUP
// ====================================================
export const step1Schema = z.object({
  companyName: z.string().min(2, "Company name must be at least 2 characters"),
  website: z.string().url("Invalid website URL. Must start with http:// or https://"),
  industry: z.string().min(1, "Please select an industry"),
  teamSize: z.string().min(1, "Please select your team size"),
  annualRevenue: z.string().min(1, "Please select estimated annual revenue"),
  targetRegion: z.string().min(1, "Please select target call region"),
});

export type Step1Data = z.infer<typeof step1Schema>;

// ====================================================
// STEP 2: PHONE NUMBER PROVISIONING
// ====================================================
export const step2Schema = z.object({
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
    path: ["portedNumber"], // Put the error on portedNumber or can handle dynamically
  }
);

export type Step2Data = z.infer<typeof step2Schema>;

// ====================================================
// STEP 3: AI AGENT CONFIGURATION
// ====================================================
export const step3Schema = z.object({
  agentName: z.string().min(2, "Agent name must be at least 2 characters"),
  companyDescription: z.string().min(20, "Please provide at least 20 characters describing your company"),
  valueProposition: z.string().min(10, "Please provide a value proposition (at least 10 characters)"),
  voice: z.string().min(1, "Please select a voice profile"),
  tone: z.string().min(1, "Please select a tone profile"),
  timezone: z.string().min(1, "Please select a timezone"),
  callingHoursStart: z.string().regex(/^\d{2}:\d{2}$/, "Invalid time format (HH:MM)"),
  callingHoursEnd: z.string().regex(/^\d{2}:\d{2}$/, "Invalid time format (HH:MM)"),
  productName: z.string().min(2, "Product name must be at least 2 characters"),
  productPrice: z.string().min(1, "Please specify product pricing (e.g. $99/mo)"),
  productFeatures: z.string().min(10, "Please outline core features (at least 10 characters)"),
  targetAudience: z.string().min(10, "Please describe the target audience (at least 10 characters)"),
  kbDescription: z.string().optional(),
  kbFaqs: z.array(z.object({
    question: z.string().min(5, "Question must be at least 5 characters"),
    answer: z.string().min(5, "Answer must be at least 5 characters")
  })).optional(),
  objectionsList: z.array(z.object({
    objection: z.string().min(5, "Objection trigger must be at least 5 characters"),
    rebuttal: z.string().min(5, "Rebuttal response must be at least 5 characters")
  })).optional(),
});

export type Step3Data = z.infer<typeof step3Schema>;

// ====================================================
// STEP 4: COMPLIANCE CONFIGURATION
// ====================================================
export const step4Schema = z.object({
  consentConfirmed: z.boolean().refine((val) => val === true, {
    message: "You must confirm prior express written consent to proceed",
  }),
  recordingDisclosure: z.boolean(),
  country: z.string().min(1, "Please select a country"),
});

export type Step4Data = z.infer<typeof step4Schema>;

// ====================================================
// STEP 5: IMPORT CONTACTS
// ====================================================
export const step5Schema = z.object({
  importSource: z.enum(["csv", "hubspot", "salesforce"]),
  campaignGoal: z.string().min(1, "Please select a campaign goal"),
  playbookGreeting: z.string().min(10, "Playbook greeting script must be at least 10 characters"),
  playbookBookingLink: z.string().url("Invalid booking URL. Must start with http:// or https://").or(z.string().length(0)).optional(),
});

export type Step5Data = z.infer<typeof step5Schema>;

// ====================================================
// STEP 6: TEST CALL
// ====================================================
export const step6Schema = z.object({
  testPhone: z.string().regex(/^\+[1-9]\d{1,14}$/, "Must be a valid E.164 phone number, e.g. +19195551234"),
});

export type Step6Data = z.infer<typeof step6Schema>;

// ====================================================
// AGGREGATE WIZARD DATA TYPE
// ====================================================
export interface OnboardingWizardState {
  currentStep: number;
  step1: Step1Data | null;
  step2: Step2Data | null;
  step3: Step3Data | null;
  step4: Step4Data | null;
  step5: Step5Data | null;
  step6: Step6Data | null;
  isCompleted: boolean;
}
