import {
  Task,
  TaskCreateRequest,
  StartAnalysisRequest,
  PaginatedResults,
  SpiderResultsResponse,
  FilterKeywordsPreset,
  FilterKeywordsRequest,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE = API_BASE.replace(/^http/, 'ws');

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || `HTTP ${res.status}`);
  }

  return res.json();
}

// ===== Task APIs =====

export async function createTask(req: TaskCreateRequest): Promise<Task> {
  return fetchApi<Task>('/api/tasks/', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function listTasks(): Promise<{ tasks: Task[]; total: number }> {
  return fetchApi('/api/tasks/');
}

export async function getTask(id: string): Promise<Task> {
  return fetchApi(`/api/tasks/${id}`);
}

export async function getSpiderResults(taskId: string): Promise<SpiderResultsResponse> {
  return fetchApi(`/api/tasks/${taskId}/spider-results`);
}

export async function startAnalysis(
  taskId: string,
  req?: StartAnalysisRequest
): Promise<{ status: string; task_id: string }> {
  return fetchApi(`/api/tasks/${taskId}/start-analysis`, {
    method: 'POST',
    body: JSON.stringify(req || {}),
  });
}

// ===== Results APIs =====

export async function getTaskResults(
  taskId: string,
  offset = 0,
  limit = 50
): Promise<PaginatedResults> {
  return fetchApi<PaginatedResults>(
    `/api/results/${taskId}?offset=${offset}&limit=${limit}`
  );
}

export function getExportExcelUrl(taskId: string): string {
  return `${API_BASE}/api/export/${taskId}/excel`;
}

export function getExportCsvUrl(taskId: string): string {
  return `${API_BASE}/api/export/${taskId}/csv`;
}

// ===== Filter Keywords APIs =====

export async function getDefaultKeywords(): Promise<{ keywords: string[] }> {
  return fetchApi('/api/keywords/defaults');
}

export async function listKeywordPresets(): Promise<FilterKeywordsPreset[]> {
  return fetchApi('/api/keywords/presets');
}

export async function createKeywordPreset(req: FilterKeywordsRequest): Promise<FilterKeywordsPreset> {
  return fetchApi('/api/keywords/presets', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function updateKeywordPreset(
  presetId: string,
  req: FilterKeywordsRequest
): Promise<FilterKeywordsPreset> {
  return fetchApi(`/api/keywords/presets/${presetId}`, {
    method: 'PUT',
    body: JSON.stringify(req),
  });
}

export async function deleteKeywordPreset(presetId: string): Promise<void> {
  return fetchApi(`/api/keywords/presets/${presetId}`, { method: 'DELETE' });
}

// ===== WebSocket =====

export function connectTaskWebSocket(taskId: string): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/ws/tasks/${taskId}`);
  return ws;
}

// ===== Health =====

export async function healthCheck(): Promise<{ status: string }> {
  return fetchApi('/api/health');
}
