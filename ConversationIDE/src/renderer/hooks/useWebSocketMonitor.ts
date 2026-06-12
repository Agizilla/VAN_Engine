import { useState, useEffect, useCallback, useRef } from 'react';

export interface StepExecution {
  id: string;
  action: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

export interface PipelineExecution {
  id: string;
  agent: string;
  pipeline: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  current_step: string;
  steps: StepExecution[];
  start_time: number;
  end_time?: number;
  error?: string;
}

export interface MonitorEvent {
  event: string;
  data: any;
  timestamp: number;
}

export function useWebSocketMonitor(url: string = 'ws://localhost:8765/ws') {
  const [isConnected, setIsConnected] = useState(false);
  const [executions, setExecutions] = useState<PipelineExecution[]>([]);
  const [lastEvent, setLastEvent] = useState<MonitorEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('[WebSocket] Connected to monitor');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastEvent(data);

        if (data.event === 'init') {
          setExecutions(data.data.executions || []);
        } else if (data.event === 'pipeline:start' || data.event === 'pipeline:update') {
          fetchExecutions();
        }
      } catch (err) {
        console.error('[WebSocket] Parse error:', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      reconnectTimeoutRef.current = setTimeout(connect, 2000);
    };

    ws.onerror = (err) => {
      console.error('[WebSocket] Error:', err);
    };

    wsRef.current = ws;
  }, [url]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const fetchExecutions = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8765/api/executions');
      const data = await response.json();
      setExecutions(data.executions || []);
    } catch (err) {
      console.error('[WebSocket] Failed to fetch executions:', err);
    }
  }, []);

  const startPipeline = useCallback(async (pipeline: string, agent: string, steps: { id: string; action: string }[]) => {
    try {
      const response = await fetch('http://localhost:8765/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pipeline, agent, steps })
      });
      const data = await response.json();
      return data.id;
    } catch (err) {
      console.error('[WebSocket] Failed to start pipeline:', err);
      return null;
    }
  }, []);

  const updatePipeline = useCallback(async (id: string, status: string, result?: any, error?: string) => {
    try {
      await fetch('http://localhost:8765/api/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, status, result, error })
      });
    } catch (err) {
      console.error('[WebSocket] Failed to update pipeline:', err);
    }
  }, []);

  const updateStep = useCallback(async (executionId: string, stepId: string, status: string, output?: any, error?: string) => {
    try {
      await fetch('http://localhost:8765/api/step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ executionId, stepId, status, output, error })
      });
    } catch (err) {
      console.error('[WebSocket] Failed to update step:', err);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  const stats = {
    total: executions.length,
    running: executions.filter(e => e.status === 'running').length,
    completed: executions.filter(e => e.status === 'completed').length,
    failed: executions.filter(e => e.status === 'failed').length
  };

  return { isConnected, executions, stats, lastEvent, startPipeline, updatePipeline, updateStep, refresh: fetchExecutions };
}
