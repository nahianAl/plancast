'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { CheckCircle, Clock, AlertCircle, Loader2 } from 'lucide-react';
import { JobStatusUpdate } from '@/hooks/useWebSocket';

interface JobStatusIndicatorProps {
  status: JobStatusUpdate['status'];
  progress?: number;
  message?: string;
  showProgress?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const statusConfig = {
  pending: {
    icon: Clock,
    label: 'Pending',
    color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
    progressColor: 'bg-yellow-500',
  },
  processing: {
    icon: Loader2,
    label: 'Processing',
    color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    progressColor: 'bg-blue-500',
  },
  completed: {
    icon: CheckCircle,
    label: 'Completed',
    color: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    progressColor: 'bg-green-500',
  },
  failed: {
    icon: AlertCircle,
    label: 'Failed',
    color: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
    progressColor: 'bg-red-500',
  },
};

export const JobStatusIndicator: React.FC<JobStatusIndicatorProps> = ({
  status,
  progress = 0,
  message,
  showProgress = true,
  size = 'md',
  className = '',
}) => {
  const config = statusConfig[status];
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2',
  };

  const iconSizes = {
    sm: 12,
    md: 16,
    lg: 20,
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <Badge
        variant="secondary"
        className={`${config.color} ${sizeClasses[size]} flex items-center gap-2`}
      >
        <Icon 
          size={iconSizes[size]} 
          className={status === 'processing' ? 'animate-spin' : ''} 
        />
        {config.label}
      </Badge>

      {showProgress && status === 'processing' && (
        <div className="space-y-1">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      )}

      {message && (
        <p className="text-sm text-muted-foreground">{message}</p>
      )}
    </div>
  );
};

export default JobStatusIndicator;
