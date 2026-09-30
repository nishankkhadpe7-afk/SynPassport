"use client";

import React, { useState } from "react";
import { Upload, FileText, CheckSquare, Sparkles, Shield, Database, Lock } from "lucide-react";
import { generateHeartDiseaseSampleCsv } from "@/utils/sampleData";

interface MissionSetupProps {
  onStartRun: (datasetFile: File | null, datasetText: string, missionJson: string) => Promise<void>;
  isLoading: boolean;
}

export const MissionSetup: React.FC<MissionSetupProps> = ({ onStartRun, isLoading }) => {
  const [datasetText, setDatasetText] = useState<string>("");
  const [fileName, setFileName] = useState<string>("");
  const [datasetFile, setDatasetFile] = useState<File | null>(null);

  const [purpose, setPurpose] = useState<string>("software_testing");
  const [targetColumn, setTargetColumn] = useState<string>("target");
  const [criticalSubgroup, setCriticalSubgroup] = useState<string>("age >= 65");
  const [privacyLevel, setPrivacyLevel] = useState<string>("standard");
  const [intendedUses, setIntendedUses] = useState<string[]>(["software_testing", "clinical_ml"]);

  const policyId = "software-testing";
  const policySha256 = "4a17a6fb63292a9bedb1df409fe624b30d614ce3fcec51ed32b0e766b67b98be";

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
      intended_uses: intendedUses.length > 0 ? intendedUses : [purpose],
      policy_id: policyId,
      seed: 1234,
    };

    onStartRun(datasetFile, datasetText, JSON.stringify(mission, null, 2));
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
          Purpose-Bound Assurance Setup
        </h2>
        <p className="text-slate-400 text-sm max-w-2xl mx-auto">
          Declare empirical mission parameters, upload training data, and bind deterministic policy gates before candidate synthesis.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Dataset Upload Area */}
          <div className="md:col-span-2 glass-panel rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Database className="w-4 h-4 text-indigo-400" />
                Training Dataset (CSV)
              </label>
              <button
                type="button"
                onClick={handleLoadSample}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 transition-colors px-2 py-1 rounded bg-indigo-500/10 border border-indigo-500/20"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Load Heart Disease Benchmark
              </button>
            </div>

            <div className="border-2 border-dashed border-slate-700/60 hover:border-indigo-500/50 rounded-xl p-6 text-center transition-all bg-slate-900/40">
              <input
                type="file"
                accept=".csv"
                id="dataset-upload"
                onChange={handleFileUpload}
                className="hidden"
              />
              <label
                htmlFor="dataset-upload"
                className="cursor-pointer flex flex-col items-center justify-center space-y-2"
              >
                <Upload className="w-8 h-8 text-indigo-400/80 mb-1" />
                <span className="text-sm text-slate-300 font-medium">
                  {fileName ? (
                    <span className="text-emerald-400 font-mono text-xs">{fileName} loaded</span>
                  ) : (
                    "Drop training CSV here or click to browse"
                  )}
                </span>
                <span className="text-xs text-slate-500">
                  Headers required: age, cholesterol, resting_bp, target
                </span>
              </label>
            </div>

            {datasetText && (
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-slate-400 font-mono">
                  <span>PREVIEW (FIRST 4 ROWS)</span>
                  <span>{datasetText.split("\n").filter(Boolean).length - 1} records</span>
                </div>
                <pre className="bg-slate-950/80 p-3 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto border border-slate-800/80 max-h-32">
                  {datasetText.split("\n").slice(0, 5).join("\n")}
                </pre>
              </div>
            )}
          </div>

          {/* Bound Policy Summary Card */}
          <div className="glass-panel rounded-2xl p-6 space-y-4 border border-indigo-500/20 bg-gradient-to-b from-indigo-950/30 to-slate-900/60">
            <div className="flex items-center gap-2 text-indigo-400 text-sm font-semibold">
              <Shield className="w-4 h-4" />
              <span>Assurance Policy Profile</span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-500 block uppercase tracking-wider font-mono">Policy ID</span>
                <span className="text-slate-200 font-medium font-mono text-sm">{policyId}</span>
              </div>

              <div>
                <span className="text-slate-500 block uppercase tracking-wider font-mono">SHA-256 Digest</span>
                <span className="text-indigo-300 font-mono break-all text-[11px] bg-slate-950/60 p-1.5 rounded block border border-slate-800">
                  {policySha256}
                </span>
              </div>

              <div className="pt-2 border-t border-slate-800/60 space-y-1.5 text-slate-400 text-xs">
                <div className="flex items-center justify-between">
                  <span>Candidate Evaluation Cap</span>
                  <span className="font-mono text-slate-200 font-bold">3 max</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Permitted Repairs</span>
                  <span className="font-mono text-slate-200 font-bold">2 max</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Policy Gate Status</span>
                  <span className="text-emerald-400 font-medium">LOCKED</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Form Parameters */}
        <div className="glass-panel rounded-2xl p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Primary Purpose
            </label>
            <select
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="software_testing">software_testing</option>
              <option value="clinical_ml">clinical_ml</option>
              <option value="exploratory_analytics">exploratory_analytics</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Target Column
            </label>
            <input
              type="text"
              value={targetColumn}
              onChange={(e) => setTargetColumn(e.target.value)}
              placeholder="e.g. target"
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 transition-colors font-mono"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Critical Subgroup
            </label>
            <input
              type="text"
              value={criticalSubgroup}
              onChange={(e) => setCriticalSubgroup(e.target.value)}
              placeholder="e.g. age >= 65"
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 transition-colors font-mono"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Risk Mitigation Level
            </label>
            <select
              value={privacyLevel}
              onChange={(e) => setPrivacyLevel(e.target.value)}
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="standard">standard</option>
              <option value="high">high</option>
              <option value="strict">strict</option>
            </select>
          </div>
        </div>

        {/* Intended Uses Checkboxes */}
        <div className="glass-panel rounded-2xl p-6 space-y-3">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
            Intended Uses (Scope of Assurance)
          </label>
          <div className="flex flex-wrap gap-4">
            {["software_testing", "clinical_ml", "exploratory_analytics"].map((use) => {
              const isChecked = intendedUses.includes(use);
              return (
                <button
                  type="button"
                  key={use}
                  onClick={() => toggleIntendedUse(use)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium border transition-all ${
                    isChecked
                      ? "bg-indigo-600/20 border-indigo-500/60 text-indigo-200"
                      : "bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <CheckSquare className={`w-4 h-4 ${isChecked ? "text-indigo-400" : "text-slate-600"}`} />
                  <span className="font-mono">{use}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={isLoading || (!datasetText && !datasetFile)}
            className="flex items-center gap-2.5 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-medium shadow-lg shadow-indigo-600/25 transition-all text-sm font-semibold"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Initializing Assurance Pipeline...</span>
              </>
            ) : (
              <>
                <FileText className="w-4 h-4" />
                <span>Initialize Assurance Run</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
