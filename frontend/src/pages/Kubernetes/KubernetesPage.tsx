import { useEffect, useState } from 'react';
import {
  AlertCircle,
  Brain,
  CheckCircle,
  Eye,
  FileText,
  RefreshCw,
  ShieldAlert,
  X,
} from 'lucide-react';

import { PageHeader } from '@/components/common/PageHeader';
import { LoadingState } from '@/components/common/LoadingState';

import {
  getKubernetesSnapshot,
  getKubernetesPod,
  getKubernetesPodLogs,
  type KubernetesSnapshot,
  type KubernetesPodDetails,
  type KubernetesPodLogsResponse,
} from '@/services/kubernetesService';

import {
  analyzeWithAgent,
  type AgentAnalysisResponse,
} from '@/services/dockerService';



export default function KubernetesPage() {
  const [snapshot, setSnapshot] =
    useState<KubernetesSnapshot | null>(null);

  const [selectedPod, setSelectedPod] =
    useState<KubernetesPodDetails | null>(null);

  const [selectedLogs, setSelectedLogs] =
    useState<KubernetesPodLogsResponse | null>(null);

  const [analysisResult, setAnalysisResult] =
    useState<AgentAnalysisResponse | null>(null);

  const [analyzingPodId, setAnalyzingPodId] =
    useState<string | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [detailsLoading, setDetailsLoading] =
    useState(false);

  const [logsLoading, setLogsLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  // ==================================================
  // LOAD KUBERNETES DATA
  // ==================================================

  const loadKubernetesData = async () => {
    setLoading(true);
    setError(null);

    try {
      const data =
        await getKubernetesSnapshot();

      setSnapshot(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load Kubernetes environment.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKubernetesData();
  }, []);

  // ==================================================
  // POD DETAILS
  // ==================================================

  const handleDetails = async (
    podName: string,
    namespace: string
  ) => {
    setDetailsLoading(true);
    setSelectedLogs(null);
    setError(null);

    try {
      const details =
        await getKubernetesPod(
          podName,
          namespace
        );

      setSelectedPod(details);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load pod details.'
      );
    } finally {
      setDetailsLoading(false);
    }
  };

  // ==================================================
  // POD LOGS
  // ==================================================

  const handleLogs = async (
    podName: string,
    namespace: string
  ) => {
    setLogsLoading(true);
    setSelectedPod(null);
    setError(null);

    try {
      const logs =
        await getKubernetesPodLogs(
          podName,
          namespace
        );

      setSelectedLogs(logs);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load pod logs.'
      );
    } finally {
      setLogsLoading(false);
    }
  };

  // ==================================================
  // AI INVESTIGATION
  // ==================================================

  const handleInvestigate = async (
    podName: string,
    namespace: string
  ) => {
    const resourceId =
      `${namespace}/${podName}`;

    setAnalyzingPodId(resourceId);
    setAnalysisResult(null);
    setSelectedPod(null);
    setSelectedLogs(null);
    setError(null);

    try {
      const result =
        await analyzeWithAgent({
          domain: 'kubernetes',
          resource_id: resourceId,
        });

      setAnalysisResult(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to analyze the Kubernetes pod.'
      );
    } finally {
      setAnalyzingPodId(null);
    }
  };

  // ==================================================
  // RENDER
  // ==================================================

  return (
    <div className="space-y-6">

      {/* ==================================================
          PAGE HEADER
      ================================================== */}

      <div className="flex items-start justify-between gap-4">

        <PageHeader
          title="Kubernetes Studio"
          subtitle="Monitor and analyze your Kubernetes cluster and workloads."
        />

        <button
          type="button"
          onClick={loadKubernetesData}
          disabled={loading}
          className="btn-secondary"
        >
          <RefreshCw
            size={16}
            className={
              loading
                ? 'animate-spin'
                : ''
            }
          />

          Refresh
        </button>

      </div>

      {/* ==================================================
          ERROR
      ================================================== */}

      {!loading && error && (
        <div className="card flex items-start gap-3 p-5">

          <AlertCircle
            size={20}
            className="text-danger"
          />

          <div>

            <p className="text-sm font-semibold text-text-primary">
              Kubernetes error
            </p>

            <p className="mt-1 text-xs text-text-secondary">
              {error}
            </p>

          </div>

        </div>
      )}

      {/* ==================================================
          LOADING
      ================================================== */}

      {loading && (
        <div className="card">
          <LoadingState
            label="Loading Kubernetes environment..."
          />
        </div>
      )}

      {/* ==================================================
          MAIN DASHBOARD
      ================================================== */}

      {!loading &&
        snapshot && (
          <>

            {/* ==========================================
                CLUSTER OVERVIEW
            ========================================== */}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">

              {/* Status */}

              <div className="card p-5">

                <p className="text-xs text-text-secondary">
                  Cluster
                </p>

                <p className="mt-2 text-lg font-semibold text-text-primary">
                  {snapshot.cluster.status}
                </p>

              </div>

              {/* Running */}

              <div className="card p-5">

                <p className="text-xs text-text-secondary">
                  Running Pods
                </p>

                <p className="mt-2 text-lg font-semibold text-text-primary">
                  {snapshot.cluster.runningPods}
                </p>

              </div>

              {/* Failed */}

              <div className="card p-5">

                <p className="text-xs text-text-secondary">
                  Failed Pods
                </p>

                <p className="mt-2 text-lg font-semibold text-text-primary">
                  {snapshot.cluster.failedPods}
                </p>

              </div>

              {/* Warning */}

              <div className="card p-5">

                <p className="text-xs text-text-secondary">
                  Pod Restarts
                </p>

                <p className="mt-2 text-lg font-semibold text-text-primary">
                  {snapshot.cluster.podRestarts}
                </p>

              </div>

              {/* CPU */}

              <div className="card p-5">

                <p className="text-xs text-text-secondary">
                  CPU
                </p>

                <p className="mt-2 text-lg font-semibold text-text-primary">
                  {snapshot.cluster.cpuUsagePercent}%
                </p>

              </div>

            </div>

            {/* ==========================================
                PODS
            ========================================== */}

            <div className="card p-5">

              <div className="mb-4">

                <h2 className="text-sm font-semibold text-text-primary">
                  Pods
                </h2>

                <p className="mt-1 text-xs text-text-secondary">
                  Live information from your Kubernetes cluster.
                </p>

              </div>

              {snapshot.pods.length === 0 ? (

                <p className="py-8 text-center text-sm text-text-secondary">
                  No Kubernetes pods found.
                </p>

              ) : (

                <div className="space-y-3">

                  {snapshot.pods.map((pod) => {

                    const podId =
                      `${pod.namespace}/${pod.name}`;

                    const isAnalyzing =
                      analyzingPodId === podId;

                    return (

                      <div
                        key={pod.id}
                        className="rounded-lg border border-border bg-bg-elevated p-4"
                      >

                        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">

                          {/* Pod information */}

                          <div className="min-w-0">

                            <p className="truncate text-sm font-semibold text-text-primary">
                              {pod.name}
                            </p>

                            <p className="mt-1 text-xs text-text-secondary">
                              Namespace:{' '}
                              {pod.namespace}
                            </p>

                            <p className="mt-1 text-xs text-text-secondary">
                              CPU:{' '}
                              {pod.cpu}
                              {'  '}|{'  '}
                              Memory:{' '}
                              {pod.memory}
                            </p>

                            <p className="mt-1 text-xs text-text-secondary">
                              Restarts:{' '}
                              {pod.restarts}
                            </p>

                            {pod.issue && (
                              <p className="mt-1 text-xs text-text-secondary">
                                Issue:{' '}
                                {pod.issue}
                              </p>
                            )}

                          </div>

                          {/* Actions */}

                          <div className="flex flex-wrap items-center gap-2">

                            <span className="rounded-full border border-border px-3 py-1 text-xs text-text-secondary">
                              {pod.status}
                            </span>

                            <button
                              type="button"
                              onClick={() =>
                                handleDetails(
                                  pod.name,
                                  pod.namespace
                                )
                              }
                              className="btn-secondary"
                            >
                              <Eye size={15} />
                              Details
                            </button>

                            <button
                              type="button"
                              onClick={() =>
                                handleLogs(
                                  pod.name,
                                  pod.namespace
                                )
                              }
                              className="btn-secondary"
                            >
                              <FileText
                                size={15}
                              />
                              Logs
                            </button>

                            <button
                              type="button"
                              onClick={() =>
                                handleInvestigate(
                                  pod.name,
                                  pod.namespace
                                )
                              }
                              disabled={isAnalyzing}
                              className="btn-secondary"
                            >
                              <Brain
                                size={15}
                                className={
                                  isAnalyzing
                                    ? 'animate-pulse'
                                    : ''
                                }
                              />

                              {isAnalyzing
                                ? 'Analyzing...'
                                : 'Investigate'}
                            </button>

                          </div>

                        </div>

                      </div>

                    );
                  })}

                </div>

              )}

            </div>

            {/* ==========================================
                RECOMMENDATIONS
            ========================================== */}

            <div className="card p-5">

              <div className="mb-4">

                <h2 className="text-sm font-semibold text-text-primary">
                  AI Recommendations
                </h2>

                <p className="mt-1 text-xs text-text-secondary">
                  Monitoring recommendations from the Kubernetes environment.
                </p>

              </div>

              <div className="space-y-3">

                {snapshot.recommendations.map(
                  (recommendation) => (

                    <div
                      key={recommendation.id}
                      className="rounded-lg border border-border bg-bg-elevated p-4"
                    >

                      <div className="flex items-center justify-between gap-4">

                        <p className="text-sm font-semibold text-text-primary">
                          {recommendation.title}
                        </p>

                        <span className="rounded-full border border-border px-3 py-1 text-xs capitalize text-text-secondary">
                          {recommendation.severity}
                        </span>

                      </div>

                      <p className="mt-2 text-xs leading-5 text-text-secondary">
                        {recommendation.explanation}
                      </p>

                      <p className="mt-2 rounded-md bg-bg px-3 py-2 text-xs text-text-secondary">
                        {recommendation.command}
                      </p>

                    </div>

                  )
                )}

              </div>

            </div>

            {/* ==========================================
                ANALYZING
            ========================================== */}

            {analyzingPodId && (

              <div className="card p-5">

                <div className="flex items-center gap-3">

                  <Brain
                    size={20}
                    className="animate-pulse"
                  />

                  <div>

                    <p className="text-sm font-semibold text-text-primary">
                      DevOpsGPT is analyzing the Kubernetes pod...
                    </p>

                    <p className="mt-1 text-xs text-text-secondary">
                      Investigation → Root Cause → RAG →
                      Solution → Verification
                    </p>

                  </div>

                </div>

              </div>

            )}

            {/* ==========================================
                AGENT ANALYSIS
            ========================================== */}

            {analysisResult &&
              !analyzingPodId && (

                <div className="card p-5">

                  {/* Header */}

                  <div className="mb-6 flex items-start justify-between gap-4">

                    <div>

                      <div className="flex items-center gap-2">

                        <Brain size={19} />

                        <h2 className="text-sm font-semibold text-text-primary">
                          DevOpsGPT Agent Analysis
                        </h2>

                      </div>

                      <p className="mt-1 text-xs text-text-secondary">
                        Shared agentic pipeline for{' '}
                        {analysisResult.resource_id}
                      </p>

                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        setAnalysisResult(null)
                      }
                      className="btn-ghost"
                    >
                      <X size={16} />
                    </button>

                  </div>

                  {/* ====================================
                      1. INVESTIGATION
                  ==================================== */}

                  {analysisResult.investigation && (

                    <div className="mb-4 rounded-lg border border-border bg-bg-elevated p-4">

                      <h3 className="text-sm font-semibold text-text-primary">
                        1. Investigation
                      </h3>

                      <p className="mt-2 text-xs text-text-secondary">
                        Pod:{' '}
                        {String(
                          analysisResult.investigation
                            .pod_name ??
                            'Unknown'
                        )}
                      </p>

                      <p className="mt-1 text-xs text-text-secondary">
                        Namespace:{' '}
                        {String(
                          analysisResult.investigation
                            .namespace ??
                            'Unknown'
                        )}
                      </p>

                      <p className="mt-1 text-xs text-text-secondary">
                        Status:{' '}
                        {String(
                          analysisResult.investigation
                            .status ??
                            'Unknown'
                        )}
                      </p>

                      {Array.isArray(
                        analysisResult.investigation
                          .observations
                      ) && (

                        <div className="mt-4 space-y-2">

                          {analysisResult.investigation.observations.map(
                            (
                              observation,
                              index
                            ) => (

                              <p
                                key={index}
                                className="text-xs leading-5 text-text-secondary"
                              >
                                • {String(
                                  observation
                                )}
                              </p>

                            )
                          )}

                        </div>

                      )}

                      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">

                        <div>

                          <p className="text-xs text-text-secondary">
                            Logs Available
                          </p>

                          <p className="mt-1 text-sm text-text-primary">
                            {String(
                              analysisResult.investigation
                                .logs_available
                            )}
                          </p>

                        </div>

                        <div>

                          <p className="text-xs text-text-secondary">
                            Previous Logs
                          </p>

                          <p className="mt-1 text-sm text-text-primary">
                            {String(
                              analysisResult.investigation
                                .previous_logs_available
                            )}
                          </p>

                        </div>

                        <div>

                          <p className="text-xs text-text-secondary">
                            Kubernetes Events
                          </p>

                          <p className="mt-1 text-sm text-text-primary">
                            {String(
                              analysisResult.investigation
                                .events_available
                            )}
                          </p>

                        </div>

                      </div>

                    </div>

                  )}

                  {/* ====================================
                      2. ROOT CAUSE
                  ==================================== */}

                  {analysisResult.root_cause && (

                    <div className="mb-4 rounded-lg border border-border bg-bg-elevated p-4">

                      <div className="flex items-center justify-between gap-4">

                        <h3 className="text-sm font-semibold text-text-primary">
                          2. Root Cause
                        </h3>

                        <span className="rounded-full border border-border px-3 py-1 text-xs capitalize text-text-secondary">
                          Confidence:{' '}
                          {String(
                            analysisResult.root_cause
                              .confidence ??
                              'unknown'
                          )}
                        </span>

                      </div>

                      <p className="mt-3 text-sm leading-6 text-text-primary">
                        {String(
                          analysisResult.root_cause
                            .root_cause ??
                            'No root cause generated.'
                        )}
                      </p>

                      {Array.isArray(
                        analysisResult.root_cause
                          .reasoning
                      ) && (

                        <div className="mt-4 space-y-2">

                          {analysisResult.root_cause.reasoning.map(
                            (
                              reason,
                              index
                            ) => (

                              <p
                                key={index}
                                className="text-xs leading-5 text-text-secondary"
                              >
                                • {String(
                                  reason
                                )}
                              </p>

                            )
                          )}

                        </div>

                      )}

                      <p className="mt-4 text-xs font-medium text-text-secondary">
                        More investigation required:{' '}
                        {String(
                          analysisResult.root_cause
                            .requires_more_investigation
                        )}
                      </p>

                    </div>

                  )}

                  {/* ====================================
                      3. RAG
                  ==================================== */}

                  {analysisResult.rag_result && (

                    <div className="mb-4 rounded-lg border border-border bg-bg-elevated p-4">

                      <h3 className="text-sm font-semibold text-text-primary">
                        3. Knowledge Retrieval
                      </h3>

                      <p className="mt-2 text-xs text-text-secondary">
                        {String(
                          analysisResult.rag_result
                            .message ??
                            'Knowledge retrieval completed.'
                        )}
                      </p>

                      {Array.isArray(
                        analysisResult.rag_result
                          .documents
                      ) &&
                        analysisResult.rag_result.documents.length >
                          0 && (

                          <div className="mt-4 space-y-3">

                            {analysisResult.rag_result.documents.map(
                              (
                                document,
                                index
                              ) => (

                                <div
                                  key={index}
                                  className="rounded-md border border-border p-3"
                                >

                                  <p className="text-xs font-medium text-text-primary">
                                    Knowledge Document{' '}
                                    {index + 1}
                                  </p>

                                  <p className="mt-1 text-xs leading-5 text-text-secondary">
                                    {String(
                                      document.text ??
                                        ''
                                    )}
                                  </p>

                                  <p className="mt-2 text-[11px] text-text-secondary">
                                    Score:{' '}
                                    {typeof document.score ===
                                    'number'
                                      ? document.score.toFixed(
                                          3
                                        )
                                      : 'N/A'}
                                  </p>

                                </div>

                              )
                            )}

                          </div>

                        )}

                    </div>

                  )}

                  {/* ====================================
                      4. SOLUTION
                  ==================================== */}

                  {analysisResult.solution && (

                    <div className="mb-4 rounded-lg border border-border bg-bg-elevated p-4">

                      <div className="flex items-center justify-between gap-4">

                        <h3 className="text-sm font-semibold text-text-primary">
                          4. Proposed Solution
                        </h3>

                        <span className="rounded-full border border-border px-3 py-1 text-xs capitalize text-text-secondary">
                          Risk:{' '}
                          {String(
                            analysisResult.solution
                              .risk ??
                              'unknown'
                          )}
                        </span>

                      </div>

                      <p className="mt-3 text-sm leading-6 text-text-primary">
                        {String(
                          analysisResult.solution
                            .solution ??
                            'No solution generated.'
                        )}
                      </p>

                      {Array.isArray(
                        analysisResult.solution
                          .actions
                      ) && (

                        <div className="mt-4 space-y-2">

                          {analysisResult.solution.actions.map(
                            (
                              action,
                              index
                            ) => (

                              <p
                                key={index}
                                className="text-xs leading-5 text-text-secondary"
                              >
                                {index + 1}.{' '}
                                {String(action)}
                              </p>

                            )
                          )}

                        </div>

                      )}

                      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">

                        <div>

                          <p className="text-xs text-text-secondary">
                            Execution Action
                          </p>

                          <p className="mt-1 text-sm text-text-primary">
                            {String(
                              analysisResult.solution
                                .execution_action ??
                                'none'
                            )}
                          </p>

                        </div>

                        <div>

                          <p className="text-xs text-text-secondary">
                            Safe to Execute
                          </p>

                          <p className="mt-1 text-sm text-text-primary">
                            {String(
                              analysisResult.solution
                                .safe_to_execute
                            )}
                          </p>

                        </div>

                        <div>

                          <p className="text-xs text-text-secondary">
                            Confidence
                          </p>

                          <p className="mt-1 text-sm text-text-primary">
                            {String(
                              analysisResult.solution
                                .confidence ??
                                'unknown'
                            )}
                          </p>

                        </div>

                      </div>

                      <div className="mt-4 flex items-start gap-2">

                        <ShieldAlert
                          size={15}
                        />

                        <p className="text-xs leading-5 text-text-secondary">
                          Kubernetes write actions are not
                          enabled yet. No remediation is
                          executed from this screen.
                        </p>

                      </div>

                    </div>

                  )}

                  {/* ====================================
                      5. VERIFICATION
                  ==================================== */}

                  {analysisResult.verification && (

                    <div className="rounded-lg border border-border bg-bg-elevated p-4">

                      <div className="flex items-center gap-2">

                        {analysisResult.verification
                          .verified ? (

                          <CheckCircle
                            size={18}
                          />

                        ) : (

                          <ShieldAlert
                            size={18}
                          />

                        )}

                        <h3 className="text-sm font-semibold text-text-primary">
                          5. Verification
                        </h3>

                      </div>

                      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">

                        <div>

                          <p className="text-xs text-text-secondary">
                            Verified
                          </p>

                          <p className="mt-1 text-sm text-text-primary">
                            {String(
                              analysisResult.verification
                                .verified
                            )}
                          </p>

                        </div>

                        <div>

                          <p className="text-xs text-text-secondary">
                            Safe to Execute
                          </p>

                          <p className="mt-1 text-sm text-text-primary">
                            {String(
                              analysisResult.verification
                                .safe_to_execute
                            )}
                          </p>

                        </div>

                        <div>

                          <p className="text-xs text-text-secondary">
                            Human Approval
                          </p>

                          <p className="mt-1 text-sm text-text-primary">
                            {String(
                              analysisResult.verification
                                .requires_human_approval
                            )}
                          </p>

                        </div>

                      </div>

                      {Array.isArray(
                        analysisResult.verification
                          .reasons
                      ) && (

                        <div className="mt-4 space-y-2">

                          {analysisResult.verification.reasons.map(
                            (
                              reason,
                              index
                            ) => (

                              <p
                                key={index}
                                className="text-xs leading-5 text-text-secondary"
                              >
                                • {String(
                                  reason
                                )}
                              </p>

                            )
                          )}

                        </div>

                      )}

                    </div>

                  )}

                </div>

              )}

            {/* ==========================================
                POD DETAILS
            ========================================== */}

            {detailsLoading && (

              <div className="card">

                <LoadingState
                  label="Loading pod details..."
                />

              </div>

            )}

            {selectedPod &&
              !detailsLoading && (

                <div className="card p-5">

                  <div className="mb-4 flex items-center justify-between">

                    <div>

                      <h2 className="text-sm font-semibold text-text-primary">
                        Pod Details
                      </h2>

                      <p className="mt-1 text-xs text-text-secondary">
                        {selectedPod.name}
                      </p>

                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        setSelectedPod(null)
                      }
                      className="btn-ghost"
                    >
                      <X size={16} />
                    </button>

                  </div>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">

                    <div>

                      <p className="text-xs text-text-secondary">
                        Status
                      </p>

                      <p className="mt-1 text-sm text-text-primary">
                        {selectedPod.status}
                      </p>

                    </div>

                    <div>

                      <p className="text-xs text-text-secondary">
                        Namespace
                      </p>

                      <p className="mt-1 text-sm text-text-primary">
                        {selectedPod.namespace}
                      </p>

                    </div>

                    <div>

                      <p className="text-xs text-text-secondary">
                        Node
                      </p>

                      <p className="mt-1 text-sm text-text-primary">
                        {selectedPod.node ??
                          'Unknown'}
                      </p>

                    </div>

                    <div>

                      <p className="text-xs text-text-secondary">
                        Containers
                      </p>

                      <p className="mt-1 text-sm text-text-primary">
                        {selectedPod.containers.length}
                      </p>

                    </div>

                  </div>

                  {selectedPod.container_statuses
                    .length > 0 && (

                    <div className="mt-5">

                      <p className="text-xs font-medium text-text-primary">
                        Container Status
                      </p>

                      <div className="mt-3 space-y-2">

                        {selectedPod.container_statuses.map(
                          (container) => (

                            <div
                              key={
                                container.name
                              }
                              className="rounded-md border border-border p-3"
                            >

                              <p className="text-xs font-semibold text-text-primary">
                                {container.name}
                              </p>

                              <p className="mt-1 text-xs text-text-secondary">
                                Ready:{' '}
                                {String(
                                  container.ready
                                )}
                              </p>

                              <p className="mt-1 text-xs text-text-secondary">
                                Restarts:{' '}
                                {container.restart_count}
                              </p>

                            </div>

                          )
                        )}

                      </div>

                    </div>

                  )}

                </div>

              )}

            {/* ==========================================
                POD LOGS
            ========================================== */}

            {logsLoading && (

              <div className="card">

                <LoadingState
                  label="Loading pod logs..."
                />

              </div>

            )}

            {selectedLogs &&
              !logsLoading && (

                <div className="card p-5">

                  <div className="mb-4 flex items-center justify-between">

                    <div>

                      <h2 className="text-sm font-semibold text-text-primary">
                        Pod Logs
                      </h2>

                      <p className="mt-1 text-xs text-text-secondary">
                        {selectedLogs.pod_name}
                      </p>

                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        setSelectedLogs(null)
                      }
                      className="btn-ghost"
                    >
                      <X size={16} />
                    </button>

                  </div>

                  <pre className="max-h-[500px] overflow-auto rounded-lg border border-border bg-bg p-4 text-xs leading-5 text-text-secondary">
                    {selectedLogs.logs ||
                      'No logs available.'}
                  </pre>

                </div>

              )}

          </>
        )}

    </div>
  );
}