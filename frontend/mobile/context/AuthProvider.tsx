import {
  createContext,
  useContext,
  useState,
  type PropsWithChildren,
} from 'react'
import { ApiError, apiRequest, type ApiAccount, type LoginResponse } from '@/services/api'

type AuthContextValue = {
  account: ApiAccount | null
  accessToken: string | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  registerOwner: (username: string, password: string) => Promise<void>
  registerBeneficiary: (invitationCode: string, username: string, password: string) => Promise<void>
  logout: () => void
  clearRejectedSession: (error: unknown) => boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: PropsWithChildren) {
  const [account, setAccount] = useState<ApiAccount | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const login = async (username: string, password: string) => {
    setIsLoading(true)
    try {
      const response = await apiRequest<LoginResponse>('/auth/login', {
        method: 'POST',
        body: { username, password },
      })
      setAccessToken(response.access_token)
      setAccount(null)
    } finally {
      setIsLoading(false)
    }
  }

  const registerOwner = async (username: string, password: string) => {
    setIsLoading(true)
    try {
      const registered = await apiRequest<ApiAccount>('/auth/register-owner', {
        method: 'POST',
        body: { username, password },
      })
      const response = await apiRequest<LoginResponse>('/auth/login', {
        method: 'POST',
        body: { username, password },
      })
      setAccount(registered)
      setAccessToken(response.access_token)
    } finally {
      setIsLoading(false)
    }
  }

  const registerBeneficiary = async (
    invitationCode: string,
    username: string,
    password: string,
  ) => {
    setIsLoading(true)
    try {
      const registered = await apiRequest<ApiAccount>('/auth/register-beneficiary', {
        method: 'POST',
        body: {
          invitation_code: invitationCode,
          username,
          password,
        },
      })
      const response = await apiRequest<LoginResponse>('/auth/login', {
        method: 'POST',
        body: { username, password },
      })
      setAccount(registered)
      setAccessToken(response.access_token)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setAccessToken(null)
    setAccount(null)
  }

  const clearRejectedSession = (error: unknown) => {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      logout()
      return true
    }
    return false
  }

  return (
    <AuthContext.Provider
      value={{
        account,
        accessToken,
        isLoading,
        login,
        registerOwner,
        registerBeneficiary,
        logout,
        clearRejectedSession,
      }}
    >
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
