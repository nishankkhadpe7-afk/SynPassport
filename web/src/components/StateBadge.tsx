"use client";

import React from "react";
import { VerdictState } from "@/types";

interface StateBadgeProps {
  state: VerdictState | string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const StateBadge: React.FC<StateBadgeProps> = ({
  state,
  size = "md",
  className = "",
}) => {
  const normState = (state || "").toUpperCase();

  const sizeClasses = {
    sm: "px-1.5 py-0.5 text-[10px] gap-1 leading-none font-mono",
    md: "px-2.5 py-1 text-xs gap-1.5 leading-none font-mono font-medium",
    lg: "px-3 py-1.5 text-xs gap-2 leading-none font-mono font-semibold",
  }[size];

  switch (normState) {
    case "PASS":
      return (
        <span
          className={`inline-flex items-center rounded bg-[#11151a] text-[#34d399] border border-[#34d399] ${sizeClasses} ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#34d399]" />
          <span>PASS</span>
        </span>
      );
    case "WARNING":
    case "WARN":
      return (
        <span
          className={`inline-flex items-center rounded bg-[#11151a] text-[#f59e0b] border border-[#f59e0b] ${sizeClasses} ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#f59e0b]" />
          <span>WARNING</span>
        </span>
      );
    case "FAIL":
    case "FAILED":
      return (
        <span
          className={`inline-flex items-center rounded bg-[#11151a] text-[#f87171] border border-[#f87171] ${sizeClasses} ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#f87171]" />
          <span>FAIL</span>
        </span>
      );
    case "INSUFFICIENT_EVIDENCE":
    case "INSUFFICIENT":
      return (
        <span
          className={`inline-flex items-center rounded bg-[#11151a] text-[#7ba7d9] border border-dashed border-[#7ba7d9] ${sizeClasses} ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#7ba7d9]" />
          <span>INSUFFICIENT</span>
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center rounded bg-[#11151a] text-[#8b95a3] border border-[#232a33] ${sizeClasses} ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#8b95a3]" />
          <span>{normState || "UNKNOWN"}</span>
        </span>
      );
  }
};
