"use client";

import React from "react";
import { DashboardTab } from "./Navbar";

interface SidebarStepperProps {
  activeTab: DashboardTab;
  setActiveTab: (tab: DashboardTab) => void;
  runId: string | null;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
}

interface StepItem {
  id: DashboardTab;
  stepNum: string;
  title: string;
  subtitle: string;
  statusBadge: string;
  badgeColorClass: string;
  icon: string;
}

export const SidebarStepper: React.FC<SidebarStepperProps> = ({
  activeTab,
  setActiveTab,
  isOpenMobile = false,
  onCloseMobile,
}) => {
  const steps: StepItem[] = [
    {
      id: "setup",
      stepNum: "01",
      title: "Mission Setup",
      subtitle: "Topology & Schemas",
      statusBadge: "PASS",
      badgeColorClass: "text-[#34d399]",
      icon: "check",
    },
    {
      id: "timeline",
      stepNum: "02",
      title: "Run View",
      subtitle: "Synthetic Ingestion",
      statusBadge: "LIVE",
      badgeColorClass: "text-[#34d399]",
      icon: "timeline",
    },
    {
      id: "verdicts",
      stepNum: "03",
      title: "Verdicts",
      subtitle: "Policy Bounds Audit",
      statusBadge: "FOCUS",
      badgeColorClass: "text-[#2dd4bf]",
      icon: "rule",
    },
    {
      id: "evidence",
      stepNum: "04",
      title: "Evidence",
      subtitle: "Merkle Tree Leafs",
      statusBadge: "ACTIVE",
      badgeColorClass: "text-[#57f1db]",
      icon: "data_object",
    },
    {
      id: "sufficiency",
      stepNum: "05",
      title: "Sufficiency",
      subtitle: "Sample Diversity Delta",
      statusBadge: "WARN",
      badgeColorClass: "text-[#f87171]",
      icon: "warning",
    },
    {
      id: "passport",
      stepNum: "06",
      title: "Passport",
      subtitle: "Final Attestation Seal",
      statusBadge: "SEAL",
      badgeColorClass: "text-[#859490]",
      icon: "key",
    },
    {
      id: "tamper",
      stepNum: "07",
      title: "Tamper Demo",
      subtitle: "Adversarial Injector",
      statusBadge: "SIM",
      badgeColorClass: "text-[#859490]",
      icon: "terminal",
    },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 bg-[#0a0c0f]/80 z-30 lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed left-0 top-16 bottom-0 w-72 bg-[#050f19] border-r border-[#232a33] z-40 flex flex-col justify-between overflow-y-auto transition-transform duration-200 ease-in-out ${
          isOpenMobile ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="p-4">
          {/* Header */}
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#232a33]">
            <span className="text-[10px] uppercase font-mono text-[#859490] tracking-wider font-semibold">
              Notarization Stepper
            </span>
            <span className="text-xs font-mono text-[#2dd4bf] font-medium">7 STAGES</span>
          </div>

          {/* Stepper Navigation */}
          <nav className="space-y-1">
            {steps.map((step, idx) => {
              const isActive = activeTab === step.id;
              const isLast = idx === steps.length - 1;

              return (
                <button
                  key={step.id}
                  onClick={() => {
                    setActiveTab(step.id);
                    if (onCloseMobile) onCloseMobile();
                  }}
                  className={`w-full group flex items-start gap-3 p-2.5 rounded-r border-l-2 transition-all text-left ${
                    isActive
                      ? "bg-[#17202b] border-[#2dd4bf] text-[#e6eaf0] font-semibold"
                      : "border-transparent text-[#8b95a3] hover:bg-[#11151a] hover:text-[#e6eaf0]"
                  }`}
                >
                  {/* Step Connector Indicator */}
                  <div className="flex flex-col items-center mt-0.5">
                    <div
                      className={`w-4 h-4 rounded-full flex items-center justify-center ${
                        isActive
                          ? "border-2 border-[#2dd4bf] bg-[#11151a]"
                          : "bg-[#11151a] border border-[#232a33] group-hover:border-[#859490]"
                      }`}
                    >
                      {isActive ? (
                        <div className="w-1.5 h-1.5 rounded-full bg-[#2dd4bf]" />
                      ) : (
                        <span className="material-symbols-outlined text-[10px] text-[#859490]">
                          {step.icon}
                        </span>
                      )}
                    </div>
                    {!isLast && <div className="w-px h-6 bg-[#232a33] my-1" />}
                  </div>

                  {/* Step Titles & Badge */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-sans truncate font-medium">
                        {step.stepNum}. {step.title}
                      </span>
                      <span className={`text-[10px] font-mono font-bold ${step.badgeColorClass}`}>
                        {step.statusBadge}
                      </span>
                    </div>
                    <p className="text-[11px] font-mono text-[#859490] truncate">
                      {step.subtitle}
                    </p>
                  </div>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Crypto Engine Status Card */}
        <div className="p-3 m-3 bg-[#11151a] rounded border border-[#232a33] font-mono text-xs">
          <div className="flex items-center justify-between text-[#859490] mb-1.5">
            <span className="text-[10px] uppercase font-bold tracking-wider">CRYPTO ENGINE</span>
            <span className="text-[#34d399] font-semibold text-[10px]">READY</span>
          </div>
          <div className="text-[#8b95a3] truncate text-[11px]">ALG: ED25519-SHA512</div>
          <div className="text-[#8b95a3] truncate text-[11px]">KEY: 0x8842...32FA</div>
        </div>
      </aside>
    </>
  );
};
