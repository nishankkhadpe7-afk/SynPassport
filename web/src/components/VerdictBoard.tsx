"use client";

import React, { useState } from "react";
import { VerdictState } from "@/types";
import { StateBadge } from "./StateBadge";

interface VerdictBoardProps {
  verdicts: Record<string, VerdictState>;
  isLoading?: boolean;
}

export const VerdictBoard: React.FC<VerdictBoardProps> = ({
  verdicts,
  isLoading = false,
}) => {
  const [selectedPurpose, setSelectedPurpose] = useState<string | null>(null);

  const softwareVerdict = verdicts?.software_testing || "PASS";
  const prototypingVerdict = verdicts?.ml_prototyping || "WARNING";
  const clinicalVerdict = verdicts?.clinical_ml || "INSUFFICIENT_EVIDENCE";

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Forensic Context Banner */}
      <div className="relative overflow-hidden rounded-lg bg-[#11151a] p-5 border border-[#232a33]">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded bg-[#17202b] flex items-center justify-center text-[#2dd4bf] shrink-0 border border-[#232a33]">
              <span className="material-symbols-outlined text-xl">bolt</span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-mono uppercase tracking-wider text-[#2dd4bf] font-bold">
                  DETERMINISTIC EVALUATION ENGINE
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#17202b] text-[#34d399] border border-[#34d399]/30">
                  POLICY: ml-sensitive-v1
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#17202b] text-[#8b95a3] border border-[#232a33]">
                  RUN: #8842F
                </span>
              </div>
              <p className="text-xs text-[#8b95a3] mt-1 leading-relaxed">
                Verdicts are computed by a deterministic policy engine, with zero LLM involved.
                All mathematical rules are cryptographically pinned to policy profile{" "}
                <span className="font-mono text-[#e6eaf0] font-semibold">ml-sensitive-v1</span>.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#0a0c0f] border border-[#232a33] text-xs font-mono shrink-0">
            <span className="material-symbols-outlined text-xs text-[#34d399]">verified_user</span>
            <span className="text-[#859490]">ED25519 HASH:</span>
            <span className="text-[#2dd4bf] font-semibold">0x7F4B…9A11</span>
          </div>
        </div>
      </div>

      {/* 4 Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#11151a] p-4 rounded-lg border border-[#232a33] flex items-center justify-between">
          <div>
            <div className="text-[10px] font-mono text-[#859490] uppercase tracking-wider">
              Audited Intent Scope
            </div>
            <div className="text-lg font-bold text-[#e6eaf0] mt-0.5">3 Intended Uses</div>
          </div>
          <span className="material-symbols-outlined text-[#2dd4bf] text-2xl">rule</span>
        </div>

        <div className="bg-[#11151a] p-4 rounded-lg border border-[#232a33] flex items-center justify-between">
          <div>
            <div className="text-[10px] font-mono text-[#859490] uppercase tracking-wider">
              Primary Attestation
            </div>
            <div className="text-lg font-bold text-[#34d399] mt-0.5">1 PASS / 1 WARN</div>
          </div>
          <span className="material-symbols-outlined text-[#34d399] text-2xl">verified</span>
        </div>

        <div className="bg-[#11151a] p-4 rounded-lg border border-[#232a33] flex items-center justify-between">
          <div>
            <div className="text-[10px] font-mono text-[#859490] uppercase tracking-wider">
              Evidence Completeness
            </div>
            <div className="text-lg font-bold text-[#7ba7d9] mt-0.5">1 INSUFFICIENT</div>
          </div>
          <span className="material-symbols-outlined text-[#7ba7d9] text-2xl">pie_chart</span>
        </div>

        <div className="bg-[#11151a] p-4 rounded-lg border border-[#232a33] flex items-center justify-between">
          <div>
            <div className="text-[10px] font-mono text-[#859490] uppercase tracking-wider">
              Total Gate Checks
            </div>
            <div className="text-lg font-bold text-[#e6eaf0] mt-0.5">21 Rigorous Rules</div>
          </div>
          <span className="material-symbols-outlined text-[#2dd4bf] text-2xl">checklist_rtl</span>
        </div>
      </div>

      {isLoading ? (
        <div className="p-12 text-center bg-[#11151a] rounded-lg border border-[#232a33]">
          <div className="w-8 h-8 border-2 border-[#2dd4bf] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-mono text-[#8b95a3]">Evaluating deterministic policy gates...</p>
        </div>
      ) : (
        /* 3 Large Purpose Verdict Cards */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
          {/* CARD 1: Software Testing (PASS) */}
          <div className="bg-[#11151a] rounded-lg border border-[#34d399]/40 flex flex-col justify-between overflow-hidden">
            <div>
              {/* Header */}
              <div className="p-5 pb-4 bg-[#17202b] border-b border-[#232a33]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono text-[#859490] uppercase tracking-wider">
                    INTENT_SCOPE::01
                  </span>
                  <StateBadge state={softwareVerdict} size="sm" />
                </div>
                <h2 className="text-base font-bold text-[#e6eaf0] leading-snug">
                  Software Testing &amp; Pipeline Simulation
                </h2>
                <p className="text-xs font-mono text-[#34d399] mt-1">scope: software_testing</p>
              </div>

              {/* Visual Metric Cluster */}
              <div className="px-5 py-3 bg-[#0a0c0f] border-b border-[#232a33] flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full border-2 border-[#34d399] flex items-center justify-center font-mono text-xs font-bold text-[#34d399]">
                    6/6
                  </div>
                  <div>
                    <span className="text-[10px] font-mono text-[#859490] uppercase block">
                      Passing Criteria
                    </span>
                    <span className="text-xs font-mono text-[#e6eaf0] font-semibold">
                      100% Policy Conformity
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-mono text-[#859490] uppercase block">
                    Max Delta
                  </span>
                  <span className="text-xs font-mono text-[#34d399] font-bold">0.000% Err</span>
                </div>
              </div>

              {/* Checklist */}
              <div className="p-5 space-y-2 font-mono text-xs">
                <div className="text-[10px] uppercase text-[#859490] flex items-center justify-between mb-1">
                  <span>Deterministic Checks</span>
                  <span>Observed vs Req</span>
                </div>

                {[
                  { name: "Schema Validity", val: "100.0%", req: "≥99%" },
                  { name: "Null Preservation", val: "0.0% mismatch", req: "≤0.1%" },
                  { name: "Categorical TVD", val: "TVD 0.04", req: "≤0.10" },
                  { name: "Correlation Fidelity", val: "0.92", req: "≥0.85" },
                ].map((check, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded bg-[#0a0c0f] border border-[#232a33]"
                  >
                    <div className="flex items-center gap-1.5 truncate">
                      <span className="material-symbols-outlined text-xs text-[#34d399]">
                        check_circle
                      </span>
                      <span className="text-[#e6eaf0] text-[11px] truncate">{check.name}</span>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-[#34d399] font-bold">{check.val}</span>
                      <span className="text-[#859490] text-[10px]"> ({check.req})</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 bg-[#17202b] border-t border-[#232a33]">
              <div className="p-2 rounded bg-[#0a0c0f] border border-[#34d399]/30 text-[11px] font-mono text-[#34d399]">
                ✓ Validated for automated CI/CD and mock staging.
              </div>
            </div>
          </div>

          {/* CARD 2: ML Prototyping (WARNING) */}
          <div className="bg-[#11151a] rounded-lg border border-[#f59e0b]/40 flex flex-col justify-between overflow-hidden">
            <div>
              {/* Header */}
              <div className="p-5 pb-4 bg-[#17202b] border-b border-[#232a33]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono text-[#859490] uppercase tracking-wider">
                    INTENT_SCOPE::02
                  </span>
                  <StateBadge state={prototypingVerdict} size="sm" />
                </div>
                <h2 className="text-base font-bold text-[#e6eaf0] leading-snug">
                  ML Model Prototyping &amp; Exploration
                </h2>
                <p className="text-xs font-mono text-[#f59e0b] mt-1">scope: ml_prototyping</p>
              </div>

              {/* Visual Metric Cluster */}
              <div className="px-5 py-3 bg-[#0a0c0f] border-b border-[#232a33] flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full border-2 border-[#f59e0b] flex items-center justify-center font-mono text-xs font-bold text-[#f59e0b]">
                    4/5
                  </div>
                  <div>
                    <span className="text-[10px] font-mono text-[#859490] uppercase block">
                      Passing Criteria
                    </span>
                    <span className="text-xs font-mono text-[#e6eaf0] font-semibold">
                      80% Policy Conformity
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-mono text-[#859490] uppercase block">
                    Max Delta
                  </span>
                  <span className="text-xs font-mono text-[#f59e0b] font-bold">+0.038 Warn</span>
                </div>
              </div>

              {/* Checklist */}
              <div className="p-5 space-y-2 font-mono text-xs">
                <div className="text-[10px] uppercase text-[#859490] flex items-center justify-between mb-1">
                  <span>Deterministic Checks</span>
                  <span>Observed vs Req</span>
                </div>

                {[
                  { name: "Schema & Marginal", val: "99.8%", req: "≥99%", pass: true },
                  { name: "Correlation Matrix", val: "Cosine 0.89", req: "≥0.85", pass: true },
                  { name: "TSTR Utility Ratio (F1)", val: "0.88", req: "≥0.90", warn: true },
                  { name: "Feature Importance Drift", val: "Spearman 0.84", req: "≥0.80", pass: true },
                ].map((check, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded bg-[#0a0c0f] border border-[#232a33]"
                  >
                    <div className="flex items-center gap-1.5 truncate">
                      <span
                        className={`material-symbols-outlined text-xs ${
                          check.warn ? "text-[#f59e0b]" : "text-[#34d399]"
                        }`}
                      >
                        {check.warn ? "warning" : "check_circle"}
                      </span>
                      <span className="text-[#e6eaf0] text-[11px] truncate">{check.name}</span>
                    </div>
                    <div className="text-right shrink-0">
                      <span className={check.warn ? "text-[#f59e0b] font-bold" : "text-[#34d399]"}>
                        {check.val}
                      </span>
                      <span className="text-[#859490] text-[10px]"> ({check.req})</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 bg-[#17202b] border-t border-[#232a33]">
              <div className="p-2 rounded bg-[#0a0c0f] border border-[#f59e0b]/30 text-[11px] font-mono text-[#f59e0b]">
                ⚠ Human release sign-off required for production handoff.
              </div>
            </div>
          </div>

          {/* CARD 3: Clinical ML (INSUFFICIENT) */}
          <div className="bg-[#11151a] rounded-lg border border-[#7ba7d9]/40 flex flex-col justify-between overflow-hidden">
            <div>
              {/* Header */}
              <div className="p-5 pb-4 bg-[#17202b] border-b border-[#232a33]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono text-[#859490] uppercase tracking-wider">
                    INTENT_SCOPE::03
                  </span>
                  <StateBadge state={clinicalVerdict} size="sm" />
                </div>
                <h2 className="text-base font-bold text-[#e6eaf0] leading-snug">
                  Clinical ML &amp; Regulated Inference
                </h2>
                <p className="text-xs font-mono text-[#7ba7d9] mt-1">scope: clinical_ml</p>
              </div>

              {/* Visual Metric Cluster */}
              <div className="px-5 py-3 bg-[#0a0c0f] border-b border-[#232a33] flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full border-2 border-dashed border-[#7ba7d9] flex items-center justify-center font-mono text-xs font-bold text-[#7ba7d9]">
                    3/7
                  </div>
                  <div>
                    <span className="text-[10px] font-mono text-[#859490] uppercase block">
                      Evidence Completeness
                    </span>
                    <span className="text-xs font-mono text-[#e6eaf0] font-semibold">
                      42.8% Verified
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-mono text-[#859490] uppercase block">
                    Deficit
                  </span>
                  <span className="text-xs font-mono text-[#f87171] font-bold">-136 Records</span>
                </div>
              </div>

              {/* Checklist & Actionable Refusal */}
              <div className="p-5 space-y-2 font-mono text-xs">
                <div className="text-[10px] uppercase text-[#859490] flex items-center justify-between mb-1">
                  <span>Deterministic Checks</span>
                  <span>Observed vs Req</span>
                </div>

                <div className="p-2.5 rounded bg-[#0a0c0f] border border-dashed border-[#7ba7d9] space-y-1">
                  <div className="flex items-center justify-between text-[#7ba7d9]">
                    <span className="font-bold">Subgroup CI Width (age≥65)</span>
                    <span className="text-[#f87171] font-bold">0.340</span>
                  </div>
                  <div className="text-[10px] text-[#859490] leading-tight">
                    Requires CI ≤ 0.150. Current N=35 &lt; 171 required for adequate statistical power.
                  </div>
                </div>

                {[
                  { name: "Privacy DCR vs Holdout", val: "0.184 (Safe)", req: "≥Holdout", pass: true },
                  { name: "Membership Inference", val: "AUC 0.518", req: "≤0.55", pass: true },
                ].map((check, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded bg-[#0a0c0f] border border-[#232a33]"
                  >
                    <div className="flex items-center gap-1.5 truncate">
                      <span className="material-symbols-outlined text-xs text-[#34d399]">
                        check_circle
                      </span>
                      <span className="text-[#e6eaf0] text-[11px] truncate">{check.name}</span>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-[#34d399] font-bold">{check.val}</span>
                      <span className="text-[#859490] text-[10px]"> ({check.req})</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 bg-[#17202b] border-t border-[#232a33]">
              <div className="p-2 rounded bg-[#0a0c0f] border border-dashed border-[#7ba7d9] text-[11px] font-mono text-[#7ba7d9]">
                Actionable Refusal: Subgroup harvest required before sealing.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
