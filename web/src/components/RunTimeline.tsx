"use client";

import React, { useState } from "react";
import { RunStatus, AgentEvent, BudgetUsed } from "@/types";
import { StateBadge } from "./StateBadge";
import { Card, EmptyState, Meter, Notice, PageHeader, SkeletonBlock, cx } from "./ui";

interface RunTimelineProps {
  runId: string;
  runStatus: RunStatus | null;
  events: AgentEvent[];
  budgetUsed: BudgetUsed | null;
  isLoading: boolean;
  error?: string | null;
}

const EVENT_LABELS: Record<string, string> = {
  status: "Status",
  step: "Step",
  plan: "Plan",
  candidate: "Candidate generated",
  generate: "Candidate generated",
  evaluation: "Evaluation",
  evaluate: "Evaluation",
  checks: "Checks",
  check: "Check",
  decision: "Agent decision",
  repair: "Repair applied",
  rejection: "Agent proposal rejected",
  agent_rejection: "Agent proposal rejected",
  finalized: "Finalized",
  finalize: "Finalized",
  completed: "Run completed",
  failed: "Run failed",
  approved: "Release approved",
};

// Marker colour carries the event's meaning; the label always says it in words too.
function markerTone(type: string): string {
  switch (type.toLowerCase()) {
    case "repair":
      return "bg-warn";
    case "rejection":
    case "agent_rejection":
    case "failed":
      return "bg-fail";
    case "completed":
    case "finalized":
    case "finalize":
    case "approved":
      return "bg-pass";
    case "candidate":
    case "generate":
    case "decision":
      return "bg-accent";
    default:
      return "bg-line-strong";
  }
}

const STATUS_TEXT: Record<string, string> = {
  QUEUED: "Queued",
  RUNNING: "Running",
  COMPLETED: "Completed",
  FAILED: "Failed",
};

function humanize(type: string): string {
  return EVENT_LABELS[type.toLowerCase()] || type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, " ");
}

export const RunTimeline: React.FC<RunTimelineProps> = ({
  runId,
  runStatus,
  events,
  budgetUsed,
  isLoading,
  error,
}) => {
  const candidatesUsed = budgetUsed?.candidates_evaluated ?? runStatus?.candidates?.length ?? 0;
  const maxCandidates = budgetUsed?.max_candidates ?? 3;
  const repairsUsed = budgetUsed?.repairs_attempted ?? runStatus?.repairs?.length ?? 0;
  const maxRepairs = budgetUsed?.max_repairs ?? 2;

  const status = runStatus?.status;
  const statusLabel = status ? STATUS_TEXT[status] || status : "Starting";

  return (
    <div className="space-y-8">
      <PageHeader
        title="Agent timeline"
        description={
          <>
            Every step the agent took, in order. Run <span className="font-mono text-ink">{runId}</span>
          </>
        }
        meta={
          <span
            className={cx(
              "text-sm font-medium",
              status === "COMPLETED" ? "text-pass" : status === "FAILED" ? "text-fail" : "text-accent"
            )}
            role="status"
          >
            {statusLabel}
            {status === "RUNNING" && <span className="text-ink-3 font-normal"> · streaming live</span>}
          </span>
        }
      />

      {(error || runStatus?.error) && (
        <Notice tone="fail" role="alert" title="The run stopped with an error">
          <span className="font-mono">{error || runStatus?.error}</span>
          <span className="block mt-1">Check the API window for details, then start a new run from Setup.</span>
        </Notice>
      )}

      {/* Budgets enforced in code */}
      <div className="grid gap-6 sm:grid-cols-2">
        <Card as="div">
          <div className="flex items-baseline justify-between mb-3">
            <span className="text-sm text-ink-2">Candidates generated</span>
            <span className="text-lg font-semibold tabular-nums text-ink">
              {candidatesUsed} <span className="text-sm font-normal text-ink-3">of {maxCandidates}</span>
            </span>
          </div>
          <Meter
            value={candidatesUsed}
            max={maxCandidates}
            tone={candidatesUsed >= maxCandidates ? "warn" : "accent"}
            label="Candidate budget used"
          />
          <p className="mt-3 text-sm text-ink-3">
            {candidatesUsed >= maxCandidates ? "Budget used up." : "Hard cap enforced by the policy, not the agent."}
          </p>
        </Card>
        <Card as="div">
          <div className="flex items-baseline justify-between mb-3">
            <span className="text-sm text-ink-2">Repairs attempted</span>
            <span className="text-lg font-semibold tabular-nums text-ink">
              {repairsUsed} <span className="text-sm font-normal text-ink-3">of {maxRepairs}</span>
            </span>
          </div>
          <Meter
            value={repairsUsed}
            max={maxRepairs}
            tone={repairsUsed >= maxRepairs ? "fail" : "warn"}
            label="Repair budget used"
          />
          <p className="mt-3 text-sm text-ink-3">
            {repairsUsed >= maxRepairs ? "No repairs left." : "Only whitelisted repairs are allowed."}
          </p>
        </Card>
      </div>

      {runStatus?.agent_rejections && runStatus.agent_rejections.length > 0 && (
        <Card
          title={`${runStatus.agent_rejections.length} agent ${
            runStatus.agent_rejections.length === 1 ? "proposal" : "proposals"
          } rejected`}
          description="The policy blocked these actions. Thresholds and the whitelist cannot be changed by the agent."
        >
          <ul className="divide-y divide-line">
            {runStatus.agent_rejections.map((rej, idx) => (
              <li key={idx} className="py-3 first:pt-0 last:pb-0 space-y-1">
                <p className="text-base font-medium text-ink font-mono">{rej.proposal}</p>
                <p className="text-sm text-ink-2">{rej.reason}</p>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card title="Events">
        {events.length === 0 ? (
          isLoading || status === "RUNNING" || status === "QUEUED" ? (
            <SkeletonBlock lines={4} label="Waiting for the first agent event" />
          ) : (
            <EmptyState
              title="No events yet"
              description="Events stream in here as soon as a run starts. Start one from Setup."
            />
          )
        ) : (
          <ol className="relative space-y-0">
            {events.map((ev, index) => {
              const time = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : `Step ${index + 1}`;
              const rawStatus = ev.data?.status ? String(ev.data.status) : "";
              const message =
                ev.data?.message || ev.data?.plan || ev.data?.diagnosis || (rawStatus ? STATUS_TEXT[rawStatus] || rawStatus : "");
              const isLast = index === events.length - 1;
              return (
                <li key={index} className="relative grid grid-cols-[20px_minmax(0,1fr)] gap-4 pb-6 last:pb-0">
                  <div className="relative flex justify-center">
                    <span className={cx("mt-2 w-2.5 h-2.5 rounded-full z-10", markerTone(ev.type))} aria-hidden="true" />
                    {!isLast && <span className="absolute top-5 bottom-[-8px] w-px bg-line" aria-hidden="true" />}
                  </div>

                  <div className="space-y-2 min-w-0">
                    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                      <p className="text-base font-medium text-ink">
                        {humanize(ev.type)}
                        {Boolean(ev.data?.candidate_id) && (
                          <span className="ml-2 font-mono text-sm font-normal text-ink-2">
                            {String(ev.data.candidate_id)}
                          </span>
                        )}
                      </p>
                      <time className="text-sm text-ink-3 tabular-nums">{time}</time>
                    </div>

                    {Boolean(ev.data?.generator) && (
                      <p className="text-sm text-ink-2">
                        Generator <span className="font-mono text-ink">{String(ev.data.generator)}</span>
                        {Boolean(ev.data?.requested_generator) &&
                          ev.data.requested_generator !== ev.data.generator && (
                            <span className="text-warn">
                              {" "}
                              (requested <span className="font-mono">{String(ev.data.requested_generator)}</span>)
                            </span>
                          )}
                      </p>
                    )}

                    {Boolean(ev.data?.note) && !ev.data?.action && (
                      <p className="text-sm text-ink-3 max-w-prose">{String(ev.data.note)}</p>
                    )}

                    {Boolean(message) && <Reasoning text={String(message)} />}

                    {Boolean(ev.data?.decided_by) && (
                      <p className="text-sm text-ink-2">
                        Decided by <span className="text-ink">{String(ev.data.decided_by)}</span>
                        {Boolean(ev.data?.decision) && (
                          <>
                            {" · "}
                            <span className="font-mono text-ink">{String(ev.data.decision)}</span>
                          </>
                        )}
                      </p>
                    )}

                    {Boolean(ev.data?.verdicts && typeof ev.data.verdicts === "object") && (
                      <div className="flex flex-wrap gap-x-4 gap-y-2">
                        {Object.entries(ev.data.verdicts as Record<string, string>).map(([use, state]) => (
                          <span key={use} className="inline-flex items-center gap-2 text-sm text-ink-2">
                            <span className="font-mono">{use}</span>
                            <StateBadge state={state} size="sm" />
                          </span>
                        ))}
                      </div>
                    )}

                    {Boolean(ev.data?.action) && (
                      <div className="rounded bg-surface-2 px-3 py-2 text-sm">
                        <span className="text-ink-2">Repair </span>
                        <span className="font-mono text-ink">{String(ev.data.action)}</span>
                        {Boolean(ev.data.params) && Object.keys(ev.data.params as object).length > 0 && (
                          <span className="block font-mono text-ink-3 break-all">{JSON.stringify(ev.data.params)}</span>
                        )}
                        {Boolean(ev.data.note) && <span className="block text-ink-2 mt-1">{String(ev.data.note)}</span>}
                      </div>
                    )}

                    {Boolean(ev.data?.reason) && !ev.data?.action && (
                      <p className="text-sm text-fail">{String(ev.data.reason)}</p>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </Card>
    </div>
  );
};

/** Long agent reasoning is clamped to three lines with a toggle to read all of it. */
const Reasoning: React.FC<{ text: string }> = ({ text }) => {
  const [open, setOpen] = useState(false);
  const long = text.length > 260;
  return (
    <div className="max-w-prose space-y-1">
      <p className={cx("text-sm text-ink-2", long && !open && "line-clamp-3")}>{text}</p>
      {long && (
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          className="text-sm text-accent hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent rounded-sm"
        >
          {open ? "Show less" : "Show full reasoning"}
        </button>
      )}
    </div>
  );
};
