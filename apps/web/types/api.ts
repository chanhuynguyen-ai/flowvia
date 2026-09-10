export type Workspace = {
  id: string;
  name: string;
  kind: "personal" | "team" | string;
  timezone: string;
  role: "owner" | "builder" | "reviewer" | "viewer" | string;
};

export type CurrentUser = {
  id: string;
  email: string;
  display_name: string;
};

export type SessionResponse = {
  user: CurrentUser;
  current_workspace: Workspace;
  workspaces: Workspace[];
};

export type ApiErrorShape = {
  code?: string;
  message?: string;
  details?: unknown;
  request_id?: string;
};

export type LiteOverview = {
  connections_total: number;
  connections_active: number;
  messages_today: number;
  agents_total: number;
  workflows_total: number;
  runs_total: number;
  runs_success: number;
  channel_counts: Record<string, number>;
};

export type LiteConnection = {
  id: string;
  slug: string;
  provider: string;
  name: string;
  status: string;
  credential_ref?: string | null;
  config: Record<string, unknown>;
  last_checked_at?: string | null;
};

export type LiteMessage = {
  id: string;
  channel: string;
  sender_name: string;
  sender_handle?: string | null;
  body: string;
  ai_summary?: string | null;
  status: string;
  received_at: string;
};

export type LiteAgent = {
  id: string;
  slug: string;
  name: string;
  description: string;
  provider: string;
  model: string;
  status: string;
};

export type WorkflowNode = {
  id: string;
  type: string;
  label: string;
  x: number;
  y: number;
  state?: string;
};

export type WorkflowEdge = {
  source: string;
  target: string;
};

export type LiteWorkflow = {
  id: string;
  slug: string;
  name: string;
  description: string;
  status: string;
  active_version: number;
  graph_json: {
    nodes?: WorkflowNode[];
    edges?: WorkflowEdge[];
  };
  updated_at: string;
};

export type LiteRun = {
  id: string;
  workflow_id: string;
  status: string;
  trigger_channel: string;
  input_preview: string;
  output_preview?: string | null;
  started_at: string;
  completed_at?: string | null;
};

export type TelegramTestResult = {
  configured: boolean;
  connected: boolean;
  bot_username?: string | null;
  bot_name?: string | null;
  message: string;
};
