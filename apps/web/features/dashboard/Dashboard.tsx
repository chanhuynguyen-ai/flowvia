import type { Workspace } from '../../types/api'

type DashboardProps = {
  workspace: Workspace
}

const cards = [
  {
    title: 'Workflow foundation',
    body: 'API, database foundation và workspace identity đã có source. Editor graph thuộc M2.',
    state: 'Foundation',
  },
  {
    title: 'Module registry',
    body: 'Contracts blueprint vẫn là nguồn định nghĩa. Runtime handler chưa được bật ở M1.',
    state: 'M2 planned',
  },
  {
    title: 'HR business pack',
    body: 'HR vẫn là pack tùy chọn, không được hardcode vào platform core.',
    state: 'M3 planned',
  },
]

export function Dashboard({ workspace }: DashboardProps) {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Tổng quan</p>
          <h1>{workspace.name}</h1>
          <p className="muted">
            {workspace.kind === 'personal' ? 'Không gian cá nhân' : 'Không gian nhóm'}
            {' · '}
            {workspace.timezone}
          </p>
        </div>
        <span className="role-pill">{workspace.role}</span>
      </header>

      <div className="notice-card">
        <strong>M1 foundation đang hoạt động.</strong>
        <span>
          Các thẻ bên dưới mô tả trạng thái triển khai thật, không phải số liệu
          vận hành giả.
        </span>
      </div>

      <section className="summary-grid" aria-label="Trạng thái milestone">
        {cards.map((card) => (
          <article className="summary-card" key={card.title}>
            <span className="state-chip">{card.state}</span>
            <h2>{card.title}</h2>
            <p>{card.body}</p>
          </article>
        ))}
      </section>
    </div>
  )
}
