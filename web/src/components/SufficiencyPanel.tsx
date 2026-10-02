"use client";

import React from "react";
import { SufficiencyResponse } from "@/types";
import { StateBadge } from "./StateBadge";
import { Card, Meter, PageHeader, SkeletonBlock, Stat } from "./ui";

interface SufficiencyPanelProps {
  sufficiency: SufficiencyResponse | null;
  isLoading?: boolean;
}

export const SufficiencyPanel: React.FC<SufficiencyPanelProps> = ({
  sufficiency,
  isLoading = false,
}) => {
  const currentN = sufficiency?.current_n ?? 35;
  const requiredMinN = sufficiency?.required_min_n ?? 171;
  const ciWidth = sufficiency?.ci_width ?? 0.32;
  const targetWidth = 0.15;
  const subgroups = sufficiency?.subgroups ?? [
    {
      subgroup_query: "age >= 65",
      current_n: 35,
      required_min_n: 171,
      projected_ci_width: 0.32,
      target_ci_width: 0.15,
      state: "INSUFFICIENT_EVIDENCE",
      reason:
        "Subgroup 'age >= 65' has N=35 < required 171 for target CI width 0.15 (projected: 0.320).",
    },
  ];

  const primarySubgroup = subgroups[0];
  const deficit = Math.max(0, requiredMinN - currentN);
  const progressPct = Math.min(100, Math.round((currentN / requiredMinN) * 100));

  const enough = deficit === 0;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Sufficiency"
        description="Whether each critical subgroup has enough real records to support a confident verdict. When it does not, SynPassport refuses and says exactly what is missing."
      />

      {isLoading ? (
        <Card>
          <SkeletonBlock lines={5} label="Computing subgroup sample sizes" />
        </Card>
      ) : (
        <>
          <Card>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="space-y-2 max-w-prose">
                <p className="text-sm text-ink-2">
                  Subgroup <span className="font-mono text-ink">{primarySubgroup?.subgroup_query || "age >= 65"}</span>
                </p>
                <p className="text-xl font-semibold tracking-tight text-ink">
                  {enough ? (
                    <>Enough records for a confident verdict</>
                  ) : (
                    <>
                      Collect <span className="tabular-nums">{deficit}</span> more records aged 65+
                    </>
                  )}
                </p>
                <p className="text-base text-ink-2">
                  Need at least <span className="tabular-nums text-ink">{requiredMinN}</span>; this dataset has{" "}
                  <span className="tabular-nums text-ink">{currentN}</span>.
                </p>
              </div>
              <StateBadge state={primarySubgroup?.state || "INSUFFICIENT_EVIDENCE"} size="lg" />
            </div>

            <div className="mt-6 space-y-2">
              <Meter value={currentN} max={requiredMinN} tone={enough ? "pass" : "warn"} label="Records collected toward the minimum" />
              <div className="flex justify-between text-sm text-ink-3 tabular-nums">
                <span>{currentN} collected</span>
                <span>{progressPct}% of the minimum</span>
                <span>{requiredMinN} needed</span>
              </div>
            </div>

            <div className="mt-6 grid gap-6 border-t border-line pt-6 sm:grid-cols-2">
              <Stat
                label="Projected 95% CI width"
                value={<>&plusmn;{ciWidth.toFixed(3)}</>}
                tone={ciWidth > targetWidth ? "text-warn" : "text-pass"}
                note={
                  enough
                    ? `With n = ${currentN}, estimates for this group are precise enough.`
                    : `With n = ${currentN}, estimates for this group are too uncertain to trust.`
                }
              />
              <Stat
                label="Width the policy allows"
                value={<>&le;{targetWidth.toFixed(3)}</>}
                note={`Required for clinical ML release; reached at n \u2265 ${requiredMinN}.`}
              />
            </div>

            <p className="mt-6 text-sm text-ink-2 max-w-prose">
              {enough ? (
                <>
                  This group is large enough for SynPassport to judge it with confidence. Had it been underpowered, the result would be{" "}
                  <span className="font-mono text-ink">INSUFFICIENT_EVIDENCE</span> with the number of records still needed.
                </>
              ) : (
                <>
                  Rather than giving a weak pass on an underpowered group, SynPassport returns{" "}
                  <span className="font-mono text-ink">INSUFFICIENT_EVIDENCE</span>. To authorize clinical ML, collect at least {deficit} more
                  records for patients aged 65+.
                </>
              )}
            </p>
          </Card>

          <Card title="All critical subgroups">
            <div className="overflow-x-auto -mx-6 px-6">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-ink-2">
                    <th scope="col" className="text-left font-medium pb-3 pr-4">Subgroup</th>
                    <th scope="col" className="text-right font-medium pb-3 px-4">Records</th>
                    <th scope="col" className="text-right font-medium pb-3 px-4">Needed</th>
                    <th scope="col" className="text-right font-medium pb-3 px-4">Projected CI</th>
                    <th scope="col" className="text-right font-medium pb-3 px-4">Allowed CI</th>
                    <th scope="col" className="text-left font-medium pb-3 pl-4">Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {subgroups.map((sub, i) => (
                    <tr key={i}>
                      <td className="py-3 pr-4 font-mono text-ink whitespace-nowrap">{sub.subgroup_query}</td>
                      <td className="py-3 px-4 text-right tabular-nums text-ink">{sub.current_n}</td>
                      <td className="py-3 px-4 text-right tabular-nums text-ink-2">{sub.required_min_n}</td>
                      <td className="py-3 px-4 text-right tabular-nums text-ink-2">&plusmn;{sub.projected_ci_width.toFixed(3)}</td>
                      <td className="py-3 px-4 text-right tabular-nums text-ink-2">&le;{sub.target_ci_width.toFixed(3)}</td>
                      <td className="py-3 pl-4">
                        <StateBadge state={sub.state} size="sm" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
};
