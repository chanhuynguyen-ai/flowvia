import { useEffect, useState } from "react";
import {
  ArrowRight,
  Bot,
  Check,
  ChevronRight,
  GitBranch,
  Inbox,
  Radio,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { api, errorMessage } from "../../lib/platform";
import { useRealtime } from "../../hooks/useRealtime";
import {
  Badge,
  ChannelIcon,
  dateTime,
  Empty,
  ErrorNotice,
} from "../../components/UI";
import type { Overview, Run } from "../../types/platform";
import type { Workspace } from "../../types/api";
export function Dashboard({
  workspace,
  navigate,
  analytics = false,
}: {
  workspace: Workspace;
  navigate?: (page: string) => void;
  analytics?: boolean;
}) {
  const [overview, setOverview] = useState<Overview>(),
    [runs, setRuns] = useState<Run[]>([]),
    [error, setError] = useState("");
  const { tick } = useRealtime();
  useEffect(() => {
    Promise.all([api.overview(), api.runs()])
      .then(([o, r]) => {
        setOverview(o);
        setRuns(r);
      })
      .catch((e) => setError(errorMessage(e)));
  }, [workspace.id, tick]);
  const o = overview;
  const metrics = [
    {
      label: "Messages today",
      value: o?.messages_today,
      icon: Inbox,
      detail: o?.timezone ?? "Workspace timezone",
    },
    {
      label: "Active workflows",
      value: o?.workflows_active,
      icon: Workflow,
      detail: `${o?.workflows_total ?? 0} workflows in your workspace`,
    },
    {
      label: "Successful runs",
      value: o?.runs_success,
      icon: Check,
      detail: `${o?.runs_total ?? 0} executions in total`,
    },
    {
      label: "Awaiting approval",
      value: o?.pending_approvals,
      icon: ShieldCheck,
      detail: "Ready for your review",
    },
  ];
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <span className="eyebrow">
            {analytics ? "WORKSPACE ACTIVITY" : "YOUR AUTOMATION WORKSPACE"}
          </span>
          <h1>{analytics ? "Analytics" : "Overview"}</h1>
          <p className="muted">
            {analytics
              ? "Số liệu được tính từ tin nhắn và lượt chạy đã lưu."
              : "Kết nối hội thoại. Điều phối agent. Làm việc theo cách của bạn."}
          </p>
        </div>
        <button className="btn primary" onClick={() => navigate?.("workflows")}>
          <GitBranch size={17} />
          Open workflows
          <ArrowRight size={16} />
        </button>
      </header>
      <ErrorNotice message={error} />
      <div className="metric-grid">
        {metrics.map((m) => (
          <article className="metric" key={m.label}>
            <div>
              <span>{m.label}</span>
              <m.icon size={18} />
            </div>
            <strong>{m.value ?? "—"}</strong>
            <small>{m.detail}</small>
          </article>
        ))}
      </div>
      {!analytics && (
        <div className="overview-feature">
          <div>
            <span className="eyebrow">TELEGRAM FIRST</span>
            <h2>Your first conversation workflow.</h2>
            <p className="muted">
              Nhận tin nhắn, soạn câu trả lời bằng agent và kiểm tra trước khi
              gửi. Bắt đầu với chế độ chạy thử.
            </p>
            <button className="btn" onClick={() => navigate?.("workflows")}>
              Continue building
              <ArrowRight size={16} />
            </button>
          </div>
          <div className="overview-pipeline">
            <span>
              <ChannelIcon channel="telegram" size={27} />
              <strong>Message</strong>
            </span>
            <ChevronRight size={17} />
            <span>
              <Bot size={27} />
              <strong>Agent</strong>
            </span>
            <ChevronRight size={17} />
            <span>
              <ShieldCheck size={27} />
              <strong>Approval</strong>
            </span>
          </div>
        </div>
      )}
      <div className="dashboard-columns">
        <section className="panel">
          <header className="panel-heading">
            <h2>{analytics ? "Execution outcomes" : "Recent executions"}</h2>
            <button className="btn subtle" onClick={() => navigate?.("runs")}>
              View all
              <ArrowRight size={14} />
            </button>
          </header>
          {analytics ? (
            <div className="bar-list">
              {Object.entries(o?.run_statuses ?? {}).map(([status, count]) => (
                <div key={status}>
                  <div>
                    <Badge status={status} />
                    <strong>{count}</strong>
                  </div>
                  <span className="bar-track">
                    <span
                      style={{
                        width: `${(count / Math.max(o?.runs_total ?? 1, 1)) * 100}%`,
                      }}
                    />
                  </span>
                </div>
              ))}
              {!o?.runs_total && <Empty title="No execution data yet" />}
            </div>
          ) : runs.length ? (
            runs.slice(0, 5).map((r) => (
              <button
                className="activity-row"
                key={r.id}
                onClick={() => navigate?.("runs")}
              >
                <span className="activity-icon">
                  <Workflow size={17} />
                </span>
                <span>
                  <strong>{r.input_preview || "Workflow execution"}</strong>
                  <small>
                    {dateTime(r.started_at)} ·{" "}
                    {r.mode === "dry_run" ? "Dry run" : "Live"}
                  </small>
                </span>
                <Badge status={r.status} />
              </button>
            ))
          ) : (
            <Empty title="Ready for your first run">
              <p>Execution results appear here after you test a workflow.</p>
            </Empty>
          )}
        </section>
        <section className="panel">
          <header className="panel-heading">
            <h2>Channel activity</h2>
            <Radio size={17} />
          </header>
          <div className="channel-bars">
            {Object.entries(o?.channel_counts ?? {}).map(([c, count]) => (
              <div className="channel-bar" key={c}>
                <span className="channel-label">
                  <ChannelIcon channel={c} size={17} />
                  {c === "manual" ? "Test messages" : c}
                  <strong>{count}</strong>
                </span>
                <span className="bar-track">
                  <span
                    style={{
                      width: `${(count / Math.max(o?.messages_today ?? 1, 1)) * 100}%`,
                    }}
                  />
                </span>
              </div>
            ))}
            {!o?.messages_today && <Empty title="No messages today" />}
          </div>
          <footer className="panel-footer">
            <span>{o?.connections_active ?? 0} connected accounts</span>
            <button
              className="btn subtle"
              onClick={() => navigate?.("connections")}
            >
              Manage
              <ArrowRight size={14} />
            </button>
          </footer>
        </section>
      </div>
    </div>
  );
}
