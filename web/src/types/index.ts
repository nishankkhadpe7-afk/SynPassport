export type VerdictState = "PASS" | "WARNING" | "FAIL" | "INSUFFICIENT_EVIDENCE";

export interface CandidateRecord {
  candidate_id: string;
  generator: string;
  verdicts: Record<string, VerdictState>;
  fail_count?: number;
  inconclusive_count?: number;
  mean_score?: number;
  csv_path?: string;
}

export interface BudgetUsed {
  candidates_evaluated: number;
  max_candidates: number;
  repairs_attempted: number;
  max_repairs: number;
}

export interface RunStatus {
  run_id: string;
  status: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";
  candidates: CandidateRecord[];
  repairs: Array<{ action: string; params: Record<string, unknown>; candidate_id?: string }>;
  agent_rejections: Array<{ proposal: string; reason: string }>;
  budget_used: BudgetUsed;
  verdicts: Record<string, VerdictState>;
  best_candidate_id?: string | null;
  error?: string | null;
}

export interface DcrBin {
  low: number;
  high: number;
  to_training: number;
  to_holdout: number;
}

export interface DcrResult {
  candidate: string;
  sample_size: number;
  seed: number;
  bins: DcrBin[];
  p5_to_training: number;
  p5_to_holdout: number;
  median_to_training: number;
  median_to_holdout: number;
  share_closer_to_training: number;
  exact_copies_of_training: number;
}

export interface PolicySummary {
  id: string;
  version: number;
  name: string;
  description: string;
  sha256: string;
  uses: Record<string, string[]>;
  requires: Record<string, unknown>;
  budget: { max_candidates?: number; max_repairs?: number };
  human_approval?: string;
}

export interface EvidenceItem {
  check_id: string;
  value: number | null;
  ci_low: number | null;
  ci_high: number | null;
  n: number | null;
  seed: number | null;
  state: string | null;
  threshold_ref: unknown;
  extra?: Record<string, unknown>;
}

export interface AgentEvent {
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface SubgroupSufficiencyItem {
  subgroup_query: string;
  current_n: number;
  required_min_n: number;
  projected_ci_width: number;
  target_ci_width: number;
  state: string;
  reason: string;
}

export interface SufficiencyResponse {
  run_id: string;
  current_n: number;
  required_min_n: number;
  ci_width: number;
  subgroups: SubgroupSufficiencyItem[];
}

export interface VerificationResult {
  valid: boolean;
  reason_code: string;
  description: string;
  details?: Record<string, unknown>;
}
