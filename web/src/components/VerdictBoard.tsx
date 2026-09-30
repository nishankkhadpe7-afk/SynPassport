"use client";

import React from "react";
import {
  FileCheck2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Shield,
  Layers,
  Info,
} from "lucide-react";
import { VerdictState } from "@/types";
import { StateBadge } from "./StateBadge";

interface VerdictBoardProps {
  verdicts: Record<string, VerdictState>;
  isLoading?: boolean;
}

const USE_CHECKS_MAPPING: Record<string, string[]> = {
  software_testing: ["schema_validity", "marginal_fidelity"],
  ml_prototyping: [
    "schema_validity",
    "marginal_fidelity",
    "correlation_fidelity",
    "utility_tstr_ratio",
  ],
  clinical_ml: [
    "schema_validity",
    "marginal_fidelity",
    "correlation_fidelity",
    "utility_tstr_ratio",
    "subgroup_utility_ci_width",
    "privacy_dcr_vs_holdout",
    "membership_inference_auc",
  ],
  exploratory_analytics: [
    "schema_validity",
    "marginal_fidelity",
    "correlation_fidelity",
  ],
};

const DEFAULT_BLOCKING_REASONS: Record<string, Record<VerdictState, string>> = {
  clinical_ml: {
    PASS: "All required empirical gates satisfied. No unacceptable risk detected under the specified attacks. Supports audit.",
    WARNING: "Empirical metrics within cautionary tolerance band. Human release authorization required.",
    FAIL: "Adversarial privacy checks or utility bounds violated under specified attack model.",
    INSUFFICIENT_EVIDENCE:
      "Critical subgroup sample size (N=35) yields CI width 0.32 > target threshold 0.15. Requires >= 171 records for 'age >= 65'.",
  },
  software_testing: {
    PASS: "Schema structure and marginal distributions validated. No unacceptable risk detected under the specified attacks. Supports audit.",
    WARNING: "Marginal distribution divergence near threshold boundaries.",
    FAIL: "Schema invalid or columns missing compared to reference dataset.",
    INSUFFICIENT_EVIDENCE: "Insufficient record count to assess column distributions.",
  },
  ml_prototyping: {
    PASS: "General utility and correlation structures confirmed. No unacceptable risk detected under the specified attacks. Supports audit.",
    WARNING: "TSTR utility ratio slightly below ideal target but within tolerance.",
    FAIL: "TSTR utility ratio dropped below critical bound (ratio < 0.85).",
    INSUFFICIENT_EVIDENCE: "Target class balance insufficient to establish model baseline.",
  },
  exploratory_analytics: {
    PASS: "Descriptive statistics match baseline expectations. No unacceptable risk detected under the specified attacks. Supports audit.",
    WARNING: "Higher order covariance divergence noted.",
    FAIL: "Key feature distributions diverge significantly from baseline.",
    INSUFFICIENT_EVIDENCE: "Sample size too small to evaluate bivariate dependencies.",
  },
};

export const VerdictBoard: React.FC<VerdictBoardProps> = ({
  verdicts,
  isLoading = false,
}) => {
  const intendedUses = Object.keys(verdicts).length > 0
    ? Object.keys(verdicts)
    : ["software_testing", "clinical_ml", "ml_prototyping"];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <FileCheck2 className="w-5 h-5 text-indigo-400" />
            Purpose-Bound Verdict Board
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Independent, purpose-scoped verdicts computed deterministically by the policy engine.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          Total Intended Uses: <span className="text-white font-bold">{intendedUses.length}</span>
        </div>
      </div>

      {isLoading ? (
        <div className="glass-panel p-12 text-center rounded-2xl">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-xs font-mono">Evaluating purpose gates against policy specification...</p>
        </div>
      ) : intendedUses.length === 0 ? (
        <div className="glass-panel p-12 text-center rounded-2xl text-slate-400 text-xs font-mono">
          No intended uses evaluated yet. Run an assurance mission to view verdicts.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {intendedUses.map((use) => {
            const state: VerdictState = verdicts[use] || "INSUFFICIENT_EVIDENCE";
            const requiredChecks = USE_CHECKS_MAPPING[use] || [
              "schema_validity",
              "marginal_fidelity",
            ];

            const reasonMap = DEFAULT_BLOCKING_REASONS[use] || DEFAULT_BLOCKING_REASONS.clinical_ml;
            const explanation = reasonMap[state];

            return (
              <div
                key={use}
                className="glass-panel rounded-2xl p-5 space-y-4 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
              >
                <div className="space-y-3">
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <span className="text-[11px] font-mono text-indigo-400 uppercase tracking-wider block">
                        Intended Use
                      </span>
                      <h3 className="text-base font-bold font-mono text-white tracking-wide">
                        {use}
                      </h3>
                    </div>
                    <StateBadge state={state} size="md" />
                  </div>

                  {/* Required Checks List */}
                  <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
                    <span className="text-[11px] font-mono uppercase text-slate-500 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5" />
                      Required Pre-Registered Checks ({requiredChecks.length})
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {requiredChecks.map((check) => (
                        <span
                          key={check}
                          className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300"
                        >
                          {check}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Blocking Reason / Rationale Callout */}
                <div
                  className={`p-3 rounded-xl border text-xs font-sans mt-3 space-y-1 ${
                    state === "PASS"
                      ? "bg-emerald-950/20 border-emerald-900/40 text-emerald-300"
                      : state === "WARNING"
                      ? "bg-amber-950/20 border-amber-900/40 text-amber-300"
                      : state === "FAIL"
                      ? "bg-rose-950/20 border-rose-900/40 text-rose-300"
                      : "bg-slate-900/80 border-slate-700/60 text-slate-300"
                  }`}
                >
                  <div className="flex items-center gap-1.5 font-semibold text-[11px] uppercase tracking-wider">
                    <Info className="w-3.5 h-3.5 shrink-0" />
                    <span>
                      {state === "PASS"
                        ? "Gate Decision: Cleared for Use"
                        : state === "WARNING"
                        ? "Gate Decision: Cautionary Release"
                        : state === "FAIL"
                        ? "Gate Decision: Blocked (Failure)"
                        : "Gate Decision: Actionable Refusal"}
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed opacity-90">{explanation}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Assurance Summary Alert */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start gap-3 text-xs text-slate-400">
        <Shield className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold text-slate-200">Enforcement Model:</span>
          <p>
            Verdicts are strictly scoped by purpose. Passing for <code className="text-indigo-300">software_testing</code>{" "}
            does not authorize deployment for <code className="text-indigo-300">clinical_ml</code>.
            Each consumer verifies purpose compatibility at ingestion time. Supports audit.
          </p>
        </div>
      </div>
    </div>
  );
};
