'use client'

import { SessionProvider } from 'next-auth/react'
import { WebSocketProvider } from '@/lib/websocket-context'
import { NotificationProvider } from '@/hooks/useNotifications'
import React from 'react'
import { AuthProvider } from '@/lib/auth-context'

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <React.StrictMode>
      <SessionProvider>
        <NotificationProvider>
            <WebSocketProvider>
              {children}
            </WebSocketProvider>
        </NotificationProvider>
      </SessionProvider>
    </React.StrictMode>
  )
}
