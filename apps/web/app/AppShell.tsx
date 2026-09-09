import { useMemo, useState } from 'react'

import { BrandMark } from '../components/BrandMark'
import { Dashboard } from '../features/dashboard/Dashboard'
import type { SessionResponse } from '../types/api'

type AppShellProps = {
  session: SessionResponse
  busy: boolean
  onSwitchWorkspace: (workspaceId: string) => Promise<void>
  onLogout: () => Promise<void>
}

type PageKey = 'overview' | 'workflows' | 'approvals' | 'modules' | 'settings'

export function AppShell({
  session,
  busy,
  onSwitchWorkspace,
  onLogout,
}: AppShellProps) {
  const [page, setPage] = useState<PageKey>('overview')

  const navItems = useMemo(() => {
    const role = session.current_workspace.role
    const items: { key: PageKey; label: string; enabled: boolean }[] = [
      { key: 'overview', label: 'Tổng quan', enabled: true },
      { key: 'workflows', label: 'Workflows', enabled: true },
      {
        key: 'approvals',
        label: 'Phê duyệt',
        enabled: ['owner', 'reviewer'].includes(role),
      },
      { key: 'modules', label: 'Module', enabled: true },
      {
        key: 'settings',
        label: 'Cài đặt',
        enabled: role === 'owner',
      },
    ]
    return items.filter((item) => item.enabled)
  }, [session.current_workspace.role])

  function placeholder(title: string, milestone: string, description: string) {
    return (
      <div className="page-stack">
        <header className="page-header">
          <div>
            <p className="eyebrow">{milestone}</p>
            <h1>{title}</h1>
            <p className="muted">{description}</p>
          </div>
        </header>
        <div className="empty-state">
          <strong>Chưa triển khai ở M1</strong>
          <span>
            Màn hình này được giữ làm route/shell, không hiển thị dữ liệu giả hoặc
            hành động chưa có backend.
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <BrandMark />

        <label className="workspace-control">
          <span>Không gian làm việc</span>
          <select
            value={session.current_workspace.id}
            disabled={busy}
            onChange={(event) => onSwitchWorkspace(event.target.value)}
          >
            {session.workspaces.map((workspace) => (
              <option value={workspace.id} key={workspace.id}>
                {workspace.name}
              </option>
            ))}
          </select>
        </label>

        <nav aria-label="Điều hướng chính">
          {navItems.map((item) => (
            <button
              className={page === item.key ? 'nav-button nav-button--active' : 'nav-button'}
              key={item.key}
              type="button"
              onClick={() => setPage(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span>{session.user.display_name}</span>
          <small>{session.user.email}</small>
          <button className="text-button" type="button" onClick={onLogout} disabled={busy}>
            Đăng xuất
          </button>
        </div>
      </aside>

      <main className="app-content">
        {page === 'overview' ? (
          <Dashboard workspace={session.current_workspace} />
        ) : null}
        {page === 'workflows'
          ? placeholder(
              'Workflows',
              'M2 planned',
              'Canvas, validation, publish và durable run sẽ được triển khai ở vertical slice tiếp theo.',
            )
          : null}
        {page === 'approvals'
          ? placeholder(
              'Phê duyệt',
              'M2 planned',
              'Human Approval bền vững sẽ chỉ bật sau khi runtime và version model tồn tại.',
            )
          : null}
        {page === 'modules'
          ? placeholder(
              'Module catalog',
              'Contracts prepared',
              'Manifest JSON đã có trong blueprint; registry API thực thi thuộc M2.',
            )
          : null}
        {page === 'settings'
          ? placeholder(
              'Cài đặt',
              'M1 shell',
              'Workspace identity đã có; quản trị thành viên/credential sẽ mở theo phase sau.',
            )
          : null}
      </main>
    </div>
  )
}
