'use client';

import React, { useState } from 'react';
import { Bell, X } from 'lucide-react';
import { useNotifications } from '@/hooks/useNotifications';

interface NotificationBannerProps {
  onDismiss?: () => void;
}

export const NotificationBanner: React.FC<NotificationBannerProps> = ({ onDismiss }) => {
  const { isSupported, permission, requestPermission } = useNotifications();
  const [isRequesting, setIsRequesting] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  // Don't show if notifications aren't supported, already granted, or dismissed
  if (!isSupported || permission === 'granted' || permission === 'denied' || isDismissed) {
    return null;
  }

  const handleRequestPermission = async () => {
    setIsRequesting(true);
    try {
      const result = await requestPermission();
      if (result === 'granted') {
        setIsDismissed(true);
        onDismiss?.();
      }
    } catch (error) {
      console.error('Failed to request notification permission:', error);
    } finally {
      setIsRequesting(false);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  return (
    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
      <div className="flex items-start space-x-3">
        <Bell className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="text-sm font-medium text-blue-900 dark:text-blue-100">
            Enable Notifications
          </h3>
          <p className="text-sm text-blue-700 dark:text-blue-200 mt-1">
            Get notified when your floor plan conversions are complete, even when you&apos;re on another tab.
          </p>
          <div className="mt-3 flex items-center space-x-3">
            <button
              onClick={handleRequestPermission}
              disabled={isRequesting}
              className="text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-3 py-1.5 rounded-md transition-colors"
            >
              {isRequesting ? 'Requesting...' : 'Enable Notifications'}
            </button>
            <button
              onClick={handleDismiss}
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 transition-colors"
            >
              Maybe later
            </button>
          </div>
        </div>
        <button
          onClick={handleDismiss}
          className="text-blue-400 hover:text-blue-600 dark:text-blue-300 dark:hover:text-blue-100 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default NotificationBanner;
