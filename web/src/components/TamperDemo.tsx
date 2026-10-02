"use client";

import React, { useEffect, useMemo, useState } from "react";
import { VerificationResult } from "@/types";
import { StateBadge } from "./StateBadge";
import { Button, Card, EmptyState, Mono, Notice, PageHeader, Select, cx } from "./ui";

interface TamperDemoProps {
  passport: Record<string, unknown> | null;
  candidateCsv: string;
  onVerifyCustom: (
    datasetContent: string,
    passportContent: Record<string, unknown>,
    purpose: string
  ) => Promise<VerificationResult>;
  isVerifying?: boolean;
}

const USE_LABELS: Record<string, string> = {
  software_testing: "Software testing",
  ml_prototyping: "ML prototyping",
  clinical_ml: "Clinical ML",
  exploratory_analytics: "Exploratory analytics",
};

/** SHA-256 of the exact UTF-8 bytes, matching how the server hashes the file. */
async function sha256Hex(text: string): Promise<string> {
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/** Nudge the first numeric cell of the first data row by +0.1, keeping everything else byte-identical. */
function tamperOneCell(csv: string): { text: string; column: string } | null {
  const eol = csv.includes("\r\n") ? "\r\n" : "\n";
  const lines = csv.split(eol);
  if (lines.length < 2) return null;
  const header = lines[0].split(",");
  const cells = lines[1].split(",");
  for (let i = 0; i < cells.length; i++) {
    const n = Number(cells[i]);
    if (cells[i].trim() !== "" && Number.isFinite(n)) {
      const decimals = Math.max(1, (cells[i].split(".")[1] || "").length);
      cells[i] = (n + 0.1).toFixed(decimals);
      lines[1] = cells.join(",");
      return { text: lines.join(eol), column: header[i] || `column ${i + 1}` };
    }
  }
  return null;
}

export const TamperDemo: React.FC<TamperDemoProps> = ({
  passport,
  candidateCsv,
  onVerifyCustom,
  isVerifying = false,
}) => {
  const original = candidateCsv;
  const eol = original.includes("\r\n") ? "\r\n" : "\n";

  const dataset = (passport?.dataset ?? {}) as Record<string, unknown>;
  const manifestHash = String(dataset.sha256 || "");
  const datasetName = String(dataset.name || "candidate.csv");
  const purposes = Object.keys((passport?.verdicts ?? {}) as Record<string, unknown>);

  const [csvContent, setCsvContent] = useState<string>(original);
  const [computedHash, setComputedHash] = useState<string>("");
  const [purpose, setPurpose] = useState<string>(purposes[0] || "software_testing");
  const [verifyResult, setVerifyResult] = useState<VerificationResult | null>(null);
  const [lastChange, setLastChange] = useState<string>("");

  // Load the real bound dataset whenever a run's file arrives
  useEffect(() => {
    setCsvContent(original);
    setVerifyResult(null);
    setLastChange("");
  }, [original]);

  // Keep the chosen purpose valid for this passport
  useEffect(() => {
    if (purposes.length > 0 && !purposes.includes(purpose)) setPurpose(purposes[0]);
  }, [purposes, purpose]);

  // Hash exactly what will be sent to the server
  useEffect(() => {
    let cancelled = false;
    if (!csvContent) {
      setComputedHash("");
      return;
    }
    if (typeof crypto === "undefined" || !crypto.subtle) {
      setComputedHash("");
      return;
    }
    sha256Hex(csvContent).then((h) => {
      if (!cancelled) setComputedHash(h);
    });
    return () => {
      cancelled = true;
    };
  }, [csvContent]);

  const isModified = csvContent !== original;
  const hashesMatch = Boolean(computedHash) && computedHash === manifestHash;
  const rowCount = useMemo(() => Math.max(0, csvContent.split(/\r?\n/).filter(Boolean).length - 1), [csvContent]);

  const resetResult = () => setVerifyResult(null);

  const handleTamperSingleCell = () => {
    const result = tamperOneCell(csvContent);
    if (result) {
      setCsvContent(result.text);
      setLastChange(`Changed the first value in “${result.column}” by +0.1`);
      resetResult();
    }
  };

  const handleResetOriginal = () => {
    setCsvContent(original);
    setLastChange("");
    resetResult();
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    file.arrayBuffer().then((buf) => {
      setCsvContent(new TextDecoder("utf-8").decode(buf));
      setLastChange(`Loaded ${file.name}`);
      resetResult();
    });
    e.target.value = "";
  };

  const handleEdit = (value: string) => {
    // Browsers normalize textarea line endings to "\n"; restore the file's own endings
    // so an edit that is undone by hand still hashes identically.
    setCsvContent(eol === "\r\n" ? value.replace(/\r?\n/g, "\r\n") : value);
    setLastChange("Edited by hand");
    resetResult();
  };

  const handleRunVerify = async () => {
    if (!passport) return;
    const res = await onVerifyCustom(csvContent, passport, purpose);
    setVerifyResult(res);
  };

  if (!passport || !original) {
    return (
      <div className="space-y-8">
        <PageHeader
          title="Tamper test"
          description="Change a single value in the synthetic data and verify it against its passport. Any change breaks the hash binding, and the loader refuses the file."
        />
        <EmptyState
          title={passport ? "Loading the signed dataset" : "No signed dataset yet"}
          description={
            passport
              ? "Fetching the exact file this passport is bound to."
              : "Complete a run from Setup. The tamper test uses the real synthetic file its passport signed."
          }
        />
      </div>
    );
  }

  const guardBlocked = verifyResult ? !verifyResult.valid : null;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Tamper test"
        description="Change a single value in the synthetic data and verify it against its passport. Any change breaks the hash binding, and the loader refuses the file."
      />

      <Card
        title="Synthetic dataset"
        description={
          <>
            The exact file the passport signed, <span className="font-mono text-ink">{datasetName}</span>. Edit any character, or use a quick action.
          </>
        }
        actions={
          <span className={cx("text-sm font-medium", isModified ? "text-fail" : "text-pass")} role="status">
            {isModified ? "Modified" : "Original"}
          </span>
        }
      >
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <Button variant="danger" size="sm" onClick={handleTamperSingleCell}>
            Tamper one cell
          </Button>
          <Button variant="ghost" size="sm" onClick={handleResetOriginal} disabled={!isModified}>
            Reset to original
          </Button>
          <label className="relative inline-flex">
            <input type="file" accept=".csv" onChange={handleFileUpload} className="peer sr-only" />
            <span className="inline-flex items-center h-8 px-3 rounded text-sm text-ink-2 hover:text-ink hover:bg-surface-2 cursor-pointer transition-colors peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-accent">
              Upload a CSV
            </span>
          </label>
          {lastChange && isModified && <span className="text-sm text-ink-2">{lastChange}</span>}
        </div>

        <label htmlFor="tamper-csv" className="sr-only">
          Synthetic dataset CSV
        </label>
        <textarea
          id="tamper-csv"
          value={csvContent}
          onChange={(e) => handleEdit(e.target.value)}
          rows={8}
          spellCheck={false}
          className="w-full rounded border border-line-strong bg-surface-2 p-3 font-mono text-sm leading-relaxed text-ink resize-y focus:border-accent focus:outline-none"
        />
        <p className="mt-2 text-sm text-ink-3 tabular-nums">{rowCount} records</p>

        <div className="mt-6 pt-6 border-t border-line flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-2 sm:w-64">
            <label htmlFor="tamper-purpose" className="block text-sm font-medium text-ink">
              Verify for purpose
            </label>
            <Select
              id="tamper-purpose"
              value={purpose}
              onChange={(v) => {
                setPurpose(v);
                resetResult();
              }}
              options={(purposes.length > 0 ? purposes : ["software_testing"]).map((p) => ({
                value: p,
                label: USE_LABELS[p] || p,
              }))}
            />
          </div>
          <Button variant="primary" onClick={handleRunVerify} loading={isVerifying}>
            {isVerifying ? "Verifying…" : "Verify dataset and passport"}
          </Button>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card
          title="Verification result"
          actions={verifyResult ? <StateBadge state={verifyResult.valid ? "PASS" : "FAIL"} size="sm" /> : undefined}
        >
          {verifyResult ? (
            <Notice
              tone={verifyResult.valid ? "pass" : "fail"}
              role={verifyResult.valid ? "status" : "alert"}
              title={
                verifyResult.valid
                  ? "Verified: the file matches its passport"
                  : verifyResult.reason_code === "DATASET_HASH_MISMATCH"
                  ? "Rejected: the file was changed"
                  : "Rejected"
              }
            >
              <span className="font-mono text-ink">{verifyResult.reason_code}</span>
              <span className="block">{verifyResult.description}</span>
            </Notice>
          ) : (
            <p className="text-sm text-ink-2">
              The server recomputes the hash and checks the signature, purpose and approval. Run a verification to see its verdict.
            </p>
          )}

          <dl className="mt-6 space-y-4">
            <div className="space-y-1">
              <dt className="text-sm text-ink-2">Hash recorded in the passport</dt>
              <dd>
                <Mono className="text-ink-2">{manifestHash || "Not recorded"}</Mono>
              </dd>
            </div>
            <div className="space-y-1">
              <dt className="text-sm text-ink-2">Hash of the file above</dt>
              <dd>
                {computedHash ? (
                  <Mono className={hashesMatch ? "text-pass" : "text-fail"}>{computedHash}</Mono>
                ) : (
                  <span className="text-sm text-ink-3">Computing…</span>
                )}
              </dd>
            </div>
            {computedHash && (
              <p className={cx("text-sm font-medium", hashesMatch ? "text-pass" : "text-fail")}>
                {hashesMatch ? "Hashes match." : "Hashes differ: the file is not the one that was signed."}
              </p>
            )}
          </dl>
        </Card>

        <Card
          title="Loader guard"
          description={
            <>
              What a training script sees when it calls <span className="font-mono text-ink">synpassport.load_dataset()</span> with this file.
            </>
          }
        >
          <pre className="whitespace-pre-wrap break-words rounded bg-inverse p-4 font-mono text-sm leading-relaxed text-on-inverse">
            <span className="block opacity-60">$ python -m pipeline.train</span>
            <span className="block">{`>>> df = synpassport.load_dataset("${datasetName}", purpose="${purpose}")`}</span>
            {guardBlocked === null ? (
              <span className="block mt-2 opacity-70">Waiting for verification…</span>
            ) : guardBlocked ? (
              <>
                <span className="block mt-2 font-semibold" style={{ color: "var(--on-inverse-fail)" }}>
                  {`PassportError: [${verifyResult?.reason_code}]`}
                </span>
                <span className="block">{verifyResult?.description}</span>
                <span className="block mt-2">Training blocked. Exit code 1.</span>
              </>
            ) : (
              <>
                <span className="block mt-2" style={{ color: "var(--on-inverse-pass)" }}>
                  {`Binding verified for purpose '${purpose}'.`}
                </span>
                <span className="block">{`Loaded ${rowCount} records.`}</span>
              </>
            )}
          </pre>
          <p className="mt-4 text-sm text-ink-3">
            This panel mirrors the server&apos;s real verdict: the loader runs the same checks before any training starts.
          </p>
        </Card>
      </div>
    </div>
  );
};

