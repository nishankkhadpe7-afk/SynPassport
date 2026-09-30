"use client";

import React from "react";
import {
  Shield,
  Activity,
  Layers,
  BarChart3,
  Users,
  FileCheck2,
  AlertOctagon,
  Sparkles,
} from "lucide-react";

export type DashboardTab =
  | "setup"
  | "timeline"
  | "verdicts"
  | "evidence"
  | "sufficiency"
  | "passport"
  | "tamper";

interface NavbarProps {
  activeTab: DashboardTab;
  setActiveTab: (tab: DashboardTab) => void;
  isReplay: boolean;
  apiConnected: boolean;
  runId: string | null;
  runStatus: string | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  isReplay,
  apiConnected,
  runId,
  runStatus,
}) => {
  const navItems: Array<{ id: DashboardTab; label: string; icon: React.ReactNode; requiresRun?: boolean }> = [
    { id: "setup", label: "1. Setup", icon: <Layers className="w-3.5 h-3.5" /> },
    { id: "timeline", label: "2. Agent Timeline", icon: <Activity className="w-3.5 h-3.5" />, requiresRun: true },
    { id: "verdicts", label: "3. Verdict Board", icon: <FileCheck2 className="w-3.5 h-3.5" />, requiresRun: true },
    { id: "evidence", label: "4. Evidence Drill-Down", icon: <BarChart3 className="w-3.5 h-3.5" />, requiresRun: true },
    { id: "sufficiency", label: "5. Sufficiency", icon: <Users className="w-3.5 h-3.5" />, requiresRun: true },
    { id: "passport", label: "6. Evidence Passport", icon: <Shield className="w-3.5 h-3.5" />, requiresRun: true },
    { id: "tamper", label: "7. Tamper Demo", icon: <AlertOctagon className="w-3.5 h-3.5" /> },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-md shadow-indigo-500/20 text-white">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-bold tracking-tight text-white">SynPassport</span>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/60">
                  v0.1.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Purpose-Bound Assurance &amp; Evidence Passports
              </p>
            </div>
          </div>

          {/* Right Status Indicators */}
          <div className="flex items-center gap-3">
            {/* Replay Mode Indicator */}
            {isReplay && (
              <div
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium animate-pulse"
                title="Backend is operating in deterministic replay mode with cached runs"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>Replay Mode Active</span>
              </div>
            )}

            {/* Run ID Pill */}
            {runId && (
              <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
                <span className="text-slate-500">RUN:</span>
                <span className="text-indigo-400 font-semibold">{runId.slice(0, 14)}</span>
                {runStatus && (
                  <span
                    className={`px-1.5 py-0.2 rounded text-[10px] uppercase font-bold ${
                      runStatus === "COMPLETED"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : runStatus === "RUNNING"
                        ? "bg-indigo-500/20 text-indigo-400"
                        : runStatus === "FAILED"
                        ? "bg-rose-500/20 text-rose-400"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {runStatus}
                  </span>
                )}
              </div>
            )}

            {/* API Connection Indicator */}
            <div
              className={`flex items-center gap-1.5 text-xs font-mono px-2 py-1 rounded-md border ${
                apiConnected
                  ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                  : "bg-rose-500/10 border-rose-500/20 text-rose-400"
              }`}
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  apiConnected ? "bg-emerald-400 animate-pulse" : "bg-rose-500"
                }`}
              />
              <span className="hidden sm:inline">
                {apiConnected ? "API Connected" : "API Offline"}
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs Bar */}
        <div className="flex overflow-x-auto space-x-1 py-2 scrollbar-none border-t border-slate-900">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            const disabled = item.requiresRun && !runId;

            return (
              <button
                key={item.id}
                onClick={() => !disabled && setActiveTab(item.id)}
                disabled={disabled}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                    : disabled
                    ? "text-slate-600 cursor-not-allowed opacity-50"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/80"
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
