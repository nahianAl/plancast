'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { 
  Plus, 
  Download, 
  Eye, 
  Trash2, 
  Settings, 
  LogOut, 
  User, 
  BarChart3, 
  Calendar,
  FileText,
  Image,
  Box,
  TrendingUp,
  Activity
} from 'lucide-react'

interface Project {
  id: string
  name: string
  status: 'processing' | 'completed' | 'failed'
  progress: number
  created_at: string
  completed_at?: string
  file_size: string
  output_formats: string[]
  thumbnail?: string
}

interface UsageStats {
  total_projects: number
  completed_projects: number
  failed_projects: number
  total_file_size: string
  this_month: number
  last_month: number
}

export default function DashboardPage() {
  const { user, logout, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [projects, setProjects] = useState<Project[]>([])
  const [stats, setStats] = useState<UsageStats>({
    total_projects: 0,
    completed_projects: 0,
    failed_projects: 0,
    total_file_size: '0 MB',
    this_month: 0,
    last_month: 0
  })
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/signin')
    } else if (user) {
      loadDashboardData()
    }
  }, [authLoading, user, router])

  const loadDashboardData = async () => {
    try {
      // TODO: Replace with real API calls
      // Mock data for now
      const mockProjects: Project[] = [
        {
          id: '1',
          name: 'Modern House Floor Plan',
          status: 'completed',
          progress: 100,
          created_at: '2024-01-15T10:30:00Z',
          completed_at: '2024-01-15T10:45:00Z',
          file_size: '2.4 MB',
          output_formats: ['GLB', 'OBJ', 'STL'],
          thumbnail: '/api/projects/1/thumbnail'
        },
        {
          id: '2',
          name: 'Office Building Layout',
          status: 'processing',
          progress: 65,
          created_at: '2024-01-14T14:20:00Z',
          file_size: '1.8 MB',
          output_formats: ['GLB', 'OBJ']
        },
        {
          id: '3',
          name: 'Apartment Complex',
          status: 'completed',
          progress: 100,
          created_at: '2024-01-13T09:15:00Z',
          completed_at: '2024-01-13T09:35:00Z',
          file_size: '3.2 MB',
          output_formats: ['GLB', 'OBJ', 'STL', 'FBX']
        }
      ]

      const mockStats: UsageStats = {
        total_projects: 12,
        completed_projects: 10,
        failed_projects: 2,
        total_file_size: '28.6 MB',
        this_month: 3,
        last_month: 9
      }

      setProjects(mockProjects)
      setStats(mockStats)
      setIsLoading(false)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      setIsLoading(false)
    }
  }

  const handleSignOut = async () => {
    logout()
    router.push('/')
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
      case 'processing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✅'
      case 'processing':
        return '🔄'
      case 'failed':
        return '❌'
      default:
        return '⏳'
    }
  }

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <h2 className="mt-4 text-xl font-semibold text-gray-900 dark:text-white">
            Loading your dashboard...
          </h2>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Dashboard
              </h1>
              <div className="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
              <p className="text-gray-600 dark:text-gray-300">
                Welcome back, {user.name}
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <button className="p-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                <Settings className="w-5 h-5" />
              </button>
              <button
                onClick={handleSignOut}
                className="p-2 text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 transition-colors"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <BarChart3 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Total Projects</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_projects}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Completed</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.completed_projects}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-lg">
                <Activity className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Failed</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.failed_projects}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                <FileText className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Total Size</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_file_size}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
          <div className="flex flex-wrap gap-4">
            <Link
              href="/convert"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Conversion
            </Link>
            <Link
              href="/demo"
              className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:border-blue-500 hover:text-blue-600 dark:hover:border-blue-400 dark:hover:text-blue-400 transition-colors"
            >
              <Eye className="w-4 h-4 mr-2" />
              View Demo
            </Link>
            <Link
              href="/contact"
              className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:border-blue-500 hover:text-blue-600 dark:hover:border-blue-400 dark:hover:text-blue-400 transition-colors"
            >
              <User className="w-4 h-4 mr-2" />
              Contact Support
            </Link>
          </div>
        </div>

        {/* Recent Projects */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Projects</h2>
              <Link
                href="/projects"
                className="text-sm text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
              >
                View all projects
              </Link>
            </div>
          </div>
          
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {projects.map((project) => (
              <div key={project.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                      <Image className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white">{project.name}</h3>
                      <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400 mt-1">
                        <span className="flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          {new Date(project.created_at).toLocaleDateString()}
                        </span>
                        <span className="flex items-center">
                          <FileText className="w-3 h-3 mr-1" />
                          {project.file_size}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                      {getStatusIcon(project.status)} {project.status}
                    </span>
                    
                    {project.status === 'processing' && (
                      <div className="w-20 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${project.progress}%` }}
                        ></div>
                      </div>
                    )}
                    
                    <div className="flex items-center space-x-2">
                      {project.status === 'completed' && (
                        <>
                          <Link
                            href={`/convert/preview/${project.id}`}
                            className="p-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                            title="View 3D model"
                          >
                            <Eye className="w-4 h-4" />
                          </Link>
                          <button className="p-2 text-gray-600 dark:text-gray-300 hover:text-green-600 dark:hover:text-green-400 transition-colors" title="Download">
                            <Download className="w-4 h-4" />
                          </button>
                        </>
                      )}
                      <button className="p-2 text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 transition-colors" title="Delete">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
                
                {project.status === 'completed' && project.output_formats && (
                  <div className="mt-3 flex items-center space-x-2">
                    <span className="text-xs text-gray-500 dark:text-gray-400">Available formats:</span>
                    {project.output_formats.map((format) => (
                      <span
                        key={format}
                        className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                      >
                        <Box className="w-3 h-3 mr-1" />
                        {format}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Monthly Usage Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mt-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Monthly Usage</h2>
          <div className="grid grid-cols-2 gap-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">This Month</p>
              <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">{stats.this_month}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">conversions</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">Last Month</p>
              <p className="text-3xl font-bold text-gray-600 dark:text-gray-400">{stats.last_month}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">conversions</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
