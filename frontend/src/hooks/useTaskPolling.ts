'use client';

import { useEffect, useRef, useCallback } from 'react';
import { getTask, Task } from '@/lib/api';

export function useTaskPolling(
  taskId: string | null,
  onUpdate: (task: Task) => void,
  interval: number = 3000
) {
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!taskId) return;

    const poll = async () => {
      try {
        const task = await getTask(taskId);
        onUpdateRef.current(task);

        if (task.status === 'completed' || task.status === 'failed') {
          stopPolling();
        }
      } catch {
        // Ignore polling errors
      }
    };

    // Initial fetch
    poll();

    timerRef.current = setInterval(poll, interval);
    return stopPolling;
  }, [taskId, interval, stopPolling]);

  return { stopPolling };
}
