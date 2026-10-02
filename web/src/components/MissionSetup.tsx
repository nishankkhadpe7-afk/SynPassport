"use client";

import React, { useEffect, useMemo, useState } from "react";
import { PolicySummary } from "@/types";
import { generateHeartDiseaseSampleCsv } from "@/utils/sampleData";
import { Button, Card, Field, Mono, PageHeader, Select, inputClass, cx } from "./ui";

interface MissionSetupProps {
  onStartRun: (datasetFile: File | null, datasetText: string, missionJson: string) => Promise<void>;
  isLoading: boolean;
  apiBaseUrl: string;
}

// Only uses a policy actually judges are offered, so every ticked use gets a verdict.
const USE_OPTIONS: Array<{ id: string; label: string; note: string }> = [
  { id: "software_testing", label: "Software testing", note: "Fixtures and integration tests" },
  { id: "ml_prototyping", label: "ML prototyping", note: "Internal model experiments" },
  { id: "clinical_ml", label: "Clinical ML", note: "High-stakes model training" },
];

const USE_LABELS: Record<string, string> = Object.fromEntries(USE_OPTIONS.map((u) => [u.id, u.label]));

/** The strictest policy needed for the chosen uses. */
function policyFor(uses: string[]): string {
  if (uses.includes("clinical_ml")) return "ml-sensitive-v1";
  if (uses.includes("ml_prototyping")) return "ml-prototyping";
  return "software-testing";
}

function previewRows(text: string, maxRows = 4): { header: string[]; rows: string[][]; total: number } {
  const lines = text.split("\n").filter((l) => l.trim().length > 0);
  const header = (lines[0] || "").split(",");
  const rows = lines.slice(1, maxRows + 1).map((l) => l.split(","));
  return { header, rows, total: Math.max(0, lines.length - 1) };
}

export const MissionSetup: React.FC<MissionSetupProps> = ({ onStartRun, isLoading, apiBaseUrl }) => {
  const [datasetText, setDatasetText] = useState<string>("");
  const [fileName, setFileName] = useState<string>("");
  const [datasetFile, setDatasetFile] = useState<File | null>(null);

  const [purpose, setPurpose] = useState<string>("software_testing");
  const [targetColumn, setTargetColumn] = useState<string>("target");
  const [criticalSubgroup, setCriticalSubgroup] = useState<string>("age >= 65");
  const [privacyLevel, setPrivacyLevel] = useState<string>("standard");
  const [intendedUses, setIntendedUses] = useState<string[]>(["software_testing"]);

  const allUses = useMemo(
    () => Array.from(new Set([purpose, ...intendedUses])),
    [purpose, intendedUses]
  );
  const policyId = policyFor(allUses);
  const [policy, setPolicy] = useState<PolicySummary | null>(null);
  const [policyError, setPolicyError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setPolicy(null);
    setPolicyError(null);
    fetch(`${apiBaseUrl}/policies/${policyId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data: PolicySummary) => !cancelled && setPolicy(data))
      .catch((err: Error) => !cancelled && setPolicyError(err.message));
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, policyId]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setDatasetFile(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        setDatasetText(event.target?.result as string);
      };
      reader.readAsText(file);
    }
  };

  const handleLoadSample = () => {
    const sample = generateHeartDiseaseSampleCsv();
    setDatasetText(sample);
    setFileName("heart_disease_benchmark.csv");
    setDatasetFile(null);
  };

  const toggleIntendedUse = (use: string) => {
    setIntendedUses((prev) =>
      prev.includes(use) ? prev.filter((item) => item !== use) : [...prev, use]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!datasetText && !datasetFile) return;

    const mission = {
      purpose,
      target_column: targetColumn,
      critical_subgroups: criticalSubgroup ? [criticalSubgroup] : [],
      privacy_level: privacyLevel,
      intended_uses: allUses,
      policy_id: policyId,
      seed: 1234,
    };

    onStartRun(datasetFile, datasetText, JSON.stringify(mission, null, 2));
  };

  const hasData = Boolean(datasetText || datasetFile);
  const preview = datasetText ? previewRows(datasetText) : null;
  const columns = preview?.header.map((h) => h.trim()) ?? [];
  const targetMissing = columns.length > 0 && targetColumn.trim() !== "" && !columns.includes(targetColumn.trim());
  const subgroupColumn = criticalSubgroup.trim().split(/\s*(?:>=|<=|==|!=|>|<)\s*/)[0]?.trim() ?? "";
  const subgroupMissing = columns.length > 0 && subgroupColumn !== "" && !columns.includes(subgroupColumn);
  const unjudgedUses = policy ? allUses.filter((u) => !(u in policy.uses)) : [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Start an assurance run"
        description="Upload the real training data, say what the synthetic copy will be used for, and SynPassport generates candidates, tests them against a locked policy, and issues a signed passport."
      />

      <form onSubmit={handleSubmit} className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-6 min-w-0">
          {/* Dataset */}
          <Card
            title="Training data"
            description="CSV with a header row. The sample needs age, cholesterol, resting_bp and target."
            actions={
              <Button type="button" variant="ghost" size="sm" onClick={handleLoadSample}>
                Use sample heart-disease data
              </Button>
            }
          >
            <div>
              <input
                type="file"
                accept=".csv"
                id="dataset-upload"
                onChange={handleFileUpload}
                className="peer sr-only"
              />
              <label
                htmlFor="dataset-upload"
                className={cx(
                  "flex flex-col items-center justify-center gap-1 rounded border border-dashed px-6 py-8 text-center cursor-pointer transition-colors duration-200 ease-out",
                  "peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-accent peer-focus-visible:outline-offset-2",
                  fileName ? "border-pass bg-pass-soft" : "border-line-strong hover:border-accent hover:bg-accent-soft"
                )}
              >
                {fileName ? (
                  <>
                    <span className="text-base font-medium text-ink">{fileName}</span>
                    <span className="text-sm text-ink-2">
                      {preview ? `${preview.total} records loaded` : "Loaded"} · choose a different file
                    </span>
                  </>
                ) : (
                  <>
                    <span className="text-base font-medium text-ink">Choose a CSV file</span>
                    <span className="text-sm text-ink-2">or use the sample data above</span>
                  </>
                )}
              </label>
            </div>

            {preview && preview.rows.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-sm text-ink-2">First {preview.rows.length} of {preview.total} records</p>
                <div className="overflow-x-auto rounded border border-line">
                  <table className="w-full text-sm">
                    <thead className="bg-surface-2 text-ink-2">
                      <tr>
                        {preview.header.map((h, i) => (
                          <th key={i} scope="col" className="text-left font-medium px-3 py-2 whitespace-nowrap">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line">
                      {preview.rows.map((row, r) => (
                        <tr key={r}>
                          {row.map((cell, c) => (
                            <td key={c} className="px-3 py-2 font-mono text-ink tabular-nums whitespace-nowrap">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </Card>

          {/* Mission */}
          <Card title="Mission" description="These are recorded in the passport and cannot change after the run starts.">
            <div className="grid gap-5 sm:grid-cols-2">
              <Field id="purpose" label="Primary purpose">
                <Select
                  id="purpose"
                  value={purpose}
                  onChange={setPurpose}
                  options={[
                    { value: "software_testing", label: "Software testing" },
                    { value: "ml_prototyping", label: "ML prototyping" },
                    { value: "clinical_ml", label: "Clinical ML" },
                  ]}
                />
              </Field>

              <Field id="target-column" label="Target column" hint="The label a downstream model would predict.">
                <input
                  id="target-column"
                  type="text"
                  value={targetColumn}
                  onChange={(e) => setTargetColumn(e.target.value)}
                  placeholder="target"
                  aria-describedby="target-column-hint"
                  aria-invalid={targetMissing}
                  className={cx(inputClass, "font-mono")}
                />
                {targetMissing && (
                  <p className="mt-1 text-sm text-warn" role="status">
                    Not a column in this file. Columns: {columns.slice(0, 8).join(", ")}
                    {columns.length > 8 ? "…" : ""}
                  </p>
                )}
              </Field>

              <Field id="subgroup" label="Critical subgroup" hint="A group that must be well represented, e.g. age >= 65.">
                <input
                  id="subgroup"
                  type="text"
                  value={criticalSubgroup}
                  onChange={(e) => setCriticalSubgroup(e.target.value)}
                  placeholder="age >= 65"
                  aria-describedby="subgroup-hint"
                  aria-invalid={subgroupMissing}
                  className={cx(inputClass, "font-mono")}
                />
                {subgroupMissing && (
                  <p className="mt-1 text-sm text-warn" role="status">
                    “{subgroupColumn}” is not a column in this file.
                  </p>
                )}
              </Field>

              <Field id="privacy-level" label="Privacy level">
                <Select
                  id="privacy-level"
                  value={privacyLevel}
                  onChange={setPrivacyLevel}
                  options={[
                    { value: "standard", label: "Standard" },
                    { value: "high", label: "High" },
                    { value: "strict", label: "Strict" },
                  ]}
                />
              </Field>
            </div>

            <fieldset className="mt-6 space-y-3">
              <legend className="text-sm font-medium text-ink">Intended uses</legend>
              <p className="text-sm text-ink-3">Each use gets its own verdict. Passing one never authorizes another.</p>
              <div className="grid gap-2 sm:grid-cols-3">
                {USE_OPTIONS.map((use) => {
                  const checked = intendedUses.includes(use.id);
                  return (
                    <label
                      key={use.id}
                      className={cx(
                        "flex items-start gap-3 rounded border px-3 py-3 cursor-pointer transition-colors duration-200 ease-out",
                        checked ? "border-accent bg-accent-soft" : "border-line-strong hover:bg-surface-2"
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleIntendedUse(use.id)}
                        className="mt-1 h-4 w-4 accent-[var(--accent)]"
                      />
                      <span className="space-y-0.5">
                        <span className="block text-base font-medium text-ink">{use.label}</span>
                        <span className="block text-sm text-ink-2">{use.note}</span>
                      </span>
                    </label>
                  );
                })}
              </div>
            </fieldset>
          </Card>
        </div>

        {/* Policy summary + primary action */}
        <aside className="space-y-6 lg:sticky lg:top-32 self-start">
          <Card
            as="div"
            title="Policy"
            description="Chosen from the intended uses (the strictest one needed) and locked before any data is generated."
          >
            {policyError ? (
              <p className="text-sm text-fail" role="alert">
                Could not load policy {policyId} ({policyError}). Check that the API is running.
              </p>
            ) : !policy ? (
              <p className="text-sm text-ink-3">Loading {policyId}…</p>
            ) : (
              <dl className="space-y-4 text-sm">
                <div className="space-y-1">
                  <dt className="text-ink-2">Profile</dt>
                  <dd className="text-ink">
                    {policy.name} <span className="text-ink-3">v{policy.version}</span>
                    <Mono className="block text-ink-2">{policy.id}</Mono>
                  </dd>
                </div>
                <div className="space-y-1">
                  <dt className="text-ink-2">SHA-256</dt>
                  <dd>
                    <Mono className="text-ink-2 break-all">{policy.sha256}</Mono>
                  </dd>
                </div>
                <div className="space-y-1 border-t border-line pt-4">
                  <dt className="text-ink-2">Checks per use</dt>
                  <dd>
                    <ul className="space-y-1">
                      {allUses.map((u) => (
                        <li key={u} className="flex justify-between gap-2">
                          <span className="text-ink">{USE_LABELS[u] || u}</span>
                          <span className="text-ink-2 tabular-nums">
                            {policy.uses[u]
                              ? policy.uses[u].includes("all")
                                ? `all ${Object.keys(policy.requires).length}`
                                : policy.uses[u].length
                              : "not judged"}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </dd>
                </div>
                <div className="flex justify-between border-t border-line pt-4">
                  <dt className="text-ink-2">Candidates</dt>
                  <dd className="text-ink tabular-nums">up to {policy.budget.max_candidates ?? 3}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-2">Agent repairs</dt>
                  <dd className="text-ink tabular-nums">up to {policy.budget.max_repairs ?? 2}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-2">Human approval</dt>
                  <dd className="text-ink">{policy.human_approval === "required" ? "Required" : "Optional"}</dd>
                </div>
                {unjudgedUses.length > 0 && (
                  <p className="text-sm text-warn">This policy gives no verdict for: {unjudgedUses.join(", ")}.</p>
                )}
              </dl>
            )}
          </Card>

          <div className="space-y-2">
            <Button
              type="submit"
              variant="primary"
              loading={isLoading}
              disabled={!hasData || !policy}
              className="w-full"
            >
              {isLoading ? "Starting run…" : "Start assurance run"}
            </Button>
            {!hasData && <p className="text-sm text-ink-3 text-center">Add training data to continue.</p>}
          </div>
        </aside>
      </form>
    </div>
  );
};
