'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useNotifications } from './useNotifications';

interface UseWebSocketOptions {
  url?: string;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onMessage?: (type: string, data: any) => void;
  onError?: (error: Error) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    url = process.env.NEXT_PUBLIC_WS_URL || 'wss://api.getplancast.com',
    onConnect,
    onDisconnect,
    onMessage,
    onError,
  } = options;

  const socketRef = useRef<Socket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<Error | null>(null);
  const { addNotification } = useNotifications();

  const maxReconnectAttempts = 5;
  const reconnectDelay = 1000;

  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      return;
    }

    try {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }

      console.log('🔌 Attempting WebSocket connection to:', url);
      socketRef.current = io(url, {
        path: '/socket.io',
        transports: ['websocket', 'polling'],
        upgrade: true,
        rememberUpgrade: true,
        withCredentials: true,
        timeout: 20000,
        forceNew: true
      });

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

        if (reason === 'io server disconnect') {
          return;
        }

        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = reconnectDelay * Math.pow(2, reconnectAttemptsRef.current);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        } else {
            addNotification({
                id: 'ws-reconnect-failed',
                type: 'error',
                message: 'Could not reconnect to the server. Please refresh the page.',
                duration: null,
            });
        }
      });

      socketRef.current.on('connect_error', (error) => {
        console.error('🔌 WebSocket connection error:', error);
        setConnectionError(error);
        setIsConnected(false);
        onError?.(error);
        addNotification({
            id: 'ws-connect-error',
            type: 'error',
            message: 'Could not connect to the server. Please check your connection.',
            duration: 5000,
        });
      });

      socketRef.current.on('message', (data: { type: string; payload: any }) => {
        onMessage?.(data.type, data.payload);
      });

    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      setConnectionError(error as Error);
    }
  }, [url, onConnect, onDisconnect, onMessage, onError, addNotification]);

  useEffect(() => {
    connect();

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const sendMessage = useCallback((type: string, data: Record<string, unknown>): boolean => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('message', { type, payload: data });
      return true;
    }
    return false;
  }, []);

  return { isConnected, connectionError, sendMessage };
};
