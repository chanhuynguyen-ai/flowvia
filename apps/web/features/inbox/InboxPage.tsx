import { useEffect, useState } from "react";
import { ArrowRight, Inbox, Play, Plus, Search } from "lucide-react";
import { api, errorMessage } from "../../lib/platform";
import { useRealtime } from "../../hooks/useRealtime";
import {
  Badge,
  ChannelIcon,
  dateTime,
  Empty,
  ErrorNotice,
  Modal,
} from "../../components/UI";
import { RunInspector } from "../workflow-runs/RunInspector";
import type { Message, Run, Workflow } from "../../types/platform";
import type { Workspace } from "../../types/api";
export function InboxPage({ workspace }: { workspace: Workspace }) {
  const [messages, setMessages] = useState<Message[]>([]),
    [workflows, setWorkflows] = useState<Workflow[]>([]),
    [selected, setSelected] = useState<string>(),
    [search, setSearch] = useState(""),
    [channel, setChannel] = useState("all"),
    [workflowId, setWorkflowId] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [runId, setRunId] = useState<string>(),
    [demo, setDemo] = useState(false),
    [body, setBody] = useState("Xin chào, mình cần được tư vấn thêm.");
  const { tick } = useRealtime(),
    canRun = ["owner", "builder"].includes(workspace.role);
  useEffect(() => {
    let alive = true;
    Promise.all([api.inbox(), api.workflows()])
      .then(([m, w]) => {
        if (!alive) return;
        setMessages(m);
        setWorkflows(w);
        setWorkflowId(
          (prev) => prev || w.find((x) => x.active_version > 0)?.id || "",
        );
        setSelected((prev) => prev || m[0]?.id);
      })
      .catch((e) => setError(errorMessage(e)));
    return () => {
      alive = false;
    };
  }, [workspace.id, tick]);
  const filtered = messages.filter(
    (m) =>
      (channel === "all" || m.channel === channel) &&
      `${m.sender_name} ${m.body}`.toLowerCase().includes(search.toLowerCase()),
  );
  const current = messages.find((m) => m.id === selected);
  async function run() {
    if (!current || !workflowId) return;
    setBusy(true);
    setError("");
    try {
      const r = await api.post<Run>(
        `/workflows/${workflowId}/runs`,
        {
          mode: "dry_run",
          payload: {
            body: current.body,
            chat_id: current.external_thread_id || "demo-chat",
            sender_name: current.sender_name,
            message_id: current.id,
          },
        },
        crypto.randomUUID(),
      );
      setRunId(r.id);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  async function createDemo() {
    setBusy(true);
    try {
      const m = await api.post<{ id: string }>("/inbox/demo", { body });
      setSelected(m.id);
      setMessages(await api.inbox());
      setDemo(false);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  function choose(m: Message) {
    setSelected(m.id);
    setRunId(undefined);
    if (workspace.role !== "viewer" && m.status === "new")
      api
        .patch(`/inbox/${m.id}/read`, {})
        .then(() =>
          setMessages((list) =>
            list.map((i) => (i.id === m.id ? { ...i, status: "read" } : i)),
          ),
        )
        .catch((e) => setError(errorMessage(e)));
  }
  return (
    <div className="page-stack inbox-page">
      <header className="page-header">
        <div>
          <span className="eyebrow">ALL CONVERSATIONS, ONE PLACE</span>
          <h1>Inbox</h1>
          <p className="muted">Xem tin nhắn và đưa nội dung vào workflow.</p>
        </div>
        <button
          className="btn"
          disabled={!canRun}
          onClick={() => setDemo(true)}
        >
          <Plus size={16} />
          Add test message
        </button>
      </header>
      <ErrorNotice message={error} />
      <div className="inbox-filters">
        <label className="search-input">
          <Search size={17} />
          <input
            aria-label="Search messages"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search conversations…"
          />
        </label>
        <select
          aria-label="Filter channel"
          value={channel}
          onChange={(e) => setChannel(e.target.value)}
        >
          <option value="all">All channels</option>
          {[...new Set(messages.map((m) => m.channel))].map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <span className="muted small">{filtered.length} messages</span>
      </div>
      <div className="inbox-layout">
        <section className="message-list">
          {filtered.length === 0 ? (
            <Empty title="No messages found">
              <p>Connect Telegram or add a test message.</p>
            </Empty>
          ) : (
            filtered.map((m) => (
              <button
                className={`message-item ${selected === m.id ? "selected" : ""}`}
                key={m.id}
                onClick={() => choose(m)}
              >
                <span className="message-avatar">
                  {m.sender_name.slice(0, 1)}
                </span>
                <span className="message-item-body">
                  <span className="message-item-heading">
                    <strong>{m.sender_name}</strong>
                    <time>{dateTime(m.received_at)}</time>
                  </span>
                  <span className="message-snippet">{m.body}</span>
                  <span className="message-source">
                    <ChannelIcon channel={m.channel} size={12} />
                    {m.demo ? "Test message" : m.channel}
                    {m.status === "new" && <span className="unread-dot" />}
                  </span>
                </span>
              </button>
            ))
          )}
        </section>
        {runId ? (
          <RunInspector
                key={runId}
            runId={runId}
            role={workspace.role}
            onClose={() => setRunId(undefined)}
          />
        ) : current ? (
          <section className="conversation">
            <header>
              <span className="message-avatar">{current.sender_name[0]}</span>
              <div>
                <h2>{current.sender_name}</h2>
                <span className="muted small">
                  {current.sender_handle || current.channel}
                </span>
              </div>
              <Badge status={current.demo ? "demo" : current.status} />
            </header>
            <div className="conversation-content">
              <span className="date-divider">
                {dateTime(current.received_at)}
              </span>
              <div className="chat-bubble">{current.body}</div>
            </div>
            <div className="conversation-action">
              <h3>
                <Inbox size={18} />
                Process with a workflow
              </h3>
              <p className="muted small">
                Chạy thử với nội dung này và kiểm tra bản phản hồi.
              </p>
              <div className="button-row">
                <select
                  aria-label="Choose workflow for message"
                  value={workflowId}
                  onChange={(e) => setWorkflowId(e.target.value)}
                >
                  {workflows
                    .filter((w) => w.active_version > 0)
                    .map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.name}
                      </option>
                    ))}
                </select>
                <button
                  className="btn primary"
                  disabled={!canRun || busy || !workflowId}
                  onClick={run}
                >
                  <Play size={16} />
                  Test run
                  <ArrowRight size={15} />
                </button>
              </div>
            </div>
          </section>
        ) : (
          <Empty title="Select a conversation" />
        )}
      </div>
      {demo && (
        <Modal title="Add a test message" onClose={() => setDemo(false)}>
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              createDemo();
            }}
          >
            <label>
              Message
              <textarea
                rows={5}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                required
              />
            </label>
            <ErrorNotice message={error} />
            <button className="btn primary" disabled={busy}>
              Add message
            </button>
          </form>
        </Modal>
      )}
    </div>
  );
}
