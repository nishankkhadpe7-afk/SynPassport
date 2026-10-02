"use client";

import React, { useEffect, useState } from "react";
import { VerificationResult } from "@/types";
import { Button, Card, EmptyState, Mono, Notice, PageHeader, SkeletonBlock, inputClass } from "./ui";

interface PassportPanelProps {
  runId: string;
  passport: Record<string, unknown> | null;
  onApprove: (approver: string) => Promise<void>;
  onVerify: () => Promise<void>;
  verificationResult: VerificationResult | null;
  isApproving?: boolean;
  isVerifying?: boolean;
  isLoading?: boolean;
}

function asRecord(v: unknown): Record<string, unknown> {
  return v && typeof v === "object" ? (v as Record<string, unknown>) : {};
}

export const PassportPanel: React.FC<PassportPanelProps> = ({
  runId,
  passport,
  onApprove,
  onVerify,
  verificationResult,
  isApproving = false,
  isVerifying = false,
  isLoading = false,
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [showApproveModal, setShowApproveModal] = useState<boolean>(false);
  const [approverEmail, setApproverEmail] = useState<string>("data-governance-officer@hospital.org");

  const handleCopyJson = () => {
    if (!passport) return;
    navigator.clipboard.writeText(JSON.stringify(passport, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJson = () => {
    if (!passport) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(passport, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `synpassport_${runId || "manifest"}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleConfirmApproval = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!approverEmail.trim()) return;
    await onApprove(approverEmail.trim());
    setShowApproveModal(false);
  };

  const humanApproval = passport?.human_approval as Record<string, unknown> | undefined;
  const isApproved = humanApproval?.status === "APPROVED" || Boolean(humanApproval?.approved);
  const approver = humanApproval?.approver as string | undefined;

  // Read the fields the passport actually contains, for display only
  const dataset = asRecord(passport?.dataset);
  const policy = asRecord(passport?.policy);
  const signature = asRecord(passport?.signature);
  const datasetHash = String(dataset.sha256 || passport?.dataset_hash || "");
  const policyHash = String(policy.sha256 || policy.hash || "");
  const signatureValue = typeof passport?.signature === "string" ? String(passport.signature) : String(signature.value || "");
  const keyId = String(signature.key_id || "");
  const approvedAt = humanApproval?.timestamp ? String(humanApproval.timestamp) : "";

  // Close the dialog with Escape
  useEffect(() => {
    if (!showApproveModal) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setShowApproveModal(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [showApproveModal]);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Evidence passport"
        description="The signed record of this run: which data, which policy, what was found, and who approved release. Changing a single byte breaks the signature."
        meta={
          passport ? (
            <span className={isApproved ? "text-sm font-medium text-pass" : "text-sm text-ink-2"}>
              {isApproved ? "Approved for release" : "Awaiting human approval"}
            </span>
          ) : undefined
        }
        actions={
          <>
            <Button variant="secondary" onClick={() => setShowApproveModal(true)} disabled={!passport || isApproving}>
              {isApproved ? "Approve again" : "Approve release"}
            </Button>
            <Button variant="primary" onClick={onVerify} disabled={!passport} loading={isVerifying}>
              {isVerifying ? "Verifying…" : "Verify passport"}
            </Button>
          </>
        }
      />

      {verificationResult && (
        <Notice
          tone={verificationResult.valid ? "pass" : "fail"}
          role={verificationResult.valid ? "status" : "alert"}
          title={verificationResult.valid ? "Passport verified" : "Verification failed"}
        >
          <span className="font-mono text-ink">{verificationResult.reason_code}</span>
          <span className="block">{verificationResult.description}</span>
        </Notice>
      )}

      {isLoading ? (
        <Card>
          <SkeletonBlock lines={6} label="Loading the passport" />
        </Card>
      ) : !passport ? (
        <EmptyState
          title="No passport yet"
          description="The passport is generated and signed when the run completes. Follow progress on the Agent timeline."
        />
      ) : (
        <>
          <Card as="div" flush>
            <dl className="divide-y divide-line">
              <div className="grid gap-1 px-6 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6">
                <dt className="text-sm text-ink-2">Dataset</dt>
                <dd className="space-y-1">
                  {Boolean(dataset.name) && <p className="text-base text-ink">{String(dataset.name)}</p>}
                  <Mono className="text-ink-2">{datasetHash || "Not recorded"}</Mono>
                </dd>
              </div>
              <div className="grid gap-1 px-6 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6">
                <dt className="text-sm text-ink-2">Policy</dt>
                <dd className="space-y-1">
                  <p className="text-base text-ink font-mono">{String(policy.id || "ml-sensitive-v1")}</p>
                  {policyHash && <Mono className="text-ink-2">{policyHash}</Mono>}
                </dd>
              </div>
              <div className="grid gap-1 px-6 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6">
                <dt className="text-sm text-ink-2">Signature</dt>
                <dd className="space-y-1">
                  <p className="text-base text-ink">
                    {String(signature.alg || "Ed25519")}
                    {keyId && <span className="text-ink-2"> · key {keyId.slice(0, 16)}</span>}
                  </p>
                  <Mono className="text-ink-2">{signatureValue || "Unsigned"}</Mono>
                </dd>
              </div>
              <div className="grid gap-1 px-6 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6">
                <dt className="text-sm text-ink-2">Human approval</dt>
                <dd className="text-base text-ink">
                  {isApproved ? (
                    <>
                      Approved by <span className="font-medium">{approver}</span>
                      {approvedAt && <span className="block text-sm text-ink-2 tabular-nums">{approvedAt}</span>}
                    </>
                  ) : (
                    <span className="text-ink-2">Pending</span>
                  )}
                </dd>
              </div>
            </dl>
          </Card>

          <Card
            title="Passport document"
            description={`${Object.keys(passport).length} top-level fields, in canonical JSON.`}
            actions={
              <>
                <Button variant="ghost" size="sm" onClick={handleCopyJson}>
                  {copied ? "Copied" : "Copy JSON"}
                </Button>
                <Button variant="ghost" size="sm" onClick={handleDownloadJson}>
                  Download
                </Button>
              </>
            }
          >
            <pre className="max-h-[480px] overflow-auto rounded bg-surface-2 p-4 font-mono text-sm leading-relaxed text-ink">
              {JSON.stringify(passport, null, 2)}
            </pre>
          </Card>
        </>
      )}

      {showApproveModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[rgba(28,24,21,0.45)]"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setShowApproveModal(false);
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="approve-title"
            aria-describedby="approve-desc"
            className="w-full max-w-md rounded-lg bg-surface border border-line shadow-overlay p-6 space-y-5"
          >
            <div className="space-y-1">
              <h2 id="approve-title" className="text-lg font-semibold text-ink">
                Approve release
              </h2>
              <p id="approve-desc" className="text-sm text-ink-2">
                Your identifier is written into the passport and the passport is re-signed. The previous signature is kept in the audit trail.
              </p>
            </div>

            <form onSubmit={handleConfirmApproval} className="space-y-5">
              <div className="space-y-2">
                <label htmlFor="approver" className="block text-sm font-medium text-ink">
                  Approver email or employee ID
                </label>
                <input
                  id="approver"
                  type="text"
                  value={approverEmail}
                  onChange={(e) => setApproverEmail(e.target.value)}
                  placeholder="auditor@enterprise.org"
                  className={`${inputClass} font-mono`}
                  autoFocus
                  required
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button type="button" variant="ghost" onClick={() => setShowApproveModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" loading={isApproving}>
                  {isApproving ? "Signing…" : "Approve and sign"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
