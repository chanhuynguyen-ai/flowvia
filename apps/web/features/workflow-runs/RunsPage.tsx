import { useEffect, useState } from "react";
import { api, errorMessage } from "../../lib/platform";
import { useRealtime } from "../../hooks/useRealtime";
import { Badge, dateTime, Empty, ErrorNotice } from "../../components/UI";
import { RunInspector } from "./RunInspector";
import type { Run, Workflow } from "../../types/platform";
import type { Workspace } from "../../types/api";
export function RunsPage({ workspace }: { workspace: Workspace }) {
  const [runs, setRuns] = useState<Run[]>([]),
    [workflows, setWorkflows] = useState<Workflow[]>([]),
    [selected, setSelected] = useState<string>(),
    [filter, setFilter] = useState("all"),
    [error, setError] = useState("");
  const { tick } = useRealtime();
  useEffect(() => {
    Promise.all([api.runs(), api.workflows()])
      .then(([r, w]) => {
        setRuns(r);
        setWorkflows(w);
      })
      .catch((e) => setError(errorMessage(e)));
  }, [workspace.id, tick]);
  const items = runs.filter((r) => filter === "all" || r.status === filter);
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <span className="eyebrow">EXECUTION HISTORY</span>
          <h1>Runs</h1>
          <p className="muted">
            Theo dõi kết quả, kiểm tra từng bước và duyệt các hành động đang
            chờ.
          </p>
        </div>
        <select
          aria-label="Filter runs by status"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="all">All statuses</option>
          {[
            "succeeded",
            "waiting_human",
            "failed",
            "queued",
            "delivery_unknown",
            "cancelled",
            "rejected",
          ].map((s) => (
            <option value={s} key={s}>
              {s.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </header>
      <ErrorNotice message={error} />
      <div className={`runs-layout ${selected ? "has-selection" : ""}`}>
        <div className="panel table-container">
          {items.length === 0 ? (
            <Empty title="No runs yet">
              <p>Test a workflow to start building your execution history.</p>
            </Empty>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Workflow / input</th>
                  <th>Status</th>
                  <th>Mode</th>
                  <th>Started</th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr
                    key={r.id}
                    className={selected === r.id ? "selected" : ""}
                  >
                    <td>
                      <button
                        className="table-link"
                        onClick={() => setSelected(r.id)}
                      >
                        <strong>
                          {workflows.find((w) => w.id === r.workflow_id)
                            ?.name ?? "Workflow"}
                        </strong>
                        <span>{r.input_preview || r.id.slice(0, 8)}</span>
                      </button>
                    </td>
                    <td>
                      <Badge status={r.status} />
                    </td>
                    <td>
                      <Badge status={r.mode} />
                    </td>
                    <td>{dateTime(r.started_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        {selected && (
          <RunInspector
            key={selected}
            runId={selected}
            role={workspace.role}
            onClose={() => setSelected(undefined)}
          />
        )}
      </div>
    </div>
  );
}
