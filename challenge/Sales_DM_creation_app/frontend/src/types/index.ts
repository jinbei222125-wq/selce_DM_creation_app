export type EvidenceItem = {
  source: string;
  title: string;
  snippet: string;
  url: string;
};

export type HookItem = {
  id: number;
  title: string;
  reason: string;
  related_evidence_indices: number[];
};

export type ToneType = "polite" | "casual" | "problem_solver";

export type DMDraft = {
  tone: ToneType;
  title: string;
  body_markdown: string;
};

export type GenerateDMRequest = {
  target_url: string;
  target_role?: string | null;
  company_name?: string | null;
  your_product_name: string;
  your_product_summary: string;
  preferred_tones?: ToneType[];
};

export type GenerateDMResponse = {
  generation_id?: number | null;
  evidences: EvidenceItem[];
  hooks: HookItem[];
  drafts: DMDraft[];
  created_at: string;
};

export type ProgressUpdate = {
  stage: "researching" | "analyzing" | "writing" | "completed";
  message: string;
  progress: number;
};
