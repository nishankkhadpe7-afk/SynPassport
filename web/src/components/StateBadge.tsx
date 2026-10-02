"use client";

import React from "react";
import { VerdictState } from "@/types";

interface StateBadgeProps {
  state: VerdictState | string;
  size?: "sm" | "md" | "lg";
}

/* Verdicts render as passport stamps: a double-ruled chip in the verdict's ink.
   Colour is never the only signal — the word is always printed. */
const STATES: Record<string, { label: string; color: string; bg: string }> = {
  PASS: { label: "Pass", color: "var(--pass)", bg: "var(--pass-soft)" },
  WARNING: { label: "Warning", color: "var(--warn)", bg: "var(--warn-soft)" },
  FAIL: { label: "Fail", color: "var(--fail)", bg: "var(--fail-soft)" },
  INSUFFICIENT_EVIDENCE: { label: "Insufficient evidence", color: "var(--neutral)", bg: "var(--neutral-soft)" },
  INSUFFICIENT: { label: "Insufficient evidence", color: "var(--neutral)", bg: "var(--neutral-soft)" },
};

export const StateBadge: React.FC<StateBadgeProps> = ({ state, size = "md" }) => {
  const key = (state || "").toUpperCase();
  const spec = STATES[key] || {
    label: state ? state.charAt(0) + state.slice(1).toLowerCase() : "Unknown",
    color: "var(--ink-2)",
    bg: "var(--surface-2)",
  };

  const sizing = {
    sm: "text-sm px-2 py-0.5",
    md: "text-sm px-2.5 py-1",
    lg: "text-base px-3.5 py-1.5",
  }[size];

  return (
    <span
      className={`stamp ${sizing}`}
      style={{ color: spec.color, ["--stamp-bg" as string]: spec.bg } as React.CSSProperties}
    >
      {spec.label}
    </span>
  );
};
