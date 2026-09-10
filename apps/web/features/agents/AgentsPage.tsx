import { useEffect, useState } from "react";
import { Bot, KeyRound, Plus, Save } from "lucide-react";
import { api, errorMessage } from "../../lib/platform";
import { Badge, ErrorNotice, Modal } from "../../components/UI";
import type { Agent, Credential } from "../../types/platform";
import type { Workspace } from "../../types/api";
const blank: Omit<Agent, "id" | "status"> = {
  name: "New assistant",
  description: "",
  provider: "openrouter",
  model: "",
  system_prompt:
    "Bạn là trợ lý hỗ trợ. Trả lời ngắn gọn, lịch sự bằng tiếng Việt.",
  credential_id: null,
};
export function AgentsPage({ workspace }: { workspace: Workspace }) {
  const [agents, setAgents] = useState<Agent[]>([]),
    [creds, setCreds] = useState<Credential[]>([]),
    [editing, setEditing] = useState<string>(),
    [form, setForm] = useState(blank),
    [secret, setSecret] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const editable = ["owner", "builder"].includes(workspace.role);
  const refresh = () =>
    Promise.all([
      api.agents().then(setAgents),
      editable ? api.credentials().then(setCreds) : Promise.resolve(),
    ]);
  useEffect(() => {
    refresh().catch((e) => setError(errorMessage(e)));
  }, [workspace.id]);
  function open(a?: Agent) {
    setEditing(a?.id ?? "new");
    setSecret("");
    setForm(
      a
        ? {
            name: a.name,
            description: a.description,
            provider: "openrouter",
            model: a.model,
            system_prompt: a.system_prompt,
            credential_id: a.credential_id,
          }
        : blank,
    );
    setError("");
  }
  async function save() {
    setBusy(true);
    setError("");
    try {
      let body = { ...form };
      if (secret.trim()) {
        const c = await api.post<Credential>("/credentials", {
          name: `${form.name} · OpenRouter`,
          provider: "openrouter",
          secret: secret.trim(),
        });
        body.credential_id = c.id;
      }
      if (editing === "new") await api.post("/agents", body);
      else await api.patch(`/agents/${editing}`, body);
      setEditing(undefined);
      setSecret("");
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
          <span className="eyebrow">YOUR INTELLIGENCE LAYER</span>
          <h1>Agents</h1>
          <p className="muted">
            Cấu hình model và hướng dẫn, sau đó nối agent vào workflow.
          </p>
        </div>
        <button
          className="btn primary"
          disabled={!editable}
          onClick={() => open()}
        >
          <Plus size={17} />
          Create agent
        </button>
      </header>
      <ErrorNotice message={error} />
      <div className="agent-grid">
        {agents.map((a) => (
          <article className="agent-card" key={a.id}>
            <div className="card-top">
              <span className="agent-emblem">
                <Bot size={28} />
              </span>
              <Badge status={a.status} />
            </div>
            <h2>{a.name}</h2>
            <p className="muted">
              {a.description || "A configurable assistant for your workflows."}
            </p>
            <div className="model-label">
              <span>MODEL</span>
              <strong>{a.model || "Demo mode"}</strong>
            </div>
            <div className="connection-meta">
              <span>
                <KeyRound size={14} />
                {a.credential_id
                  ? "Credential selected"
                  : "Add an API key for live AI"}
              </span>
            </div>
            <button
              className="btn full"
              disabled={!editable}
              onClick={() => open(a)}
            >
              Configure agent
            </button>
          </article>
        ))}
      </div>
      <div className="info-block">
        <Bot size={21} />
        <p>
          Dry run dùng phản hồi mẫu để thử luồng. Live dùng model OpenRouter bạn
          chọn, có hỗ trợ structured output. Mỗi lần publish workflow sẽ lưu lại
          cấu hình agent tương ứng.
        </p>
      </div>
      {editing && (
        <Modal
          title="Configure agent"
          onClose={() => {
            setEditing(undefined);
            setSecret("");
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
              Name
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </label>
            <label>
              Description
              <input
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
              />
            </label>
            <label>
              OpenRouter model ID
              <input
                value={form.model}
                placeholder="provider/model-name"
                onChange={(e) => setForm({ ...form, model: e.target.value })}
              />
            </label>
            <label>
              Instructions
              <textarea
                rows={5}
                value={form.system_prompt}
                onChange={(e) =>
                  setForm({ ...form, system_prompt: e.target.value })
                }
              />
            </label>
            <label>
              Credential
              <select
                value={form.credential_id ?? ""}
                onChange={(e) =>
                  setForm({ ...form, credential_id: e.target.value || null })
                }
              >
                <option value="">Demo only · no credential</option>
                {creds
                  .filter(
                    (c) => c.provider === "openrouter" && c.status === "active",
                  )
                  .map((c) => (
                    <option value={c.id} key={c.id}>
                      {c.name}
                    </option>
                  ))}
              </select>
            </label>
            {workspace.role === "owner" && (
              <label>
                Or add a new OpenRouter API key
                <input
                  type="password"
                  autoComplete="new-password"
                  value={secret}
                  onChange={(e) => setSecret(e.target.value)}
                  placeholder="API key"
                />
              </label>
            )}
            <ErrorNotice message={error} />
            <button className="btn primary" disabled={busy}>
              <Save size={16} />
              {busy ? "Saving…" : "Save agent"}
            </button>
          </form>
        </Modal>
      )}
    </div>
  );
}
