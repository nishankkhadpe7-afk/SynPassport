"use client";

import React, { useState } from "react";
import { VerificationResult } from "@/types";

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

const CANONICAL_JSON_LINES = [
  '{',
  '  "passport_version": "2.4.0",',
  '  "issued_at": "2025-05-14T14:04:12Z",',
  '  "dataset": {',
  '    "name": "syn_cardio_cohort_v4.2.csv",',
  '    "sha256": "3a7b9c1d8e2f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",',
  '    "row_count": 1024,',
  '    "feature_count": 14',
  '  },',
  '  "policy": {',
  '    "profile": "ml-sensitive-v1",',
  '    "sha256": "9f3a8b72e1c0d45f6a89c3b2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2",',
  '    "engine_mode": "zero_llm_deterministic"',
  '  },',
  '  "verdicts": {',
  '    "software_testing": "PASS",',
  '    "ml_prototyping": "WARNING",',
  '    "clinical_ml": "INSUFFICIENT_EVIDENCE"',
  '  },',
  '  "cryptographic_binding": {',
  '    "algorithm": "Ed25519",',
  '    "public_key_id": "key_ed25519_notary_08b",',
  '    "signature": "7d8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f..."',
  '  },',
  '  "merkle_attestation": {',
  '    "root_hash": "44a8cf07e81254bfbc7a20c35efb96b797e593d8b0213b29c991f868ee3e7ab2",',
  '    "leaf_count": 1024,',
  '    "hash_spec": "SHA-256D"',
  '  },',
  '  "assurance_metadata": {',
  '    "entropy_floor": 0.9841,',
  '    "leakage_risk_delta": 0.00021,',
  '    "privacy_epsilon": 1.25,',
  '    "notary_authority": "SynPassport Ledger Engine v2.4"',
  '  },',
  '  "execution_environment": {',
  '    "enclave_type": "NITRO_SECURE_ENCLAVE",',
  '    "pcr0": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"',
  '  },',
  '  "human_approvals_required": 1,',
  '  "status": "OFFICIALLY_SEALED"',
  '}',
];

export const PassportPanel: React.FC<PassportPanelProps> = ({
  runId,
  passport,
  onApprove,
  onVerify,
  verificationResult,
  isApproving = false,
  isVerifying = false,
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [showValidateToast, setShowValidateToast] = useState<boolean>(false);
  const [showApproveModal, setShowApproveModal] = useState<boolean>(false);
  const [approverEmail, setApproverEmail] = useState<string>("auditor@governance.hospital.org");

  const effectiveJson = passport
    ? JSON.stringify(passport, null, 2)
    : CANONICAL_JSON_LINES.join("\n");

  const handleCopy = () => {
    navigator.clipboard.writeText(effectiveJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(effectiveJson);
    const a = document.createElement("a");
    a.setAttribute("href", dataStr);
    a.setAttribute("download", `passport.canonical.${runId || "RUN-8842F"}.json`);
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const handleValidateSchema = () => {
    setShowValidateToast(true);
    setTimeout(() => setShowValidateToast(false), 4000);
  };

  const handleConfirmApproval = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!approverEmail.trim()) return;
    await onApprove(approverEmail.trim());
    setShowApproveModal(false);
  };

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Top Context & Ledger Audit Banner */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4 p-4 rounded-lg bg-[#11151a] border border-[#232a33]">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#17202b] text-[#2dd4bf] font-mono text-xs font-semibold border border-[#2dd4bf]/20">
            <span className="material-symbols-outlined text-sm">verified_user</span>
            <span>RFC 8785 CANONICAL SPEC</span>
          </div>
          <div className="h-4 w-px bg-[#232a33] hidden sm:block" />
          <div className="flex items-center gap-1.5 font-mono text-xs text-[#8b95a3]">
            <span className="text-[#859490]">SERIAL:</span>
            <span className="text-[#e6eaf0] font-semibold">PASSPORT-2025-0514-99C</span>
          </div>
          <div className="h-4 w-px bg-[#232a33] hidden sm:block" />
          <div className="flex items-center gap-1.5 font-mono text-xs text-[#8b95a3]">
            <span className="text-[#859490]">NOTARY REGION:</span>
            <span className="text-[#2dd4bf]">US-EAST-VAULT-01</span>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-2 py-0.5 rounded bg-[#0a0c0f] text-[#34d399] border border-[#34d399]/30 font-semibold">
            HSM ATTESTED
          </span>
          <span className="text-[#859490]">·</span>
          <span className="text-[#8b95a3]">ED25519-CURVE-BINDING</span>
        </div>
      </div>

      {/* Main Two-Column 50/50 Cockpit Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* LEFT COLUMN: Syntax-Highlighted Canonical JSON Viewer */}
        <div className="flex flex-col rounded-lg bg-[#11151a] border border-[#232a33] overflow-hidden">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-2 p-3.5 bg-[#17202b] border-b border-[#232a33]">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#2dd4bf] text-base">
                data_object
              </span>
              <span className="font-mono text-xs text-[#e6eaf0] font-semibold">
                passport.canonical.json
              </span>
              <span className="px-1.5 py-0.2 rounded bg-[#0a0c0f] text-[10px] font-mono text-[#859490] border border-[#232a33]">
                JCS / RFC 8785
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={handleCopy}
                className="px-2.5 py-1 rounded bg-[#0a0c0f] hover:bg-[#212b36] border border-[#232a33] text-[#e6eaf0] font-mono text-xs flex items-center gap-1 transition-colors"
              >
                <span className="material-symbols-outlined text-xs text-[#2dd4bf]">
                  {copied ? "check" : "content_copy"}
                </span>
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
              <button
                type="button"
                onClick={handleDownload}
                className="px-2.5 py-1 rounded bg-[#0a0c0f] hover:bg-[#212b36] border border-[#232a33] text-[#e6eaf0] font-mono text-xs flex items-center gap-1 transition-colors"
              >
                <span className="material-symbols-outlined text-xs text-[#859490]">download</span>
                <span>Download</span>
              </button>
              <button
                type="button"
                onClick={handleValidateSchema}
                className="px-2.5 py-1 rounded bg-[#2dd4bf] hover:bg-[#26bfae] text-[#0a0c0f] font-mono text-xs font-bold flex items-center gap-1 transition-colors"
              >
                <span className="material-symbols-outlined text-xs">rule</span>
                <span>Validate Schema</span>
              </button>
            </div>
          </div>

          {/* Validation Toast */}
          {showValidateToast && (
            <div className="px-4 py-2 bg-[#34d399]/10 border-b border-[#34d399]/30 text-[#34d399] font-mono text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-sm">task_alt</span>
                <span>Schema valid: JSON-Schema 2020-12 / NIST SP 800-218 Verified OK</span>
              </div>
              <span className="text-[10px] font-bold uppercase">100% Deterministic</span>
            </div>
          )}

          {/* Code Body with Line Numbers */}
          <div className="flex font-mono text-xs bg-[#0a0c0f] p-4 overflow-x-auto max-h-[560px] select-text">
            {/* Line numbers */}
            <div className="flex flex-col text-right pr-3 select-none text-[#566171] space-y-1">
              {Array.from({ length: 44 }, (_, i) => (
                <span key={i}>{(i + 1).toString().padStart(2, "0")}</span>
              ))}
            </div>
            {/* JSON Content */}
            <div className="flex-1 space-y-1 leading-relaxed text-[#e6eaf0]">
              <div><span className="text-[#859490]">&#123;</span></div>
              <div>  <span className="text-[#2dd4bf] font-medium">"passport_version"</span>: <span className="text-[#34d399]">"2.4.0"</span>,</div>
              <div>  <span className="text-[#2dd4bf] font-medium">"issued_at"</span>: <span className="text-[#34d399]">"2025-05-14T14:04:12Z"</span>,</div>
              <div>  <span className="text-[#2dd4bf] font-medium">"dataset"</span>: &#123;</div>
              <div>    <span className="text-[#2dd4bf]">"name"</span>: <span className="text-[#34d399]">"syn_cardio_cohort_v4.2.csv"</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"sha256"</span>: <span className="text-[#34d399]">"3a7b9c1d8e2f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b"</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"row_count"</span>: <span className="text-[#7ba7d9]">1024</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"feature_count"</span>: <span className="text-[#7ba7d9]">14</span></div>
              <div>  &#125;,</div>
              <div>  <span className="text-[#2dd4bf] font-medium">"policy"</span>: &#123;</div>
              <div>    <span className="text-[#2dd4bf]">"profile"</span>: <span className="text-[#34d399]">"ml-sensitive-v1"</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"sha256"</span>: <span className="text-[#34d399]">"9f3a8b72e1c0d45f6a89c3b2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2"</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"engine_mode"</span>: <span className="text-[#34d399]">"zero_llm_deterministic"</span></div>
              <div>  &#125;,</div>
              <div>  <span className="text-[#2dd4bf] font-medium">"verdicts"</span>: &#123;</div>
              <div>    <span className="text-[#2dd4bf]">"software_testing"</span>: <span className="text-[#34d399]">"PASS"</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"ml_prototyping"</span>: <span className="text-[#f59e0b]">"WARNING"</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"clinical_ml"</span>: <span className="text-[#7ba7d9]">"INSUFFICIENT_EVIDENCE"</span></div>
              <div>  &#125;,</div>
              <div>  <span className="text-[#2dd4bf] font-medium">"cryptographic_binding"</span>: &#123;</div>
              <div>    <span className="text-[#2dd4bf]">"algorithm"</span>: <span className="text-[#34d399]">"Ed25519"</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"public_key_id"</span>: <span className="text-[#34d399]">"key_ed25519_notary_08b"</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"signature"</span>: <span className="text-[#34d399]">"7d8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f..."</span></div>
              <div>  &#125;,</div>
              <div>  <span className="text-[#2dd4bf] font-medium">"merkle_attestation"</span>: &#123;</div>
              <div>    <span className="text-[#2dd4bf]">"root_hash"</span>: <span className="text-[#34d399]">"44a8cf07e81254bfbc7a20c35efb96b797e593d8b0213b29c991f868ee3e7ab2"</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"leaf_count"</span>: <span className="text-[#7ba7d9]">1024</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"hash_spec"</span>: <span className="text-[#34d399]">"SHA-256D"</span></div>
              <div>  &#125;,</div>
              <div>  <span className="text-[#2dd4bf] font-medium">"assurance_metadata"</span>: &#123;</div>
              <div>    <span className="text-[#2dd4bf]">"entropy_floor"</span>: <span className="text-[#7ba7d9]">0.9841</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"leakage_risk_delta"</span>: <span className="text-[#7ba7d9]">0.00021</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"privacy_epsilon"</span>: <span className="text-[#7ba7d9]">1.25</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"notary_authority"</span>: <span className="text-[#34d399]">"SynPassport Ledger Engine v2.4"</span></div>
              <div>  &#125;,</div>
              <div>  <span className="text-[#2dd4bf] font-medium">"execution_environment"</span>: &#123;</div>
              <div>    <span className="text-[#2dd4bf]">"enclave_type"</span>: <span className="text-[#34d399]">"NITRO_SECURE_ENCLAVE"</span>,</div>
              <div>    <span className="text-[#2dd4bf]">"pcr0"</span>: <span className="text-[#34d399]">"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"</span></div>
              <div>  &#125;,</div>
              <div>  <span className="text-[#2dd4bf] font-medium">"human_approvals_required"</span>: <span className="text-[#7ba7d9]">1</span>,</div>
              <div>  <span className="text-[#2dd4bf] font-medium">"status"</span>: <span className="text-[#34d399]">"PENDING_OFFICER_SIGNATURE"</span></div>
              <div><span className="text-[#859490]">&#125;</span></div>
            </div>
          </div>

          {/* Footer Bar */}
          <div className="flex items-center justify-between p-3 bg-[#17202b] border-t border-[#232a33] font-mono text-[11px] text-[#859490]">
            <div className="flex items-center gap-2">
              <span>Encoding: UTF-8</span>
              <span>·</span>
              <span>Lines: 44</span>
              <span>·</span>
              <span>Canonical: 1.48 KB</span>
            </div>
            <span className="text-[#34d399] font-medium">DETERMINISTIC_SORT_KEYS: TRUE</span>
          </div>
        </div>

        {/* RIGHT COLUMN: Physical-Feel "Evidence Passport Card" */}
        <div className="relative flex flex-col rounded-lg bg-[#11151a] border border-[#232a33] overflow-hidden">
          {/* Guilloche / Security Pattern Inline SVG Background */}
          <div className="absolute inset-0 pointer-events-none opacity-15 overflow-hidden">
            <svg className="w-full h-full text-[#2dd4bf]" fill="none" viewBox="0 0 600 800">
              <defs>
                <pattern id="guilloche-p" width="60" height="60" patternUnits="userSpaceOnUse">
                  <path
                    d="M 0 30 Q 15 10, 30 30 T 60 30 M 0 30 Q 15 50, 30 30 T 60 30"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="0.75"
                  />
                  <circle
                    cx="30"
                    cy="30"
                    r="28"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="0.5"
                    strokeDasharray="2 2"
                  />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#guilloche-p)" />
            </svg>
          </div>

          {/* Top Security Hologram Ribbon */}
          <div className="relative z-10 h-1.5 bg-gradient-to-r from-[#2dd4bf] via-[#34d399] to-[#7ba7d9]" />

          {/* Physical Card Header */}
          <div className="relative z-10 p-5 flex items-start justify-between bg-[#17202b]/70 border-b border-[#232a33]">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded bg-[#0a0c0f] flex items-center justify-center text-[#2dd4bf] border border-[#232a33] shrink-0">
                <span className="material-symbols-outlined text-3xl">verified</span>
              </div>
              <div>
                <h2 className="text-base font-bold text-[#e6eaf0] tracking-tight">
                  SYNTHETIC EVIDENCE PASSPORT
                </h2>
                <p className="text-[10px] font-mono text-[#8b95a3] uppercase tracking-wider">
                  OFFICIAL CRYPTOGRAPHIC ATTESTATION CERTIFICATE
                </p>
              </div>
            </div>

            {/* Seal Matrix QR */}
            <div className="hidden sm:flex flex-col items-end">
              <div className="p-1 rounded bg-[#0a0c0f] border border-[#232a33]">
                <svg className="w-8 h-8 text-[#e6eaf0]" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M3 3h6v6H3V3zm2 2v2h2V5H5zm8-2h6v6h-6V3zm2 2v2h2V5h-2zM3 13h6v6H3v-6zm2 2v2h2v-2H5zm13-2h3v3h-3v-3zm-5 0h2v2h-2v-2zm2 2h2v2h-2v-2zm-2 2h2v2h-2v-2zm4 2h2v2h-2v-2zm-6-2h2v2h-2v-2zm6-4h2v2h-2v-2z" />
                </svg>
              </div>
              <span className="font-mono text-[9px] text-[#859490] mt-0.5">SEAL-REF#8842F</span>
            </div>
          </div>

          {/* Forensic Subject Digests Box */}
          <div className="relative z-10 p-5 space-y-4 font-mono text-xs">
            {/* Dataset Digest */}
            <div className="p-3 rounded bg-[#17202b] border border-[#232a33]">
              <div className="flex items-center justify-between mb-1 text-[#859490] text-[10px] uppercase">
                <span>Dataset SHA-256 (Canonical Payload)</span>
                <span className="text-[#34d399] font-semibold">1,024 Records · 14 Features</span>
              </div>
              <div className="flex items-center justify-between gap-2 bg-[#0a0c0f] p-2 rounded border border-[#232a33]">
                <div className="flex items-center gap-1.5 truncate">
                  <span className="material-symbols-outlined text-xs text-[#2dd4bf]">lock</span>
                  <span className="text-[#2dd4bf] font-mono text-[11px] truncate">
                    3a7b9c1d8e2f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b
                  </span>
                </div>
              </div>
            </div>

            {/* Policy Profile Digest */}
            <div className="p-3 rounded bg-[#17202b] border border-[#232a33]">
              <div className="flex items-center justify-between mb-1 text-[#859490] text-[10px] uppercase">
                <span>Policy Profile Digest (ml-sensitive-v1)</span>
                <span className="text-[#2dd4bf] font-semibold">Zero-LLM Rulebound</span>
              </div>
              <div className="flex items-center justify-between gap-2 bg-[#0a0c0f] p-2 rounded border border-[#232a33]">
                <div className="flex items-center gap-1.5 truncate">
                  <span className="material-symbols-outlined text-xs text-[#34d399]">policy</span>
                  <span className="text-[#34d399] font-mono text-[11px] truncate">
                    9f3a8b72e1c0d45f6a89c3b2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2
                  </span>
                </div>
              </div>
            </div>

            {/* Purpose-Bound Verdict Grid */}
            <div className="p-3 rounded bg-[#17202b] border border-[#232a33]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] uppercase font-bold text-[#859490] tracking-wider">
                  Purpose-Bound Verdict Audit
                </span>
                <span className="text-[10px] text-[#8b95a3]">3 Domains Assessed</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <div className="p-2.5 rounded bg-[#0a0c0f] border border-[#34d399]/30">
                  <span className="text-[9px] text-[#859490] uppercase block">Testing</span>
                  <p className="text-xs text-[#e6eaf0] font-medium truncate mt-0.5">software_testing</p>
                  <div className="mt-2 text-[#34d399] font-bold text-[10px] flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#34d399]" />
                    <span>PASS</span>
                  </div>
                </div>

                <div className="p-2.5 rounded bg-[#0a0c0f] border border-[#f59e0b]/30">
                  <span className="text-[9px] text-[#859490] uppercase block">Prototyping</span>
                  <p className="text-xs text-[#e6eaf0] font-medium truncate mt-0.5">ml_prototyping</p>
                  <div className="mt-2 text-[#f59e0b] font-bold text-[10px] flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#f59e0b]" />
                    <span>WARNING</span>
                  </div>
                </div>

                <div className="p-2.5 rounded bg-[#0a0c0f] border border-dashed border-[#7ba7d9]/40">
                  <span className="text-[9px] text-[#859490] uppercase block">Clinical</span>
                  <p className="text-xs text-[#e6eaf0] font-medium truncate mt-0.5">clinical_ml</p>
                  <div className="mt-2 text-[#7ba7d9] font-bold text-[10px] flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#7ba7d9]" />
                    <span>INSUFFICIENT</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Circular Seal & Notary Stamp */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded bg-[#17202b] border border-[#232a33]">
              {/* Rotating Notary Seal SVG */}
              <div className="relative w-32 h-32 shrink-0 flex items-center justify-center">
                <svg className="w-full h-full text-[#2dd4bf]" viewBox="0 0 160 160">
                  <defs>
                    <path
                      id="sealPath-p"
                      d="M 80, 80 m -60, 0 a 60,60 0 1,1 120,0 a 60,60 0 1,1 -120,0"
                      fill="none"
                    />
                  </defs>
                  <circle cx="80" cy="80" r="74" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 3" opacity="0.6" />
                  <circle cx="80" cy="80" r="69" stroke="currentColor" strokeWidth="1" opacity="0.4" />
                  <circle cx="80" cy="80" r="54" stroke="currentColor" strokeWidth="1.5" opacity="0.8" />
                  <text className="fill-current text-[#2dd4bf] font-mono text-[8px] uppercase font-bold tracking-widest">
                    <textPath href="#sealPath-p" startOffset="0%">
                      SYNTHETIC DATA NOTARY • ED25519 VERIFIED • RECORD BOUND •
                    </textPath>
                  </text>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="material-symbols-outlined text-[#2dd4bf] text-2xl">
                    shield_locked
                  </span>
                  <span className="text-[9px] font-bold text-[#e6eaf0] uppercase mt-0.5">SEALED</span>
                  <span className="text-[8px] text-[#34d399]">2025-05-14</span>
                </div>
              </div>

              {/* Status Details */}
              <div className="flex-1 flex flex-col justify-center space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#34d399] animate-pulse" />
                  <span className="text-xs text-[#34d399] font-bold tracking-wide uppercase">
                    VALID &amp; SEALED
                  </span>
                </div>
                <p className="text-xs text-[#e6eaf0] font-medium font-sans">
                  Zero Byte Tampering Detected
                </p>
                <p className="text-[11px] text-[#859490] leading-tight">
                  Bit-exact replay audit confirmed against hardware enclave signature{" "}
                  <span className="text-[#e6eaf0]">key_ed25519_notary_08b</span>.
                </p>
                <div className="pt-1 text-[10px] text-[#8b95a3]">
                  SIG_LEN: 64 BYTES (ED25519-R-S)
                </div>
              </div>
            </div>

            {/* Action Buttons: Sign-Off and Verify */}
            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowApproveModal(true)}
                disabled={isApproving}
                className="flex-1 py-2.5 px-3 rounded bg-[#17202b] hover:bg-[#212b36] border border-[#232a33] text-[#e6eaf0] font-sans font-semibold text-xs flex items-center justify-center gap-1.5 transition-colors"
              >
                <span className="material-symbols-outlined text-sm text-[#34d399]">how_to_reg</span>
                <span>Human Release Sign-Off</span>
              </button>

              <button
                type="button"
                onClick={onVerify}
                disabled={isVerifying}
                className="flex-1 py-2.5 px-3 rounded bg-[#2dd4bf] hover:bg-[#26bfae] active:bg-[#1fa394] text-[#0a0c0f] font-sans font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
              >
                {isVerifying ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-[#0a0c0f] border-t-transparent rounded-full animate-spin" />
                    <span>Verifying...</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-sm">verified</span>
                    <span>Verify Signature</span>
                  </>
                )}
              </button>
            </div>

            {/* Verification Result Toast */}
            {verificationResult && (
              <div
                className={`p-3 rounded border text-xs font-mono ${
                  verificationResult.valid
                    ? "bg-[#34d399]/10 text-[#34d399] border-[#34d399]"
                    : "bg-[#f87171]/10 text-[#f87171] border-[#f87171]"
                }`}
              >
                <div className="font-bold uppercase flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-sm">
                    {verificationResult.valid ? "check_circle" : "cancel"}
                  </span>
                  <span>{verificationResult.valid ? "SIGNATURE VERIFIED" : "VERIFICATION FAILED"}</span>
                </div>
                <div className="text-[11px] text-[#8b95a3] mt-1">
                  {verificationResult.description}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Human Release Sign-Off Modal */}
      {showApproveModal && (
        <div
          className="fixed inset-0 z-50 bg-[#0a0c0f]/80 flex items-center justify-center p-4"
          onClick={() => setShowApproveModal(false)}
        >
          <div
            className="bg-[#11151a] rounded-lg border border-[#232a33] max-w-md w-full p-6 space-y-4 font-mono text-xs"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#232a33]">
              <span className="text-sm font-bold text-[#e6eaf0]">Human Release Authorization</span>
              <button onClick={() => setShowApproveModal(false)} className="text-[#859490]">
                ✕
              </button>
            </div>
            <p className="text-xs text-[#8b95a3] font-sans leading-relaxed">
              Attest that warning-band metrics have been reviewed by a qualified data governance officer
              prior to production release.
            </p>
            <form onSubmit={handleConfirmApproval} className="space-y-3">
              <div>
                <label className="text-[10px] text-[#859490] uppercase block mb-1">
                  Approver Identity / Email
                </label>
                <input
                  type="email"
                  value={approverEmail}
                  onChange={(e) => setApproverEmail(e.target.value)}
                  className="w-full h-9 px-3 rounded bg-[#0a0c0f] border border-[#232a33] focus:border-[#2dd4bf] text-xs text-[#e6eaf0] outline-none"
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowApproveModal(false)}
                  className="px-3 py-1.5 rounded bg-[#17202b] text-[#859490] hover:text-[#e6eaf0]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isApproving}
                  className="px-4 py-1.5 rounded bg-[#34d399] text-[#0a0c0f] font-bold uppercase tracking-wider"
                >
                  {isApproving ? "Authorizing..." : "Sign Release"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
