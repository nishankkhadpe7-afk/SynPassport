"use client";

import React from "react";
import {
  Users,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  ShieldAlert,
  ArrowRight,
  Info,
} from "lucide-react";
import { SufficiencyResponse } from "@/types";
import { StateBadge } from "./StateBadge";

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
  const ciWidth = sufficiency?.ci_width ?? 0.32;
  const targetWidth = 0.15;
  const subgroups = sufficiency?.subgroups ?? [
    {
      subgroup_query: "age >= 65",
      current_n: 35,
      required_min_n: 171,
      projected_ci_width: 0.32,
      target_ci_width: 0.15,
      state: "INSUFFICIENT_EVIDENCE",
      reason:
        "Subgroup 'age >= 65' has N=35 < required 171 for target CI width 0.15 (projected: 0.320).",
    },
  ];

  const primarySubgroup = subgroups[0];
  const deficit = Math.max(0, requiredMinN - currentN);
  const progressPct = Math.min(100, Math.round((currentN / requiredMinN) * 100));

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-400" />
            Subgroup Sample Size Sufficiency &amp; Power
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Empirical statistical power verification preventing false certainty on under-represented cohorts.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">Policy Principle:</span>
          <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-indigo-300">
            Actionable Refusal
          </span>
        </div>
      </div>

      {isLoading ? (
        <div className="glass-panel p-12 text-center rounded-2xl">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-xs font-mono">Computing subgroup statistical power requirements...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Main Actionable Refusal Card: "need >= N records aged 65+" */}
          <div className="glass-panel rounded-2xl p-6 border border-slate-700/80 bg-gradient-to-b from-slate-900/90 to-slate-950 space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                    Target Critical Subgroup
                  </span>
                  <code className="text-xs font-mono bg-indigo-950/80 text-indigo-300 px-2 py-0.5 rounded border border-indigo-800/60 font-semibold">
                    {primarySubgroup?.subgroup_query || "age >= 65"}
                  </code>
                </div>
                <h3 className="text-2xl font-bold tracking-tight text-white flex items-baseline gap-2">
                  <span>need &gt;= {requiredMinN} records aged 65+</span>
                </h3>
                <p className="text-slate-400 text-xs">
                  Current available sample: <strong className="text-slate-200">{currentN} records</strong>{" "}
                  (Deficit: <span className="text-amber-400 font-mono font-semibold">{deficit} records</span> needed).
                </p>
              </div>

              <StateBadge state={primarySubgroup?.state || "INSUFFICIENT_EVIDENCE"} size="lg" />
            </div>

            {/* Sample Progress Bar */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400">
                  Current Sample: <strong className="text-white">{currentN}</strong>
                </span>
                <span className="text-slate-400">
                  Target Min N: <strong className="text-indigo-300">{requiredMinN}</strong>
                </span>
              </div>

              <div className="w-full bg-slate-950 rounded-full h-3.5 overflow-hidden border border-slate-800 p-0.5">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    progressPct >= 100 ? "bg-emerald-500" : "bg-gradient-to-r from-indigo-500 to-amber-500"
                  }`}
                  style={{ width: `${progressPct}%` }}
                />
              </div>

              <div className="flex justify-between text-[11px] font-mono text-slate-500">
                <span>0</span>
                <span>{progressPct}% statistical power achieved</span>
                <span>{requiredMinN} req</span>
              </div>
            </div>

            {/* Confidence Interval Precision Comparison */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                  Projected 95% CI Width
                </span>
                <div className="text-2xl font-mono font-bold text-amber-400">
                  &plusmn;{ciWidth.toFixed(3)}
                </div>
                <p className="text-[11px] text-slate-500">
                  Wide interval due to small sample size N={currentN}. High estimation uncertainty.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                  Policy Target CI Width Limit
                </span>
                <div className="text-2xl font-mono font-bold text-emerald-400">
                  &le;{targetWidth.toFixed(3)}
                </div>
                <p className="text-[11px] text-slate-500">
                  Mandatory threshold for clinical ML release. Requires N &ge; {requiredMinN}.
                </p>
              </div>
            </div>

            {/* Actionable Refusal Message */}
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-700/60 flex items-start gap-3 text-xs text-slate-300">
              <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-semibold text-slate-100">
                  Actionable Refusal Principle (Design Decision §1.6):
                </span>
                <p className="text-slate-400 leading-relaxed">
                  Unlike traditional systems that grant a weak pass on underpowered subsets, SynPassport
                  explicitly halts with <code className="text-slate-200">INSUFFICIENT_EVIDENCE</code>.
                  To achieve authorization for high-stakes purposes such as <code className="text-indigo-300">clinical_ml</code>,
                  expand data collection for patients aged 65+ by at least {deficit} records.
                </p>
              </div>
            </div>
          </div>

          {/* Subgroup Cohort Breakdown Table */}
          <div className="glass-panel rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Users className="w-4 h-4 text-indigo-400" />
              All Monitored Critical Subgroups
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="pb-3 font-semibold">Subgroup Query</th>
                    <th className="pb-3 font-semibold">Current N</th>
                    <th className="pb-3 font-semibold">Required Min N</th>
                    <th className="pb-3 font-semibold">Projected CI</th>
                    <th className="pb-3 font-semibold">Target CI</th>
                    <th className="pb-3 font-semibold">Gate State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {subgroups.map((sub, i) => (
                    <tr key={i} className="hover:bg-slate-900/40">
                      <td className="py-3 text-indigo-300 font-semibold">{sub.subgroup_query}</td>
                      <td className="py-3 text-white">{sub.current_n}</td>
                      <td className="py-3 text-slate-400">{sub.required_min_n}</td>
                      <td className="py-3 text-amber-400">&plusmn;{sub.projected_ci_width.toFixed(3)}</td>
                      <td className="py-3 text-emerald-400">&le;{sub.target_ci_width.toFixed(3)}</td>
                      <td className="py-3">
                        <StateBadge state={sub.state} size="sm" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
