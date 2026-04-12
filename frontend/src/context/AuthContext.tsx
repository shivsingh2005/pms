'use client'

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  useEffect,
} from 'react'
import { useRouter } from 'next/navigation'
import { useSessionStore } from '@/store/useSessionStore'
import type { User } from '@/types'

interface AuthCtx {
  user: User | null
  ready: boolean
  loading: boolean
  login: (u: User, token: string) => void
  logout: () => void
}

const Ctx = createContext<AuthCtx | null>(null)

const VALID_ROLES = ['employee', 'manager', 'hr', 'leadership']

const ROLE_HOME: Record<string, string> = {
  employee: '/employee/dashboard',
  manager: '/manager/dashboard',
  hr: '/hr/dashboard',
  leadership: '/leadership/dashboard',
}

function readUser(): User | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem('pms_user') ?? localStorage.getItem('user')
    if (!raw) return null
    const u = JSON.parse(raw) as User
    if (!VALID_ROLES.includes((u?.role ?? '').toLowerCase())) {
      return null
    }
    return { ...u, role: u.role.toLowerCase() as User['role'] }
  } catch {
    return null
  }
}

function toSessionUser(user: User): User {
  return {
    ...user,
    roles: user.roles && user.roles.length ? user.roles : [user.role],
    organization_id: user.organization_id ?? '',
    manager_id: user.manager_id ?? null,
    department: user.department ?? null,
    title: user.title ?? null,
    first_login: user.first_login ?? false,
    onboarding_complete: user.onboarding_complete ?? true,
    is_active: user.is_active ?? true,
  }
}

export function AuthProvider({
  children,
}: {
  children: React.ReactNode
}) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const storedUser = readUser()
    if (storedUser) {
      setUser(storedUser)
      useSessionStore.getState().setUser(storedUser)
    }
    setReady(true)
  }, [])

  const login = useCallback((u: User, token: string) => {
    const normalized: User = {
      ...u,
      role: u.role.toLowerCase() as User['role'],
    }
    const sessionUser = toSessionUser(normalized)
    try {
      localStorage.setItem('pms_user', JSON.stringify(sessionUser))
      localStorage.setItem('user', JSON.stringify(sessionUser))
      localStorage.setItem('pms_token', token)
      localStorage.setItem('session', JSON.stringify({ userId: normalized.id, email: normalized.email, role: normalized.role }))
    } catch {
      // no-op on storage failures
    }
    useSessionStore.getState().setUser(sessionUser)
    setUser(sessionUser)
    router.push(ROLE_HOME[normalized.role] ?? '/login')
  }, [router])

  const logout = useCallback(() => {
    setUser(null)
    useSessionStore.getState().logout()
    try {
      localStorage.removeItem('pms_user')
      localStorage.removeItem('user')
      localStorage.removeItem('pms_token')
      localStorage.removeItem('session')
    } catch {
      // no-op on storage failures
    }
    router.push('/login')
  }, [router])

  const value = useMemo(
    () => ({ user, ready, loading: !ready, login, logout }),
    [user, ready, login, logout]
  )

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useAuth(): AuthCtx {
  const c = useContext(Ctx)
  if (!c) throw new Error('useAuth: missing AuthProvider')
  return c
}
