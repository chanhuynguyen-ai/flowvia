import { useEffect, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Bot,
  ChevronDown,
  CircleHelp,
  GitBranch,
  Inbox,
  LayoutDashboard,
  LogOut,
  Menu,
  Network,
  Settings,
  X,
} from "lucide-react";
import { Dashboard } from "../features/dashboard/Dashboard";
import { WorkflowEditorPage } from "../features/workflow-editor/WorkflowEditorPage";
import { ConnectionsPage } from "../features/connections/ConnectionsPage";
import { SettingsPage } from "../features/connections/SettingsPage";
import { AgentsPage } from "../features/agents/AgentsPage";
import { InboxPage } from "../features/inbox/InboxPage";
import { RunsPage } from "../features/workflow-runs/RunsPage";
import { RealtimeContext, useWorkspaceStream } from "../hooks/useRealtime";
import { api } from "../lib/platform";
import type { SessionResponse } from "../types/api";

export function AppShell({
  session,
  busy,
  onSwitchWorkspace,
  onLogout,
}: {
  session: SessionResponse;
  busy: boolean;
  onSwitchWorkspace: (id: string) => Promise<void>;
  onLogout: () => Promise<void>;
}) {
  const [page, setPage] = useState("workflows"),
    [mobile, setMobile] = useState(false),
    [unread, setUnread] = useState(0),
    [editorDirty, setEditorDirty] = useState(false);
  const workspace = session.current_workspace,
    realtime = useWorkspaceStream(workspace.id);
  const navigation = [
    { key: "overview", label: "Overview", icon: LayoutDashboard },
    { key: "inbox", label: "Inbox", icon: Inbox },
    { key: "workflows", label: "Workflows", icon: GitBranch },
    { key: "agents", label: "Agents", icon: Bot },
    { key: "connections", label: "Connections", icon: Network },
    { key: "runs", label: "Runs", icon: Activity },
    { key: "analytics", label: "Analytics", icon: Activity },
    ...(workspace.role === "owner"
      ? [{ key: "settings", label: "Settings", icon: Settings }]
      : []),
  ];
  useEffect(() => {
    let alive = true;
    api
      .overview()
      .then((o) => {
        if (alive) setUnread(o.unread);
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [workspace.id, realtime.tick]);
  function canLeave() {
    return (
      !editorDirty ||
      window.confirm("Workflow có thay đổi chưa lưu. Bỏ các thay đổi này?")
    );
  }
  function navigate(key: string) {
    if (key !== page && !canLeave()) return;
    setPage(key);
    setMobile(false);
  }
  return (
    <RealtimeContext.Provider value={realtime}>
      <div className="app-shell">
        <div className="mobile-heading">
          <button
            className="icon-button"
            aria-label="Toggle navigation"
            onClick={() => setMobile(!mobile)}
          >
            {mobile ? <X /> : <Menu />}
          </button>
          <strong>Flowvia</strong>
          <span>{page}</span>
        </div>
        <aside className={`sidebar ${mobile ? "open" : ""}`}>
          <a
            className="brand"
            href="#"
            onClick={(e) => {
              e.preventDefault();
              navigate("workflows");
            }}
          >
            <span className="brand-symbol">F</span>
            <strong>
              Flowvia<span className="edition">LITE</span>
            </strong>
          </a>
          <div className="workspace-picker">
            <span className="workspace-avatar">{workspace.name[0]}</span>
            <label>
              <span>Workspace</span>
              <select
                aria-label="Workspace"
                value={workspace.id}
                disabled={busy}
                onChange={(e) => {
                  if (canLeave()) onSwitchWorkspace(e.target.value);
                }}
              >
                {session.workspaces.map((w) => (
                  <option value={w.id} key={w.id}>
                    {w.name}
                  </option>
                ))}
              </select>
            </label>
            <ChevronDown size={14} />
          </div>
          <div className="nav-section-label">WORKSPACE</div>
          <nav aria-label="Main navigation">
            {navigation.map((item) => (
              <button
                key={item.key}
                className={`nav-button ${page === item.key ? "active" : ""}`}
                onClick={() => navigate(item.key)}
              >
                <item.icon size={18} />
                <span>{item.label}</span>
                {item.key === "inbox" && unread > 0 && <small>{unread}</small>}
              </button>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <div className="realtime-status">
              <span
                className={`connection-dot ${realtime.connected ? "connected" : ""}`}
              />
              <span>
                {realtime.connected
                  ? "Live updates connected"
                  : "Reconnecting updates…"}
              </span>
            </div>
            <a
              className="help-link"
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
            >
              <CircleHelp size={16} />
              API documentation
              <ArrowUpRight size={14} />
            </a>
            <div className="sidebar-profile">
              <span className="profile-avatar">
                {session.user.display_name[0]}
              </span>
              <div>
                <strong>{session.user.display_name}</strong>
                <small>{workspace.role}</small>
              </div>
              <button
                className="icon-button"
                aria-label="Sign out"
                onClick={() => {
                  if (canLeave()) onLogout();
                }}
                disabled={busy}
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </aside>
        <main
          className={`main-content ${page === "workflows" ? "canvas-page" : ""}`}
          key={workspace.id}
        >
          {page === "overview" && (
            <Dashboard workspace={workspace} navigate={navigate} />
          )}{" "}
          {page === "workflows" && (
            <WorkflowEditorPage
              workspace={workspace}
              onDirtyChange={setEditorDirty}
            />
          )}{" "}
          {page === "inbox" && <InboxPage workspace={workspace} />}{" "}
          {page === "connections" && <ConnectionsPage workspace={workspace} />}{" "}
          {page === "agents" && <AgentsPage workspace={workspace} />}{" "}
          {page === "runs" && <RunsPage workspace={workspace} />}{" "}
          {page === "analytics" && (
            <Dashboard workspace={workspace} analytics navigate={navigate} />
          )}{" "}
          {page === "settings" && workspace.role === "owner" && (
            <SettingsPage workspace={workspace} />
          )}
        </main>
      </div>
    </RealtimeContext.Provider>
  );
}
