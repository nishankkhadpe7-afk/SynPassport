"use client";

import React, { useState } from "react";
import { DcrResult, EvidenceItem } from "@/types";
import { StateBadge } from "./StateBadge";
import { Card, EmptyState, PageHeader, SkeletonBlock, cx } from "./ui";

interface EvidenceDrilldownProps {
  evidence: EvidenceItem[];
  isLoading?: boolean;
  /** Candidate whose evidence is shown (the one the passport signs). */
  candidateId?: string | null;
  dcr?: DcrResult | null;
}

const CHECK_LABELS: Record<string, string> = {
  schema_validity: "Schema validity",
  marginal_fidelity: "Marginal fidelity",
  correlation_fidelity: "Correlation fidelity",
  utility_tstr_ratio: "Utility (train synthetic, test real)",
  subgroup_utility_ci: "Subgroup utility",
  subgroup_utility_ci_width: "Subgroup utility CI width",
  privacy_dcr_vs_holdout: "Distance to closest record",
  membership_inference_auc: "Membership inference attack",
  sufficiency: "Subgroup sample size",
  identifier_leakage: "Identifier leakage",
};

const FILTERS: Array<{ id: string; label: string }> = [
  { id: "ALL", label: "All" },
  { id: "PASS", label: "Pass" },
  { id: "WARNING", label: "Warning" },
  { id: "FAIL", label: "Fail" },
  { id: "INSUFFICIENT_EVIDENCE", label: "Insufficient" },
];

const BAND_TONE: Record<string, { fill: string; edge: string }> = {
  PASS: { fill: "var(--pass-soft)", edge: "var(--pass)" },
  WARNING: { fill: "var(--warn-soft)", edge: "var(--warn)" },
  FAIL: { fill: "var(--fail-soft)", edge: "var(--fail)" },
};

export const EvidenceDrilldown: React.FC<EvidenceDrilldownProps> = ({
  evidence,
  isLoading = false,
  candidateId = null,
  dcr = null,
}) => {
  const [filterState, setFilterState] = useState<string>("ALL");

  const displayItems = evidence ?? [];

  const filteredItems = displayItems.filter((item) => {
    if (filterState === "ALL") return true;
    return (item.state || "").toUpperCase() === filterState;
  });

  // The API sends thresholds as text such as "{'min': 0.8}"; read them for display.
  const parseThreshold = (ref: unknown): unknown => {
    if (typeof ref !== "string") return ref;
    const match = ref.match(/'(min|max)':\s*([0-9.]+)/);
    return match ? { [match[1]]: Number(match[2]) } : ref;
  };

  const getThresholdNumber = (raw: unknown): number | null => {
    const ref = parseThreshold(raw);
    if (typeof ref === "number") return ref;
    if (typeof ref === "object" && ref !== null) {
      const obj = ref as Record<string, unknown>;
      if ("min" in obj && typeof obj.min === "number") return obj.min;
      if ("max" in obj && typeof obj.max === "number") return obj.max;
    }
    return null;
  };

  const formatThreshold = (raw: unknown): string => {
    const ref = parseThreshold(raw);
    if (typeof ref === "string") return ref.replace(/_/g, " ");
    if (typeof ref === "number") return String(ref);
    if (typeof ref === "object" && ref !== null) {
      const obj = ref as Record<string, unknown>;
      if ("min" in obj) return `\u2265 ${obj.min}`;
      if ("max" in obj) return `\u2264 ${obj.max}`;
    }
    return "pass";
  };

  const clampPct = (num: number) => Math.max(0, Math.min(100, num * 100));

  return (
    <div className="space-y-8">
      <PageHeader
        title="Evidence"
        description={
          <>
            Each pre-registered check with its measured value, 95% confidence interval and the policy threshold it was
            judged against.
            {candidateId && (
              <>
                {" "}
                Showing <span className="font-mono text-ink">{candidateId}</span>, the candidate the passport signs.
              </>
            )}
          </>
        }
        actions={
          <div role="group" aria-label="Filter checks by result" className="inline-flex rounded border border-line-strong bg-surface p-0.5">
            {FILTERS.map((f) => (
              <button
                key={f.id}
                type="button"
                aria-pressed={filterState === f.id}
                onClick={() => setFilterState(f.id)}
                className={cx(
                  "h-8 px-3 rounded-sm text-sm transition-colors duration-200 ease-out",
                  filterState === f.id ? "bg-surface-2 text-ink font-medium" : "text-ink-2 hover:text-ink"
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
        }
      />

      {isLoading ? (
        <Card>
          <SkeletonBlock lines={6} label="Loading evidence" />
        </Card>
      ) : displayItems.length === 0 ? (
        <EmptyState
          title="No evidence yet"
          description="Complete a run from Setup. Every check the policy requires appears here with its measured value."
        />
      ) : filteredItems.length === 0 ? (
        <EmptyState
          title="No checks with this result"
          description="Choose another filter, or All, to see every check."
        />
      ) : (
        <Card flush>
          <ul className="divide-y divide-line">
            {filteredItems.map((item, idx) => {
              // For CI-width checks the policy judges the width of the interval, not the
              // estimate itself, so show and plot the width.
              const isWidthCheck =
                item.check_id.endsWith("_ci_width") && item.ci_low != null && item.ci_high != null;
              const width = isWidthCheck ? (item.ci_high as number) - (item.ci_low as number) : null;
              const val = width ?? item.value ?? 0;
              const low = isWidthCheck ? val : item.ci_low ?? val;
              const high = isWidthCheck ? val : item.ci_high ?? val;
              const threshNum = getThresholdNumber(item.threshold_ref);
              const tone = BAND_TONE[(item.state || "").toUpperCase()] || {
                fill: "var(--neutral-soft)",
                edge: "var(--neutral)",
              };
              const hasInterval = item.ci_low !== null && item.ci_high !== null && high > low;

              return (
                <li key={`${item.check_id}_${idx}`} className="p-6 space-y-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-0.5 min-w-0">
                      <h2 className="text-base font-semibold text-ink">{CHECK_LABELS[item.check_id] || item.check_id}</h2>
                      <p className="font-mono text-sm text-ink-3">{item.check_id}</p>
                    </div>
                    <StateBadge state={item.state || "UNKNOWN"} size="sm" />
                  </div>

                  <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-4">
                    <div>
                      <dt className="text-ink-2">{isWidthCheck ? "CI width" : "Value"}</dt>
                      <dd className="text-base font-semibold text-ink tabular-nums">
                        {width != null
                          ? width.toFixed(3)
                          : typeof item.value === "number"
                            ? item.value.toFixed(3)
                            : String(item.value)}
                      </dd>
                      {isWidthCheck && typeof item.value === "number" && (
                        <dd className="text-sm text-ink-3 tabular-nums">estimate {item.value.toFixed(3)}</dd>
                      )}
                    </div>
                    <div>
                      <dt className="text-ink-2">95% CI</dt>
                      <dd className="text-ink tabular-nums">
                        {isWidthCheck
                          ? `${(item.ci_low as number).toFixed(3)} \u2013 ${(item.ci_high as number).toFixed(3)}`
                          : hasInterval
                            ? `${low.toFixed(3)} \u2013 ${high.toFixed(3)}`
                            : "Not reported"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-ink-2">Threshold</dt>
                      <dd className="text-ink tabular-nums">{formatThreshold(item.threshold_ref)}</dd>
                    </div>
                    <div>
                      <dt className="text-ink-2">Sample</dt>
                      <dd className="text-ink tabular-nums">{item.n != null ? `n = ${item.n}` : "n not reported"}
                        {item.seed != null && `, seed ${item.seed}`}</dd>
                    </div>
                  </dl>

                  {/* Interval plot on a 0–1 scale */}
                  <div aria-hidden="true" className="space-y-1">
                    <div className="relative h-6">
                      <div className="absolute inset-x-0 top-1/2 h-px bg-line" />
                      {[0, 25, 50, 75, 100].map((t) => (
                        <div key={t} className="absolute top-1/2 -translate-y-1/2 h-2 w-px bg-line-strong" style={{ left: `${t}%` }} />
                      ))}
                      <div
                        className="absolute top-1/2 -translate-y-1/2 h-3 rounded-full border"
                        style={{
                          left: `${clampPct(low)}%`,
                          width: `${Math.max(1, clampPct(high) - clampPct(low))}%`,
                          background: tone.fill,
                          borderColor: tone.edge,
                        }}
                      />
                      <div
                        className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-ink border-2 border-surface"
                        style={{ left: `${clampPct(val)}%` }}
                      />
                      {threshNum !== null && (
                        <div
                          className="absolute inset-y-0 -translate-x-1/2 border-l-2 border-dashed border-ink-2"
                          style={{ left: `${clampPct(threshNum)}%` }}
                        />
                      )}
                    </div>
                    <div className="flex justify-between text-sm text-ink-3 tabular-nums">
                      <span>0</span>
                      <span>0.5</span>
                      <span>1</span>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </Card>
      )}

      <DcrCard dcr={dcr} />
    </div>
  );
};

const fmt = (n: number) => (n < 0.01 ? n.toFixed(4) : n.toFixed(3));

const DcrCard: React.FC<{ dcr: DcrResult | null }> = ({ dcr }) => {
  if (!dcr) {
    return (
      <Card
        title="Distance to closest record"
        description="How close synthetic rows sit to real rows the generator saw, compared with real rows it never saw."
      >
        <p className="text-sm text-ink-2">Available once a run has finished and its passport is signed.</p>
      </Card>
    );
  }
  const max = Math.max(1, ...dcr.bins.map((b) => Math.max(b.to_training, b.to_holdout)));
  const share = Math.round(dcr.share_closer_to_training * 100);
  const closerThanExpected = dcr.share_closer_to_training > 0.6;

  return (
    <Card
      title="Distance to closest record"
      description={
        <>
          For {dcr.sample_size} sampled rows of <span className="font-mono text-ink">{dcr.candidate}</span>: the
          distance to the closest real row the generator was trained on, and to the closest real holdout row it never
          saw. If synthetic rows sit much closer to training rows, real records may have been memorised.
        </>
      }
    >
      <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-ink-2 mb-4">
        <span className="inline-flex items-center gap-2">
          <span className="w-3 h-3 rounded-sm" style={{ background: "var(--ink-2)" }} aria-hidden="true" />
          To closest training row
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="w-3 h-3 rounded-sm" style={{ background: "var(--line-strong)" }} aria-hidden="true" />
          To closest holdout row
        </span>
      </div>

      <div className="overflow-x-auto">
        <div
          className="grid gap-2 items-end h-40 min-w-[480px] border-b border-line"
          style={{ gridTemplateColumns: `repeat(${dcr.bins.length}, minmax(0, 1fr))` }}
          role="img"
          aria-label={`Histogram of distances. ${share}% of synthetic rows are closer to a training row than to any holdout row.`}
        >
          {dcr.bins.map((bin, i) => (
            <div key={i} className="flex items-end justify-center gap-0.5 h-full">
              <div
                className="w-1/2 rounded-t-sm"
                style={{ height: `${(bin.to_training / max) * 100}%`, background: "var(--ink-2)" }}
                title={`${fmt(bin.low)}–${fmt(bin.high)}: ${bin.to_training} rows closest to training`}
              />
              <div
                className="w-1/2 rounded-t-sm"
                style={{ height: `${(bin.to_holdout / max) * 100}%`, background: "var(--line-strong)" }}
                title={`${fmt(bin.low)}–${fmt(bin.high)}: ${bin.to_holdout} rows closest to holdout`}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-between min-w-[480px] pt-2 text-sm text-ink-3 tabular-nums">
          <span>0</span>
          <span>distance (scaled features)</span>
          <span>{fmt(dcr.bins[dcr.bins.length - 1]?.high ?? 0)}+</span>
        </div>
      </div>

      <dl className="mt-6 grid gap-x-6 gap-y-3 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-ink-2">Closer to a training row</dt>
          <dd className={cx("text-base font-semibold tabular-nums", closerThanExpected ? "text-warn" : "text-ink")}>
            {share}% <span className="text-sm font-normal text-ink-3">(about 50% expected)</span>
          </dd>
        </div>
        <div>
          <dt className="text-ink-2">Median distance</dt>
          <dd className="text-ink tabular-nums">
            training {fmt(dcr.median_to_training)} · holdout {fmt(dcr.median_to_holdout)}
          </dd>
        </div>
        <div>
          <dt className="text-ink-2">Exact copies of training rows</dt>
          <dd className={cx("tabular-nums", dcr.exact_copies_of_training > 0 ? "text-fail font-semibold" : "text-ink")}>
            {dcr.exact_copies_of_training}
          </dd>
        </div>
      </dl>
      <p className="mt-4 text-sm text-ink-3 max-w-prose">
        Computed from this run&apos;s files (seed {dcr.seed}). Whether it counts towards a verdict depends on the
        policy: the privacy check is required for clinical ML.
      </p>
    </Card>
  );
};
