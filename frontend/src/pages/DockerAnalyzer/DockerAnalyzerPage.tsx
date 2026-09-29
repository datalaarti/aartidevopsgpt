import { useEffect, useState } from 'react';
import {
  Container,
  Image,
  Network,
  HardDrive,
  RefreshCw,
  AlertCircle,
  Eye,
  FileText,
  X,
  Brain,
  CheckCircle,
  ShieldAlert,
} from 'lucide-react';

import { PageHeader } from '@/components/common/PageHeader';
import { LoadingState } from '@/components/common/LoadingState';

import {
  getDockerStatus,
  getDockerContainers,
  getDockerImages,
  getDockerNetworks,
  getDockerVolumes,
  getDockerContainer,
  getDockerContainerLogs,
  analyzeWithAgent,
  approveAgentAction,
  type DockerContainer,
  type DockerImage,
  type DockerNetwork,
  type DockerVolume,
  type AgentAnalysisResponse,
} from '@/services/dockerService';

interface DockerContainerDetails {
  id: string;
  name: string;
  status: string;
  image: string[];
  created?: string;
  ports?: Record<string, unknown> | null;
  networks: string[];
}

interface DockerLogsResponse {
  container_id: string;
  container_name: string;
  logs: string;
}

export default function DockerAnalyzerPage() {
  const [connected, setConnected] = useState(false);

  const [containers, setContainers] =
    useState<DockerContainer[]>([]);

  const [images, setImages] =
    useState<DockerImage[]>([]);

  const [networks, setNetworks] =
    useState<DockerNetwork[]>([]);

  const [volumes, setVolumes] =
    useState<DockerVolume[]>([]);

  const [selectedContainer, setSelectedContainer] =
    useState<DockerContainerDetails | null>(null);

  const [selectedLogs, setSelectedLogs] =
    useState<DockerLogsResponse | null>(null);

  const [analysisResult, setAnalysisResult] =
    useState<AgentAnalysisResponse | null>(null);

  const [analyzingContainerId, setAnalyzingContainerId] =
    useState<string | null>(null);

  const [approvalLoading, setApprovalLoading] =
    useState(false);

  const [remediationResult, setRemediationResult] =
    useState<{
      resolved: boolean;
      message: string;
      post_verification?: Record<string, unknown>;
    } | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [detailsLoading, setDetailsLoading] =
    useState(false);

  const [logsLoading, setLogsLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const loadDockerData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [
        statusData,
        containersData,
        imagesData,
        networksData,
        volumesData,
      ] = await Promise.all([
        getDockerStatus(),
        getDockerContainers(),
        getDockerImages(),
        getDockerNetworks(),
        getDockerVolumes(),
      ]);

      setConnected(statusData.connected);
      setContainers(containersData.containers);
      setImages(imagesData.images);
      setNetworks(networksData.networks);
      setVolumes(volumesData.volumes);
    } catch (err) {
      setConnected(false);

      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load Docker environment.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDockerData();
  }, []);

  const handleDetails = async (
    containerId: string
  ) => {
    setDetailsLoading(true);
    setSelectedLogs(null);

    try {
      const details =
        await getDockerContainer(containerId);

      setSelectedContainer(details);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load container details.'
      );
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleLogs = async (
    containerId: string
  ) => {
    setLogsLoading(true);
    setSelectedContainer(null);

    try {
      const logs =
        await getDockerContainerLogs(containerId);

      setSelectedLogs(logs);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load container logs.'
      );
    } finally {
      setLogsLoading(false);
    }
  };

  const handleAnalyze = async (
    containerId: string
  ) => {
    setAnalyzingContainerId(containerId);
    setSelectedContainer(null);
    setSelectedLogs(null);
    setAnalysisResult(null);
    setRemediationResult(null);
    setError(null);

    try {
      const result =
        await analyzeWithAgent({
          domain: 'docker',
          resource_id: containerId,
        });

      setAnalysisResult(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to analyze the Docker container.'
      );
    } finally {
      setAnalyzingContainerId(null);
    }
  };

  const handleApproveRemediation =
    async () => {
      if (!analysisResult?.verification) {
        setError(
          'Verification data is not available for this action.'
        );
        return;
      }

      if (!analysisResult.solution) {
        setError(
          'Solution data is not available for this action.'
        );
        return;
      }

      const safeToExecute =
        Boolean(
          analysisResult.solution
            .safe_to_execute
        ) &&
        Boolean(
          analysisResult.verification
            .safe_to_execute
        );

      const executionAction =
        String(
          analysisResult.solution
            .execution_action ?? 'none'
        );

      const currentStatus =
        String(
          analysisResult.investigation
            ?.status ?? ''
        ).toLowerCase();

      if (!safeToExecute) {
        setError(
          'This remediation cannot be executed because the solution and verification stages did not approve it.'
        );
        return;
      }

      if (
        executionAction !==
        'restart_container'
      ) {
        setError(
          'The proposed action is not supported by the available Docker remediation tools.'
        );
        return;
      }

      if (
        currentStatus === 'running'
      ) {
        setError(
          'The container is already running. Restart remediation is not available for a running container.'
        );
        return;
      }

      setApprovalLoading(true);
      setError(null);
      setRemediationResult(null);

      try {
        const result =
          await approveAgentAction({
            domain:
              analysisResult.domain,

            resource_id:
              analysisResult.resource_id,

            action:
              'restart_container',

            approved: true,

            verification:
              analysisResult.verification,
          });

        setRemediationResult({
          resolved:
            Boolean(result.resolved),

          message:
            result.message,

          post_verification:
            result.post_verification,
        });

        await loadDockerData();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to execute approved remediation.'
        );
      } finally {
        setApprovalLoading(false);
      }
    };

  const runningContainers =
    containers.filter(
      (container) =>
        container.status === 'running'
    ).length;

  const stoppedContainers =
    containers.filter(
      (container) =>
        container.status !== 'running'
    ).length;

  const investigation =
    analysisResult?.investigation;

  const rootCause =
    analysisResult?.root_cause;

  const ragResult =
    analysisResult?.rag_result;

  const solution =
    analysisResult?.solution;

  const verification =
    analysisResult?.verification;

  const executionAction =
    String(
      solution?.execution_action ??
        'none'
    );

  const canApproveRemediation =
    Boolean(
      solution?.safe_to_execute &&
        verification?.safe_to_execute
    ) &&
    executionAction ===
      'restart_container' &&
    String(
      investigation?.status ?? ''
    ).toLowerCase() !== 'running';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between gap-4">
        <PageHeader
          title="Docker Studio"
          subtitle="Monitor and analyze the Docker Engine running on your machine."
        />

        <button
          type="button"
          onClick={loadDockerData}
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

      {/* Docker Connection */}
      <div className="card flex items-center gap-3 p-4">
        <span
          className={`h-3 w-3 rounded-full ${
            connected
              ? 'bg-success'
              : 'bg-danger'
          }`}
        />

        <div>
          <p className="text-sm font-semibold text-text-primary">
            Docker Engine
          </p>

          <p className="text-xs text-text-secondary">
            {connected
              ? 'Connected to Docker Desktop'
              : 'Docker Desktop is unavailable'}
          </p>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="card">
          <LoadingState
            label="Loading Docker environment..."
          />
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="card flex items-start gap-3 p-5">
          <AlertCircle
            className="text-danger"
            size={20}
          />

          <div>
            <p className="text-sm font-semibold text-text-primary">
              Docker error
            </p>

            <p className="mt-1 text-xs text-text-secondary">
              {error}
            </p>
          </div>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Overview */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="card p-5">
              <div className="flex items-center gap-3">
                <Container size={20} />

                <div>
                  <p className="text-xs text-text-secondary">
                    Containers
                  </p>

                  <p className="text-2xl font-semibold text-text-primary">
                    {containers.length}
                  </p>
                </div>
              </div>

              <p className="mt-3 text-xs text-text-secondary">
                {runningContainers} running ·{' '}
                {stoppedContainers} stopped
              </p>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-3">
                <Image size={20} />

                <div>
                  <p className="text-xs text-text-secondary">
                    Images
                  </p>

                  <p className="text-2xl font-semibold text-text-primary">
                    {images.length}
                  </p>
                </div>
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-3">
                <Network size={20} />

                <div>
                  <p className="text-xs text-text-secondary">
                    Networks
                  </p>

                  <p className="text-2xl font-semibold text-text-primary">
                    {networks.length}
                  </p>
                </div>
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-3">
                <HardDrive size={20} />

                <div>
                  <p className="text-xs text-text-secondary">
                    Volumes
                  </p>

                  <p className="text-2xl font-semibold text-text-primary">
                    {volumes.length}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Containers */}
          <div className="card p-5">
            <div className="mb-4">
              <h2 className="text-sm font-semibold text-text-primary">
                Containers
              </h2>

              <p className="mt-1 text-xs text-text-secondary">
                Live information from your Docker Engine
              </p>
            </div>

            {containers.length === 0 ? (
              <p className="py-8 text-center text-sm text-text-secondary">
                No Docker containers found.
              </p>
            ) : (
              <div className="space-y-3">
                {containers.map(
                  (container) => (
                    <div
                      key={container.id}
                      className="rounded-lg border border-border bg-bg-elevated p-4"
                    >
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-text-primary">
                            {container.name}
                          </p>

                          <p className="mt-1 text-xs text-text-secondary">
                            Image:{' '}
                            {container
                              .image.length >
                            0
                              ? container.image.join(
                                  ', '
                                )
                              : 'Unknown'}
                          </p>

                          <p className="mt-1 text-xs text-text-secondary">
                            ID:{' '}
                            {container.id.slice(
                              0,
                              12
                            )}
                          </p>
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full border border-border px-3 py-1 text-xs capitalize text-text-secondary">
                            {container.status}
                          </span>

                          <button
                            type="button"
                            onClick={() =>
                              handleDetails(
                                container.id
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
                                container.id
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
                              handleAnalyze(
                                container.id
                              )
                            }
                            disabled={
                              analyzingContainerId ===
                              container.id
                            }
                            className="btn-secondary"
                          >
                            <Brain
                              size={15}
                              className={
                                analyzingContainerId ===
                                container.id
                                  ? 'animate-pulse'
                                  : ''
                              }
                            />

                            {analyzingContainerId ===
                            container.id
                              ? 'Analyzing...'
                              : 'Analyze'}
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                )}
              </div>
            )}
          </div>

          {/* Agent Analysis Loading */}
          {analyzingContainerId && (
            <div className="card">
              <LoadingState
                label="DevOpsGPT is analyzing the container..."
              />
            </div>
          )}

          {/* Agent Analysis */}
          {analysisResult &&
            !analyzingContainerId && (
              <div className="card p-5">
                <div className="mb-6 flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <Brain size={19} />

                      <h2 className="text-sm font-semibold text-text-primary">
                        DevOpsGPT Agent Analysis
                      </h2>
                    </div>

                    <p className="mt-1 text-xs text-text-secondary">
                      Common agentic pipeline
                      analysis for{' '}
                      {analysisResult.resource_id.slice(
                        0,
                        12
                      )}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      setAnalysisResult(
                        null
                      );
                      setRemediationResult(
                        null
                      );
                    }}
                    className="btn-ghost"
                  >
                    <X size={16} />
                  </button>
                </div>

                {/* Investigation */}
                {investigation && (
                  <div className="mb-4 rounded-lg border border-border bg-bg-elevated p-4">
                    <h3 className="text-sm font-semibold text-text-primary">
                      1. Investigation
                    </h3>

                    <p className="mt-2 text-xs text-text-secondary">
                      Container:{' '}
                      {String(
                        investigation.container_name ??
                          'Unknown'
                      )}
                    </p>

                    <p className="mt-1 text-xs text-text-secondary">
                      Status:{' '}
                      {String(
                        investigation.status ??
                          'Unknown'
                      )}
                    </p>

                    {Array.isArray(
                      investigation.observations
                    ) && (
                      <div className="mt-3 space-y-2">
                        {investigation.observations.map(
                          (
                            observation,
                            index
                          ) => (
                            <p
                              key={index}
                              className="text-xs leading-5 text-text-secondary"
                            >
                              •{' '}
                              {String(
                                observation
                              )}
                            </p>
                          )
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Root Cause */}
                {rootCause && (
                  <div className="mb-4 rounded-lg border border-border bg-bg-elevated p-4">
                    <div className="flex items-center justify-between gap-4">
                      <h3 className="text-sm font-semibold text-text-primary">
                        2. Root Cause
                      </h3>

                      <span className="rounded-full border border-border px-3 py-1 text-xs capitalize text-text-secondary">
                        Confidence:{' '}
                        {String(
                          rootCause.confidence ??
                            'unknown'
                        )}
                      </span>
                    </div>

                    <p className="mt-3 text-sm leading-6 text-text-primary">
                      {String(
                        rootCause.root_cause ??
                          'No root cause generated.'
                      )}
                    </p>

                    {Array.isArray(
                      rootCause.reasoning
                    ) && (
                      <div className="mt-3 space-y-2">
                        {rootCause.reasoning.map(
                          (
                            reason,
                            index
                          ) => (
                            <p
                              key={index}
                              className="text-xs leading-5 text-text-secondary"
                            >
                              •{' '}
                              {String(
                                reason
                              )}
                            </p>
                          )
                        )}
                      </div>
                    )}

                    <p className="mt-3 text-xs font-medium text-text-secondary">
                      More investigation
                      required:{' '}
                      {String(
                        rootCause.requires_more_investigation
                      )}
                    </p>
                  </div>
                )}

                {/* RAG */}
                {ragResult && (
                  <div className="mb-4 rounded-lg border border-border bg-bg-elevated p-4">
                    <h3 className="text-sm font-semibold text-text-primary">
                      3. Knowledge Retrieval
                    </h3>

                    <p className="mt-2 text-xs text-text-secondary">
                      {String(
                        ragResult.message ??
                          'Knowledge retrieval completed.'
                      )}
                    </p>

                    {Array.isArray(
                      ragResult.documents
                    ) &&
                      ragResult.documents
                        .length > 0 && (
                        <div className="mt-3 space-y-3">
                          {ragResult.documents.map(
                            (
                              document,
                              index
                            ) => (
                              <div
                                key={index}
                                className="rounded-md border border-border p-3"
                              >
                                <p className="text-xs font-medium text-text-primary">
                                  Knowledge
                                  Document{' '}
                                  {index +
                                    1}
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

                {/* Solution */}
                {solution && (
                  <div className="mb-4 rounded-lg border border-border bg-bg-elevated p-4">
                    <div className="flex items-center justify-between gap-4">
                      <h3 className="text-sm font-semibold text-text-primary">
                        4. Proposed Solution
                      </h3>

                      <span className="rounded-full border border-border px-3 py-1 text-xs capitalize text-text-secondary">
                        Risk:{' '}
                        {String(
                          solution.risk ??
                            'unknown'
                        )}
                      </span>
                    </div>

                    <p className="mt-3 text-sm leading-6 text-text-primary">
                      {String(
                        solution.solution ??
                          'No solution generated.'
                      )}
                    </p>

                    {Array.isArray(
                      solution.actions
                    ) && (
                      <div className="mt-3 space-y-2">
                        {solution.actions.map(
                          (
                            action,
                            index
                          ) => (
                            <p
                              key={index}
                              className="text-xs leading-5 text-text-secondary"
                            >
                              {index + 1}.{' '}
                              {String(
                                action
                              )}
                            </p>
                          )
                        )}
                      </div>
                    )}

                    <div className="mt-4 flex items-center gap-2">
                      <ShieldAlert
                        size={15}
                      />

                      <p className="text-xs font-medium text-text-secondary">
                        Safe to execute:{' '}
                        {String(
                          solution.safe_to_execute
                        )}
                      </p>
                    </div>

                    <p className="mt-2 text-xs text-text-secondary">
                      Execution action:{' '}
                      {String(
                        solution.execution_action ??
                          'none'
                      )}
                    </p>
                  </div>
                )}

                {/* Verification */}
                {verification && (
                  <div className="mb-4 rounded-lg border border-border bg-bg-elevated p-4">
                    <div className="flex items-center gap-2">
                      {verification.verified ? (
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

                    <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
                      <div>
                        <p className="text-xs text-text-secondary">
                          Verified
                        </p>

                        <p className="mt-1 text-sm text-text-primary">
                          {String(
                            verification.verified
                          )}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-text-secondary">
                          Safe to Execute
                        </p>

                        <p className="mt-1 text-sm text-text-primary">
                          {String(
                            verification.safe_to_execute
                          )}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-text-secondary">
                          Human Approval
                        </p>

                        <p className="mt-1 text-sm text-text-primary">
                          {String(
                            verification.requires_human_approval
                          )}
                        </p>
                      </div>
                    </div>

                    {Array.isArray(
                      verification.reasons
                    ) && (
                      <div className="mt-4 space-y-2">
                        {verification.reasons.map(
                          (
                            reason,
                            index
                          ) => (
                            <p
                              key={index}
                              className="text-xs leading-5 text-text-secondary"
                            >
                              •{' '}
                              {String(
                                reason
                              )}
                            </p>
                          )
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Human Approval */}
                {canApproveRemediation &&
                  !remediationResult && (
                    <div className="mb-4 rounded-lg border border-border bg-bg-elevated p-4">
                      <div className="flex items-start gap-3">
                        <ShieldAlert
                          size={19}
                        />

                        <div className="flex-1">
                          <h3 className="text-sm font-semibold text-text-primary">
                            6. Human Approval
                            Required
                          </h3>

                          <p className="mt-1 text-xs leading-5 text-text-secondary">
                            DevOpsGPT has
                            proposed a
                            Docker restart.
                            The action
                            will only be
                            executed
                            after your
                            explicit
                            approval.
                          </p>

                          <div className="mt-4">
                            <button
                              type="button"
                              onClick={
                                handleApproveRemediation
                              }
                              disabled={
                                approvalLoading
                              }
                              className="btn-secondary"
                            >
                              {approvalLoading ? (
                                <RefreshCw
                                  size={15}
                                  className="animate-spin"
                                />
                              ) : (
                                <CheckCircle
                                  size={15}
                                />
                              )}

                              {approvalLoading
                                ? 'Executing...'
                                : 'Approve & Execute Restart'}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                {/* Post-Remediation Verification */}
                {remediationResult && (
                  <div className="mb-4 rounded-lg border border-border bg-bg-elevated p-4">
                    <div className="flex items-center gap-2">
                      {remediationResult.resolved ? (
                        <CheckCircle
                          size={19}
                        />
                      ) : (
                        <ShieldAlert
                          size={19}
                        />
                      )}

                      <h3 className="text-sm font-semibold text-text-primary">
                        6. Post-Remediation
                        Verification
                      </h3>
                    </div>

                    <p className="mt-3 text-sm leading-6 text-text-primary">
                      {
                        remediationResult.message
                      }
                    </p>

                    <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
                      <div>
                        <p className="text-xs text-text-secondary">
                          Resolved
                        </p>

                        <p className="mt-1 text-sm text-text-primary">
                          {String(
                            remediationResult.resolved
                          )}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-text-secondary">
                          Container Status
                        </p>

                        <p className="mt-1 text-sm text-text-primary">
                          {String(
                            remediationResult
                              .post_verification
                              ?.status ??
                              'Unknown'
                          )}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-text-secondary">
                          Healthy
                        </p>

                        <p className="mt-1 text-sm text-text-primary">
                          {String(
                            remediationResult
                              .post_verification
                              ?.healthy ??
                              'Unknown'
                          )}
                        </p>
                      </div>
                    </div>

                    <p className="mt-4 text-xs text-text-secondary">
                      Docker Studio has been
                      refreshed with the latest
                      container state.
                    </p>
                  </div>
                )}
              </div>
            )}

          {/* Details */}
          {detailsLoading && (
            <div className="card">
              <LoadingState
                label="Loading container details..."
              />
            </div>
          )}

          {selectedContainer &&
            !detailsLoading && (
              <div className="card p-5">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h2 className="text-sm font-semibold text-text-primary">
                      Container Details
                    </h2>

                    <p className="mt-1 text-xs text-text-secondary">
                      {
                        selectedContainer.name
                      }
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() =>
                      setSelectedContainer(
                        null
                      )
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
                      {
                        selectedContainer.status
                      }
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-text-secondary">
                      Image
                    </p>

                    <p className="mt-1 text-sm text-text-primary">
                      {selectedContainer.image.join(
                        ', '
                      ) || 'Unknown'}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-text-secondary">
                      Container ID
                    </p>

                    <p className="mt-1 break-all text-sm text-text-primary">
                      {
                        selectedContainer.id
                      }
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-text-secondary">
                      Networks
                    </p>

                    <p className="mt-1 text-sm text-text-primary">
                      {selectedContainer
                        .networks
                        .length >
                      0
                        ? selectedContainer.networks.join(
                            ', '
                          )
                        : 'None'}
                    </p>
                  </div>
                </div>
              </div>
            )}

          {/* Logs */}
          {logsLoading && (
            <div className="card">
              <LoadingState
                label="Loading container logs..."
              />
            </div>
          )}

          {selectedLogs &&
            !logsLoading && (
              <div className="card p-5">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h2 className="text-sm font-semibold text-text-primary">
                      Container Logs
                    </h2>

                    <p className="mt-1 text-xs text-text-secondary">
                      {
                        selectedLogs.container_name
                      }
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

          {/* Images */}
          <div className="card p-5">
            <h2 className="mb-4 text-sm font-semibold text-text-primary">
              Images
            </h2>

            <div className="space-y-2">
              {images.map((image) => (
                <div
                  key={image.id}
                  className="rounded-lg border border-border bg-bg-elevated p-3"
                >
                  <p className="text-sm text-text-primary">
                    {image.tags.length >
                    0
                      ? image.tags.join(
                          ', '
                        )
                      : '<none>:<none>'}
                  </p>

                  <p className="mt-1 text-xs text-text-secondary">
                    ID:{' '}
                    {image.id
                      .replace(
                        'sha256:',
                        ''
                      )
                      .slice(0, 12)}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Networks */}
          <div className="card p-5">
            <h2 className="mb-4 text-sm font-semibold text-text-primary">
              Networks
            </h2>

            <div className="space-y-2">
              {networks.map(
                (network) => (
                  <div
                    key={network.id}
                    className="flex items-center justify-between rounded-lg border border-border bg-bg-elevated p-3"
                  >
                    <span className="text-sm text-text-primary">
                      {network.name}
                    </span>

                    <span className="text-xs text-text-secondary">
                      {network.driver ??
                        'unknown'}
                    </span>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Volumes */}
          <div className="card p-5">
            <h2 className="mb-4 text-sm font-semibold text-text-primary">
              Volumes
            </h2>

            <div className="space-y-2">
              {volumes.map(
                (volume) => (
                  <div
                    key={volume.name}
                    className="flex items-center justify-between rounded-lg border border-border bg-bg-elevated p-3"
                  >
                    <span className="text-sm text-text-primary">
                      {volume.name}
                    </span>

                    <span className="text-xs text-text-secondary">
                      {volume.driver ??
                        'unknown'}
                    </span>
                  </div>
                )
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}