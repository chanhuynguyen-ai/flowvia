import type { ApiErrorShape, SessionResponse } from '../types/api'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  status: number
  requestId?: string

  constructor(status: number, message: string, requestId?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.requestId = requestId
  }
}

function readCookie(name: string): string | undefined {
  const item = document.cookie
    .split('; ')
    .find((entry) => entry.startsWith(`${name}=`))

  return item ? decodeURIComponent(item.split('=').slice(1).join('=')) : undefined
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const method = (init.method ?? 'GET').toUpperCase()
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrf = readCookie('flowvia_csrf')
    if (csrf) {
      headers.set('X-CSRF-Token', csrf)
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    credentials: 'include',
  })

  if (!response.ok) {
    let body: ApiErrorShape = {}
    try {
      body = (await response.json()) as ApiErrorShape
    } catch {
      // Preserve the HTTP status even when a proxy returns non-JSON.
    }
    throw new ApiError(
      response.status,
      body.message ?? `Request failed (${response.status})`,
      body.request_id,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const authApi = {
  me: () => apiFetch<SessionResponse>('/api/v1/auth/me'),
  login: (email: string, password: string) =>
    apiFetch<SessionResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  switchWorkspace: (workspaceId: string) =>
    apiFetch<SessionResponse>('/api/v1/auth/switch-workspace', {
      method: 'POST',
      body: JSON.stringify({ workspace_id: workspaceId }),
    }),
  logout: () =>
    apiFetch<void>('/api/v1/auth/logout', {
      method: 'POST',
    }),
}
