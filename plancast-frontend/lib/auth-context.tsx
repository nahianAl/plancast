'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { compare } from 'bcryptjs'

interface User {
  id: string
  email: string
  name: string
}

interface AuthContextType {
  user: User | null
  login: (email: string, password: string) => Promise<boolean>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in from localStorage
    const savedUser = localStorage.getItem('plancast_user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (error) {
        console.error('Failed to parse saved user:', error)
        localStorage.removeItem('plancast_user')
      }
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      console.log('🔐 Login attempt:', { email, passwordLength: password.length })
      
      // Mock user data for now
      const mockUser = {
        id: "1",
        email: "demo@plancast.app",
        name: "Demo User",
        password: "$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/vHhH8eG" // "password123"
      }

      console.log('👤 Checking email:', email, 'vs', mockUser.email)
      if (email !== mockUser.email) {
        console.log('❌ Email mismatch')
        return false
      }

      console.log('🔑 Checking password against hash...')
      const isPasswordValid = await compare(password, mockUser.password)
      console.log('🔑 Password valid:', isPasswordValid)
      
      if (!isPasswordValid) {
        console.log('❌ Password validation failed')
        return false
      }

      const userData = {
        id: mockUser.id,
        email: mockUser.email,
        name: mockUser.name,
      }

      console.log('✅ Login successful:', userData)
      setUser(userData)
      localStorage.setItem('plancast_user', JSON.stringify(userData))
      return true
    } catch (error) {
      console.error('💥 Login error:', error)
      return false
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('plancast_user')
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
