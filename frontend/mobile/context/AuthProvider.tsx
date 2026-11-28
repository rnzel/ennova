// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Scripting (authentication session orchestration)

import {
  createContext,
  useContext,
  useState,
  type PropsWithChildren,
} from 'react'
import {
  ApiError,
  apiRequest,
  type ApiAccount,
  type BeneficiaryRegistrationRequest,
  type LoginResponse,
  type OwnerRegistrationRequest,
} from '@/services/api'

type AuthContextValue = {
  account: ApiAccount | null
  username: string | null
  accountRole: ApiAccount['role'] | null
  accessToken: string | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  registerOwner: (username: string, email: string, password: string) => Promise<void>
  registerBeneficiary: (
    invitationCode: string,
    username: string,
    email: string,
    password: string,
  ) => Promise<void>
  logout: () => void
  clearRejectedSession: (error: unknown) => boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: PropsWithChildren) {
  const [account, setAccount] = useState<ApiAccount | null>(null)
  const [username, setUsername] = useState<string | null>(null)
  const [accountRole, setAccountRole] = useState<ApiAccount['role'] | null>(null)
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
      setUsername(username.trim())
      setAccountRole(readSessionRole(response.access_token))
    } finally {
      setIsLoading(false)
    }
  }

  const registerOwner = async (username: string, email: string, password: string) => {
    setIsLoading(true)
    try {
      const requestBody: OwnerRegistrationRequest = {
        username,
        email: email.trim(),
        password,
      }
      const registered = await apiRequest<ApiAccount>('/auth/register-owner', {
        method: 'POST',
        body: requestBody,
      })
      const response = await apiRequest<LoginResponse>('/auth/login', {
        method: 'POST',
        body: { username, password },
      })
      setAccount(registered)
      setUsername(registered.username)
      setAccountRole(registered.role)
      setAccessToken(response.access_token)
    } finally {
      setIsLoading(false)
    }
  }

  const registerBeneficiary = async (
    invitationCode: string,
    username: string,
    email: string,
    password: string,
  ) => {
    setIsLoading(true)
    try {
      const requestBody: BeneficiaryRegistrationRequest = {
        invitation_code: invitationCode,
        username,
        email: email.trim(),
        password,
      }
      const registered = await apiRequest<ApiAccount>('/auth/register-beneficiary', {
        method: 'POST',
        body: requestBody,
      })
      const response = await apiRequest<LoginResponse>('/auth/login', {
        method: 'POST',
        body: { username, password },
      })
      setAccount(registered)
      setUsername(registered.username)
      setAccountRole(registered.role)
      setAccessToken(response.access_token)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setAccessToken(null)
    setAccount(null)
    setUsername(null)
    setAccountRole(null)
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
        username,
        accountRole,
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

function readSessionRole(token: string): ApiAccount['role'] | null {
  try {
    const encodedClaims = token.split('.')[1]
    if (!encodedClaims) return null
    const base64 = encodedClaims.replace(/-/g, '+').replace(/_/g, '/')
    const claims = JSON.parse(atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, '=')))
    return claims.role === 'owner' || claims.role === 'beneficiary' ? claims.role : null
  } catch {
    return null
  }
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
