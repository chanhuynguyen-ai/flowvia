export type GraphNode = {
  id: string;
  type: string;
  label: string;
  x: number;
  y: number;
  version?: "1";
  config: Record<string, unknown>;
};
export type GraphEdge = {
  source: string;
  target: string;
  source_handle: string;
};
export type Graph = {
  schema_version: 1;
  nodes: GraphNode[];
  edges: GraphEdge[];
};
export type Workflow = {
  id: string;
  name: string;
  description: string;
  slug: string;
  status: string;
  active_version: number;
  revision: number;
  enabled: boolean;
  execution_mode: "dry_run" | "live";
  graph_json: Graph;
  updated_at: string;
};
export type Module = {
  type: string;
  version: string;
  name: string;
  category: string;
  description: string;
  defaults: Record<string, unknown>;
  outputs: string[];
  config_schema: Record<string, unknown>;
};
export type Connection = {
  id: string;
  name: string;
  provider: string;
  status: string;
  configured: boolean;
  polling: boolean;
  bot_username?: string;
  last_checked_at?: string;
};
export type Credential = {
  id: string;
  name: string;
  provider: string;
  status: string;
};
export type Agent = {
  id: string;
  name: string;
  description: string;
  provider: "openrouter";
  model: string;
  system_prompt: string;
  credential_id: string | null;
  status: string;
};
export type Message = {
  id: string;
  connection_id?: string;
  channel: string;
  sender_name: string;
  sender_handle?: string;
  body: string;
  status: string;
  received_at: string;
  external_thread_id: string;
  demo: boolean;
};
export type Run = {
  id: string;
  workflow_id: string;
  version_id: string;
  mode: "dry_run" | "live";
  status: string;
  trigger_channel: string;
  input_preview: string;
  output_preview?: string;
  error?: string;
  started_at: string;
  completed_at?: string;
  next_node_id?: string;
};
export type Step = {
  id: string;
  node_id: string;
  node_type: string;
  status: string;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  error?: string;
  started_at?: string;
  completed_at?: string;
};
export type Approval = {
  id: string;
  node_id: string;
  status: string;
  snapshot: {
    type: string;
    text: string;
    chat_id?: string;
    connection_name?: string;
    mode: string;
  };
  snapshot_hash: string;
};
export type RunDetail = Run & {
  version_number: number;
  steps: Step[];
  approvals: Approval[];
  graph_json: Graph;
  input: Record<string, unknown>;
};
export type Overview = {
  connections_total: number;
  connections_active: number;
  messages_today: number;
  unread: number;
  agents_total: number;
  workflows_total: number;
  workflows_active: number;
  runs_total: number;
  runs_success: number;
  pending_approvals: number;
  channel_counts: Record<string, number>;
  run_statuses: Record<string, number>;
  timezone: string;
  outbound_mode: string;
};
