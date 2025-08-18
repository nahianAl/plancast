'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

export interface WebSocketMessage {
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface JobStatusUpdate {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message?: string;
  result?: Record<string, unknown>;
}

interface UseWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  onMessage?: (message: WebSocketMessage) => void;
  onJobUpdate?: (update: JobStatusUpdate) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    url = process.env.NEXT_PUBLIC_WS_URL || 'wss://api.getplancast.com',
    autoConnect = true,
    onMessage,
    onJobUpdate,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<Error | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const maxReconnectAttempts = 5;
  const reconnectDelay = 1000;

  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      return;
    }

    try {
      // Clean up existing connection
      if (socketRef.current) {
        socketRef.current.disconnect();
      }

      // Create new socket connection
      console.log('🔌 Attempting WebSocket connection to:', url);
      socketRef.current = io(url, {
        path: '/socket.io',
        transports: ['websocket', 'polling'],  // Try WebSocket first, then polling
        upgrade: true,
        rememberUpgrade: true,
        withCredentials: true,
        // TEMPORARY: Add timeout and retry settings for debugging
        timeout: 20000,
        forceNew: true
      });

      // Connection event handlers
      socketRef.current.on('connect', () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      });

      socketRef.current.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        setIsConnected(false);
        onDisconnect?.();

        // Auto-reconnect for certain disconnect reasons
        if (reason === 'io server disconnect') {
          // Server initiated disconnect, don't reconnect
          return;
        }

        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = reconnectDelay * Math.pow(2, reconnectAttemptsRef.current);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      });

      // TEMPORARY: Add error handling for CORS issues
      socketRef.current.on('connect_error', (error) => {
        console.error('🔌 WebSocket connection error:', error);
        console.error('🔌 Error details:', {
          message: error.message,
          name: error.name,
          stack: error.stack
        });
        setConnectionError(error);
        setIsConnected(false);
        onError?.(error);
      });

      // Message handlers
      socketRef.current.on('message', (data) => {
        const message: WebSocketMessage = {
          type: 'message',
          data: data as Record<string, unknown>,
          timestamp: new Date().toISOString(),
        };
        setLastMessage(message);
        onMessage?.(message);
      });

      // Job status updates
      socketRef.current.on('job_status', (data: JobStatusUpdate) => {
        const message: WebSocketMessage = {
          type: 'job_status',
          data: data as unknown as Record<string, unknown>,
          timestamp: new Date().toISOString(),
        };
        setLastMessage(message);
        onMessage?.(message);
        onJobUpdate?.(data);
      });

      // Processing progress updates
      socketRef.current.on('processing_progress', (data) => {
        const message: WebSocketMessage = {
          type: 'processing_progress',
          data: data as Record<string, unknown>,
          timestamp: new Date().toISOString(),
        };
        setLastMessage(message);
        onMessage?.(message);
        onJobUpdate?.(data);
      });

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionError(error as Error);
      onError?.(error as Error);
    }
  }, [url, onConnect, onDisconnect, onError, onMessage, onJobUpdate]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionError(null);
    reconnectAttemptsRef.current = 0;
  }, []);

  const sendMessage = useCallback((type: string, data: Record<string, unknown>) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(type, data);
      return true;
    }
    console.warn('WebSocket not connected, message not sent:', { type, data });
    return false;
  }, []);

  const subscribeToJob = useCallback((jobId: string) => {
    return sendMessage('subscribe_job', { jobId });
  }, [sendMessage]);

  const unsubscribeFromJob = useCallback((jobId: string) => {
    return sendMessage('unsubscribe_job', { jobId });
  }, [sendMessage]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    connectionError,
    lastMessage,
    connect,
    disconnect,
    sendMessage,
    subscribeToJob,
    unsubscribeFromJob,
  };
};

export default useWebSocket;
