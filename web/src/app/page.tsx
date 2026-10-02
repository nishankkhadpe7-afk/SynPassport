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
import { Notice } from "@/components/ui";
import {
  RunStatus,
  AgentEvent,
  BudgetUsed,
  DcrResult,
  EvidenceItem,
  SufficiencyResponse,
  VerificationResult,
  VerdictState,
} from "@/types";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<DashboardTab>("setup");
  const [apiConnected, setApiConnected] = useState<boolean>(false);
  const [isReplay, setIsReplay] = useState<boolean>(false);
  const [apiUrl, setApiUrl] = useState<string>(
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  );
  const API_BASE_URL = apiUrl;

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
  const [dcr, setDcr] = useState<DcrResult | null>(null);
  const [policyUses, setPolicyUses] = useState<Record<string, string[]> | null>(null);

  // Action status states
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [verificationResult, setVerificationResult] =
    useState<VerificationResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Check API health and replay mode with multi-URL fallback
  const checkHealth = useCallback(async () => {
    // Configured URL first, then the docker-compose default (8000) and the local dev port (8765)
    const candidateUrls = Array.from(
      new Set([
        apiUrl,
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8765",
        "http://localhost:8765",
      ])
    );

    for (const testUrl of candidateUrls) {
      try {
        const res = await fetch(`${testUrl}/health`, { mode: "cors" });
        if (res.ok) {
          setApiUrl(testUrl);
          setApiConnected(true);

          try {
            const configRes = await fetch(`${testUrl}/config`, { mode: "cors" });
            if (configRes.ok) {
              const cfg = await configRes.json();
              setIsReplay(Boolean(cfg.replay_mode));
            }
          } catch {
            // ignore
          }

          if (typeof window !== "undefined") {
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get("replay") === "1") {
              setIsReplay(true);
            }
          }
          return;
        }
      } catch {
        // try next candidate URL
      }
    }
    setApiConnected(false);
  }, [apiUrl]);

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

        // The policy the passport was judged against, for each use's required checks
        const polId = passData?.policy?.id;
        if (polId) {
          const polRes = await fetch(`${API_BASE_URL}/policies/${encodeURIComponent(polId)}`);
          setPolicyUses(polRes.ok ? (await polRes.json()).uses : null);
        }

        // 4. The exact synthetic file the passport is bound to (used by the tamper test)
        const dataRes = await fetch(`${API_BASE_URL}/runs/${id}/dataset`);
        if (dataRes.ok) {
          setCandidateCsv(await dataRes.text());
        }

        // 5. Distance-to-closest-record distributions computed from this run's files
        const dcrRes = await fetch(`${API_BASE_URL}/runs/${id}/dcr`);
        setDcr(dcrRes.ok ? ((await dcrRes.json()) as DcrResult) : null);
      }
    } catch (err) {
      console.warn("Artifact fetch error:", err);
    }
  }, [API_BASE_URL]);

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
    setDcr(null);
    setPolicyUses(null);
    setCandidateCsv("");
    setRunStatus(null);
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
      const sendApproval = (token?: string) =>
        fetch(`${API_BASE_URL}/runs/${runId}/approve`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { "X-Approver-Token": token } : {}),
          },
          body: JSON.stringify({ approver }),
        });

      let res = await sendApproval();
      // Server has SYNPASSPORT_APPROVER_TOKEN set: ask the approver for it once.
      if (res.status === 401 && typeof window !== "undefined") {
        const token = window.prompt("Enter the approver token configured on the API server");
        if (token) {
          res = await sendApproval(token);
        }
      }

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
  // Pick the purpose to verify from the passport itself instead of a hardcoded value:
  // the mission purpose if it has a verdict, else the first declared intended use that does.
  const resolveVerifyPurpose = (doc: Record<string, unknown>): string => {
    const verdictMap = (doc.verdicts ?? {}) as Record<string, unknown>;
    const mission = (doc.mission ?? {}) as Record<string, unknown>;
    const candidates = [
      mission.purpose,
      ...(Array.isArray(mission.intended_uses) ? mission.intended_uses : []),
    ].filter((p): p is string => typeof p === "string");
    const match = candidates.find((p) => p in verdictMap);
    return match ?? Object.keys(verdictMap)[0] ?? "software_testing";
  };

  const handleVerify = async () => {
    if (!passport) return;
    setIsVerifying(true);
    try {
      const res = await fetch(`${API_BASE_URL}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          // Send run_id so the server reads the original signed files directly from disk,
          // avoiding float precision mutation through JS JSON round-trip.
          run_id: runId,
          passport,
          dataset_content: candidateCsv || "age,target\n55,0\n67,1",
          purpose: resolveVerifyPurpose(passport),
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
    <div className="min-h-screen bg-bg flex flex-col">
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
      <main className="flex-1 max-w-page w-full mx-auto px-4 sm:px-6 py-8 sm:py-10">
        {/* Error message alert */}
        {errorMessage && (
          <div className="mb-8">
            <Notice tone="fail" role="alert" title="Something went wrong" onDismiss={() => setErrorMessage(null)}>
              <span className="font-mono">{errorMessage}</span>
              <span className="block mt-1">
                {apiConnected
                  ? "Check the inputs and try again. Details are in the API window."
                  : "The API is not reachable. Start it on port 8765, then try again."}
              </span>
            </Notice>
          </div>
        )}

        {/* Tab 1: Mission Setup */}
        {activeTab === "setup" && (
          <MissionSetup onStartRun={handleStartRun} isLoading={isLoading} apiBaseUrl={API_BASE_URL} />
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
          <VerdictBoard verdicts={verdicts} isLoading={isLoading} evidence={evidence} policyUses={policyUses} />
        )}

        {/* Tab 4: Evidence Drill-Down */}
        {activeTab === "evidence" && (
          <EvidenceDrilldown
            evidence={evidence}
            isLoading={isLoading}
            candidateId={runStatus?.best_candidate_id ?? null}
            dcr={dcr}
          />
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
      <footer className="border-t border-line">
        <p className="max-w-page mx-auto px-4 sm:px-6 py-6 text-sm text-ink-3">
          SynPassport issues evidence, not guarantees. Verdicts cover only the checks and attacks listed in each passport.
        </p>
      </footer>
    </div>
  );
}
