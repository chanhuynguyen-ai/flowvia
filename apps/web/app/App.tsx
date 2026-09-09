import { useEffect, useState } from 'react'

import { ApiError, authApi } from '../lib/api'
import type { SessionResponse } from '../types/api'
import { AppShell } from './AppShell'
import { LoginScreen } from './LoginScreen'

type AuthState =
  | { kind: 'loading' }
  | { kind: 'anonymous' }
  | { kind: 'authenticated'; session: SessionResponse }

function readableError(error: unknown): string {
  if (error instanceof ApiError) {
    const suffix = error.requestId ? ` · request ${error.requestId}` : ''
    return `${error.message}${suffix}`
  }
  return 'Không thể kết nối tới Flowvia API.'
}

export default function App() {
  const [auth, setAuth] = useState<AuthState>({ kind: 'loading' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string>()

  useEffect(() => {
    authApi
      .me()
      .then((session) => setAuth({ kind: 'authenticated', session }))
      .catch((requestError: unknown) => {
        if (requestError instanceof ApiError && requestError.status === 401) {
          setAuth({ kind: 'anonymous' })
          return
        }
        setError(readableError(requestError))
        setAuth({ kind: 'anonymous' })
      })
  }, [])

  async function login(email: string, password: string) {
    setBusy(true)
    setError(undefined)
    try {
      const session = await authApi.login(email, password)
      setAuth({ kind: 'authenticated', session })
    } catch (requestError) {
      setError(readableError(requestError))
    } finally {
      setBusy(false)
    }
  }

  async function switchWorkspace(workspaceId: string) {
    setBusy(true)
    setError(undefined)
    try {
      const session = await authApi.switchWorkspace(workspaceId)
      setAuth({ kind: 'authenticated', session })
    } catch (requestError) {
      setError(readableError(requestError))
    } finally {
      setBusy(false)
    }
  }

  async function logout() {
    setBusy(true)
    try {
      await authApi.logout()
    } finally {
      setAuth({ kind: 'anonymous' })
      setBusy(false)
    }
  }

  if (auth.kind === 'loading') {
    return (
      <main className="loading-screen" aria-busy="true">
        <span className="loading-dot" />
        <strong>Đang mở Flowvia…</strong>
      </main>
    )
  }

  if (auth.kind === 'anonymous') {
    return <LoginScreen busy={busy} error={error} onLogin={login} />
  }

  return (
    <>
      {error ? <div className="global-error">{error}</div> : null}
      <AppShell
        session={auth.session}
        busy={busy}
        onSwitchWorkspace={switchWorkspace}
        onLogout={logout}
      />
    </>
  )
}
