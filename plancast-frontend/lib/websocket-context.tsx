'use client';

import React, { createContext, useContext, useCallback, useState } from 'react';
import { useWebSocket, WebSocketMessage, JobStatusUpdate } from '@/hooks/useWebSocket';
import { useAuth } from './auth-context';
import { useNotifications } from '@/hooks/useNotifications';

interface WebSocketContextType {
  isConnected: boolean;
  connectionError: Error | null;
  lastMessage: WebSocketMessage | null;
  jobUpdates: Map<string, JobStatusUpdate>;
  subscribeToJob: (jobId: string) => void;
  unsubscribeFromJob: (jobId: string) => void;
  sendMessage: (type: string, data: any) => boolean;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const { user } = useAuth();
  const { showJobNotification } = useNotifications();
  const [jobUpdates, setJobUpdates] = useState<Map<string, JobStatusUpdate>>(new Map());

  const handleJobUpdate = useCallback((update: JobStatusUpdate) => {
    setJobUpdates(prev => {
      const newMap = new Map(prev);
      newMap.set(update.jobId, update);
      return newMap;
    });

    // Show notification for completed jobs
    if (update.status === 'completed') {
      showJobNotification(update.jobId, 'completed', update.message);
    }

    // Show notification for failed jobs
    if (update.status === 'failed') {
      showJobNotification(update.jobId, 'failed', update.message);
    }
  }, [showJobNotification]);

  const handleConnect = useCallback(() => {
    console.log('WebSocket connected to PlanCast backend');
    
    // Authenticate the connection if user is logged in
    if (user) {
      sendMessage('authenticate', { userId: user.id, email: user.email });
    }
  }, [user]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    console.log('WebSocket message received:', message);
  }, []);

  const {
    isConnected,
    connectionError,
    lastMessage,
    sendMessage,
    subscribeToJob,
    unsubscribeFromJob,
  } = useWebSocket({
    url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
    autoConnect: !!user, // Only connect when user is authenticated
    onConnect: handleConnect,
    onMessage: handleMessage,
    onJobUpdate: handleJobUpdate,
  });

  const value: WebSocketContextType = {
    isConnected,
    connectionError,
    lastMessage,
    jobUpdates,
    subscribeToJob,
    unsubscribeFromJob,
    sendMessage,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export default WebSocketProvider;
