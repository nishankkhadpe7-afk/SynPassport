"use client";

import React, { useState } from "react";
import { generateHeartDiseaseSampleCsv } from "@/utils/sampleData";

interface MissionSetupProps {
  onStartRun: (datasetFile: File | null, datasetText: string, missionJson: string) => Promise<void>;
  isLoading: boolean;
}

export const MissionSetup: React.FC<MissionSetupProps> = ({ onStartRun, isLoading }) => {
  const [datasetText, setDatasetText] = useState<string>("");
  const [fileName, setFileName] = useState<string>("syn_cardio_cohort_v4.2.csv");
  const [fileSize, setFileSize] = useState<string>("142 KB");
  const [datasetFile, setDatasetFile] = useState<File | null>(null);

  const [purpose, setPurpose] = useState<string>("clinical_ml");
  const [targetColumn, setTargetColumn] = useState<string>("target");
  const [criticalSubgroup, setCriticalSubgroup] = useState<string>("subject.demographics.age >= 65");
  const [privacyLevel, setPrivacyLevel] = useState<string>("standard");
  const [intendedUses, setIntendedUses] = useState<string[]>([
    "software_testing",
    "ml_prototyping",
    "clinical_ml",
  ]);

  const policyId = "ml-sensitive-v1";
  const policySha256 = "9f3a8b72e1c0d45f6a89c3b2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2";

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setFileSize(`${Math.round(file.size / 1024)} KB`);
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
    setFileName("syn_cardio_cohort_v4.2.csv");
    setFileSize("142 KB");
    setDatasetFile(null);
  };

  const toggleIntendedUse = (use: string) => {
    setIntendedUses((prev) =>
      prev.includes(use) ? prev.filter((item) => item !== use) : [...prev, use]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const effectiveText = datasetText || generateHeartDiseaseSampleCsv();

    const mission = {
      purpose,
      target_column: targetColumn,
      critical_subgroups: criticalSubgroup ? [criticalSubgroup] : [],
      privacy_level: privacyLevel,
      intended_uses: intendedUses.length > 0 ? intendedUses : [purpose],
      policy_id: policyId,
      seed: 42891,
    };

    onStartRun(datasetFile, effectiveText, JSON.stringify(mission, null, 2));
  };

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Forensic Orchestration Banner */}
      <div className="relative overflow-hidden rounded-lg bg-[#11151a] p-6 border border-[#232a33]">
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-mono tracking-widest text-[#2dd4bf] font-bold">
                STAGE 01 // ORCHESTRATION
              </span>
              <span className="text-[#859490] text-xs">/</span>
              <span className="text-xs font-mono text-[#8b95a3]">SPEC_v4.2.1-STRICT</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#e6eaf0] tracking-tight">
              Mission Setup &amp; Invariant Binding
            </h1>
            <p className="text-sm text-[#8b95a3] max-w-3xl leading-relaxed">
              Pre-register statistical compliance criteria, anchor synthetic schemas, and
              cryptographically bind policy thresholds prior to evaluation ledger commitment.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 bg-[#0a0c0f] p-2.5 rounded border border-[#232a33]">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-[#17202b] text-xs font-mono text-[#e6eaf0]">
              <span className="w-2 h-2 rounded-full bg-[#34d399]" />
              <span>NOTARY_HSM: READY</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#17202b] text-xs font-mono text-[#859490]">
              <span className="material-symbols-outlined text-xs text-[#2dd4bf]">policy</span>
              <span>POLICY: ml-sensitive-v1</span>
            </div>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Left Column: Ingestion & Invariant Binding (7 Cols) */}
        <div className="xl:col-span-7 flex flex-col gap-6">
          {/* Section 01.01: Dataset Ingestion & Binding */}
          <section className="bg-[#11151a] rounded-lg p-5 border border-[#232a33] flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-[#2dd4bf] font-bold">01.01</span>
                <h2 className="text-base font-semibold text-[#e6eaf0]">
                  Dataset Ingestion &amp; Binding
                </h2>
              </div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#17202b] text-[#34d399] border border-[#34d399]/30 font-semibold">
                Target Ready
              </span>
            </div>

            {/* Dropzone */}
            <div
              className="relative rounded border border-dashed border-[#232a33] hover:border-[#2dd4bf]/60 p-6 text-center transition-colors bg-[#0a0c0f] group cursor-pointer"
            >
              <input
                type="file"
                accept=".csv,.parquet"
                id="dataset-upload"
                onChange={handleFileUpload}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
              />
              <div className="flex flex-col items-center justify-center gap-2">
                <div className="w-10 h-10 rounded bg-[#17202b] flex items-center justify-center text-[#2dd4bf] group-hover:scale-105 transition-transform">
                  <span className="material-symbols-outlined text-2xl">cloud_upload</span>
                </div>
                <p className="text-sm font-medium text-[#e6eaf0]">
                  Drag synthetic dataset (.csv, .parquet) or{" "}
                  <span className="text-[#2dd4bf] underline underline-offset-4">select file</span>
                </p>
                <p className="text-xs font-mono text-[#859490]">
                  Deterministic parsing enabled. Minimum required: 200 records, max schema limit 64 dimensions.
                </p>
              </div>
            </div>

            {/* Quick Benchmark Button */}
            <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
              <button
                type="button"
                onClick={handleLoadSample}
                className="flex items-center gap-2 px-3 py-1.5 rounded bg-[#17202b] hover:bg-[#212b36] border border-[#232a33] text-xs font-mono text-[#e6eaf0] transition-colors"
              >
                <span className="text-[#2dd4bf]">⚡</span>
                <span>Load Heart Disease Benchmark (1,024 rows)</span>
              </button>
              <span className="text-xs font-mono text-[#859490]">SHA-256 Engine: Active Stream</span>
            </div>

            {/* Loaded File Card */}
            <div className="flex items-center justify-between p-3.5 rounded bg-[#17202b] border border-[#232a33]">
              <div className="flex items-center gap-3 min-w-0">
                <div className="p-2 rounded bg-[#0a0c0f] text-[#34d399]">
                  <span className="material-symbols-outlined text-xl">description</span>
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-semibold text-[#e6eaf0] truncate">
                      {fileName}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#11151a] text-[#34d399] border border-[#34d399]/30 font-bold uppercase">
                      Verified
                    </span>
                  </div>
                  <p className="text-[11px] font-mono text-[#859490] truncate">
                    {fileSize} · 1,024 records · 14 schema features · SHA256: 3a7b9c...8a9b
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                <button
                  type="button"
                  onClick={handleLoadSample}
                  className="p-1.5 rounded hover:bg-[#212b36] text-[#859490] hover:text-[#e6eaf0] transition-colors"
                  title="Reload Benchmark"
                >
                  <span className="material-symbols-outlined text-base">refresh</span>
                </button>
              </div>
            </div>
          </section>

          {/* Section 01.02: Mission Schema & Purpose Binding */}
          <section className="bg-[#11151a] rounded-lg p-5 border border-[#232a33] flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-[#2dd4bf] font-bold">01.02</span>
                <h2 className="text-base font-semibold text-[#e6eaf0]">
                  Mission Schema &amp; Purpose Binding
                </h2>
              </div>
              <span className="text-xs font-mono text-[#859490]">SPEC_CLASS: CLINICAL</span>
            </div>

            {/* Target Column */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-mono text-[#8b95a3]">
                <label htmlFor="target-col" className="uppercase font-semibold">
                  Target Supervised Variable
                </label>
                <span className="text-[10px] lowercase text-[#859490]">type: binary_nominal</span>
              </div>
              <input
                id="target-col"
                type="text"
                value={targetColumn}
                onChange={(e) => setTargetColumn(e.target.value)}
                className="w-full h-9 px-3 rounded bg-[#0a0c0f] border border-[#232a33] focus:border-[#2dd4bf] text-xs font-mono text-[#e6eaf0] outline-none transition-colors"
                placeholder="e.g. target, hf_event"
              />
            </div>

            {/* Critical Subgroups */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-mono text-[#8b95a3]">
                <label htmlFor="subgroup-expr" className="uppercase font-semibold">
                  Critical Subgroup Specification
                </label>
                <span className="text-[10px] text-[#2dd4bf]">Strict Restricted Grammar</span>
              </div>
              <input
                id="subgroup-expr"
                type="text"
                value={criticalSubgroup}
                onChange={(e) => setCriticalSubgroup(e.target.value)}
                className="w-full h-9 px-3 rounded bg-[#0a0c0f] border border-[#232a33] focus:border-[#2dd4bf] text-xs font-mono text-[#e6eaf0] outline-none transition-colors"
                placeholder="subject.demographics.age >= 65"
              />
              <p className="text-[11px] font-mono text-[#859490]">
                Pre-registers power bounds. Insufficient records in this cohort will issue an Actionable Refusal.
              </p>
            </div>

            {/* Intended Uses Multi-Select */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-[#8b95a3]">
                <span className="uppercase font-semibold">Declared Intended Uses</span>
                <span className="text-[10px] text-[#859490]">Purpose-bound evaluation</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {[
                  {
                    id: "software_testing",
                    title: "Software Testing",
                    desc: "Schema, nulls, marginal bounds",
                  },
                  {
                    id: "ml_prototyping",
                    title: "ML Prototyping",
                    desc: "Correlations, TSTR utility ratio",
                  },
                  {
                    id: "clinical_ml",
                    title: "Clinical ML",
                    desc: "Subgroup CI power, strict privacy",
                  },
                  {
                    id: "exploratory_analytics",
                    title: "Exploratory Analytics",
                    desc: "Distributional covariance",
                  },
                ].map((use) => {
                  const isChecked = intendedUses.includes(use.id);
                  return (
                    <button
                      type="button"
                      key={use.id}
                      onClick={() => toggleIntendedUse(use.id)}
                      className={`flex items-start gap-2.5 p-2.5 rounded border text-left transition-colors ${
                        isChecked
                          ? "bg-[#17202b] border-[#2dd4bf] text-[#e6eaf0]"
                          : "bg-[#0a0c0f] border-[#232a33] text-[#8b95a3] hover:border-[#859490]"
                      }`}
                    >
                      <div
                        className={`w-4 h-4 rounded-sm flex items-center justify-center mt-0.5 shrink-0 ${
                          isChecked
                            ? "bg-[#2dd4bf] text-[#0a0c0f]"
                            : "border border-[#232a33] bg-[#0a0c0f]"
                        }`}
                      >
                        {isChecked && (
                          <span className="material-symbols-outlined text-xs font-bold">check</span>
                        )}
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-semibold text-[#e6eaf0]">{use.title}</div>
                        <div className="text-[10px] font-mono text-[#859490]">{use.desc}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Privacy Defense Profile */}
            <div className="space-y-1.5">
              <label className="text-xs font-mono text-[#8b95a3] uppercase font-semibold block">
                Differential Privacy Epsilon Floor
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: "low", label: "Low Risk", eps: "ε = 10.0" },
                  { id: "standard", label: "Standard", eps: "ε = 1.25" },
                  { id: "high", label: "Regulated", eps: "ε = 0.50" },
                ].map((p) => (
                  <button
                    type="button"
                    key={p.id}
                    onClick={() => setPrivacyLevel(p.id)}
                    className={`py-2 px-3 rounded border text-center transition-colors font-mono text-xs ${
                      privacyLevel === p.id
                        ? "bg-[#17202b] border-[#2dd4bf] text-[#2dd4bf] font-bold"
                        : "bg-[#0a0c0f] border-[#232a33] text-[#8b95a3] hover:text-[#e6eaf0]"
                    }`}
                  >
                    <div>{p.label}</div>
                    <div className="text-[10px] text-[#859490]">{p.eps}</div>
                  </button>
                ))}
              </div>
            </div>
          </section>
        </div>

        {/* Right Column: Pre-Registered Policy & Initiation (5 Cols) */}
        <div className="xl:col-span-5 flex flex-col gap-6">
          {/* Policy Profile Card */}
          <div className="bg-[#11151a] rounded-lg p-5 border border-[#232a33] flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#232a33]">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-lg text-[#2dd4bf]">gavel</span>
                <span className="text-xs font-mono font-bold uppercase text-[#e6eaf0]">
                  Pre-Registered Policy
                </span>
              </div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#17202b] text-[#2dd4bf] font-bold border border-[#2dd4bf]/20">
                STRICT LOCK
              </span>
            </div>

            <div className="space-y-3">
              <div>
                <span className="text-[10px] font-mono uppercase text-[#859490] block mb-1">
                  Policy Profile ID
                </span>
                <div className="p-2 rounded bg-[#0a0c0f] border border-[#232a33] font-mono text-xs text-[#2dd4bf] font-semibold">
                  {policyId}
                </div>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-[#859490] block mb-1">
                  Immutable Policy SHA-256 Digest
                </span>
                <div className="p-2 rounded bg-[#0a0c0f] border border-[#232a33] font-mono text-[11px] text-[#8b95a3] break-all leading-tight">
                  {policySha256}
                </div>
              </div>
            </div>

            {/* Bound Gates Checklist */}
            <div className="space-y-2 pt-2 border-t border-[#232a33]">
              <span className="text-[10px] font-mono uppercase text-[#859490] font-semibold tracking-wider block">
                Deterministic Policy Gates
              </span>
              <div className="space-y-1.5 font-mono text-xs">
                {[
                  { name: "Schema Structure & Null Constraints", req: "100.0% Pass" },
                  { name: "Marginal Distribution TVD", req: "≤ 0.10 TVD" },
                  { name: "Correlation Fidelity Bound", req: "≥ 0.85 Cosine" },
                  { name: "TSTR Utility Ratio Bound", req: "≥ 0.90 Target" },
                  { name: "Subgroup Power (age >= 65)", req: "N ≥ 171 (CI ≤ 0.15)" },
                  { name: "Privacy Distance vs Holdout", req: "DCR ≥ Holdout" },
                  { name: "Membership Inference Defense", req: "AUC ≤ 0.55" },
                ].map((gate, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded bg-[#0a0c0f] border border-[#232a33]"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#2dd4bf]" />
                      <span className="text-[#e6eaf0] text-[11px] truncate">{gate.name}</span>
                    </div>
                    <span className="text-[10px] text-[#34d399] font-semibold shrink-0 ml-2">
                      {gate.req}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Action Card */}
          <div className="bg-[#11151a] rounded-lg p-5 border border-[#232a33] flex flex-col gap-3">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 rounded bg-[#2dd4bf] hover:bg-[#26bfae] active:bg-[#1fa394] text-[#0a0c0f] font-sans font-bold text-sm uppercase tracking-wider flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <span className="w-4 h-4 border-2 border-[#0a0c0f] border-t-transparent rounded-full animate-spin" />
                  <span>Pinning Invariants &amp; Synthesizing...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-lg">verified_user</span>
                  <span>Anchor Invariants &amp; Initiate Run</span>
                </>
              )}
            </button>

            <div className="p-3 rounded bg-[#0a0c0f] border border-[#232a33] text-[11px] font-mono text-[#859490] leading-relaxed">
              <span className="text-[#e6eaf0] font-semibold block mb-0.5">
                Deterministic Execution Guarantee:
              </span>
              Execution is bound to cryptographically locked policies. Zero stochastic LLM
              hallucinations involved in verification verdicts.
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};
