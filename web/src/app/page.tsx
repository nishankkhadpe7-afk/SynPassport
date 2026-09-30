"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { Navbar, DashboardTab } from "@/components/Navbar";
import { MissionSetup } from "@/components/MissionSetup";
import { RunTimeline } from "@/components/RunTimeline";
import { VerdictBoard } from "@/components/VerdictBoard";
import { EvidenceDrilldown } from "@/components/EvidenceDrilldown";
import { SufficiencyPanel } from "@/components/SufficiencyPanel";
import { PassportPanel } from "@/components/PassportPanel";
import { TamperDemo } from "@/components/TamperDemo";
import {
  RunStatus,
  AgentEvent,
  BudgetUsed,
  EvidenceItem,
  SufficiencyResponse,
  VerificationResult,
  VerdictState,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<DashboardTab>("setup");
  const [apiConnected, setApiConnected] = useState<boolean>(false);
  const [isReplay, setIsReplay] = useState<boolean>(false);

  // Run execution state
  const [runId, setRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [budgetUsed, setBudgetUsed] = useState<BudgetUsed | null>(null);
  const [verdicts, setVerdicts] = useState<Record<string, VerdictState>>({});
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [sufficiency, setSufficiency] = useState<SufficiencyResponse | null>(null);
  const [passport, setPassport] = useState<Record<string, unknown> | null>(null);
  const [candidateCsv, setCandidateCsv] = useState<string>("");

  // Action status states
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [verificationResult, setVerificationResult] =
    useState<VerificationResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Check API health and replay mode
  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      if (res.ok) {
        setApiConnected(true);
      } else {
        setApiConnected(false);
      }

      // Check config endpoint for replay mode
      try {
        const configRes = await fetch(`${API_BASE_URL}/config`);
        if (configRes.ok) {
          const cfg = await configRes.json();
          setIsReplay(Boolean(cfg.replay_mode));
        }
      } catch {
        // Fallback: check query param if set
        if (typeof window !== "undefined") {
          const urlParams = new URLSearchParams(window.location.search);
          if (urlParams.get("replay") === "1") {
            setIsReplay(true);
          }
        }
      }
    } catch {
      setApiConnected(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  // Fetch all artifacts for a run
  const fetchRunArtifacts = useCallback(async (id: string) => {
    try {
      // 1. Evidence
      const evRes = await fetch(`${API_BASE_URL}/runs/${id}/evidence`);
      if (evRes.ok) {
        const evData: EvidenceItem[] = await evRes.json();
        setEvidence(evData);
      }

      // 2. Sufficiency
      const suffRes = await fetch(`${API_BASE_URL}/runs/${id}/sufficiency`);
      if (suffRes.ok) {
        const suffData: SufficiencyResponse = await suffRes.json();
        setSufficiency(suffData);
      }

      // 3. Passport
      const passRes = await fetch(`${API_BASE_URL}/runs/${id}/passport`);
      if (passRes.ok) {
        const passData = await passRes.json();
        setPassport(passData);
      }
    } catch (err) {
      console.warn("Artifact fetch error:", err);
    }
  }, []);

  // Poll run status
  const pollRun = useCallback(
    async (id: string) => {
      try {
        const res = await fetch(`${API_BASE_URL}/runs/${id}`);
        if (!res.ok) return;

        const data: RunStatus = await res.json();
        setRunStatus(data);
        if (data.budget_used) setBudgetUsed(data.budget_used);
        if (data.verdicts) setVerdicts(data.verdicts);

        if (data.status === "COMPLETED" || data.status === "FAILED") {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          await fetchRunArtifacts(id);
        }
      } catch (err) {
        console.warn("Poll run error:", err);
      }
    },
    [fetchRunArtifacts]
  );

  // Subscribe to SSE events
  const subscribeToEvents = useCallback(
    (id: string) => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const sse = new EventSource(`${API_BASE_URL}/runs/${id}/events`);
      eventSourceRef.current = sse;

      sse.onmessage = (messageEvent) => {
        try {
          if (messageEvent.data.startsWith(":")) return; // ping
          const parsed = JSON.parse(messageEvent.data);
          setEvents((prev) => [...prev, parsed]);

          if (parsed.type === "candidate") {
            const data = parsed.data || {};
            if (data.csv_content) {
              setCandidateCsv(data.csv_content);
            }
          }

          if (parsed.type === "evaluate" && parsed.data?.verdicts) {
            setVerdicts(parsed.data.verdicts);
          }

          if (parsed.type === "completed" || parsed.type === "failed") {
            pollRun(id);
            fetchRunArtifacts(id);
          }
        } catch {
          // ignore non-json messages
        }
      };

      sse.onerror = () => {
        // SSE disconnected, fallback to polling
        sse.close();
      };
    },
    [fetchRunArtifacts, pollRun]
  );

  // Clean up SSE and polling on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  // Handle starting a new run
  const handleStartRun = async (
    datasetFile: File | null,
    datasetText: string,
    missionJson: string
  ) => {
    setIsLoading(true);
    setErrorMessage(null);
    setEvents([]);
    setVerdicts({});
    setEvidence([]);
    setSufficiency(null);
    setPassport(null);
    setVerificationResult(null);

    try {
      const formData = new FormData();
      if (datasetFile) {
        formData.append("dataset", datasetFile);
      } else {
        const blob = new Blob([datasetText], { type: "text/csv" });
        formData.append("dataset", blob, "training_dataset.csv");
      }
      formData.append("mission", missionJson);

      const res = await fetch(`${API_BASE_URL}/runs`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(errDetail.detail || `Server responded with ${res.status}`);
      }

      const created = await res.json();
      const newRunId = created.run_id;
      setRunId(newRunId);

      // Start SSE stream and polling
      subscribeToEvents(newRunId);
      pollRun(newRunId);
      pollIntervalRef.current = setInterval(() => pollRun(newRunId), 2000);

      // Switch to timeline tab
      setActiveTab("timeline");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to start run";
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle human release approval
  const handleApprove = async (approver: string) => {
    if (!runId) return;
    setIsApproving(true);
    try {
      const res = await fetch(`${API_BASE_URL}/runs/${runId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approver }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Approval failed");
      }

      const approvalData = await res.json();
      if (approvalData.passport) {
        setPassport(approvalData.passport);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Approval request failed";
      setErrorMessage(msg);
    } finally {
      setIsApproving(false);
    }
  };

  // Handle passport verification
  const handleVerify = async () => {
    if (!passport) return;
    setIsVerifying(true);
    try {
      const res = await fetch(`${API_BASE_URL}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          passport,
          dataset_content: candidateCsv || "age,target\n55,0\n67,1",
          purpose: "software_testing",
          allow_warning: true,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Verification failed");
      }

      const data: VerificationResult = await res.json();
      setVerificationResult(data);
    } catch (err: unknown) {
      setVerificationResult({
        valid: false,
        reason_code: "VERIFICATION_ERROR",
        description: err instanceof Error ? err.message : "Unable to verify passport",
      });
    } finally {
      setIsVerifying(false);
    }
  };

  // Custom verify callback for Tamper Demo
  const handleVerifyCustom = async (
    datasetContent: string,
    passportContent: Record<string, unknown>,
    purpose: string
  ): Promise<VerificationResult> => {
    setIsVerifying(true);
    try {
      const res = await fetch(`${API_BASE_URL}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          passport: passportContent,
          dataset_content: datasetContent,
          purpose,
          allow_warning: true,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        return {
          valid: false,
          reason_code: "VERIFICATION_FAILED",
          description: errData.detail || "Verification rejected by server",
        };
      }

      return await res.json();
    } catch (err: unknown) {
      return {
        valid: false,
        reason_code: "NETWORK_ERROR",
        description: err instanceof Error ? err.message : "Network error during verification",
      };
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Top Navbar with tabs & replay indicator */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isReplay={isReplay}
        apiConnected={apiConnected}
        runId={runId}
        runStatus={runStatus?.status || null}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error message alert */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-mono flex items-center justify-between">
            <span>{errorMessage}</span>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-400 hover:text-white ml-4 font-bold"
            >
              &times;
            </button>
          </div>
        )}

        {/* Tab 1: Mission Setup */}
        {activeTab === "setup" && (
          <MissionSetup onStartRun={handleStartRun} isLoading={isLoading} />
        )}

        {/* Tab 2: Agent Timeline */}
        {activeTab === "timeline" && (
          <RunTimeline
            runId={runId || "pending"}
            runStatus={runStatus}
            events={events}
            budgetUsed={budgetUsed}
            isLoading={isLoading}
            error={errorMessage}
          />
        )}

        {/* Tab 3: Verdict Board */}
        {activeTab === "verdicts" && (
          <VerdictBoard verdicts={verdicts} isLoading={isLoading} />
        )}

        {/* Tab 4: Evidence Drill-Down */}
        {activeTab === "evidence" && (
          <EvidenceDrilldown evidence={evidence} isLoading={isLoading} />
        )}

        {/* Tab 5: Sufficiency Panel */}
        {activeTab === "sufficiency" && (
          <SufficiencyPanel sufficiency={sufficiency} isLoading={isLoading} />
        )}

        {/* Tab 6: Passport Panel */}
        {activeTab === "passport" && (
          <PassportPanel
            runId={runId || ""}
            passport={passport}
            onApprove={handleApprove}
            onVerify={handleVerify}
            verificationResult={verificationResult}
            isApproving={isApproving}
            isVerifying={isVerifying}
            isLoading={isLoading}
          />
        )}

        {/* Tab 7: Tamper Demo */}
        {activeTab === "tamper" && (
          <TamperDemo
            passport={passport}
            candidateCsv={candidateCsv}
            onVerifyCustom={handleVerifyCustom}
            isVerifying={isVerifying}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500 font-mono">
        <p>SynPassport &bull; Purpose-Bound Assurance &bull; Supports Audit</p>
      </footer>
    </div>
  );
}
