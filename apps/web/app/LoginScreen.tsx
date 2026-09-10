import { FormEvent, useState } from "react";

import { BrandMark } from "../components/BrandMark";
import { Icon } from "../components/Icon";

type LoginScreenProps = {
  busy: boolean;
  error?: string;
  onLogin: (email: string, password: string) => Promise<void>;
};

export function LoginScreen({ busy, error, onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState(
    import.meta.env.DEV ? "owner@flowvia.local" : "",
  );
  const [password, setPassword] = useState(
    import.meta.env.DEV ? "FlowviaOwner123!" : "",
  );

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onLogin(email, password);
  }

  return (
    <main className="login-page">
      <section className="login-hero" aria-labelledby="login-title">
        <BrandMark />
        <div className="login-hero-copy">
          <p className="eyebrow">Omni-channel AI automation</p>
          <h1 id="login-title">
            Route conversations.
            <br />
            Run agents.
            <br />
            <span>Automate the rest.</span>
          </h1>
          <p>
            Flowvia kết nối message channels với AI agents và low-code workflows
            trong một workspace.
          </p>
          <div className="login-flow-preview">
            <span>
              <Icon name="telegram" size={16} /> Telegram
            </span>
            <Icon name="arrow" size={14} />
            <span>
              <Icon name="agents" size={16} /> Agent
            </span>
            <Icon name="arrow" size={14} />
            <span>
              <Icon name="workflows" size={16} /> Workflow
            </span>
          </div>
        </div>
        <div className="login-footnote">
          <span className="status-dot status-dot--live" /> Flowvia Lite · Your
          agents. Your workflows.
        </div>
      </section>

      <section className="login-card" aria-label="Đăng nhập Flowvia">
        <div className="login-card-inner">
          <p className="eyebrow">Workspace access</p>
          <h2>Welcome back</h2>
          <p className="muted">Sign in to your Flowvia workspace.</p>

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
              Password
              <input
                autoComplete="current-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={busy}
              />
            </label>
            <button className="primary-button" type="submit" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>

          {import.meta.env.DEV ? (
            <div className="demo-credentials">
              <span>Development account</span>
              <code>owner@flowvia.local</code>
              <code>FlowviaOwner123!</code>
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}
