import type {
  PodRecord,
  PodStatus,
} from '@/types/kubernetes';

import type {
  Severity,
} from '@/types/common';
const API_BASE_URL = 'http://127.0.0.1:8000';

// --------------------------------------------------
// Snapshot Types
// --------------------------------------------------

export interface KubernetesSnapshot {
  cluster: {
    status: string;
    runningPods: number;
    failedPods: number;
    podRestarts: number;
    cpuUsagePercent: number;
    memoryUsagePercent: number;
  };

  pods: PodRecord[];

  recommendations: {
  id: string;
  title: string;
  explanation: string;
  command: string;
  severity: Severity;
  }[];
}

// --------------------------------------------------
// Backend Response Types
// --------------------------------------------------

export interface KubernetesStatus {
  connected: boolean;
  node_count: number;
  nodes: {
    name: string;
    status: string;
  }[];
}

export interface KubernetesNode {
  name: string;
  ready: boolean;
  status: string;
  roles: string[];
  version?: string | null;
}

export interface KubernetesNodesResponse {
  count: number;
  nodes: KubernetesNode[];
}

export interface KubernetesPod {
  name: string;
  namespace: string;
  status: string;
  node?: string | null;
  restarts: number;
}

export interface KubernetesPodsResponse {
  namespace: string;
  count: number;
  pods: KubernetesPod[];
}

export interface KubernetesDeployment {
  name: string;
  namespace: string;
  replicas: number;
  available_replicas: number;
  ready_replicas: number;
}

export interface KubernetesDeploymentsResponse {
  namespace: string;
  count: number;
  deployments: KubernetesDeployment[];
}

export interface KubernetesService {
  name: string;
  namespace: string;
  type: string;
  cluster_ip?: string | null;
  ports: {
    port: number;
    target_port: string;
    protocol: string;
  }[];
}

export interface KubernetesServicesResponse {
  namespace: string;
  count: number;
  services: KubernetesService[];
}

export interface KubernetesPodDetails {
  name: string;
  namespace: string;
  status: string;
  node?: string | null;

  containers: {
    name: string;
    image?: string | null;
    command?: string[] | null;
  }[];

  container_statuses: {
    name: string;
    ready: boolean;
    restart_count: number;
    state?: Record<string, unknown> | null;
  }[];
}

export interface KubernetesPodLogsResponse {
  pod_name: string;
  namespace: string;
  logs: string;
}

// --------------------------------------------------
// Helpers
// --------------------------------------------------

function normalizePodStatus(
  status: string
): PodStatus {
  switch (status) {
    case 'Running':
      return 'Running';

    case 'Pending':
      return 'Pending';

    case 'Failed':
      return 'Failed';

    case 'Succeeded':
      return 'Succeeded';

    case 'CrashLoopBackOff':
      return 'CrashLoopBackOff';

    default:
      return 'Pending';
  }
}

// --------------------------------------------------
// Cluster Status
// --------------------------------------------------

export async function getKubernetesStatus(): Promise<KubernetesStatus> {
  const response = await fetch(
    `${API_BASE_URL}/api/kubernetes/status`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to connect to Kubernetes cluster.'
    );
  }

  return response.json();
}

// --------------------------------------------------
// Nodes
// --------------------------------------------------

export async function getKubernetesNodes(): Promise<KubernetesNodesResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/kubernetes/nodes`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch Kubernetes nodes.'
    );
  }

  return response.json();
}

// --------------------------------------------------
// Pods
// --------------------------------------------------

export async function getKubernetesPods(
  namespace = 'default'
): Promise<KubernetesPodsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/kubernetes/pods?namespace=${encodeURIComponent(
      namespace
    )}`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch Kubernetes pods.'
    );
  }

  return response.json();
}

// --------------------------------------------------
// Pod Details
// --------------------------------------------------

export async function getKubernetesPod(
  podName: string,
  namespace = 'default'
): Promise<KubernetesPodDetails> {
  const response = await fetch(
    `${API_BASE_URL}/api/kubernetes/pods/${encodeURIComponent(
      podName
    )}?namespace=${encodeURIComponent(namespace)}`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch Kubernetes pod details.'
    );
  }

  return response.json();
}

// --------------------------------------------------
// Pod Logs
// --------------------------------------------------

export async function getKubernetesPodLogs(
  podName: string,
  namespace = 'default'
): Promise<KubernetesPodLogsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/kubernetes/pods/${encodeURIComponent(
      podName
    )}/logs?namespace=${encodeURIComponent(namespace)}`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch Kubernetes pod logs.'
    );
  }

  return response.json();
}

// --------------------------------------------------
// Deployments
// --------------------------------------------------

export async function getKubernetesDeployments(
  namespace = 'default'
): Promise<KubernetesDeploymentsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/kubernetes/deployments?namespace=${encodeURIComponent(
      namespace
    )}`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch Kubernetes deployments.'
    );
  }

  return response.json();
}

// --------------------------------------------------
// Services
// --------------------------------------------------

export async function getKubernetesServices(
  namespace = 'default'
): Promise<KubernetesServicesResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/kubernetes/services?namespace=${encodeURIComponent(
      namespace
    )}`
  );

  if (!response.ok) {
    throw new Error(
      'Unable to fetch Kubernetes services.'
    );
  }

  return response.json();
}

// --------------------------------------------------
// Snapshot
// --------------------------------------------------

export async function getKubernetesSnapshot(): Promise<KubernetesSnapshot> {
  const [
    status,
    nodesResponse,
    podsResponse,
    deploymentsResponse,
  ] = await Promise.all([
    getKubernetesStatus(),
    getKubernetesNodes(),
    getKubernetesPods('default'),
    getKubernetesDeployments('default'),
  ]);

  const pods: PodRecord[] =
    podsResponse.pods.map((pod) => {
      const normalizedStatus =
        normalizePodStatus(pod.status);

      const issue =
        normalizedStatus === 'Failed'
          ? 'Pod failed'
          : pod.restarts > 0
            ? `${pod.restarts} restart(s)`
            : '';

      return {
        id: `${pod.namespace}/${pod.name}`,
        name: pod.name,
        namespace: pod.namespace,
        status: normalizedStatus,
        cpu: 'N/A',
        memory: 'N/A',
        restarts: pod.restarts,
        issue,
      };
    });

  const runningPods = pods.filter(
    (pod) => pod.status === 'Running'
  ).length;

  const failedPods = pods.filter(
    (pod) =>
      pod.status === 'Failed' ||
      pod.status === 'CrashLoopBackOff'
  ).length;

   const podRestarts =
  pods.filter(
    (pod) =>
      pod.restarts > 0
  ).length;

  const clusterHealthy =
    status.connected &&
    nodesResponse.nodes.length > 0 &&
    nodesResponse.nodes.every(
      (node) => node.ready
    );

  const recommendations: KubernetesSnapshot['recommendations'] =
    [];

  if (failedPods > 0) {
    recommendations.push({
      id: 'failed-pods',
      title: 'Failed pods detected',
      explanation:
        'One or more Kubernetes pods are in a failed state. Inspect pod details and logs before taking remediation actions.',
      command: 'kubectl get pods -A',
      severity: 'high',
    });
  }

  if (podRestarts > 0) {
    recommendations.push({
      id: 'pod-restarts',
      title: 'Pod restarts detected',
      explanation:
        'One or more pods have restarted. Investigate container logs and pod events to determine whether the restarts indicate an application problem.',
      command: 'kubectl get pods -A',
      severity: 'medium',
    });
  }

  if (recommendations.length === 0) {
    recommendations.push({
      id: 'cluster-healthy',
      title: 'Cluster is operating normally',
      explanation:
        'The Kubernetes API is reachable, the available node is Ready, and no failed pods or restart conditions were detected in the default namespace.',
      command: 'kubectl get pods -A',
      severity: 'low',
    });
  }

  return {
    cluster: {
      status: clusterHealthy
        ? 'Healthy'
        : 'Warning',

      runningPods,
      failedPods,
      podRestarts,

      // Metrics Server is not connected yet.
      cpuUsagePercent: 0,
      memoryUsagePercent: 0,
    },

    pods,
    recommendations,
  };
}