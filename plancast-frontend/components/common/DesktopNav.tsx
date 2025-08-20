'use client'

import Link from 'next/link'
import { useSession, signOut } from 'next-auth/react'
import { User, Settings, LogOut, Sun, Moon } from 'lucide-react'
import { useState } from 'react'

export function DesktopNav() {
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const { data: session, status } = useSession()
  const user = session?.user

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode)
    document.documentElement.classList.toggle('dark')
  }

  const handleSignOut = async () => {
    await signOut()
    setIsUserMenuOpen(false)
  }

  const navigation = [
    { name: 'Home', href: '/' },
    { name: 'Convert', href: '/convert' },
    { name: 'Demo', href: '/demo' },
    { name: 'Contact', href: '/contact' },
  ]

  return (
    <div className="hidden md:block">
      <div className="ml-10 flex items-baseline space-x-4">
        {navigation.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className="text-gray-500 dark:text-gray-300 hover:text-gray-700 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium"
          >
            {item.name}
          </Link>
        ))}
      </div>
      <div className="ml-4 flex items-center md:ml-6">
        {status === 'loading' ? (
          <div className="animate-pulse bg-gray-300 dark:bg-gray-700 h-8 w-24 rounded-md"></div>
        ) : user ? (
          <div className="ml-3 relative">
            <div>
              <button
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="max-w-xs bg-white dark:bg-gray-800 rounded-full flex items-center text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white"
              >
                <span className="sr-only">Open user menu</span>
                <User className="h-8 w-8 rounded-full" />
              </button>
            </div>
            {isUserMenuOpen && (
              <div className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 focus:outline-none">
                <div className="px-4 py-2 text-sm text-gray-700 dark:text-gray-200 border-b dark:border-gray-600">
                  <p className="font-semibold">{user.name}</p>
                  <p className="text-xs truncate">{user.email}</p>
                </div>
                <Link href="/dashboard" className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
                  <User className="mr-2 h-4 w-4" />
                  <span>Dashboard</span>
                </Link>
                <Link href="/settings" className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Settings</span>
                </Link>
                <button
                  onClick={handleSignOut}
                  className="w-full text-left flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Sign Out</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="space-x-4">
            <Link href="/auth/signin" className="text-gray-500 dark:text-gray-300 hover:text-gray-700 dark:hover:text-white">
              Sign In
            </Link>
            <Link href="/auth/signup" className="bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700">
              Sign Up
            </Link>
          </div>
        )}
        <button
          onClick={toggleDarkMode}
          className="ml-4 p-1 rounded-full text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white"
        >
          <span className="sr-only">View notifications</span>
          {isDarkMode ? <Sun className="h-6 w-6" /> : <Moon className="h-6 w-6" />}
        </button>
      </div>
    </div>
  )
}
