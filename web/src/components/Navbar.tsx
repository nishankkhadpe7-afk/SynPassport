"use client";

import React, { useEffect, useState } from "react";
import { cx } from "./ui";

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

// The tabs follow the order of the assurance workflow, so they are numbered.
const NAV_ITEMS: Array<{ id: DashboardTab; label: string; requiresRun?: boolean }> = [
  { id: "setup", label: "Setup" },
  { id: "timeline", label: "Agent timeline", requiresRun: true },
  { id: "verdicts", label: "Verdicts", requiresRun: true },
  { id: "evidence", label: "Evidence", requiresRun: true },
  { id: "sufficiency", label: "Sufficiency", requiresRun: true },
  { id: "passport", label: "Passport", requiresRun: true },
  { id: "tamper", label: "Tamper test" },
];

const STATUS_TEXT: Record<string, string> = {
  QUEUED: "Queued",
  RUNNING: "Running",
  COMPLETED: "Completed",
  FAILED: "Failed",
};

const STATUS_TONE: Record<string, string> = {
  RUNNING: "text-accent",
  COMPLETED: "text-pass",
  FAILED: "text-fail",
};

function useTheme(): [string, () => void] {
  const [theme, setTheme] = useState<string>("light");

  useEffect(() => {
    const attr = document.documentElement.getAttribute("data-theme");
    if (attr === "dark" || attr === "light") {
      setTheme(attr);
    } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      setTheme("dark");
    }
  }, []);

  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("synpassport-theme", next);
    } catch {
      // storage unavailable: theme still applies for this session
    }
  };

  return [theme, toggle];
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  isReplay,
  apiConnected,
  runId,
  runStatus,
}) => {
  const [theme, toggleTheme] = useTheme();

  return (
    <header className="sticky top-0 z-40 bg-bg border-b border-line">
      <div className="max-w-page mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between gap-4 h-16">
          <div className="flex items-baseline gap-3 min-w-0">
            <span className="font-display text-[24px] leading-none font-medium tracking-[-0.015em] text-ink">
              SynPassport
            </span>
            <span className="hidden sm:inline text-sm text-ink-3 truncate">Purpose-bound assurance for synthetic data</span>
          </div>

          <div className="flex items-center gap-4 text-sm">
            {isReplay && (
              <span
                className="hidden sm:inline text-ink-2"
                title="The API is replaying cached runs instead of calling the model"
              >
                Replay mode
              </span>
            )}

            {runId && (
              <span className="hidden md:inline-flex items-center gap-2 text-ink-2">
                <span className="font-mono text-ink">{runId.slice(0, 16)}</span>
                {runStatus && (
                  <span className={cx("font-medium", STATUS_TONE[runStatus] || "text-ink-2")}>
                    {STATUS_TEXT[runStatus] || runStatus}
                  </span>
                )}
              </span>
            )}

            <span className="inline-flex items-center gap-2 text-ink-2" role="status">
              <span
                aria-hidden="true"
                className={cx("w-2 h-2 rounded-full", apiConnected ? "bg-pass" : "bg-fail")}
              />
              <span className="hidden sm:inline">{apiConnected ? "API connected" : "API offline"}</span>
              <span className="sm:hidden sr-only">{apiConnected ? "API connected" : "API offline"}</span>
            </span>

            <button
              type="button"
              onClick={toggleTheme}
              className="h-8 px-3 rounded text-ink-2 hover:text-ink hover:bg-surface-2 transition-colors"
              aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
            >
              {theme === "dark" ? "Light" : "Dark"}
            </button>
          </div>
        </div>

        <nav aria-label="Assurance workflow" className="-mb-px overflow-x-auto">
          <ol className="flex gap-1 min-w-max">
            {NAV_ITEMS.map((item, index) => {
              const isActive = activeTab === item.id;
              const disabled = Boolean(item.requiresRun && !runId);
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => !disabled && setActiveTab(item.id)}
                    disabled={disabled}
                    aria-current={isActive ? "page" : undefined}
                    title={disabled ? "Start a run first" : undefined}
                    className={cx(
                      "flex items-center gap-2 h-11 px-3 border-b-2 text-sm transition-colors duration-200 ease-out",
                      isActive
                        ? "border-accent text-ink font-medium"
                        : disabled
                        ? "border-transparent text-ink-3 opacity-60 cursor-not-allowed"
                        : "border-transparent text-ink-2 hover:text-ink hover:border-line-strong"
                    )}
                  >
                    <span className={cx("tabular-nums", isActive ? "text-accent" : "text-ink-3")}>{index + 1}</span>
                    <span>{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ol>
        </nav>
      </div>
    </header>
  );
};
