'use client';

import { useState, useEffect } from 'react';
import { checkHealth, config } from '@/lib/api';
import type { HealthResponse } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';

export default function HealthCheck() {
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'degraded' | 'unhealthy' | 'checking' | 'error'>('checking');
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const checkApiHealth = async () => {
    try {
      setHealthStatus('checking');
      setError(null);
      
      const response = await checkHealth();
      setHealthData(response);
      setHealthStatus(response.status);
      setLastChecked(new Date());
    } catch (err) {
      console.error('Health check failed:', err);
      setHealthStatus('error');
      setError(err instanceof Error ? err.message : 'Unknown error');
      setLastChecked(new Date());
    }
  };

  useEffect(() => {
    checkApiHealth();
  }, []);

  const getStatusIcon = () => {
    switch (healthStatus) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'checking':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = () => {
    switch (healthStatus) {
      case 'healthy':
        return <Badge variant="default" className="bg-green-100 text-green-800">Healthy</Badge>;
      case 'degraded':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Degraded</Badge>;
      case 'unhealthy':
        return <Badge variant="destructive">Unhealthy</Badge>;
      case 'checking':
        return <Badge variant="secondary">Checking...</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {getStatusIcon()}
          Railway API Health Check
        </CardTitle>
        <CardDescription>
          Testing connection to backend API at {config.api.baseUrl}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Status:</span>
          {getStatusBadge()}
        </div>

        {lastChecked && (
          <div className="text-sm text-gray-600">
            Last checked: {lastChecked.toLocaleTimeString()}
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800 font-medium">Error:</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {healthData && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-700">Version</p>
                <p className="text-sm text-gray-900">{healthData.version}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">Uptime</p>
                <p className="text-sm text-gray-900">
                  {Math.floor(healthData.uptime_seconds / 3600)}h {Math.floor((healthData.uptime_seconds % 3600) / 60)}m
                </p>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Component Status</p>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(healthData.components).map(([component, status]) => (
                  <div key={component} className="flex items-center gap-2">
                    <span className="text-xs text-gray-600 capitalize">
                      {component.replace('_', ' ')}:
                    </span>
                    <Badge 
                      variant={status === 'healthy' ? 'default' : 'destructive'}
                      className={status === 'healthy' ? 'bg-green-100 text-green-800' : ''}
                    >
                      {String(status)}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <Button 
          onClick={checkApiHealth} 
          disabled={healthStatus === 'checking'}
          className="w-full"
        >
          {healthStatus === 'checking' ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Checking...
            </>
          ) : (
            'Check Health Again'
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
