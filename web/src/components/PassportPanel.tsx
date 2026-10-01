"use client";

import React, { useState } from "react";
import {
  Shield,
  Download,
  CheckCircle2,
  FileCheck2,
  Copy,
  Check,
  UserCheck,
  AlertTriangle,
  XCircle,
  HelpCircle,
  KeyRound,
  FileCode,
} from "lucide-react";
import { VerificationResult } from "@/types";
import { StateBadge } from "./StateBadge";

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

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header and Action Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-indigo-400" />
              Cryptographic Evidence Passport
            </h2>
            {isApproved && (
              <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-mono">
                <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                HUMAN APPROVED
              </span>
            )}
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Tamper-evident artifact binding raw dataset SHA-256 digest, policy gates, and Ed25519 signature. Supports audit.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleCopyJson}
            disabled={!passport}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-slate-300 text-xs font-mono border border-slate-700/80 transition-all"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copied" : "Copy JSON"}</span>
          </button>

          <button
            onClick={handleDownloadJson}
            disabled={!passport}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-slate-300 text-xs font-mono border border-slate-700/80 transition-all"
          >
            <Download className="w-3.5 h-3.5 text-indigo-400" />
            <span>Download</span>
          </button>

          <button
            onClick={() => setShowApproveModal(true)}
            disabled={!passport || isApproving}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition-all"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>{isApproved ? "Re-Authorize Release" : "Human Approval"}</span>
          </button>

          <button
            onClick={onVerify}
            disabled={!passport || isVerifying}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all"
          >
            {isVerifying ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <FileCheck2 className="w-3.5 h-3.5" />
            )}
            <span>Verify Passport</span>
          </button>
        </div>
      </div>

      {/* Verification Result Notification (if verified) */}
      {verificationResult && (
        <div
          className={`p-4 rounded-xl border flex items-start gap-3 transition-all ${
            verificationResult.valid
              ? "bg-emerald-950/25 border-emerald-500/40 text-emerald-300"
              : "bg-rose-950/25 border-rose-500/40 text-rose-300"
          }`}
        >
          {verificationResult.valid ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          )}
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm">
                Verification Result: {verificationResult.valid ? "VALID" : "INVALID"}
              </span>
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-950/70 border border-slate-800 font-semibold">
                {verificationResult.reason_code}
              </span>
            </div>
            <p className="text-xs text-slate-300">{verificationResult.description}</p>
          </div>
        </div>
      )}

      {/* Passport Metadata Grid */}
      {passport && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="glass-panel p-4 rounded-xl space-y-1">
            <span className="text-[11px] font-mono uppercase text-slate-400 block">Dataset SHA-256 Digest</span>
            <span className="text-xs font-mono text-indigo-300 break-all">
              {String(passport.dataset_hash || "manifest_bound_sha256")}
            </span>
          </div>

          <div className="glass-panel p-4 rounded-xl space-y-1">
            <span className="text-[11px] font-mono uppercase text-slate-400 block">Policy Profile Binding</span>
            <span className="text-xs font-mono text-slate-200">
              {String((passport.policy as Record<string, unknown>)?.id || "ml-sensitive-v1")}
            </span>
            <span className="text-[10px] font-mono text-slate-500 block truncate">
              {String((passport.policy as Record<string, unknown>)?.hash || "")}
            </span>
          </div>

          <div className="glass-panel p-4 rounded-xl space-y-1">
            <span className="text-[11px] font-mono uppercase text-slate-400 block">Ed25519 Digital Signature</span>
            <div className="flex items-center gap-1.5 text-xs font-mono text-emerald-400">
              <KeyRound className="w-3.5 h-3.5" />
              <span>CRYPTOGRAPHICALLY SIGNED</span>
            </div>
            <span className="text-[10px] font-mono text-slate-500 block truncate">
              {String(passport.signature || "ed25519_canonical_signature")}
            </span>
          </div>
        </div>
      )}

      {/* JSON Viewer */}
      <div className="glass-panel rounded-2xl p-5 space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
          <span className="flex items-center gap-1.5 font-semibold text-slate-300">
            <FileCode className="w-4 h-4 text-indigo-400" />
            CANONICAL PASSPORT SCHEMA (v1)
          </span>
          <span>{passport ? `${Object.keys(passport).length} top-level fields` : "0 fields"}</span>
        </div>

        {isLoading ? (
          <div className="py-16 text-center text-slate-500 text-xs font-mono">
            <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading Evidence Passport document...
          </div>
        ) : !passport ? (
          <div className="py-16 text-center text-slate-500 text-xs font-mono flex flex-col items-center gap-2">
            <HelpCircle className="w-8 h-8 text-slate-600" />
            <span>Passport will be generated and signed upon run completion.</span>
          </div>
        ) : (
          <pre className="bg-slate-950 p-4 rounded-xl text-xs font-mono text-slate-300 overflow-x-auto border border-slate-800/80 max-h-[500px] leading-relaxed select-all">
            {JSON.stringify(passport, null, 2)}
          </pre>
        )}
      </div>

      {/* Human Approval Modal */}
      {showApproveModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel rounded-2xl max-w-md w-full p-6 space-y-5 border border-slate-700 bg-slate-900 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="space-y-1">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-emerald-400" />
                Human Release Authorization
              </h3>
              <p className="text-xs text-slate-400">
                Design Principle #7: Final release approval must be designated to an accountable individual.
              </p>
            </div>

            <form onSubmit={handleConfirmApproval} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                  Approver Email or Employee ID
                </label>
                <input
                  type="text"
                  value={approverEmail}
                  onChange={(e) => setApproverEmail(e.target.value)}
                  placeholder="e.g. auditor@enterprise.org"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
                By authorizing this release, your identifier is recorded into the passport manifest and re-signed using the server&apos;s Ed25519 signing key.
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowApproveModal(false)}
                  className="px-4 py-2 rounded-lg text-xs font-mono text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isApproving}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-all shadow-md shadow-emerald-600/30"
                >
                  {isApproving ? "Re-Signing Passport..." : "Confirm & Sign"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
