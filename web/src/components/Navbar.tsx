"use client";

import React from "react";
import { SynPassportLogo } from "./SynPassportLogo";

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
  setIsReplay?: (val: boolean) => void;
  apiConnected: boolean;
  runId: string | null;
  runStatus: string | null;
  onToggleMobileMenu?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  isReplay,
  setIsReplay,
  apiConnected,
  runId,
  runStatus,
  onToggleMobileMenu,
}) => {
  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-[#0a0c0f] border-b border-[#232a33] z-50 px-4 sm:px-6 flex items-center justify-between">
      {/* Left: Brand & Badges */}
      <div className="flex items-center gap-3 sm:gap-4">
        {onToggleMobileMenu && (
          <button
            onClick={onToggleMobileMenu}
            className="lg:hidden p-1.5 rounded hover:bg-[#17202b] text-[#8b95a3] hover:text-[#e6eaf0] transition-colors"
            aria-label="Toggle Navigation Menu"
          >
            <span className="material-symbols-outlined text-xl">menu</span>
          </button>
        )}
        <div className="flex items-center gap-3">
          <SynPassportLogo size={36} />
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-base font-bold tracking-tight text-[#e6eaf0]">
                SynPassport
              </span>
              <span className="text-[10px] uppercase font-mono bg-[#17202b] px-1.5 py-0.5 rounded text-[#2dd4bf] border border-[#2dd4bf]/25 font-semibold">
                Cockpit v2.4
              </span>
            </div>
            <p className="text-[10px] font-mono text-[#8b95a3] tracking-wide uppercase hidden sm:block">
              SYNTHETIC_DATA_ATTESTATION
            </p>
          </div>
        </div>

        {/* Policy Digest Pill */}
        <div className="hidden xl:flex items-center gap-2 bg-[#17202b] px-2.5 py-1 rounded border border-[#232a33] text-xs font-mono text-[#8b95a3]">
          <span className="material-symbols-outlined text-xs text-[#2dd4bf]">lock</span>
          <span className="text-[#e6eaf0] font-medium">ml-sensitive-v1</span>
          <span className="text-[#859490]">·</span>
          <span className="text-[#2dd4bf]">sha256:9f3a…c1d2</span>
        </div>

        {/* Run ID Pill */}
        <div className="hidden 2xl:flex items-center gap-2 bg-[#17202b] px-2.5 py-1 rounded border border-[#232a33] text-xs font-mono">
          <span className="text-[#859490]">RUN:</span>
          <span className="text-[#e6eaf0] font-semibold truncate max-w-[130px]">
            {runId ? runId.slice(0, 16) : "RUN-202505-8842F"}
          </span>
          <span className="text-[#859490]">·</span>
          <span className="text-[#34d399] uppercase font-medium">
            {runStatus || "HEART_DISEASE_V4"}
          </span>
        </div>
      </div>

      {/* Right: Telemetry & Controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Zero-LLM Deterministic pill */}
        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded bg-[#11151a] border border-[#232a33] text-xs font-mono">
          <span className="w-2 h-2 rounded-full bg-[#34d399] animate-pulse" />
          <span className="text-[#8b95a3]">Zero-LLM Deterministic</span>
        </div>

        {/* Replay Mode Toggle */}
        <button
          type="button"
          onClick={() => setIsReplay && setIsReplay(!isReplay)}
          className="flex items-center gap-1.5 bg-[#17202b] hover:bg-[#212b36] px-2 sm:px-2.5 py-1 rounded border border-[#232a33] text-xs font-mono transition-colors"
          title="Toggle deterministic replay mode with cached runs"
        >
          <span className="text-[10px] uppercase text-[#859490] hidden sm:inline">
            Replay Mode
          </span>
          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
              isReplay
                ? "bg-[#34d399]/15 text-[#34d399] border-[#34d399]/40"
                : "bg-[#212b36] text-[#8b95a3] border-[#232a33]"
            }`}
          >
            {isReplay ? "ACTIVE" : "OFF"}
          </span>
        </button>

        <div className="h-5 w-px bg-[#232a33] hidden sm:block" />

        {/* API Status Pill */}
        <div
          className={`flex items-center gap-1.5 text-xs font-mono px-2 py-1 rounded border ${
            apiConnected
              ? "bg-[#34d399]/10 text-[#34d399] border-[#34d399]/30"
              : "bg-[#f87171]/10 text-[#f87171] border-[#f87171]/30"
          }`}
          title={apiConnected ? "Backend connected" : "Backend offline (Demo Mode Active)"}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              apiConnected ? "bg-[#34d399] animate-pulse" : "bg-[#f87171]"
            }`}
          />
          <span className="hidden md:inline font-semibold">
            {apiConnected ? "API CONNECTED" : "DEMO / OFFLINE"}
          </span>
        </div>

        <div className="h-5 w-px bg-[#232a33] hidden sm:block" />

        {/* HSM Vault Signature Key */}
        <div className="flex items-center gap-2">
          <div className="hidden sm:flex flex-col text-right">
            <span className="text-[10px] font-mono text-[#e6eaf0] font-semibold leading-tight">
              ED25519:ACTIVE
            </span>
            <span className="text-[9px] font-mono text-[#8b95a3] leading-tight">
              VAULT-SEC-01
            </span>
          </div>
          <div
            className="w-8 h-8 rounded bg-[#11151a] border border-[#232a33] flex items-center justify-center text-[#2dd4bf]"
            title="Cryptographic Hardware Security Module (HSM) Online"
          >
            <span className="material-symbols-outlined text-lg">shield_locked</span>
          </div>
        </div>
      </div>
    </header>
  );
};
