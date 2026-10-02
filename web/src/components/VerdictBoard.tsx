"use client";

import React from "react";
import { EvidenceItem, VerdictState } from "@/types";
import { StateBadge } from "./StateBadge";
import { EmptyState, PageHeader, SkeletonBlock, cx } from "./ui";

interface VerdictBoardProps {
  verdicts: Record<string, VerdictState>;
  isLoading?: boolean;
  /** Evidence of the signed candidate, with each check's state from the policy engine. */
  evidence?: EvidenceItem[];
  /** The policy's use -> required checks map ("all" means every required check). */
  policyUses?: Record<string, string[]> | null;
}

const CHECK_LABELS: Record<string, string> = {
  schema_validity: "Schema validity",
  identifier_leakage: "Identifier leakage",
  marginal_fidelity: "Marginal fidelity",
  correlation_fidelity: "Correlation fidelity",
  utility_tstr_ratio: "Utility (TSTR)",
  subgroup_utility_ci_width: "Subgroup CI width",
  subgroup_utility_ci: "Subgroup utility",
  privacy_dcr_vs_holdout: "Distance to closest record",
  membership_inference_auc: "Membership inference",
  sufficiency: "Subgroup sample size",
};

const STATE_WORD: Record<string, string> = {
  PASS: "Pass",
  WARNING: "Warning",
  FAIL: "Fail",
  INSUFFICIENT_EVIDENCE: "Insufficient evidence",
};

const SEVERITY: Record<string, number> = { FAIL: 3, INSUFFICIENT_EVIDENCE: 2, WARNING: 1, PASS: 0 };

const CHIP_TONE: Record<string, string> = {
  PASS: "text-pass",
  WARNING: "text-warn",
  FAIL: "text-fail",
  INSUFFICIENT_EVIDENCE: "text-ink-2",
};

const USE_LABELS: Record<string, string> = {
  software_testing: "Software testing",
  ml_prototyping: "ML prototyping",
  clinical_ml: "Clinical ML",
  exploratory_analytics: "Exploratory analytics",
};

const DECISION: Record<VerdictState, string> = {
  PASS: "Cleared for this use",
  WARNING: "Usable with caution",
  FAIL: "Blocked for this use",
  INSUFFICIENT_EVIDENCE: "Not enough evidence yet",
};

export const VerdictBoard: React.FC<VerdictBoardProps> = ({
  verdicts,
  isLoading = false,
  evidence = [],
  policyUses = null,
}) => {
  const intendedUses = Object.keys(verdicts);
  const stateOf = (check: string): string =>
    (evidence.find((e) => e.check_id === check)?.state || "INSUFFICIENT_EVIDENCE").toUpperCase();

  return (
    <div className="space-y-8">
      <PageHeader
        title="Verdicts"
        description="One verdict per intended use, decided by the policy engine, never by the agent. Passing software testing does not authorize clinical ML."
        meta={<span className="text-sm text-ink-2 tabular-nums">{intendedUses.length} {intendedUses.length === 1 ? "use" : "uses"}</span>}
      />

      {isLoading ? (
        <div className="grid gap-6 md:grid-cols-2">
          {[0, 1].map((i) => (
            <div key={i} className="bg-surface border border-line rounded-lg p-6">
              <SkeletonBlock lines={4} label="Evaluating verdicts" />
            </div>
          ))}
        </div>
      ) : intendedUses.length === 0 ? (
        <EmptyState title="No verdicts yet" description="Start a run from Setup to see a verdict for each intended use." />
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {intendedUses.map((use) => {
            const state: VerdictState = verdicts[use] || "INSUFFICIENT_EVIDENCE";
            const listed = policyUses?.[use] ?? [];
            const requiredChecks = listed.includes("all") ? evidence.map((e) => e.check_id) : listed;
            const blocking = requiredChecks
              .filter((c) => stateOf(c) !== "PASS")
              .sort((x, y) => (SEVERITY[stateOf(y)] ?? 0) - (SEVERITY[stateOf(x)] ?? 0));
            const explanation =
              requiredChecks.length === 0
                ? "Loading the checks this use requires…"
                : blocking.length === 0
                  ? `All ${requiredChecks.length} required checks passed on the signed candidate.`
                  : `Held back by ${blocking
                      .map((c) => `${CHECK_LABELS[c] || c} (${STATE_WORD[stateOf(c)] || stateOf(c)})`)
                      .join(", ")}. See Evidence for the measured values.`;

            return (
              <article
                key={use}
                className="bg-surface border border-line rounded-lg shadow p-6 flex flex-col gap-5"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1 min-w-0">
                    <h2 className="text-lg font-semibold text-ink">{USE_LABELS[use] || use}</h2>
                    <p className="font-mono text-sm text-ink-3">{use}</p>
                  </div>
                  <StateBadge state={state} size="lg" />
                </div>

                <div className="space-y-1">
                  <p className="text-base font-medium text-ink">{DECISION[state]}</p>
                  <p className="text-sm text-ink-2">{explanation}</p>
                </div>

                <div className="mt-auto pt-4 border-t border-line space-y-2">
                  <p className="text-sm text-ink-2">
                    {requiredChecks.length} required {requiredChecks.length === 1 ? "check" : "checks"}
                  </p>
                  <ul className="flex flex-wrap gap-2">
                    {requiredChecks.map((check) => (
                      <li
                        key={check}
                        className={cx("rounded-sm bg-surface-2 px-2 py-0.5 font-mono text-sm", CHIP_TONE[stateOf(check)])}
                        title={STATE_WORD[stateOf(check)]}
                      >
                        {check}
                      </li>
                    ))}
                  </ul>
                </div>
              </article>
            );
          })}
        </div>
      )}

      <p className="text-sm text-ink-2 max-w-prose">
        Consumers check purpose compatibility when they load the data, so a dataset approved for one use cannot quietly be used for another.
      </p>
    </div>
  );
};
