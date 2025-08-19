import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { config } from '@/lib/config';

// Create axios instance with Railway backend configuration
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: config.api.baseUrl,
    timeout: config.api.timeout,
    // Simple configuration - no withCredentials to avoid CORS complexity
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  });

  // Request interceptor for logging and authentication
  client.interceptors.request.use(
    (config) => {
      // Log request in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
      }
      
      return config;
    },
    (error) => {
      console.error('❌ Request interceptor error:', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor for logging, error handling, and retries
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      // Log response in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
      }
      
      return response;
    },
    async (error: AxiosError) => {
      const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
      
      // Log error
      console.error('❌ API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        message: error.message,
        data: error.response?.data,
      });

      // Handle retry logic for network failures
      if (
        !originalRequest._retry &&
        (error.code === 'ECONNABORTED' || 
         error.code === 'ERR_NETWORK' || 
         (error.response?.status && error.response.status >= 500)) &&
        originalRequest.method !== 'post' // Don't retry POST requests
      ) {
        originalRequest._retry = true;
        
        // Exponential backoff retry
        const retryDelay = config.api.retryDelay * Math.pow(2, 1);
        
        console.log(`🔄 Retrying request in ${retryDelay}ms...`);
        
        return new Promise(resolve => {
          setTimeout(() => {
            resolve(client(originalRequest));
          }, retryDelay);
        });
      }

      // Handle specific error cases
      if (error.response?.status === 401) {
        // Handle unauthorized (could redirect to login)
        console.error('🔐 Unauthorized access');
      } else if (error.response?.status === 403) {
        // Handle forbidden
        console.error('🚫 Access forbidden');
      } else if (error.response?.status === 429) {
        // Handle rate limiting
        console.error('⏰ Rate limit exceeded');
      } else if (error.response?.status && error.response.status >= 500) {
        // Handle server errors
        console.error('💥 Server error');
      }

      return Promise.reject(error);
    }
  );

  return client;
};

// Create and export the API client instance
export const apiClient = createApiClient();

// Utility functions for common HTTP methods
export const api = {
  // GET request
  get: <T = unknown>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.get<T>(url, config);
  },

  // POST request
  post: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.post<T>(url, data, config);
  },

  // PUT request
  put: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.put<T>(url, data, config);
  },

  // DELETE request
  delete: <T = unknown>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.delete<T>(url, config);
  },

  // Multipart form data POST (for file uploads)
  postForm: <T = unknown>(url: string, formData: FormData, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.post<T>(url, formData, {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

// Error handling utilities
export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: string,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }

  static fromAxiosError(error: AxiosError): ApiError {
    if (error.response) {
      const data = error.response.data as { error?: string; message?: string; details?: string; code?: string };
      return new ApiError(
        error.response.status,
        data?.error || data?.message || error.message,
        data?.details,
        data?.code
      );
    }
    
    if (error.code === 'ECONNABORTED') {
      return new ApiError(408, 'Request timeout', 'The request took too long to complete');
    }
    
    if (error.code === 'ERR_NETWORK') {
      return new ApiError(0, 'Network error', 'Unable to connect to the server');
    }
    
    return new ApiError(0, error.message || 'Unknown error');
  }
}

// Health check utility
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await api.get<{ status: string }>('/health');
    return response.data.status === 'healthy';
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};

// Export the client instance for direct use if needed
export default apiClient;
