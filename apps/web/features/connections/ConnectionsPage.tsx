import { useEffect, useState } from "react";
import {
  Check,
  KeyRound,
  Plus,
  RefreshCw,
  Settings2,
  ShieldCheck,
} from "lucide-react";
import { api, errorMessage } from "../../lib/platform";
import { useRealtime } from "../../hooks/useRealtime";
import { Badge, ChannelIcon, ErrorNotice, Modal } from "../../components/UI";
import type { Connection, Credential } from "../../types/platform";
import type { Workspace } from "../../types/api";

export function ConnectionsPage({ workspace }: { workspace: Workspace }) {
  const [items, setItems] = useState<Connection[]>([]),
    [credentials, setCredentials] = useState<Credential[]>([]),
    [editing, setEditing] = useState<Connection | "new">(),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const [name, setName] = useState("My Telegram bot"),
    [token, setToken] = useState(""),
    [credential, setCredential] = useState(""),
    [polling, setPolling] = useState(true);
  const { tick } = useRealtime(),
    owner = workspace.role === "owner";
  const refresh = () =>
    Promise.all([
      api.connections().then(setItems),
      owner ? api.credentials().then(setCredentials) : Promise.resolve(),
    ]);
  useEffect(() => {
    refresh().catch((e) => setError(errorMessage(e)));
  }, [workspace.id, tick]);
  function open(c: Connection | "new") {
    setEditing(c);
    setName(c === "new" ? "My Telegram bot" : c.name);
    setToken("");
    setCredential("");
    setPolling(c === "new" ? true : c.polling);
    setError("");
  }
  async function task(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    await task(async () => {
      let credentialId = credential;
      if (token.trim()) {
        const c = await api.post<Credential>("/credentials", {
          name,
          provider: "telegram",
          secret: token.trim(),
        });
        credentialId = c.id;
      }
      const body = { name, polling, credential_id: credentialId || null };
      if (editing === "new") await api.post("/connections", body);
      else if (editing) await api.patch(`/connections/${editing.id}`, body);
      setEditing(undefined);
      setToken("");
      setNotice("Connection saved. Test the bot to finish setup.");
    });
  }
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <span className="eyebrow">YOUR CHANNELS</span>
          <h1>Connections</h1>
          <p className="muted">
            Kết nối tài khoản để đưa hội thoại vào workflow của bạn.
          </p>
        </div>
        <button
          className="btn primary"
          disabled={!owner}
          onClick={() => open("new")}
        >
          <Plus size={17} />
          Add Telegram bot
        </button>
      </header>
      <ErrorNotice message={error} />
      {notice && (
        <div className="notice notice-success">
          <Check size={17} />
          {notice}
        </div>
      )}
      <div className="connection-grid">
        {items.map((c) => (
          <article
            className={`connection-card ${c.provider === "telegram" ? "available" : ""}`}
            key={c.id}
          >
            <div className="card-top">
              <span className={`provider-icon provider-${c.provider}`}>
                <ChannelIcon channel={c.provider} size={25} />
              </span>
              <Badge status={c.status} />
            </div>
            <h2>{c.name}</h2>
            <p className="muted">
              {c.provider === "telegram"
                ? "Nhận tin nhắn gửi tới bot và gửi phản hồi sau khi duyệt."
                : "Connector này đang trong kế hoạch, chưa kết nối tài khoản."}
            </p>
            <div className="connection-meta">
              {c.provider === "telegram" ? (
                <>
                  <span>
                    <KeyRound size={14} />
                    {c.configured ? "Credential saved" : "Credential required"}
                  </span>
                  <span>
                    {c.bot_username ? `@${c.bot_username}` : "Bot API"}
                    {c.polling ? " · Auto sync" : ""}
                  </span>
                </>
              ) : (
                <span>OAuth / API integration pending</span>
              )}
            </div>
            <footer className="card-actions">
              {c.provider === "telegram" ? (
                <>
                  <button
                    className="btn"
                    disabled={!owner || busy}
                    onClick={() => open(c)}
                  >
                    <Settings2 size={15} />
                    Configure
                  </button>
                  <button
                    className="btn"
                    disabled={!owner || busy || !c.configured}
                    onClick={() =>
                      task(async () => {
                        await api.post(`/connections/${c.id}/test`);
                        setNotice(
                          "Telegram bot verified. Ready to receive messages.",
                        );
                      })
                    }
                  >
                    Test
                  </button>
                  {c.status === "active" && (
                    <button
                      className="btn icon-button"
                      title="Sync messages"
                      aria-label="Sync messages"
                      disabled={!owner || busy}
                      onClick={() =>
                        task(async () => {
                          const r = await api.post<{ received: number }>(
                            `/connections/${c.id}/sync`,
                          );
                          setNotice(`Received ${r.received} new messages.`);
                        })
                      }
                    >
                      <RefreshCw size={15} />
                    </button>
                  )}
                </>
              ) : (
                <span className="muted small">Planned</span>
              )}
            </footer>
          </article>
        ))}
      </div>
      <div className="info-block">
        <ShieldCheck size={21} />
        <p>
          Telegram dùng Bot API. Hãy nhắn cho bot để nhận tin trong Inbox. Bot
          không đọc hộp thư riêng của tài khoản Telegram cá nhân.
        </p>
      </div>
      {editing && (
        <Modal
          title={
            editing === "new" ? "Connect a Telegram bot" : "Configure Telegram"
          }
          onClose={() => {
            setEditing(undefined);
            setToken("");
          }}
        >
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              save();
            }}
          >
            <label>
              Connection name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                maxLength={160}
              />
            </label>
            <label>
              Bot token
              <input
                type="password"
                autoComplete="new-password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder={
                  editing !== "new" && editing.configured
                    ? "Saved token remains unchanged"
                    : "Token from @BotFather"
                }
              />
              <small>Token được mã hóa và chỉ sử dụng ở backend.</small>
            </label>
            <label>
              Or use a saved credential
              <select
                value={credential}
                onChange={(e) => setCredential(e.target.value)}
              >
                <option value="">Choose a credential</option>
                {credentials
                  .filter(
                    (c) => c.provider === "telegram" && c.status === "active",
                  )
                  .map((c) => (
                    <option value={c.id} key={c.id}>
                      {c.name}
                    </option>
                  ))}
              </select>
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={polling}
                onChange={(e) => setPolling(e.target.checked)}
              />
              Receive messages automatically
            </label>
            <ErrorNotice message={error} />
            <button className="btn primary" disabled={busy}>
              {busy ? "Saving…" : "Save connection"}
            </button>
          </form>
        </Modal>
      )}
    </div>
  );
}
