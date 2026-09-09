import { FormEvent, useState } from 'react'

import { BrandMark } from '../components/BrandMark'

type LoginScreenProps = {
  busy: boolean
  error?: string
  onLogin: (email: string, password: string) => Promise<void>
}

export function LoginScreen({ busy, error, onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState(import.meta.env.DEV ? 'owner@flowvia.local' : '')
  const [password, setPassword] = useState(import.meta.env.DEV ? 'FlowviaOwner123!' : '')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await onLogin(email, password)
  }

  return (
    <main className="login-page">
      <section className="login-hero" aria-labelledby="login-title">
        <BrandMark />
        <div>
          <p className="eyebrow">M1 · Runnable foundation</p>
          <h1 id="login-title">Xây workflow trước. Tự động hóa sau.</h1>
          <p>
            Flowvia giữ lõi workflow độc lập với HR. Bản hiện tại mới cung cấp
            nền tảng đăng nhập, workspace và shell để chuẩn bị cho canvas bền
            vững ở M2.
          </p>
        </div>
        <ul className="foundation-list">
          <li>Workspace cá nhân và nhóm</li>
          <li>Session phía server + CSRF</li>
          <li>Tenant boundary ở backend</li>
        </ul>
      </section>

      <section className="login-card" aria-label="Đăng nhập Flowvia">
        <p className="eyebrow">Development demo</p>
        <h2>Đăng nhập</h2>
        <p className="muted">
          Dữ liệu demo là dữ liệu giả. Không dùng mật khẩu này ngoài môi trường
          local.
        </p>

        {error ? <div className="form-error">{error}</div> : null}

        <form onSubmit={submit}>
          <label>
            Email
            <input
              autoComplete="username"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={busy}
            />
          </label>

          <label>
            Mật khẩu
            <input
              autoComplete="current-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              disabled={busy}
            />
          </label>

          <button className="primary-button" type="submit" disabled={busy}>
            {busy ? 'Đang đăng nhập…' : 'Đăng nhập'}
          </button>
        </form>

        {import.meta.env.DEV ? (
          <div className="demo-credentials">
            <strong>Tài khoản owner local</strong>
            <code>owner@flowvia.local</code>
            <code>FlowviaOwner123!</code>
          </div>
        ) : null}
      </section>
    </main>
  )
}
