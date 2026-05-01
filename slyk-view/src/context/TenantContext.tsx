import { createContext, useContext, useState, ReactNode } from 'react'

interface TenantConfig {
  id: string
  name: string
  awsAccountId: string
  region: string
  agentId: string
  agentAliasId: string
  logo?: string
  primaryColor?: string
}

interface TenantContextType {
  tenant: TenantConfig | null
  setTenant: (tenant: TenantConfig) => void
  isConfigured: boolean
}

const defaultTenant: TenantConfig = {
  id: 'nesdis-ncis',
  name: 'NESDIS NCIS',
  awsAccountId: '656443597515',
  region: 'us-east-1',
  agentId: '', // Will be set from config
  agentAliasId: '',
  primaryColor: '#6366F1',
}

const TenantContext = createContext<TenantContextType | undefined>(undefined)

export function TenantProvider({ children }: { children: ReactNode }) {
  const [tenant, setTenant] = useState<TenantConfig | null>(() => {
    // Load from localStorage if available
    const saved = localStorage.getItem('slyk-tenant')
    return saved ? JSON.parse(saved) : defaultTenant
  })

  const handleSetTenant = (newTenant: TenantConfig) => {
    setTenant(newTenant)
    localStorage.setItem('slyk-tenant', JSON.stringify(newTenant))
  }

  return (
    <TenantContext.Provider value={{
      tenant,
      setTenant: handleSetTenant,
      isConfigured: !!(tenant?.agentId && tenant?.agentAliasId)
    }}>
      {children}
    </TenantContext.Provider>
  )
}

export function useTenant() {
  const context = useContext(TenantContext)
  if (!context) {
    throw new Error('useTenant must be used within TenantProvider')
  }
  return context
}
