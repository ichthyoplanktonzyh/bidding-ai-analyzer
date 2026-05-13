'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { getTask, connectTaskWebSocket } from '@/lib/api';
import type { Task, WsEvent } from '@/lib/types';

/**
 * Hook that monitors task status via WebSocket with polling fallback.
 * Merges WebSocket partial updates with the last-known full task to avoid UI flicker.
 */
export function useTaskPolling(
  taskId: string | null,
  onUpdate: (task: Task) => void,
  interval: number = 3000
) {
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;
  const lastTaskRef = useRef<Task | null>(null);

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!taskId) return;

    // Fetch full task first, then connect WebSocket
    getTask(taskId).then((task) => {
      lastTaskRef.current = task;
      onUpdateRef.current(task);
    }).catch(() => {});

    const ws = connectTaskWebSocket(taskId);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data: WsEvent = JSON.parse(event.data);
        if (data.type === 'status_update' && lastTaskRef.current) {
          const prev = lastTaskRef.current;
          // Only update if something actually changed
          if (
            prev.status !== data.status ||
            prev.progress !== data.progress ||
            prev.total_items !== data.total_items ||
            prev.analyzed_items !== data.analyzed_items ||
            prev.spider_item_count !== data.spider_item_count
          ) {
            const updated: Task = {
              ...prev,
              status: data.status,
              progress: data.progress,
              total_items: data.total_items,
              analyzed_items: data.analyzed_items,
              spider_item_count: data.spider_item_count,
              error: data.error || prev.error,
            };
            lastTaskRef.current = updated;
            onUpdateRef.current(updated);
          }
        } else if (data.type === 'pipeline_complete') {
          stopPolling();
        }
      } catch {
        // Ignore parse errors
      }
    };

    ws.onerror = () => {
      wsRef.current = null;
      const poll = async () => {
        try {
          const task = await getTask(taskId);
          lastTaskRef.current = task;
          onUpdateRef.current(task);
          if (task.status === 'completed' || task.status === 'failed') {
            stopPolling();
          }
        } catch {
          // Ignore polling errors
        }
      };
      poll();
      timerRef.current = setInterval(poll, interval);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      stopPolling();
    };
  }, [taskId, interval, stopPolling]);

  return { stopPolling };
}

/**
 * Hook for WebSocket connection to a specific task.
 */
export function useWebSocket(taskId: string | null) {
  const [lastEvent, setLastEvent] = useState<WsEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const ws = connectTaskWebSocket(taskId);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      try {
        const data: WsEvent = JSON.parse(event.data);
        setLastEvent(data);
      } catch {
        // Ignore
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
      setConnected(false);
    };
  }, [taskId]);

  return { lastEvent, connected };
}
