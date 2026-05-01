import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  username: string
  email: string
  groups: string[]
  attributes: Record<string, string>
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  getCredentials: () => Promise<any>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for existing session
    const checkAuth = async () => {
      try {
        const savedUser = localStorage.getItem('slyk-user')
        if (savedUser) {
          setUser(JSON.parse(savedUser))
        }
      } catch (error) {
        console.error('Auth check failed:', error)
      } finally {
        setIsLoading(false)
      }
    }
    checkAuth()
  }, [])

  const login = async (username: string, password: string) => {
    // In production, this would use Cognito
    // For demo, we'll simulate authentication
    setIsLoading(true)
    try {
      // Simulated user for demo
      const demoUser: User = {
        username,
        email: `${username}@noaa.gov`,
        groups: ['ISSO', 'SecurityTeam'],
        attributes: {
          'custom:tenant': 'nesdis-ncis',
          'custom:role': 'ISSO'
        }
      }
      setUser(demoUser)
      localStorage.setItem('slyk-user', JSON.stringify(demoUser))
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('slyk-user')
  }

  const getCredentials = async () => {
    // In production, this would get temporary AWS credentials from Cognito Identity Pool
    // For demo, we return null (will use environment credentials)
    return null
  }

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      logout,
      getCredentials
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
