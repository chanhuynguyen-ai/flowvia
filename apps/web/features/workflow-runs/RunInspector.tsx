import { useEffect, useState } from "react";
import { Check, ChevronDown, Copy, ShieldCheck, Square, X } from "lucide-react";
import { api, errorMessage } from "../../lib/platform";
import { useRealtime } from "../../hooks/useRealtime";
import { Badge, dateTime, ErrorNotice, NodeIcon } from "../../components/UI";
import type { RunDetail, Approval } from "../../types/platform";

export function RunInspector({
  runId,
  role,
  onClose,
}: {
  runId: string;
  role: string;
  onClose?: () => void;
}) {
  const [run, setRun] = useState<RunDetail>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { tick } = useRealtime();
  const refresh = () =>
    api
      .run(runId)
      .then(setRun)
      .catch((e) => setError(errorMessage(e)));
  useEffect(() => {
    let alive = true;
    api
      .run(runId)
      .then((r) => {
        if (alive) setRun(r);
      })
      .catch((e) => {
        if (alive) setError(errorMessage(e));
      });
    return () => {
      alive = false;
    };
  }, [runId, tick]);
  useEffect(() => {
    const timer = setInterval(refresh, 2500);
    return () => clearInterval(timer);
  }, [runId]);
  async function decide(a: Approval, decision: "approve" | "reject") {
    setBusy(true);
    setError("");
    try {
      await api.post(`/approvals/${a.id}/decide`, {
        decision,
        snapshot_hash: a.snapshot_hash,
      });
      await refresh();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  async function cancel() {
    setBusy(true);
    setError("");
    try {
      await api.post(`/runs/${runId}/cancel`);
      await refresh();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  const active =
    run && ["queued", "waiting_human", "waiting_delivery"].includes(run.status);
  return (
    <section className="run-inspector">
      <header className="panel-heading">
        <div>
          <span className="eyebrow">EXECUTION DETAILS</span>
          <h2>{run ? `Run ${run.id.slice(0, 8)}` : "Loading run…"}</h2>
        </div>
        {onClose && (
          <button
            className="icon-button"
            aria-label="Close run details"
            onClick={onClose}
          >
            <X size={19} />
          </button>
        )}
      </header>
      <ErrorNotice message={error} />
      {run && (
        <>
          <div className="run-summary">
            <Badge status={run.status} />
            <Badge status={run.mode} />
            <span>Version {run.version_number}</span>
            <span>{dateTime(run.started_at)}</span>
          </div>
          {run.mode === "dry_run" && (
            <p className="muted small run-disclaimer">
              Chạy thử: phản hồi AI được mô phỏng, không gửi tin ra ngoài.
            </p>
          )}
          {run.error && <ErrorNotice message={run.error} />}
          {run.approvals
            .filter((a) => a.status === "pending")
            .map((a) => (
              <div className="approval-card" key={a.id}>
                <div className="approval-heading">
                  <ShieldCheck size={19} />
                  <strong>Review this action</strong>
                </div>
                <dl>
                  <dt>Action</dt>
                  <dd>
                    {a.snapshot.type === "telegram_send"
                      ? "Telegram message"
                      : "Record result"}
                  </dd>
                  {a.snapshot.chat_id && (
                    <>
                      <dt>Recipient</dt>
                      <dd>{a.snapshot.chat_id}</dd>
                    </>
                  )}
                  {a.snapshot.connection_name && (
                    <>
                      <dt>Connection</dt>
                      <dd>{a.snapshot.connection_name}</dd>
                    </>
                  )}
                </dl>
                <div className="message-preview">{a.snapshot.text}</div>
                {["owner", "reviewer"].includes(role) ? (
                  <div className="button-row">
                    <button
                      className="btn primary"
                      disabled={busy}
                      onClick={() => decide(a, "approve")}
                    >
                      <Check size={16} />
                      {run.mode === "live"
                        ? a.snapshot.type === "telegram_send"
                          ? "Approve & send"
                          : "Approve & record"
                        : "Approve test"}
                    </button>
                    <button
                      className="btn"
                      disabled={busy}
                      onClick={() => decide(a, "reject")}
                    >
                      Reject
                    </button>
                  </div>
                ) : (
                  <p className="muted small">
                    An owner or reviewer can approve this action.
                  </p>
                )}
              </div>
            ))}
          <div className="steps-list">
            {run.graph_json.nodes.map((node) => {
              const s = run.steps.find((item) => item.node_id === node.id);
              return (
                <details
                  key={node.id}
                  className="step-detail"
                  open={s?.status === "failed" || s?.status === "waiting_human"}
                >
                  <summary>
                    <span className={`step-icon step-${s?.status}`}>
                      <NodeIcon type={node.type} size={17} />
                    </span>
                    <span className="step-name">{node.label}</span>
                    <Badge status={s?.status ?? "pending"} />
                    <ChevronDown size={14} />
                  </summary>
                  {s && (
                    <div className="step-data">
                      {s.error && <ErrorNotice message={s.error} />}
                      <span className="eyebrow">INPUT</span>
                      <pre>{JSON.stringify(s.input_json, null, 2)}</pre>
                      <span className="eyebrow">OUTPUT</span>
                      <pre>{JSON.stringify(s.output_json, null, 2)}</pre>
                    </div>
                  )}
                </details>
              );
            })}
          </div>
          {active && ["owner", "builder"].includes(role) && (
            <button className="btn subtle" disabled={busy} onClick={cancel}>
              <Square size={14} />
              Cancel pending steps
            </button>
          )}
          <button
            className="btn subtle"
            onClick={() =>
              navigator.clipboard
                .writeText(run.id)
                .catch(() => setError("Cannot copy to clipboard"))
            }
          >
            <Copy size={14} />
            Copy run ID
          </button>
        </>
      )}
    </section>
  );
}
