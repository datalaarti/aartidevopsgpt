import { mockDelay } from '@/lib/utils';
import { mockDockerAnalysis } from '@/mocks/dockerMockData';
import type { DockerAnalysisResult } from '@/types/docker';

export interface AnalyzeDockerfileRequest {
  dockerfileContent: string;
}

// Keep the existing mock Dockerfile analyzer for now.
// We will replace this with a real AI endpoint later.
export async function analyzeDockerfile(
  _request: AnalyzeDockerfileRequest
): Promise<DockerAnalysisResult> {
  return mockDelay(mockDockerAnalysis, 1500);
}

// --------------------------------------------------
// Real Docker Backend API
// --------------------------------------------------

const API_BASE_URL = 'http://127.0.0.1:8000';

export interface DockerStatus {
  connected: boolean;
  message: string;
}

export interface DockerContainer {
  id: string;
  name: string;
  status: string;
  image: string[];
  created?: string;
  ports?: Record<string, unknown> | null;
}

export interface DockerContainersResponse {
  count: number;
  containers: DockerContainer[];
}

export interface DockerImage {
  id: string;
  tags: string[];
  created?: string;
  size?: number;
}

export interface DockerImagesResponse {
  count: number;
  images: DockerImage[];
}

export interface DockerVolume {
  name: string;
  driver?: string;
}

export interface DockerVolumesResponse {
  count: number;
  volumes: DockerVolume[];
}

export interface DockerNetwork {
  id: string;
  name: string;
  driver?: string;
}

export interface DockerNetworksResponse {
  count: number;
  networks: DockerNetwork[];
}

export async function getDockerStatus(): Promise<DockerStatus> {
  const response = await fetch(
    `${API_BASE_URL}/api/docker/status`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to connect to Docker backend.'
    );
  }

  return response.json();
}

export async function getDockerContainers(): Promise<DockerContainersResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/docker/containers`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch Docker containers.'
    );
  }

  return response.json();
}

export async function getDockerContainer(
  containerId: string
) {
  const response = await fetch(
    `${API_BASE_URL}/api/docker/containers/${containerId}`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch container details.'
    );
  }

  return response.json();
}

export async function getDockerContainerLogs(
  containerId: string
) {
  const response = await fetch(
    `${API_BASE_URL}/api/docker/containers/${containerId}/logs`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch container logs.'
    );
  }

  return response.json();
}

export async function getDockerImages(): Promise<DockerImagesResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/docker/images`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch Docker images.'
    );
  }

  return response.json();
}

export async function getDockerVolumes(): Promise<DockerVolumesResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/docker/volumes`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch Docker volumes.'
    );
  }

  return response.json();
}

export async function getDockerNetworks(): Promise<DockerNetworksResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/docker/networks`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch Docker networks.'
    );
  }

  return response.json();
}

// --------------------------------------------------
// DevOpsGPT Agent Analysis
// --------------------------------------------------

export interface AgentAnalysisRequest {
  domain: string;
  resource_id: string;
}

export interface AgentAnalysisResponse {
  domain: string;
  resource_id: string;
  investigation: Record<string, any> | null;
  root_cause: Record<string, any> | null;
  rag_result: Record<string, any> | null;
  solution: Record<string, any> | null;
  verification: Record<string, any> | null;
}

export async function analyzeWithAgent(
  request: AgentAnalysisRequest
): Promise<AgentAnalysisResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/agent/analyze`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();

    throw new Error(
      errorText || 'Agent analysis failed.'
    );
  }

  return response.json();
}

// --------------------------------------------------
// Human Approval + Remediation
// --------------------------------------------------

export interface ApprovalRequest {
  domain: string;
  resource_id: string;
  action: 'restart_container';
  approved: boolean;
  verification: Record<string, unknown>;
}

export interface ApprovalResponse {
  approved: boolean;
  executed: boolean;
  action?: string;
  result?: Record<string, unknown>;
  post_verification?: Record<string, unknown>;
  resolved?: boolean;
  message: string;
}

export async function approveAgentAction(
  request: ApprovalRequest
): Promise<ApprovalResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/agent/approve`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();

    throw new Error(
      errorText || 'Unable to execute approved action.'
    );
  }

  return response.json();
}