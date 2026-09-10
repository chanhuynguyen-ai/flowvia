import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  Position,
  addEdge,
  useNodesState,
  useEdgesState,
  type Node as RFNode,
  type Edge as RFEdge,
  type NodeProps,
  type OnNodesChange,
  type OnEdgesChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Check,
  ChevronDown,
  Download,
  GitBranch,
  PanelLeftClose,
  PanelLeftOpen,
  Play,
  Plus,
  Save,
  Search,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { api, errorMessage } from "../../lib/platform";
import type {
  Agent,
  Connection,
  Graph,
  GraphNode,
  Module,
  Run,
  Workflow,
} from "../../types/platform";
import type { Workspace } from "../../types/api";
import {
  Badge,
  Empty,
  ErrorNotice,
  Modal,
  NodeIcon,
} from "../../components/UI";
import { RunInspector } from "../workflow-runs/RunInspector";

type FlowNode = RFNode<{ spec: GraphNode; status?: string }, "flowvia">;
function NodeCard({ data, selected }: NodeProps<FlowNode>) {
  const spec = data.spec;
  return (
    <div
      className={`workflow-node node-${spec.type} ${selected ? "selected" : ""}`}
    >
      {!spec.type.endsWith("_trigger") && (
        <Handle type="target" position={Position.Left} id="in" />
      )}
      <div className="node-main">
        <span className="node-icon">
          <NodeIcon type={spec.type} size={23} />
        </span>
        <div>
          <strong>{spec.label}</strong>
          <span>{spec.type.replaceAll("_", " ")}</span>
        </div>
      </div>
      <div className="node-footer">
        <span>
          {spec.type === "ai_agent"
            ? "OpenRouter"
            : spec.type === "human_approval"
              ? "Human in the loop"
              : spec.type.includes("telegram")
                ? "Telegram Bot API"
                : "Flowvia core"}
        </span>
        <span>v1</span>
      </div>
      {spec.type === "if_else" ? (
        <>
          <Handle
            type="source"
            position={Position.Right}
            id="true"
            style={{ top: "35%" }}
          />
          <Handle
            type="source"
            position={Position.Right}
            id="false"
            style={{ top: "72%" }}
          />
          <span className="port-label true">true</span>
          <span className="port-label false">false</span>
        </>
      ) : (
        <Handle type="source" position={Position.Right} id="out" />
      )}
    </div>
  );
}
const nodeTypes = { flowvia: NodeCard };
const toNodes = (w: Workflow): FlowNode[] =>
  w.graph_json.nodes.map((n) => ({
    id: n.id,
    type: "flowvia",
    position: { x: n.x, y: n.y },
    data: { spec: { ...n, config: n.config ?? {} } },
  }));
const toEdges = (w: Workflow) =>
  w.graph_json.edges.map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    sourceHandle: e.source_handle ?? "out",
    targetHandle: "in",
    type: "default",
  }));

export function WorkflowEditorPage({
  workspace,
  onDirtyChange,
}: {
  workspace: Workspace;
  onDirtyChange: (dirty: boolean) => void;
}) {
  return (
    <ReactFlowProvider>
      <Editor workspace={workspace} onDirtyChange={onDirtyChange} />
    </ReactFlowProvider>
  );
}
function Editor({
  workspace,
  onDirtyChange,
}: {
  workspace: Workspace;
  onDirtyChange: (dirty: boolean) => void;
}) {
  const [workflows, setWorkflows] = useState<Workflow[]>([]),
    [workflow, setWorkflow] = useState<Workflow>();
  const [modules, setModules] = useState<Module[]>([]),
    [connections, setConnections] = useState<Connection[]>([]),
    [agents, setAgents] = useState<Agent[]>([]);
  const [nodes, setNodes, onNodesChange] = useNodesState<FlowNode>([]),
    [edges, setEdges, onEdgesChange] = useEdgesState<RFEdge>([]);
  const [selected, setSelected] = useState<string>(),
    [dirty, setDirty] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [search, setSearch] = useState(""),
    [palette, setPalette] = useState(true),
    [runId, setRunId] = useState<string>(),
    [testOpen, setTestOpen] = useState(false),
    [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState("My new workflow"),
    [input, setInput] = useState(
      "Xin chào, mình muốn tìm hiểu về dịch vụ của bạn.",
    ),
    [chatId, setChatId] = useState("demo-chat"),
    [mode, setMode] = useState<"dry_run" | "live">("dry_run");
  const [tab, setTab] = useState<"editor" | "runs">("editor"),
    [runs, setRuns] = useState<Run[]>([]);
  const canEdit = ["owner", "builder"].includes(workspace.role);
  const hasConfigError = nodes.some(
    (n) =>
      n.data.spec.type === "data_map" &&
      typeof n.data.spec.config.fields === "string",
  );
  const choose = useCallback(
    (w: Workflow) => {
      setWorkflow(w);
      setNodes(toNodes(w));
      setEdges(toEdges(w));
      setSelected(undefined);
      setDirty(false);
      setError("");
      setNotice("");
      setRunId(undefined);
    },
    [setNodes, setEdges],
  );
  useEffect(() => {
    let alive = true;
    Promise.all([
      api.workflows(),
      api.modules(),
      api.connections(),
      api.agents(),
    ])
      .then(([w, m, c, a]) => {
        if (!alive) return;
        setWorkflows(w);
        setModules(m);
        setConnections(c);
        setAgents(a);
        if (w[0])
          choose(
            w.find((item) => item.slug === "telegram-assistant-v1") ?? w[0],
          );
      })
      .catch((e) => setError(errorMessage(e)));
    return () => {
      alive = false;
    };
  }, [workspace.id, choose]);
  useEffect(() => {
    if (tab === "runs")
      api
        .runs()
        .then(setRuns)
        .catch((e) => setError(errorMessage(e)));
  }, [tab, runId]);
  useEffect(() => {
    const guard = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [dirty]);
  useEffect(() => {
    onDirtyChange(dirty);
    return () => onDirtyChange(false);
  }, [dirty, onDirtyChange]);
  const updateNodes: OnNodesChange<FlowNode> = useCallback(
    (changes) => {
      onNodesChange(changes);
      if (changes.some((c) => c.type === "position" || c.type === "remove"))
        setDirty(true);
    },
    [onNodesChange],
  );
  const updateEdges: OnEdgesChange = useCallback(
    (changes) => {
      onEdgesChange(changes);
      if (changes.some((c) => c.type !== "select")) setDirty(true);
    },
    [onEdgesChange],
  );
  const current = nodes.find((n) => n.id === selected);
  const graph = (): Graph => ({
    schema_version: 1,
    nodes: nodes.map((n) => ({
      ...n.data.spec,
      x: n.position.x,
      y: n.position.y,
      version: "1",
    })),
    edges: edges.map((e) => ({
      source: e.source,
      target: e.target,
      source_handle: e.sourceHandle ?? "out",
    })),
  });
  function updateSpec(updates: Partial<GraphNode>) {
    setNodes((ns) =>
      ns.map((n) =>
        n.id === selected
          ? { ...n, data: { ...n.data, spec: { ...n.data.spec, ...updates } } }
          : n,
      ),
    );
    setDirty(true);
  }
  function config(key: string, value: unknown) {
    if (current)
      updateSpec({ config: { ...current.data.spec.config, [key]: value } });
  }
  function addNode(m: Module) {
    const id = `${m.type}-${crypto.randomUUID().slice(0, 8)}`;
    const defaults = { ...m.defaults };
    if (m.type.includes("telegram"))
      defaults.connection_id =
        connections.find((c) => c.provider === "telegram")?.id ?? "";
    if (m.type === "ai_agent") defaults.agent_id = agents[0]?.id ?? "";
    setNodes((ns) => [
      ...ns,
      {
        id,
        type: "flowvia",
        position: {
          x: 100 + (ns.length % 3) * 270,
          y: 120 + Math.floor(ns.length / 3) * 190,
        },
        data: {
          spec: {
            id,
            type: m.type,
            label: m.name,
            x: 0,
            y: 0,
            config: defaults,
          },
        },
      },
    ]);
    setSelected(id);
    setDirty(true);
  }
  async function save() {
    if (hasConfigError)
      throw Error("Fix the JSON in Edit fields before saving.");
    if (!workflow) return;
    const w = await api.patch<Workflow>(`/workflows/${workflow.id}`, {
      name: workflow.name,
      description: workflow.description,
      revision: workflow.revision,
      graph_json: graph(),
    });
    setWorkflow(w);
    setWorkflows((list) => list.map((i) => (i.id === w.id ? w : i)));
    setDirty(false);
    return w;
  }
  async function action(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await fn();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  async function publishCurrent() {
    const w = dirty ? await save() : workflow;
    if (!w) return;
    const result = await api.post<{ workflow: Workflow; version_id: string }>(
      `/workflows/${w.id}/publish`,
      { revision: w.revision },
    );
    setWorkflow(result.workflow);
    setWorkflows((list) =>
      list.map((i) => (i.id === w.id ? result.workflow : i)),
    );
    return result;
  }
  async function test() {
    await action(async () => {
      let w = workflow;
      if (!w) return;
      if (dirty || w.status === "draft" || w.active_version === 0) {
        const p = await publishCurrent();
        w = p?.workflow;
      }
      if (!w) return;
      const versions = await api.get<{ id: string; number: number }[]>(
        `/workflows/${w.id}/versions`,
      );
      const version = versions.find((v) => v.number === w!.active_version);
      if (!version)
        throw Error("Published version is unavailable. Reload the workflow.");
      const r = await api.post<Run>(
        `/workflows/${w.id}/runs`,
        {
          mode,
          version_id: version.id,
          payload: {
            body: input,
            chat_id: chatId,
            sender_name: "Test visitor",
          },
        },
        crypto.randomUUID(),
      );
      setRunId(r.id);
      setTestOpen(false);
      setSelected(undefined);
    });
  }
  async function create() {
    await action(async () => {
      const w = await api.post<Workflow>("/workflows", { name });
      setWorkflows((list) => [w, ...list]);
      choose(w);
      setCreateOpen(false);
    });
  }
  function switchTo(id: string) {
    if (
      dirty &&
      !window.confirm("Bạn có thay đổi chưa lưu. Bỏ các thay đổi này?")
    )
      return;
    const w = workflows.find((x) => x.id === id);
    if (w) choose(w);
  }
  async function validate() {
    await action(async () => {
      const w = dirty ? await save() : workflow;
      if (!w) return;
      const v = await api.post<{ valid: boolean; errors: string[] }>(
        `/workflows/${w.id}/validate`,
      );
      if (!v.valid) throw Error(v.errors.join("\n"));
      setNotice("Graph is valid. Ready to publish.");
    });
  }
  function exportGraph() {
    if (!workflow) return;
    const blob = new Blob(
      [
        JSON.stringify(
          {
            name: workflow.name,
            description: workflow.description,
            graph_json: graph(),
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "flowvia-workflow.json";
    a.click();
    URL.revokeObjectURL(url);
  }
  async function importGraph(file: File) {
    await action(async () => {
      if (file.size > 1_000_000) throw Error("Workflow file exceeds 1 MB");
      const body = JSON.parse(await file.text());
      if (!body.graph_json?.nodes || !body.graph_json?.edges)
        throw Error("Choose a Flowvia workflow JSON file");
      const w = await api.post<Workflow>("/workflows", {
        name: String(body.name || "Imported workflow").slice(0, 180),
        description: body.description || "",
        graph_json: body.graph_json,
      });
      setWorkflows((list) => [w, ...list]);
      choose(w);
      setNotice("Imported. Check the workspace connections, then validate.");
    });
  }
  const cfg = current?.data.spec.config ?? {};
  const groups = useMemo(
    () => [...new Set(modules.map((m) => m.category))],
    [modules],
  );
  return (
    <div className="editor-page">
      <header className="editor-heading">
        <div className="workflow-heading">
          <span className="breadcrumb">
            Workspace <span>/</span> Workflows
          </span>
          <div className="workflow-title">
            <select
              aria-label="Choose workflow"
              value={workflow?.id ?? ""}
              onChange={(e) => switchTo(e.target.value)}
            >
              {workflows.length === 0 && <option>No workflows yet</option>}
              {workflows.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
            <ChevronDown size={17} />
            {workflow && <Badge status={dirty ? "unsaved" : workflow.status} />}
          </div>
        </div>
        <div className="button-row">
          <label
            className="btn icon-button"
            title="Import workflow"
            aria-label="Import workflow"
          >
            <Upload size={17} />
            <input
              type="file"
              accept=".json"
              hidden
              disabled={!canEdit || busy}
              onChange={(e) => {
                if (e.target.files?.[0]) importGraph(e.target.files[0]);
                e.target.value = "";
              }}
            />
          </label>
          <button
            className="btn icon-button"
            title="Export workflow"
            aria-label="Export workflow"
            disabled={!workflow}
            onClick={exportGraph}
          >
            <Download size={17} />
          </button>
          <button
            className="btn"
            disabled={!canEdit || busy}
            onClick={() => setCreateOpen(true)}
          >
            <Plus size={16} />
            New
          </button>
          <button
            className="btn"
            disabled={!canEdit || !workflow || busy || !dirty || hasConfigError}
            onClick={() =>
              action(async () => {
                await save();
                setNotice("Draft saved.");
              })
            }
          >
            <Save size={16} />
            Save
          </button>
          <button
            className="btn primary"
            disabled={!canEdit || !workflow || busy || hasConfigError}
            onClick={() =>
              action(async () => {
                await publishCurrent();
                setNotice("Published a new immutable version.");
              })
            }
          >
            {busy ? "Working…" : "Publish"}
            <GitBranch size={15} />
          </button>
        </div>
      </header>
      <div className="editor-tabs">
        <div className="tab-buttons">
          <button
            className={tab === "editor" ? "active" : ""}
            onClick={() => setTab("editor")}
          >
            Editor
          </button>
          <button
            className={tab === "runs" ? "active" : ""}
            onClick={() => setTab("runs")}
          >
            Executions
          </button>
        </div>
        <div className="editor-state">
          {workflow && (
            <>
              <span>Version {workflow.active_version || "—"}</span>
              <select
                className="mode-select"
                aria-label="Incoming message execution mode"
                value={workflow.execution_mode}
                disabled={
                  workspace.role !== "owner" ||
                  busy ||
                  dirty ||
                  workflow.enabled
                }
                onChange={(e) => {
                  const next = e.target.value;
                  action(async () => {
                    const w = await api.post<Workflow>(
                      `/workflows/${workflow.id}/activation`,
                      { enabled: false, mode: next },
                    );
                    setWorkflow(w);
                    setWorkflows((list) =>
                      list.map((i) => (i.id === w.id ? w : i)),
                    );
                  });
                }}
              >
                <option value="dry_run">Dry run</option>
                <option value="live">Live</option>
              </select>
              <span className="divider" />
              <span>
                {workflow.enabled ? "Listening for messages" : "Manual testing"}
              </span>
              <button
                className={`toggle ${workflow.enabled ? "on" : ""}`}
                aria-label={
                  workflow.enabled ? "Pause workflow" : "Activate workflow"
                }
                disabled={
                  workspace.role !== "owner" ||
                  busy ||
                  !workflow.active_version ||
                  dirty
                }
                onClick={() =>
                  action(async () => {
                    const w = await api.post<Workflow>(
                      `/workflows/${workflow.id}/activation`,
                      {
                        enabled: !workflow.enabled,
                        mode: workflow.execution_mode,
                      },
                    );
                    setWorkflow(w);
                    setWorkflows((list) =>
                      list.map((i) => (i.id === w.id ? w : i)),
                    );
                  })
                }
              />
            </>
          )}
        </div>
      </div>
      {hasConfigError && (
        <div className="editor-notice">
          <ErrorNotice message="Edit fields contains invalid JSON. Select that node to fix it before saving or running." />
        </div>
      )}
      {error && (
        <div className="editor-notice">
          <ErrorNotice message={error} />
          <button
            className="icon-button"
            aria-label="Dismiss error"
            onClick={() => setError("")}
          >
            <X size={16} />
          </button>
        </div>
      )}
      {notice && (
        <div className="notice notice-success">
          <Check size={16} />
          {notice}
        </div>
      )}
      {!workflow ? (
        <Empty title="Create your first workflow">
          <p>
            Start with a trigger, connect your agent, then choose an action.
          </p>
          <button
            className="btn primary"
            disabled={!canEdit}
            onClick={() => setCreateOpen(true)}
          >
            <Plus size={17} />
            Create workflow
          </button>
        </Empty>
      ) : tab === "editor" ? (
        <div
          className={`editor-layout ${palette ? "with-palette" : ""} ${current || runId ? "with-inspector" : ""}`}
        >
          {palette && (
            <aside className="node-palette">
              <div className="panel-heading">
                <strong>Add a node</strong>
                <button
                  className="icon-button"
                  aria-label="Hide node library"
                  onClick={() => setPalette(false)}
                >
                  <PanelLeftClose size={17} />
                </button>
              </div>
              <label className="search-input">
                <Search size={16} />
                <input
                  aria-label="Search nodes"
                  placeholder="Search nodes…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </label>
              {groups.map((group) => (
                <div className="palette-group" key={group}>
                  <span className="eyebrow">{group}</span>
                  {modules
                    .filter(
                      (m) =>
                        m.category === group &&
                        `${m.name} ${m.description}`
                          .toLowerCase()
                          .includes(search.toLowerCase()),
                    )
                    .map((m) => (
                      <button
                        key={m.type}
                        className="palette-node"
                        disabled={!canEdit}
                        onClick={() => addNode(m)}
                      >
                        <span className={`palette-icon node-${m.type}`}>
                          <NodeIcon type={m.type} size={17} />
                        </span>
                        <span>{m.name}</span>
                        <Plus size={14} />
                      </button>
                    ))}
                </div>
              ))}
              <div className="palette-hint">
                Select a node to add it.
                <br />
                Drag between ports to connect.
              </div>
            </aside>
          )}
          <section className="canvas" aria-label="Workflow canvas">
            {!palette && (
              <button
                className="canvas-library btn"
                onClick={() => setPalette(true)}
              >
                <PanelLeftOpen size={16} />
                Nodes
              </button>
            )}
            <ReactFlow
              key={workflow.id}
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              onNodesChange={updateNodes}
              onEdgesChange={updateEdges}
              onConnect={(c) => {
                setEdges((es) => addEdge({ ...c, type: "default" }, es));
                setDirty(true);
              }}
              onNodeClick={(_, n) => {
                setSelected(n.id);
                setRunId(undefined);
              }}
              onPaneClick={() => setSelected(undefined)}
              nodesDraggable={canEdit}
              nodesConnectable={canEdit}
              edgesReconnectable={canEdit}
              deleteKeyCode={canEdit ? "Delete" : null}
              fitView
              fitViewOptions={{ padding: 0.2, maxZoom: 1 }}
              minZoom={0.25}
              maxZoom={1.5}
              colorMode="dark"
            >
              <Background
                variant={BackgroundVariant.Dots}
                gap={22}
                size={1}
                color="#303033"
              />
              <Controls showInteractive={false} />
            </ReactFlow>
            <div className="canvas-caption">
              <span className="canvas-mark">F</span>Your agents. Your workflows.
            </div>
            <div className="canvas-actions">
              <button
                className="btn"
                disabled={!canEdit || busy || hasConfigError}
                onClick={validate}
              >
                <Check size={16} />
                Validate
              </button>
              <button
                className="btn execute"
                disabled={!canEdit || busy || hasConfigError}
                onClick={() => setTestOpen(true)}
              >
                <Play size={16} fill="currentColor" />
                Test workflow
              </button>
            </div>
          </section>
          {runId ? (
            <RunInspector
              key={runId}
              runId={runId}
              role={workspace.role}
              onClose={() => setRunId(undefined)}
            />
          ) : (
            current && (
              <aside className="node-inspector">
                <div className="panel-heading">
                  <div className="inspector-title">
                    <span
                      className={`palette-icon node-${current.data.spec.type}`}
                    >
                      <NodeIcon type={current.data.spec.type} />
                    </span>
                    <strong>{current.data.spec.label}</strong>
                  </div>
                  <button
                    className="icon-button"
                    aria-label="Close node settings"
                    onClick={() => setSelected(undefined)}
                  >
                    <X size={17} />
                  </button>
                </div>
                <div className="inspector-subtitle">
                  Parameters <span>Node v1</span>
                </div>
                <fieldset disabled={!canEdit} className="node-fields">
                  <label>
                    Node name
                    <input
                      value={current.data.spec.label}
                      onChange={(e) => updateSpec({ label: e.target.value })}
                    />
                  </label>
                  {current.data.spec.type.includes("telegram") && (
                    <label>
                      Connection
                      <select
                        value={String(cfg.connection_id ?? "")}
                        onChange={(e) =>
                          config("connection_id", e.target.value)
                        }
                      >
                        <option value="">Select a Telegram bot</option>
                        {connections
                          .filter((c) => c.provider === "telegram")
                          .map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.name} · {c.status.replaceAll("_", " ")}
                            </option>
                          ))}
                      </select>
                    </label>
                  )}
                  {current.data.spec.type === "ai_agent" && (
                    <>
                      <label>
                        Agent
                        <select
                          value={String(cfg.agent_id ?? "")}
                          onChange={(e) => config("agent_id", e.target.value)}
                        >
                          <option value="">Choose an agent</option>
                          {agents.map((a) => (
                            <option key={a.id} value={a.id}>
                              {a.name}
                            </option>
                          ))}
                        </select>
                      </label>
                      <div className="info-block">
                        <NodeIcon type="ai_agent" size={18} />
                        <p>
                          Configure instructions and a model in Agents.
                          Publishing keeps that configuration for future runs.
                        </p>
                      </div>
                    </>
                  )}
                  {current.data.spec.type === "telegram_send" && (
                    <label>
                      Recipient chat ID
                      <input
                        value={String(cfg.chat_id ?? "")}
                        onChange={(e) => config("chat_id", e.target.value)}
                      />
                      <small>
                        Use {"{{ input.chat_id }}"} to reply to the sender.
                      </small>
                    </label>
                  )}
                  {["telegram_send", "record_action"].includes(
                    current.data.spec.type,
                  ) && (
                    <label>
                      Message
                      <textarea
                        rows={5}
                        value={String(cfg.text ?? "")}
                        onChange={(e) => config("text", e.target.value)}
                      />
                      <small>
                        Map an output, for example {"{{ data.reply }}"}.
                      </small>
                    </label>
                  )}
                  {current.data.spec.type === "data_map" && (
                    <MapFields
                      key={current.id}
                      value={cfg.fields ?? {}}
                      onChange={(value) => config("fields", value)}
                    />
                  )}
                  {current.data.spec.type === "if_else" && (
                    <>
                      <label>
                        Field path
                        <input
                          value={String(cfg.field ?? "")}
                          onChange={(e) => config("field", e.target.value)}
                        />
                      </label>
                      <label>
                        Condition
                        <select
                          value={String(cfg.operator ?? "contains")}
                          onChange={(e) => config("operator", e.target.value)}
                        >
                          <option value="contains">Contains</option>
                          <option value="equals">Equals</option>
                          <option value="exists">Exists</option>
                        </select>
                      </label>
                      <label>
                        Value
                        <input
                          value={String(cfg.value ?? "")}
                          onChange={(e) => config("value", e.target.value)}
                        />
                      </label>
                    </>
                  )}
                  {current.data.spec.type === "human_approval" && (
                    <div className="info-block">
                      <NodeIcon type="human_approval" />
                      <p>
                        An owner or reviewer approves the exact recipient and
                        message. Connect this node directly to an action.
                      </p>
                    </div>
                  )}
                  {current.data.spec.type === "manual_trigger" && (
                    <p className="muted small">
                      Choose Test workflow to enter the message that starts this
                      run.
                    </p>
                  )}
                </fieldset>
                <div className="inspector-bottom">
                  <span className="muted small">
                    Connect nodes to map your flow.
                  </span>
                  <button
                    className="btn danger"
                    disabled={!canEdit}
                    onClick={() => {
                      setNodes((ns) => ns.filter((n) => n.id !== selected));
                      setEdges((es) =>
                        es.filter(
                          (e) => e.source !== selected && e.target !== selected,
                        ),
                      );
                      setSelected(undefined);
                      setDirty(true);
                    }}
                  >
                    <Trash2 size={15} />
                    Remove node
                  </button>
                </div>
              </aside>
            )
          )}
        </div>
      ) : (
        <div className="execution-layout">
          <div className="execution-list">
            {runs.filter((r) => r.workflow_id === workflow.id).length === 0 ? (
              <Empty title="No executions yet">
                <p>Run this workflow from the editor to see its history.</p>
              </Empty>
            ) : (
              runs
                .filter((r) => r.workflow_id === workflow.id)
                .map((r) => (
                  <button
                    className={`run-row ${runId === r.id ? "selected" : ""}`}
                    key={r.id}
                    onClick={() => setRunId(r.id)}
                  >
                    <span>{r.input_preview || r.id.slice(0, 8)}</span>
                    <Badge status={r.status} />
                    <Badge status={r.mode} />
                  </button>
                ))
            )}
          </div>
          {runId && (
            <RunInspector key={runId} runId={runId} role={workspace.role} />
          )}
        </div>
      )}
      {testOpen && (
        <Modal
          title="Test your workflow"
          onClose={() => !busy && setTestOpen(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              test();
            }}
            className="form-stack"
          >
            <p className="muted">
              {dirty ||
              workflow?.status === "draft" ||
              !workflow?.active_version
                ? "Bản nháp sẽ được lưu và phát hành trước khi chạy thử. Workflow đang bật sẽ dùng bản mới cho tin nhắn tiếp theo."
                : `Chạy bản đã phát hành v${workflow.active_version}. Thay đổi cấu hình agent cần Publish để áp dụng.`}
            </p>
            <label>
              Incoming message
              <textarea
                rows={4}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                required
              />
            </label>
            <label>
              Telegram chat ID
              <input
                value={chatId}
                onChange={(e) => setChatId(e.target.value)}
                required
              />
            </label>
            <label>
              Execution mode
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as "dry_run" | "live")}
              >
                <option value="dry_run">Dry run · no external messages</option>
                {workspace.role === "owner" && (
                  <option value="live">
                    Live · uses your configured accounts
                  </option>
                )}
              </select>
            </label>
            <div className="info-block">
              <p>
                {mode === "dry_run"
                  ? "AI trả lời mẫu để bạn kiểm tra luồng. Không cần API key."
                  : "AI dùng model và tài khoản đã cấu hình. Tin gửi Telegram vẫn cần duyệt trong lượt chạy."}
              </p>
            </div>
            <ErrorNotice message={error} />
            <button className="btn execute" disabled={busy}>
              <Play size={16} />
              {busy ? "Starting…" : "Run workflow"}
            </button>
          </form>
        </Modal>
      )}
      {createOpen && (
        <Modal title="Create a workflow" onClose={() => setCreateOpen(false)}>
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              create();
            }}
          >
            <label>
              Workflow name
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                maxLength={180}
              />
            </label>
            <button className="btn primary" disabled={busy}>
              Create workflow
            </button>
            <ErrorNotice message={error} />
          </form>
        </Modal>
      )}
    </div>
  );
}
function MapFields({
  value,
  onChange,
}: {
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  const [text, setText] = useState(
      typeof value === "string" ? value : JSON.stringify(value, null, 2),
    ),
    [error, setError] = useState("");
  return (
    <label>
      Mapped fields (JSON)
      <textarea
        rows={9}
        className="mono"
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          try {
            const v = JSON.parse(e.target.value);
            if (!v || Array.isArray(v) || typeof v !== "object") throw Error();
            onChange(v);
            setError("");
          } catch {
            onChange(e.target.value);
            setError("Enter a valid JSON object before saving or testing");
          }
        }}
      />
      {error ? (
        <small className="error-text">{error}</small>
      ) : (
        <small>Example: {'{"text":"{{ input.body }}"}'}</small>
      )}
    </label>
  );
}
