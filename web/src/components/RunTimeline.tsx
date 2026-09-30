"use client";

import React from "react";
import {
  Compass,
  Database,
  Search,
  Wrench,
  ShieldAlert,
  CheckCircle2,
  Clock,
  Cpu,
  BarChart,
  RefreshCw,
  AlertCircle,
  HelpCircle,
} from "lucide-react";
import { RunStatus, AgentEvent, BudgetUsed } from "@/types";
import { StateBadge } from "./StateBadge";

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
  isLoading,
  error,
}) => {
  const candidatesUsed = budgetUsed?.candidates_evaluated ?? runStatus?.candidates?.length ?? 0;
  const maxCandidates = budgetUsed?.max_candidates ?? 3;
  const repairsUsed = budgetUsed?.repairs_attempted ?? runStatus?.repairs?.length ?? 0;
  const maxRepairs = budgetUsed?.max_repairs ?? 2;

  const candidatePct = Math.min(100, Math.round((candidatesUsed / maxCandidates) * 100));
  const repairPct = Math.min(100, Math.round((repairsUsed / maxRepairs) * 100));

  const getEventIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "plan":
        return <Compass className="w-4 h-4 text-sky-400" />;
      case "candidate":
      case "generate":
        return <Database className="w-4 h-4 text-indigo-400" />;
      case "evaluate":
      case "checks":
      case "check":
        return <Search className="w-4 h-4 text-violet-400" />;
      case "repair":
        return <Wrench className="w-4 h-4 text-amber-400" />;
      case "rejection":
      case "agent_rejection":
        return <ShieldAlert className="w-4 h-4 text-rose-400" />;
      case "finalize":
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getEventBadgeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "plan":
        return "bg-sky-500/10 text-sky-400 border-sky-500/30";
      case "candidate":
      case "generate":
        return "bg-indigo-500/10 text-indigo-400 border-indigo-500/30";
      case "evaluate":
      case "checks":
      case "check":
        return "bg-violet-500/10 text-violet-400 border-violet-500/30";
      case "repair":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "rejection":
      case "agent_rejection":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      case "finalize":
      case "completed":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      default:
        return "bg-slate-800 text-slate-400 border-slate-700";
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header and Live Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold tracking-tight text-white">Agent Execution Timeline</h2>
            {runStatus?.status === "RUNNING" && (
              <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 text-xs font-mono">
                <RefreshCw className="w-3 h-3 animate-spin" />
                STREAMING SSE
              </span>
            )}
          </div>
          <p className="text-slate-400 text-xs font-mono mt-0.5">
            Run ID: <span className="text-slate-200">{runId}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right text-xs">
            <span className="text-slate-500 uppercase tracking-wider block font-mono">Status</span>
            <span className="font-semibold text-slate-200 uppercase font-mono">
              {runStatus?.status || "INITIALIZING"}
            </span>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {(error || runStatus?.error) && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start gap-3 text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" />
          <div>
            <div className="font-semibold">Pipeline Execution Alert</div>
            <div className="text-xs font-mono mt-1 text-rose-200">{error || runStatus?.error}</div>
          </div>
        </div>
      )}

      {/* Budget Meters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Candidates Meter */}
        <div className="glass-panel p-5 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 flex items-center gap-1.5 font-medium">
              <Cpu className="w-4 h-4 text-indigo-400" />
              Candidate Generation Budget
            </span>
            <span className="font-mono font-bold text-slate-200">
              {candidatesUsed} / {maxCandidates} used
            </span>
          </div>
          <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                candidatePct >= 100 ? "bg-amber-500" : "bg-indigo-500"
              }`}
              style={{ width: `${candidatePct}%` }}
            />
          </div>
          <div className="flex justify-between text-[11px] text-slate-500">
            <span>Enforced by policy engine in code</span>
            <span className={candidatesUsed >= maxCandidates ? "text-amber-400 font-medium" : ""}>
              {candidatesUsed >= maxCandidates ? "Budget Exhausted" : "Budget Available"}
            </span>
          </div>
        </div>

        {/* Repairs Meter */}
        <div className="glass-panel p-5 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 flex items-center gap-1.5 font-medium">
              <Wrench className="w-4 h-4 text-amber-400" />
              Repair Budget (Whitelist Only)
            </span>
            <span className="font-mono font-bold text-slate-200">
              {repairsUsed} / {maxRepairs} used
            </span>
          </div>
          <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                repairPct >= 100 ? "bg-rose-500" : "bg-amber-500"
              }`}
              style={{ width: `${repairPct}%` }}
            />
          </div>
          <div className="flex justify-between text-[11px] text-slate-500">
            <span>Permitted: tune_params, switch_gen, enable_dp</span>
            <span className={repairsUsed >= maxRepairs ? "text-rose-400 font-medium" : ""}>
              {repairsUsed >= maxRepairs ? "Repairs Capped" : "Repairs Remaining"}
            </span>
          </div>
        </div>
      </div>

      {/* Agent Rejections Section (if any) */}
      {runStatus?.agent_rejections && runStatus.agent_rejections.length > 0 && (
        <div className="glass-panel p-4 rounded-xl border border-rose-500/25 bg-rose-950/20 space-y-2">
          <div className="flex items-center gap-2 text-rose-400 text-xs font-semibold uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4" />
            <span>Agent Whitelist Enforcements ({runStatus.agent_rejections.length} Action Rejected)</span>
          </div>
          <div className="space-y-2">
            {runStatus.agent_rejections.map((rej, idx) => (
              <div
                key={idx}
                className="text-xs bg-slate-950/60 p-2.5 rounded-lg border border-rose-900/40 text-slate-300 font-mono flex flex-col gap-1"
              >
                <div className="flex items-center justify-between text-rose-300">
                  <span className="font-semibold">Rejected Action: {rej.proposal}</span>
                  <span className="text-[10px] text-rose-400 font-bold uppercase">POLICY HARD RULE</span>
                </div>
                <div className="text-slate-400">{rej.reason}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Timeline Stream */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <BarChart className="w-4 h-4 text-indigo-400" />
          Event Sequence
        </h3>

        {events.length === 0 && !isLoading && (
          <div className="py-12 text-center text-slate-500 text-xs font-mono flex flex-col items-center justify-center gap-2">
            <HelpCircle className="w-8 h-8 text-slate-600" />
            <span>Awaiting agent execution dispatch...</span>
          </div>
        )}

        <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
          {events.map((ev, index) => {
            const dateStr = ev.timestamp
              ? new Date(ev.timestamp).toLocaleTimeString()
              : `Step ${index + 1}`;

            return (
              <div key={index} className="relative group">
                {/* Timeline Node Icon */}
                <div className="absolute -left-[27px] top-1.5 w-6 h-6 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center shadow">
                  {getEventIcon(ev.type)}
                </div>

                {/* Event Card */}
                <div className="bg-slate-900/60 hover:bg-slate-900/90 border border-slate-800/80 rounded-xl p-4 transition-all space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={`text-[11px] font-mono uppercase px-2 py-0.5 rounded-md border font-semibold ${getEventBadgeColor(
                          ev.type
                        )}`}
                      >
                        {ev.type}
                      </span>
                      {Boolean(ev.data?.candidate_id) && (
                        <span className="text-xs font-mono text-indigo-300 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/50">
                          {String(ev.data.candidate_id)}
                        </span>
                      )}
                      {Boolean(ev.data?.generator) && (
                        <span className="text-xs font-mono text-slate-400">
                          generator: <span className="text-slate-200">{String(ev.data.generator)}</span>
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] text-slate-500 font-mono">{dateStr}</span>
                  </div>

                  {/* Message / Description */}
                  {Boolean(ev.data?.message || ev.data?.plan || ev.data?.diagnosis) && (
                    <p className="text-xs text-slate-300 leading-relaxed font-sans">
                      {String(ev.data.message || ev.data.plan || ev.data.diagnosis)}
                    </p>
                  )}

                  {/* Check Results Breakdown if evaluate event */}
                  {Boolean(ev.data?.verdicts && typeof ev.data.verdicts === "object") && (
                    <div className="pt-2 border-t border-slate-800/60 flex flex-wrap gap-2">
                      {Object.entries(ev.data.verdicts as Record<string, string>).map(
                        ([use, state]) => (
                          <div
                            key={use}
                            className="flex items-center gap-1.5 bg-slate-950/60 px-2.5 py-1 rounded-lg border border-slate-800 text-xs"
                          >
                            <span className="font-mono text-slate-400">{use}:</span>
                            <StateBadge state={state} size="sm" />
                          </div>
                        )
                      )}
                    </div>
                  )}

                  {/* Repair Action Details */}
                  {Boolean(ev.data?.action) && (
                    <div className="text-xs font-mono bg-slate-950/50 p-2 rounded border border-slate-800/80 text-amber-300/90">
                      Applied Repair: <span className="text-white font-bold">{String(ev.data.action)}</span>
                      {Boolean(ev.data.params) && (
                        <span className="text-slate-400 block mt-0.5 text-[11px]">
                          {JSON.stringify(ev.data.params)}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
