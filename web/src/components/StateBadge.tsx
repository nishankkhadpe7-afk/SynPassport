"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle } from "lucide-react";
import { VerdictState } from "@/types";

interface StateBadgeProps {
  state: VerdictState | string;
  size?: "sm" | "md" | "lg";
}

export const StateBadge: React.FC<StateBadgeProps> = ({ state, size = "md" }) => {
  const normState = (state || "").toUpperCase();

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs gap-1",
    md: "px-3 py-1 text-xs font-medium gap-1.5",
    lg: "px-4 py-1.5 text-sm font-semibold gap-2",
  }[size];

  const iconSizes = {
    sm: "w-3 h-3",
    md: "w-3.5 h-3.5",
    lg: "w-4 h-4",
  }[size];

  switch (normState) {
    case "PASS":
      return (
        <span
          className={`inline-flex items-center rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 ${sizeClasses}`}
        >
          <CheckCircle2 className={`${iconSizes} text-emerald-400 shrink-0`} />
          <span>PASS</span>
        </span>
      );
    case "WARNING":
      return (
        <span
          className={`inline-flex items-center rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30 ${sizeClasses}`}
        >
          <AlertTriangle className={`${iconSizes} text-amber-400 shrink-0`} />
          <span>WARNING</span>
        </span>
      );
    case "FAIL":
      return (
        <span
          className={`inline-flex items-center rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/30 ${sizeClasses}`}
        >
          <XCircle className={`${iconSizes} text-rose-400 shrink-0`} />
          <span>FAIL</span>
        </span>
      );
    case "INSUFFICIENT_EVIDENCE":
    case "INSUFFICIENT":
      return (
        <span
          className={`inline-flex items-center rounded-full bg-slate-500/20 text-slate-300 border border-slate-500/40 ${sizeClasses}`}
        >
          <HelpCircle className={`${iconSizes} text-slate-400 shrink-0`} />
          <span>INSUFFICIENT EVIDENCE</span>
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center rounded-full bg-slate-800 text-slate-400 border border-slate-700 ${sizeClasses}`}
        >
          <HelpCircle className={`${iconSizes} text-slate-400 shrink-0`} />
          <span>{state || "UNKNOWN"}</span>
        </span>
      );
  }
};
