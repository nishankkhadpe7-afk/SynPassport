"use client";

import React, { useState, useEffect } from "react";
import { RunStatus, AgentEvent, BudgetUsed } from "@/types";

interface RunTimelineProps {
  runId: string;
  runStatus: RunStatus | null;
  events: AgentEvent[];
  budgetUsed: BudgetUsed | null;
  isLoading: boolean;
  error?: string | null;
}

export const RunTimeline: React.FC<RunTimelineProps> = ({
  runId,
  runStatus,
  events,
  budgetUsed,
  error,
}) => {
  const [seconds, setSeconds] = useState<number>(252); // T+00:04:12 initial

  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatClock = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `T+00:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const candidatesUsed = budgetUsed?.candidates_evaluated ?? runStatus?.candidates?.length ?? 2;
  const maxCandidates = budgetUsed?.max_candidates ?? 3;
  const repairsUsed = budgetUsed?.repairs_attempted ?? runStatus?.repairs?.length ?? 1;
  const maxRepairs = budgetUsed?.max_repairs ?? 2;

  const candidatePct = Math.min(100, Math.round((candidatesUsed / maxCandidates) * 100));
  const repairPct = Math.min(100, Math.round((repairsUsed / maxRepairs) * 100));

  const isCompleted = runStatus?.status === "COMPLETED";

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Top Header Card */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#11151a] p-4 sm:p-5 rounded-lg border border-[#232a33]">
        <div className="flex items-center gap-3.5 min-w-0">
          <div className="w-10 h-10 rounded bg-[#17202b] flex items-center justify-center text-[#2dd4bf] shrink-0 border border-[#232a33]">
            <span className="material-symbols-outlined text-xl">timeline</span>
          </div>
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-base sm:text-lg font-bold text-[#e6eaf0] truncate">
                Assurance Execution Trace
              </h1>
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#17202b] text-[#2dd4bf] font-mono text-[10px] uppercase font-bold border border-[#2dd4bf]/25">
                <span className="w-1.5 h-1.5 rounded-full bg-[#2dd4bf] animate-ping" />
                {isCompleted ? "CERTIFIED · COMPLETE" : "STREAMING · CYCLE 02"}
              </span>
            </div>
            <p className="text-xs font-mono text-[#8b95a3] truncate">
              Session: <span className="text-[#e6eaf0] font-semibold">{runId || "RUN-202505-8842F"}</span>{" "}
              · Heart Disease Synth Attestation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0a0c0f] border border-[#232a33] font-mono text-xs text-[#859490]">
            <span className="material-symbols-outlined text-xs text-[#2dd4bf]">timer</span>
            <span>CLOCK</span>
            <span className="text-[#e6eaf0] font-semibold">{formatClock(seconds)}</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#17202b] text-[#34d399] border border-[#34d399]/30 font-mono text-xs font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-[#34d399] animate-pulse" />
            <span>LIVE INGESTION</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded bg-[#11151a] border border-[#f87171] text-[#f87171] text-xs font-mono">
          {error}
        </div>
      )}

      {/* Main Two-Column Trace & Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Trace Stages (8 Cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          <div className="relative flex flex-col gap-4 pl-4 sm:pl-6">
            {/* Continuous Vertical Timeline Rule */}
            <div className="absolute left-[27px] sm:left-[35px] top-6 bottom-6 w-px bg-[#232a33]" />

            {/* Stage 1: Plan */}
            <div className="relative flex items-start gap-4">
              <div className="w-10 h-10 rounded bg-[#17202b] text-[#34d399] flex items-center justify-center shrink-0 border border-[#232a33] z-10">
                <span className="material-symbols-outlined text-lg">schema</span>
              </div>
              <div className="flex-1 bg-[#11151a] rounded-lg p-4 border border-[#232a33] hover:border-[#859490] transition-colors">
                <div className="flex flex-wrap items-center justify-between gap-1 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#17202b] text-[#8b95a3]">
                      01. Plan
                    </span>
                    <h2 className="text-sm font-semibold text-[#e6eaf0]">
                      Synthesizer Policy Plan Compiled
                    </h2>
                  </div>
                  <div className="flex items-center gap-1.5 font-mono text-xs">
                    <span className="text-[#34d399] font-semibold">DONE</span>
                    <span className="text-[#859490]">·</span>
                    <span className="text-[#859490]">14:02:11</span>
                  </div>
                </div>
                <p className="text-xs text-[#8b95a3] mb-2 leading-relaxed">
                  CTGAN initialized with Laplace noise injection mechanism. Baseline parameters locked to deterministic seed.
                </p>
                <div className="flex items-center gap-2 font-mono text-xs bg-[#0a0c0f] px-2.5 py-1 rounded border border-[#232a33] inline-flex">
                  <span className="text-[#859490]">param:</span>
                  <span className="text-[#2dd4bf] font-medium">epsilon = 0.50</span>
                  <span className="text-[#859490]">|</span>
                  <span className="text-[#859490]">dist:</span>
                  <span className="text-[#e6eaf0]">Laplace(0, 1.414)</span>
                </div>
              </div>
            </div>

            {/* Stage 2: Generate Candidate #1 */}
            <div className="relative flex items-start gap-4">
              <div className="w-10 h-10 rounded bg-[#17202b] text-[#34d399] flex items-center justify-center shrink-0 border border-[#232a33] z-10">
                <span className="material-symbols-outlined text-lg">cyclone</span>
              </div>
              <div className="flex-1 bg-[#11151a] rounded-lg p-4 border border-[#232a33] hover:border-[#859490] transition-colors">
                <div className="flex flex-wrap items-center justify-between gap-1 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#17202b] text-[#8b95a3]">
                      02. Generate
                    </span>
                    <h2 className="text-sm font-semibold text-[#e6eaf0]">
                      Candidate #1 Generated
                    </h2>
                  </div>
                  <div className="flex items-center gap-1.5 font-mono text-xs">
                    <span className="text-[#34d399] font-semibold">DONE</span>
                    <span className="text-[#859490]">·</span>
                    <span className="text-[#859490]">14:02:45</span>
                  </div>
                </div>
                <p className="text-xs text-[#8b95a3] mb-2 leading-relaxed">
                  Synthetic batch compiled with 1,024 records across 14 clinical dimensions.
                </p>
                <div className="flex items-center gap-2 flex-wrap font-mono text-xs">
                  <span className="bg-[#0a0c0f] px-2 py-0.5 rounded border border-[#232a33] text-[#8b95a3]">
                    Batch Size: <span className="text-[#e6eaf0] font-semibold">1,024</span>
                  </span>
                  <span className="bg-[#0a0c0f] px-2 py-0.5 rounded border border-[#232a33] text-[#8b95a3]">
                    Digest: <span className="text-[#2dd4bf]">sha256:7bb2…e910</span>
                  </span>
                </div>
              </div>
            </div>

            {/* Stage 3: Checks Completed (FAIL / REPAIR NEEDED) */}
            <div className="relative flex items-start gap-4">
              <div className="w-10 h-10 rounded bg-[#11151a] text-[#f87171] border border-[#f87171] flex items-center justify-center shrink-0 z-10">
                <span className="material-symbols-outlined text-lg">gavel</span>
              </div>
              <div className="flex-1 bg-[#11151a] rounded-lg p-4 border border-[#f87171]/50">
                <div className="flex flex-wrap items-center justify-between gap-1 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#17202b] text-[#f87171] font-bold">
                      03. Checks
                    </span>
                    <h2 className="text-sm font-semibold text-[#e6eaf0]">
                      Candidate #1 Verification Checks Evaluated
                    </h2>
                  </div>
                  <div className="flex items-center gap-1.5 font-mono text-xs">
                    <span className="px-1.5 py-0.2 rounded bg-[#17202b] text-[#f87171] border border-[#f87171] font-bold uppercase text-[10px]">
                      FAIL / REPAIR
                    </span>
                    <span className="text-[#859490]">·</span>
                    <span className="text-[#859490]">14:03:10</span>
                  </div>
                </div>
                <p className="text-xs text-[#8b95a3] mb-2 leading-relaxed">
                  Subgroup utility CI width exceeded target 0.15 (observed: 0.340) on cohort{" "}
                  <code className="text-[#2dd4bf] font-mono">age &gt;= 65</code>. Automatic repair
                  triggered by policy invariant.
                </p>
                <div className="p-2.5 rounded bg-[#0a0c0f] border border-[#232a33] font-mono text-xs space-y-1">
                  <div className="flex justify-between text-[#859490]">
                    <span>Policy rule breached:</span>
                    <span className="text-[#f87171]">subgroup_utility_ci_width &lt;= 0.15</span>
                  </div>
                  <div className="flex justify-between text-[#859490]">
                    <span>Observed:</span>
                    <span className="text-[#f87171] font-bold">0.340 ± 0.035</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Stage 4: Policy Constrained Repair */}
            <div className="relative flex items-start gap-4">
              <div className="w-10 h-10 rounded bg-[#17202b] text-[#f59e0b] flex items-center justify-center shrink-0 border border-[#232a33] z-10">
                <span className="material-symbols-outlined text-lg">build</span>
              </div>
              <div className="flex-1 bg-[#11151a] rounded-lg p-4 border border-[#232a33] hover:border-[#859490] transition-colors">
                <div className="flex flex-wrap items-center justify-between gap-1 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#17202b] text-[#f59e0b]">
                      04. Repair
                    </span>
                    <h2 className="text-sm font-semibold text-[#e6eaf0]">
                      Policy Constrained Repair Applied
                    </h2>
                  </div>
                  <div className="flex items-center gap-1.5 font-mono text-xs">
                    <span className="text-[#34d399] font-semibold">DONE</span>
                    <span className="text-[#859490]">·</span>
                    <span className="text-[#859490]">14:03:35</span>
                  </div>
                </div>
                <p className="text-xs text-[#8b95a3] mb-2 leading-relaxed">
                  Resampling &amp; reweighting geriatric subgroup age &gt;= 65. Re-synthesizing
                  candidate with conditional prior constraints.
                </p>
                <div className="flex items-center gap-2 font-mono text-xs text-[#859490]">
                  <span className="text-[#e6eaf0]">Action:</span>
                  <span className="text-[#2dd4bf]">resample_subgroup</span>
                  <span>|</span>
                  <span className="text-[#e6eaf0]">Target Delta:</span>
                  <span className="text-[#34d399]">+136 records</span>
                </div>
              </div>
            </div>

            {/* Stage 5: Candidate #2 Generated & Evaluated */}
            <div className="relative flex items-start gap-4">
              <div className="w-10 h-10 rounded bg-[#17202b] text-[#34d399] flex items-center justify-center shrink-0 border border-[#232a33] z-10">
                <span className="material-symbols-outlined text-lg">check_circle</span>
              </div>
              <div className="flex-1 bg-[#11151a] rounded-lg p-4 border border-[#232a33] hover:border-[#859490] transition-colors">
                <div className="flex flex-wrap items-center justify-between gap-1 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#17202b] text-[#34d399]">
                      05. Candidate #2
                    </span>
                    <h2 className="text-sm font-semibold text-[#e6eaf0]">
                      Candidate #2 Evaluated
                    </h2>
                  </div>
                  <div className="flex items-center gap-1.5 font-mono text-xs">
                    <span className="text-[#34d399] font-semibold">CERTIFIED</span>
                    <span className="text-[#859490]">·</span>
                    <span className="text-[#859490]">14:04:02</span>
                  </div>
                </div>
                <p className="text-xs text-[#8b95a3] leading-relaxed">
                  Candidate #2 satisfies all software testing and prototyping gates. Clinical ML
                  bounded by sufficiency warning. Ready for evidence notary.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Telemetry & Envelope (4 Cols) */}
        <div className="lg:col-span-4 flex flex-col gap-5">
          {/* Budget & Envelope */}
          <div className="bg-[#11151a] rounded-lg p-5 border border-[#232a33] flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#232a33]">
              <span className="text-xs font-mono font-bold uppercase text-[#e6eaf0]">
                Budget &amp; Enclave Envelope
              </span>
              <span className="text-[10px] font-mono text-[#34d399] uppercase">Within Limits</span>
            </div>

            {/* Candidate Generations Meter */}
            <div className="space-y-1.5 font-mono text-xs">
              <div className="flex justify-between text-[#8b95a3]">
                <span>Candidates Evaluated</span>
                <span className="text-[#e6eaf0] font-bold">
                  {candidatesUsed} / {maxCandidates}
                </span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-[#0a0c0f] border border-[#232a33] overflow-hidden">
                <div
                  className="h-full bg-[#2dd4bf] transition-all"
                  style={{ width: `${candidatePct}%` }}
                />
              </div>
            </div>

            {/* Repairs Attempted Meter */}
            <div className="space-y-1.5 font-mono text-xs">
              <div className="flex justify-between text-[#8b95a3]">
                <span>Repair Cycles</span>
                <span className="text-[#e6eaf0] font-bold">
                  {repairsUsed} / {maxRepairs}
                </span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-[#0a0c0f] border border-[#232a33] overflow-hidden">
                <div
                  className="h-full bg-[#f59e0b] transition-all"
                  style={{ width: `${repairPct}%` }}
                />
              </div>
            </div>

            {/* Hardware Memory Envelope */}
            <div className="space-y-1.5 font-mono text-xs">
              <div className="flex justify-between text-[#8b95a3]">
                <span>Memory Enclave (Nitro)</span>
                <span className="text-[#e6eaf0] font-bold">1.4 GB / 4.0 GB</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-[#0a0c0f] border border-[#232a33] overflow-hidden">
                <div className="h-full bg-[#34d399] transition-all" style={{ width: "35%" }} />
              </div>
            </div>
          </div>

          {/* Real-Time Agent Events Stream */}
          <div className="bg-[#11151a] rounded-lg p-5 border border-[#232a33] flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#232a33]">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#2dd4bf] animate-ping" />
                <span className="text-xs font-mono font-bold uppercase text-[#e6eaf0]">
                  Live Telemetry Feed
                </span>
              </div>
              <span className="text-[10px] font-mono text-[#859490]">ZERO_LLM</span>
            </div>

            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1 font-mono text-xs">
              {events.length > 0 ? (
                events.map((ev, i) => (
                  <div
                    key={i}
                    className="p-2 rounded bg-[#0a0c0f] border border-[#232a33] text-[11px] space-y-0.5"
                  >
                    <div className="flex justify-between text-[#859490]">
                      <span className="text-[#2dd4bf] font-bold uppercase">{ev.type}</span>
                      <span>{ev.timestamp ? ev.timestamp.slice(11, 19) : "14:04:10"}</span>
                    </div>
                    <div className="text-[#8b95a3] truncate">
                      {JSON.stringify(ev.data).slice(0, 70)}
                    </div>
                  </div>
                ))
              ) : (
                [
                  { type: "PLAN_LOCK", time: "14:02:11", msg: "Policy parameters locked to seed 42891" },
                  { type: "BATCH_GEN", time: "14:02:45", msg: "Batch 1,024 records materialized" },
                  { type: "GATE_FAIL", time: "14:03:10", msg: "CI width threshold breached on age>=65" },
                  { type: "REPAIR_APPLY", time: "14:03:35", msg: "Reweighting priors for cohort balance" },
                  { type: "BATCH_GEN_2", time: "14:04:02", msg: "Candidate #2 generated with N=1,024" },
                  { type: "LEDGER_LOCK", time: "14:04:12", msg: "Merkle root anchored to notary" },
                ].map((ev, i) => (
                  <div
                    key={i}
                    className="p-2 rounded bg-[#0a0c0f] border border-[#232a33] text-[11px] space-y-0.5"
                  >
                    <div className="flex justify-between text-[#859490]">
                      <span className="text-[#2dd4bf] font-bold uppercase">{ev.type}</span>
                      <span>{ev.time}</span>
                    </div>
                    <div className="text-[#8b95a3] truncate">{ev.msg}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
