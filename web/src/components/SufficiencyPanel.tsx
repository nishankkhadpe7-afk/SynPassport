"use client";

import React from "react";
import { SufficiencyResponse } from "@/types";

interface SufficiencyPanelProps {
  sufficiency: SufficiencyResponse | null;
  isLoading?: boolean;
}

export const SufficiencyPanel: React.FC<SufficiencyPanelProps> = ({
  sufficiency,
  isLoading = false,
}) => {
  const currentN = sufficiency?.current_n ?? 35;
  const requiredMinN = sufficiency?.required_min_n ?? 171;
  const deficit = Math.max(0, requiredMinN - currentN);
  const validatedPct = Math.round((currentN / requiredMinN) * 100);

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="relative overflow-hidden rounded-lg bg-[#11151a] border border-[#232a33]">
        <div className="p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-4 max-w-4xl">
            <div className="p-3 rounded bg-[#17202b] text-[#7ba7d9] shrink-0 border border-[#232a33]">
              <span className="material-symbols-outlined text-2xl">biotech</span>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#17202b] text-[#7ba7d9] border border-[#7ba7d9]/30 font-bold">
                  STAGE 05 · SUFFICIENCY AUDIT
                </span>
                <span className="text-xs font-mono text-[#859490]">POLICY ID: MED-BOUND-2025.04B</span>
                <span className="text-xs font-mono text-[#f87171] bg-[#17202b] px-2 py-0.5 rounded border border-[#f87171]/30">
                  STATISTICAL_UNDERPOWER
                </span>
              </div>
              <h1 className="text-lg sm:text-xl font-bold text-[#e6eaf0] tracking-tight">
                NEED ≥ 171 RECORDS AGED 65+ FOR CLINICAL_ML VERDICT
              </h1>
              <p className="text-xs text-[#8b95a3] mt-1 leading-relaxed">
                The current synthetic generation lacks sufficient statistical power to bound geriatric
                clinical performance within pre-registered confidence limits. Notarization cannot seal
                passport until subgroup bounds verify.
              </p>
            </div>
          </div>

          <div className="shrink-0 flex flex-col items-start md:items-end gap-1 font-mono text-xs">
            <div className="flex items-center gap-2 bg-[#0a0c0f] px-3 py-1.5 rounded border border-[#232a33]">
              <span className="w-2 h-2 rounded-full bg-[#7ba7d9] animate-pulse" />
              <span className="text-[#8b95a3]">ALPHA THRESHOLD:</span>
              <span className="text-[#7ba7d9] font-bold">α ≤ 0.05</span>
            </div>
            <span className="text-[10px] text-[#859490]">MANDATE: FDA/EMA 21 CFR PT 11</span>
          </div>
        </div>

        {/* Progress Strip */}
        <div className="h-1 w-full bg-[#17202b]">
          <div className="h-1 bg-[#7ba7d9] transition-all" style={{ width: `${validatedPct}%` }} />
        </div>
      </div>

      {isLoading ? (
        <div className="p-12 text-center bg-[#11151a] rounded-lg border border-[#232a33]">
          <div className="w-8 h-8 border-2 border-[#7ba7d9] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-mono text-[#8b95a3]">Computing subgroup power requirements...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Subgroup Quota & Hypotheses (4 Cols) */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            {/* Subgroup Quota Card */}
            <div className="rounded-lg bg-[#11151a] p-5 border border-[#232a33] flex flex-col justify-between">
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#232a33]">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[#7ba7d9] text-base">
                    donut_large
                  </span>
                  <span className="text-xs font-mono uppercase tracking-wider text-[#e6eaf0] font-semibold">
                    Subgroup Quota
                  </span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#17202b] text-[#7ba7d9] font-bold border border-[#7ba7d9]/30">
                  {validatedPct}% VALIDATED
                </span>
              </div>

              {/* Radial Meter SVG */}
              <div className="flex flex-col items-center my-3">
                <div className="relative w-40 h-40 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 120 120">
                    <circle
                      cx="60"
                      cy="60"
                      r="48"
                      fill="transparent"
                      stroke="#17202b"
                      strokeWidth="8"
                    />
                    <circle
                      cx="60"
                      cy="60"
                      r="48"
                      fill="transparent"
                      stroke="#7ba7d9"
                      strokeWidth="8"
                      strokeDasharray="301.6"
                      strokeDashoffset={301.6 * (1 - currentN / requiredMinN)}
                      strokeLinecap="round"
                      className="transition-all duration-1000"
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center justify-center text-center font-mono">
                    <span className="text-2xl font-bold text-[#e6eaf0] leading-none">
                      {currentN}
                    </span>
                    <span className="text-[10px] text-[#859490] mt-1 font-semibold">
                      OF {requiredMinN} RECS
                    </span>
                    <span className="text-[9px] text-[#7ba7d9] uppercase tracking-wider mt-0.5 font-bold">
                      AGE ≥ 65
                    </span>
                  </div>
                </div>

                {/* Deficit Balance */}
                <div className="w-full mt-4 p-3 rounded bg-[#0a0c0f] border border-[#232a33] flex items-center justify-between">
                  <div className="flex flex-col">
                    <span className="text-[10px] font-mono uppercase text-[#859490]">
                      Deficit Balance
                    </span>
                    <span className="text-sm font-mono font-bold text-[#f87171]">
                      -{deficit} Records
                    </span>
                  </div>
                  <div className="flex flex-col text-right">
                    <span className="text-[10px] font-mono uppercase text-[#859490]">
                      Shortfall Delta
                    </span>
                    <span className="text-xs font-mono font-bold text-[#7ba7d9]">-79.5%</span>
                  </div>
                </div>
              </div>

              {/* Cohort Rule Parameters */}
              <div className="pt-2 font-mono text-xs text-[#8b95a3] space-y-1.5 border-t border-[#232a33]">
                <div className="flex justify-between">
                  <span className="text-[#859490]">Cohort Rule:</span>
                  <span className="text-[#e6eaf0] font-semibold">`subject.age &gt;= 65`</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#859490]">Target Mix:</span>
                  <span className="text-[#e6eaf0]">16.7% of N=1,024</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#859490]">Current Mix:</span>
                  <span className="text-[#f87171] font-medium">3.42% (Depleted)</span>
                </div>
              </div>
            </div>

            {/* Power & Hypotheses Card */}
            <div className="rounded-lg bg-[#11151a] p-5 border border-[#232a33] space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-[#232a33]">
                <div className="flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[#2dd4bf] text-base">tune</span>
                  <span className="text-xs uppercase tracking-wider text-[#e6eaf0] font-semibold">
                    Power &amp; Hypotheses
                  </span>
                </div>
                <span className="text-[10px] text-[#859490] uppercase">β SENSITIVITY</span>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-[#8b95a3]">Statistical Power (1 - β)</span>
                  <span className="text-[#f87171] font-bold">41.2% / Target 90.0%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-[#0a0c0f] border border-[#232a33] overflow-hidden">
                  <div className="h-full bg-[#f87171]" style={{ width: "41.2%" }} />
                </div>
                <p className="text-[10px] text-[#859490] mt-1">
                  High probability of Type II false acceptance on geriatric mortality.
                </p>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-[#8b95a3]">Hypothesis Rejection</span>
                  <span className="text-[#e6eaf0] font-bold">p = 0.084 (Req &lt; 0.01)</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-[#0a0c0f] border border-[#232a33] overflow-hidden">
                  <div className="h-full bg-[#7ba7d9]" style={{ width: "28%" }} />
                </div>
                <p className="text-[10px] text-[#859490] mt-1">
                  Unable to reject null hypothesis H0: AUC_geriatric ≤ 0.50.
                </p>
              </div>

              <div className="p-2.5 rounded bg-[#0a0c0f] border border-[#232a33] flex items-center gap-2">
                <span className="material-symbols-outlined text-[#2dd4bf] text-base">memory</span>
                <div className="text-[11px]">
                  <div className="text-[#e6eaf0] font-semibold">Resynthesis Estimate:</div>
                  <div className="text-[#859490]">+350 targeted seed queries to harvest 140 records.</div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Uncertainty Decay Curve (8 Cols) */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            <div className="rounded-lg bg-[#11151a] p-5 border border-[#232a33] flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#232a33] gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-[#2dd4bf] text-lg">
                      query_stats
                    </span>
                    <h2 className="text-sm font-bold text-[#e6eaf0]">
                      Uncertainty Decay Curve: CI Width = f(N)
                    </h2>
                  </div>
                  <p className="text-xs text-[#8b95a3] mt-0.5">
                    Empirical 95% Confidence Interval half-width bounding clinical metric ROC-AUC
                  </p>
                </div>
                <div className="flex items-center gap-2 font-mono text-xs">
                  <span className="px-2 py-0.5 rounded bg-[#0a0c0f] text-[#2dd4bf] border border-[#232a33]">
                    TARGET ±0.150
                  </span>
                  <span className="px-2 py-0.5 rounded bg-[#0a0c0f] text-[#7ba7d9] border border-[#232a33]">
                    CURRENT ±0.320
                  </span>
                </div>
              </div>

              {/* Area Chart SVG */}
              <div className="relative w-full h-64 bg-[#0a0c0f] rounded border border-[#232a33] p-4 flex flex-col justify-between">
                <svg className="w-full h-full" viewBox="0 0 500 200" fill="none">
                  {/* Grid Lines */}
                  <line x1="40" y1="20" x2="480" y2="20" stroke="#232a33" strokeWidth="1" />
                  <line x1="40" y1="60" x2="480" y2="60" stroke="#232a33" strokeWidth="1" />
                  <line x1="40" y1="100" x2="480" y2="100" stroke="#232a33" strokeWidth="1" />
                  <line x1="40" y1="140" x2="480" y2="140" stroke="#232a33" strokeWidth="1" />
                  <line x1="40" y1="180" x2="480" y2="180" stroke="#232a33" strokeWidth="1" />

                  {/* Policy Threshold Target Line (y = 0.15 => pixel y = 140) */}
                  <line
                    x1="40"
                    y1="140"
                    x2="480"
                    y2="140"
                    stroke="#2dd4bf"
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                  />
                  <text x="430" y="134" fill="#2dd4bf" fontSize="9" fontFamily="monospace">
                    CI = 0.150
                  </text>

                  {/* Decay Curve Area */}
                  <path
                    d="M 50 40 Q 120 120 280 140 T 480 165 L 480 180 L 50 180 Z"
                    fill="#7ba7d9"
                    fillOpacity="0.15"
                  />
                  <path
                    d="M 50 40 Q 120 120 280 140 T 480 165"
                    stroke="#7ba7d9"
                    strokeWidth="2.5"
                    fill="none"
                  />

                  {/* Current Operating Point: N=35, CI=0.320 */}
                  <circle cx="95" cy="72" r="5" fill="#f87171" stroke="#0a0c0f" strokeWidth="1.5" />
                  <text x="105" y="70" fill="#f87171" fontSize="10" fontFamily="monospace" fontWeight="bold">
                    N=35 (CI ±0.320)
                  </text>

                  {/* Target Crossing Point: N=171, CI=0.150 */}
                  <circle cx="280" cy="140" r="5" fill="#2dd4bf" stroke="#0a0c0f" strokeWidth="1.5" />
                  <text x="290" y="135" fill="#2dd4bf" fontSize="10" fontFamily="monospace" fontWeight="bold">
                    N=171 (Target Boundary)
                  </text>

                  {/* Axis Labels */}
                  <text x="45" y="195" fill="#859490" fontSize="9" fontFamily="monospace">N=0</text>
                  <text x="150" y="195" fill="#859490" fontSize="9" fontFamily="monospace">N=75</text>
                  <text x="270" y="195" fill="#859490" fontSize="9" fontFamily="monospace">N=171</text>
                  <text x="380" y="195" fill="#859490" fontSize="9" fontFamily="monospace">N=250</text>
                  <text x="460" y="195" fill="#859490" fontSize="9" fontFamily="monospace">N=350</text>
                </svg>
              </div>

              {/* Actionable Refusal Recommendation */}
              <div className="p-4 rounded bg-[#0a0c0f] border border-[#232a33] font-mono text-xs space-y-2">
                <div className="flex items-center gap-2 text-[#7ba7d9] font-bold">
                  <span className="material-symbols-outlined text-base">psychology</span>
                  <span>Actionable Refusal: Subgroup Harvest Protocol</span>
                </div>
                <p className="text-[#8b95a3] text-[11px] leading-relaxed">
                  The synthesis pipeline must not issue a clinical verdict on undersampled cohorts. To
                  resolve this refusal:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-1">
                  <div className="p-2 rounded bg-[#11151a] border border-[#232a33]">
                    <span className="text-[#e6eaf0] font-semibold block mb-0.5">1. Prior Resampling</span>
                    <span className="text-[#859490]">Increase conditional probability P(age &ge; 65) by 4.2x in generative seed.</span>
                  </div>
                  <div className="p-2 rounded bg-[#11151a] border border-[#232a33]">
                    <span className="text-[#e6eaf0] font-semibold block mb-0.5">2. Bound Recheck</span>
                    <span className="text-[#859490]">Evaluate N &ge; 171 records through bootstrap CI estimator.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
