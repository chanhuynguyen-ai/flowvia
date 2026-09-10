import { useEffect, useState } from "react";
import { KeyRound, ShieldCheck, Trash2 } from "lucide-react";
import { api, errorMessage } from "../../lib/platform";
import { apiFetch } from "../../lib/api";
import { Badge, Empty, ErrorNotice } from "../../components/UI";
import type { Credential, Overview } from "../../types/platform";
import type { Workspace } from "../../types/api";
export function SettingsPage({ workspace }: { workspace: Workspace }) {
  const [credentials, setCredentials] = useState<Credential[]>([]),
    [overview, setOverview] = useState<Overview>(),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const refresh = () =>
    Promise.all([
      api.credentials().then(setCredentials),
      api.overview().then(setOverview),
    ]);
  useEffect(() => {
    refresh().catch((e) => setError(errorMessage(e)));
  }, [workspace.id]);
  async function revoke(c: Credential) {
    if (
      !window.confirm(
        `Revoke “${c.name}”? Workflows using this credential will stop before their next external action.`,
      )
    )
      return;
    setBusy(true);
    try {
      await apiFetch(`/api/v1/credentials/${c.id}`, { method: "DELETE" });
      await refresh();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <span className="eyebrow">WORKSPACE CONTROL</span>
          <h1>Settings</h1>
          <p className="muted">
            Thông tin workspace và quyền truy cập các tài khoản kết nối.
          </p>
        </div>
      </header>
      <ErrorNotice message={error} />
      <section className="panel settings-panel">
        <header className="panel-heading">
          <h2>Workspace</h2>
          <ShieldCheck size={18} />
        </header>
        <dl className="settings-list">
          <dt>Name</dt>
          <dd>{workspace.name}</dd>
          <dt>Type</dt>
          <dd>{workspace.kind}</dd>
          <dt>Your role</dt>
          <dd>
            <Badge status={workspace.role} />
          </dd>
          <dt>Timezone</dt>
          <dd>{workspace.timezone}</dd>
          <dt>Server outbound mode</dt>
          <dd>
            <Badge status={overview?.outbound_mode ?? "loading"} />
          </dd>
        </dl>
        <p className="muted small">
          Live sending requires the server to allow live mode, an active
          connection and approval of the exact message.
        </p>
      </section>
      <section className="panel">
        <header className="panel-heading">
          <div className="button-row">
            <KeyRound size={18} />
            <h2>Credential vault</h2>
          </div>
          <span className="muted small">Encrypted at rest</span>
        </header>
        {credentials.length === 0 ? (
          <Empty title="No saved credentials">
            <p>Add a bot token in Connections or an API key in Agents.</p>
          </Empty>
        ) : (
          <div className="credential-list">
            {credentials.map((c) => (
              <div className="credential-row" key={c.id}>
                <span className="credential-symbol">
                  <KeyRound size={20} />
                </span>
                <span>
                  <strong>{c.name}</strong>
                  <small>{c.provider}</small>
                </span>
                <Badge status={c.status} />
                <button
                  className="btn danger"
                  disabled={busy || c.status !== "active"}
                  onClick={() => revoke(c)}
                >
                  <Trash2 size={15} />
                  Revoke
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
