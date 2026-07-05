import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";

export interface AnalyzeDomainResponse {
  company_name: string;
  company_description: string;
  value_proposition: string;
  estimated_industries: { industry: string; confidence: number }[];
  estimated_regions: { region: string; confidence: number }[];
  estimated_decision_makers: { title: string; confidence: number }[];
  potential_competitors: string[];
  potential_objections: { objection: string; rebuttal: string }[];
  suggested_segments: { segment: string; confidence: number; rationale: string }[];
  brand_voice_tone: string;
}

export async function analyzeDomain(website: string): Promise<AnalyzeDomainResponse> {
  const response = await fetch(`${BACKEND_URL}/api/onboarding/analyze-domain`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ website }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to analyze domain");
  }

  return response.json();
}

export interface CompletePayload {
  tenant_id: string;
  company_name: string;
  website: string;
  industry?: string;
  team_size?: string;
  annual_revenue?: string;
  target_region?: string;
  phone_number?: string | null;
  agent_name?: string | null;
  company_description?: string;
  value_proposition?: string;
  voice?: string;
  tone?: string;
  timezone?: string;
  calling_hours_start?: string;
  calling_hours_end?: string;
  product_name?: string;
  product_price?: string;
  product_features?: string;
  target_audience?: string;
  kb_description?: string;
  kb_faqs?: any[];
  objections_list?: any[];
  recording_disclosure?: boolean;
  consent_confirmed?: boolean;
  country?: string;
  import_source?: string;
  campaign_goal?: string;
  playbook_greeting?: string;
  playbook_booking_link?: string;
  icp_industries?: string[];
  icp_company_sizes?: string[];
  icp_regions?: string[];
  decision_maker_titles?: string[];
  avoid_list?: string[];
  competitors?: string[];
  brand_voice_tone?: string;
  icp_segments?: any[];
  buyer_personas?: any[];
}

export async function completeOnboarding(payload: CompletePayload): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/api/onboarding/complete`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to complete onboarding");
  }
}
