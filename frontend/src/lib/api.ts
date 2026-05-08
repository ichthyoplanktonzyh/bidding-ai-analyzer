import { Task, TaskCreateRequest, PaginatedResults } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

// ===== Health =====

export async function healthCheck(): Promise<{ status: string }> {
  return fetchApi('/api/health');
}
