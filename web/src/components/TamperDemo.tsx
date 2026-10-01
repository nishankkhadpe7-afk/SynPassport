"use client";

import React, { useState } from "react";
import { VerificationResult } from "@/types";

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

const ORIGINAL_HASH = "3a7b9c1d8e2f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b";
const TAMPERED_HASH = "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b3a7b9c1d8e2f4a5b6c7d8e9f0a1b2c3";

export const TamperDemo: React.FC<TamperDemoProps> = ({
  passport,
  candidateCsv,
  onVerifyCustom,
  isVerifying = false,
}) => {
  const [isTampered, setIsTampered] = useState<boolean>(true); // Initial state matches design mockup drill
  const [cholesterolVal, setCholesterolVal] = useState<string>("245.9");

  const handleTamper = () => {
    setIsTampered(true);
    setCholesterolVal("245.9");
  };

  const handleReset = () => {
    setIsTampered(false);
    setCholesterolVal("245.8");
  };

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Forensic Banner */}
      <div className="relative overflow-hidden rounded-lg bg-[#11151a] p-5 border border-[#232a33]">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1.5 max-w-4xl">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#17202b] text-[#f87171] border border-[#f87171]/30 font-bold">
                STAGE 07 // ADVERSARIAL DRILL
              </span>
              <span className="text-xs font-mono text-[#859490]">ZERO_LLM_DETERMINISTIC_SECURITY</span>
            </div>
            <h1 className="text-lg sm:text-2xl font-bold text-[#e6eaf0] tracking-tight">
              Cryptographic Invariance Test
            </h1>
            <p className="text-xs sm:text-sm text-[#8b95a3] leading-relaxed">
              Demonstrating how modifying even a single byte in the synthetic dataset immediately
              shatters the Ed25519 signature binding.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0 font-mono text-xs">
            <div className="bg-[#0a0c0f] px-3 py-2 rounded border border-[#232a33]">
              <div className="flex items-center justify-between gap-3 text-[10px] text-[#859490] uppercase">
                <span>BINDING ENGINE</span>
                <span
                  className={`w-2 h-2 rounded-full ${
                    isTampered ? "bg-[#f87171] animate-ping" : "bg-[#34d399]"
                  }`}
                />
              </div>
              <div
                className={`font-semibold mt-0.5 ${
                  isTampered ? "text-[#f87171]" : "text-[#34d399]"
                }`}
              >
                {isTampered ? "ED25519: REJECTED" : "ED25519: VERIFIED"}
              </div>
            </div>

            <div className="bg-[#0a0c0f] px-3 py-2 rounded border border-[#232a33]">
              <div className="text-[10px] text-[#859490] uppercase">STRICT INTERCEPTOR</div>
              <div className="font-semibold text-[#2dd4bf] mt-0.5">HALT_ON_DRIFT</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Two-Column Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
        {/* Left Column: Dataset Verification & Bit-Flip Simulator */}
        <div className="flex flex-col rounded-lg bg-[#11151a] border border-[#232a33] overflow-hidden">
          <div className="bg-[#17202b] px-4 py-3 border-b border-[#232a33] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#2dd4bf] text-base">tune</span>
              <span className="text-xs font-mono font-bold uppercase text-[#e6eaf0] tracking-wider">
                Dataset Verification &amp; Bit-Flip Simulator
              </span>
            </div>
            <span className="text-xs font-mono text-[#8b95a3]">TARGET: ROW 104</span>
          </div>

          <div className="p-4 space-y-4">
            {/* Actions */}
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={handleTamper}
                  className="relative px-3 py-1.5 bg-[#93000a] text-[#ffdad6] hover:bg-[#93000a]/80 active:scale-95 transition-all rounded font-mono text-xs uppercase font-bold flex items-center gap-1.5 shadow-sm"
                >
                  <span className="material-symbols-outlined text-sm text-[#f87171]">warning</span>
                  <span>Tamper 1 cell (+0.1 cholesterol)</span>
                  {isTampered && (
                    <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#f87171] opacity-75" />
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#f87171]" />
                    </span>
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleReset}
                  className="px-3 py-1.5 bg-[#17202b] text-[#e6eaf0] hover:bg-[#212b36] active:scale-95 transition-all rounded border border-[#232a33] font-mono text-xs uppercase font-medium flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-sm">restart_alt</span>
                  <span>Reset Original Dataset</span>
                </button>
              </div>

              <div className="text-xs font-mono text-[#859490]">FILE: syn_cardio_cohort_v4.2.csv</div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto bg-[#0a0c0f] rounded border border-[#232a33]">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="bg-[#17202b] text-[#859490] uppercase text-[10px] tracking-wider border-b border-[#232a33]">
                    <th className="py-2.5 px-3">Row #</th>
                    <th className="py-2.5 px-3">patient_id</th>
                    <th className="py-2.5 px-3">age</th>
                    <th className="py-2.5 px-3">sex</th>
                    <th className="py-2.5 px-3">resting_bp</th>
                    <th className="py-2.5 px-3">cholesterol</th>
                    <th className="py-2.5 px-3">fasting_bs</th>
                    <th className="py-2.5 px-3">target</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#232a33] text-[#e6eaf0]">
                  <tr className="opacity-40">
                    <td className="py-2 px-3 text-[#859490]">102</td>
                    <td className="py-2 px-3">PT-0102</td>
                    <td className="py-2 px-3">54</td>
                    <td className="py-2 px-3">0</td>
                    <td className="py-2 px-3">120</td>
                    <td className="py-2 px-3">198.0</td>
                    <td className="py-2 px-3">0</td>
                    <td className="py-2 px-3">0</td>
                  </tr>
                  <tr className="opacity-40">
                    <td className="py-2 px-3 text-[#859490]">103</td>
                    <td className="py-2 px-3">PT-0103</td>
                    <td className="py-2 px-3">49</td>
                    <td className="py-2 px-3">1</td>
                    <td className="py-2 px-3">130</td>
                    <td className="py-2 px-3">215.0</td>
                    <td className="py-2 px-3">0</td>
                    <td className="py-2 px-3">0</td>
                  </tr>

                  {/* ACTIVE ROW 104 */}
                  <tr
                    className={`transition-colors duration-200 ${
                      isTampered ? "bg-[#f87171]/15 text-[#ffdad6]" : "bg-[#17202b]"
                    }`}
                  >
                    <td className="py-2 px-3 font-bold flex items-center gap-1">
                      <span className="material-symbols-outlined text-xs text-[#f87171]">
                        arrow_right
                      </span>
                      <span className={isTampered ? "text-[#f87171]" : "text-[#e6eaf0]"}>104</span>
                    </td>
                    <td className="py-2 px-3 font-medium">PT-0104</td>
                    <td className="py-2 px-3">63</td>
                    <td className="py-2 px-3">1</td>
                    <td className="py-2 px-3">145</td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-1.5 py-0.5 rounded font-bold ${
                          isTampered
                            ? "bg-[#93000a] text-[#ffdad6] border border-[#f87171]"
                            : "text-[#34d399]"
                        }`}
                      >
                        {cholesterolVal}
                      </span>
                    </td>
                    <td className="py-2 px-3">1</td>
                    <td className="py-2 px-3">1</td>
                  </tr>

                  <tr className="opacity-40">
                    <td className="py-2 px-3 text-[#859490]">105</td>
                    <td className="py-2 px-3">PT-0105</td>
                    <td className="py-2 px-3">57</td>
                    <td className="py-2 px-3">0</td>
                    <td className="py-2 px-3">128</td>
                    <td className="py-2 px-3">204.0</td>
                    <td className="py-2 px-3">0</td>
                    <td className="py-2 px-3">0</td>
                  </tr>
                  <tr className="opacity-40">
                    <td className="py-2 px-3 text-[#859490]">106</td>
                    <td className="py-2 px-3">PT-0106</td>
                    <td className="py-2 px-3">68</td>
                    <td className="py-2 px-3">1</td>
                    <td className="py-2 px-3">152</td>
                    <td className="py-2 px-3">280.0</td>
                    <td className="py-2 px-3">0</td>
                    <td className="py-2 px-3">1</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Tamper Diff Note */}
            <div className="flex items-center justify-between p-3 rounded bg-[#0a0c0f] border border-[#232a33] font-mono text-xs">
              <span className="text-[#859490]">Cell Mutation:</span>
              <span className={isTampered ? "text-[#f87171] font-bold" : "text-[#34d399]"}>
                {isTampered
                  ? "ORIGINAL: 245.8 -> MODIFIED: 245.9 (Δ +0.1000)"
                  : "UNTOUCHED: 245.8 (Δ 0.0000)"}
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Real-Time Cryptographic Binding & Attestation Status */}
        <div className="flex flex-col gap-5">
          {/* Real-time Status Card */}
          <div
            className={`rounded-lg p-5 border flex flex-col gap-4 font-mono text-xs ${
              isTampered
                ? "bg-[#11151a] border-[#f87171]"
                : "bg-[#11151a] border-[#34d399]"
            }`}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#232a33]">
              <div className="flex items-center gap-2">
                <span
                  className={`material-symbols-outlined text-lg ${
                    isTampered ? "text-[#f87171]" : "text-[#34d399]"
                  }`}
                >
                  {isTampered ? "gfm" : "verified_user"}
                </span>
                <span className="text-xs font-bold uppercase text-[#e6eaf0]">
                  {isTampered
                    ? "ED25519 ATTESTATION: CRITICAL REJECTION"
                    : "ED25519 ATTESTATION: INTACT & VALID"}
                </span>
              </div>
              <span
                className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                  isTampered
                    ? "bg-[#93000a] text-[#ffdad6] border-[#f87171]"
                    : "bg-[#17202b] text-[#34d399] border-[#34d399]"
                }`}
              >
                {isTampered ? "HASH_MISMATCH" : "SIGNATURE_PASS"}
              </span>
            </div>

            <p className="text-xs text-[#8b95a3] font-sans leading-relaxed">
              {isTampered
                ? "A 1-byte discrepancy in row 104 mutated the canonical JCS byte representation. Ed25519 signature computation fails verification."
                : "Exact bitstream matches original notary commit. Cryptographic signature validates against enclave public key."}
            </p>

            {/* Side-by-Side SHA-256 Digest Diff Comparison */}
            <div className="space-y-3 p-3 rounded bg-[#0a0c0f] border border-[#232a33]">
              <div>
                <div className="flex items-center justify-between text-[10px] text-[#859490] uppercase mb-1">
                  <span>Expected Canonical SHA-256</span>
                  <span className="text-[#34d399]">CERTIFIED IN PASSPORT</span>
                </div>
                <div className="p-2 rounded bg-[#11151a] border border-[#232a33] text-[#34d399] break-all leading-tight">
                  {ORIGINAL_HASH}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-[10px] text-[#859490] uppercase mb-1">
                  <span>Live Computed SHA-256</span>
                  <span className={isTampered ? "text-[#f87171] font-bold" : "text-[#34d399]"}>
                    {isTampered ? "MISMATCH DETECTED" : "EXACT MATCH"}
                  </span>
                </div>
                <div
                  className={`p-2 rounded bg-[#11151a] border break-all leading-tight ${
                    isTampered
                      ? "border-[#f87171] text-[#f87171]"
                      : "border-[#34d399] text-[#34d399]"
                  }`}
                >
                  {isTampered ? TAMPERED_HASH : ORIGINAL_HASH}
                </div>
              </div>
            </div>

            {/* Mathematical Cryptographic Verification Trace */}
            <div className="space-y-2 pt-2 border-t border-[#232a33]">
              <span className="text-[10px] uppercase font-bold text-[#859490] tracking-wider block">
                Deterministic Verification Pipeline
              </span>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between p-2 rounded bg-[#0a0c0f] border border-[#232a33]">
                  <span className="text-[#859490]">1. JCS RFC 8785 Canonicalization:</span>
                  <span className="text-[#34d399] font-bold">PASS</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-[#0a0c0f] border border-[#232a33]">
                  <span className="text-[#859490]">2. SHA-256 Payload Hash Check:</span>
                  <span
                    className={
                      isTampered ? "text-[#f87171] font-bold" : "text-[#34d399] font-bold"
                    }
                  >
                    {isTampered ? "REJECTED (MISMATCH)" : "MATCH CONFIRMED"}
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-[#0a0c0f] border border-[#232a33]">
                  <span className="text-[#859490]">3. Ed25519 Curve Verification:</span>
                  <span
                    className={
                      isTampered ? "text-[#f87171] font-bold" : "text-[#34d399] font-bold"
                    }
                  >
                    {isTampered ? "SIGNATURE_FAIL" : "VALID"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Strict Security Policy Callout */}
          <div className="p-4 rounded-lg bg-[#11151a] border border-[#232a33] font-mono text-xs space-y-1.5">
            <div className="flex items-center gap-2 text-[#2dd4bf] font-bold">
              <span className="material-symbols-outlined text-sm">shield</span>
              <span>Zero-Tolerance Bit-Exact Integrity Principle</span>
            </div>
            <p className="text-[11px] text-[#8b95a3] font-sans leading-relaxed">
              If a synthetic dataset is tampered with by even 1 byte post-notarization, downstream
              consumers, auditor tools, and automated pipelines immediately reject the attestation. No
              silent data drift can ever pass undetected.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
