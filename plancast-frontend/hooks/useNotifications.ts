'use client';

import { useEffect, useState, useCallback } from 'react';

export interface NotificationOptions {
  title: string;
  body: string;
  icon?: string;
  tag?: string;
  requireInteraction?: boolean;
  silent?: boolean;
}

export const useNotifications = () => {
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    // Check if notifications are supported
    setIsSupported('Notification' in window);
    
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }
  }, []);

  const requestPermission = useCallback(async (): Promise<NotificationPermission> => {
    if (!isSupported) {
      return 'denied';
    }

    if (permission === 'granted') {
      return 'granted';
    }

    try {
      const result = await Notification.requestPermission();
      setPermission(result);
      return result;
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return 'denied';
    }
  }, [isSupported, permission]);

  const showNotification = useCallback(async (options: NotificationOptions): Promise<boolean> => {
    if (!isSupported) {
      console.warn('Notifications are not supported in this browser');
      return false;
    }

    // Request permission if not already granted
    const currentPermission = permission === 'granted' ? 'granted' : await requestPermission();
    
    if (currentPermission !== 'granted') {
      console.warn('Notification permission not granted');
      return false;
    }

    try {
      const notification = new Notification(options.title, {
        body: options.body,
        icon: options.icon || '/favicon.ico',
        tag: options.tag,
        requireInteraction: options.requireInteraction || false,
        silent: options.silent || false,
      });

      // Auto-close notification after 5 seconds if not requiring interaction
      if (!options.requireInteraction) {
        setTimeout(() => {
          notification.close();
        }, 5000);
      }

      return true;
    } catch (error) {
      console.error('Error showing notification:', error);
      return false;
    }
  }, [isSupported, permission, requestPermission]);

  const showJobNotification = useCallback(async (
    jobId: string, 
    status: 'completed' | 'failed',
    message?: string
  ): Promise<boolean> => {
    const options: NotificationOptions = {
      title: `PlanCast - Job ${status === 'completed' ? 'Completed' : 'Failed'}`,
      body: status === 'completed' 
        ? message || 'Your floor plan conversion is ready!'
        : message || 'Your floor plan conversion failed. Please try again.',
      icon: '/favicon.ico',
      tag: `job-${jobId}`,
      requireInteraction: status === 'failed', // Keep error notifications visible
    };

    return await showNotification(options);
  }, [showNotification]);

  return {
    isSupported,
    permission,
    requestPermission,
    showNotification,
    showJobNotification,
    isGranted: permission === 'granted',
    isDenied: permission === 'denied',
    isDefault: permission === 'default',
  };
};

export default useNotifications;
