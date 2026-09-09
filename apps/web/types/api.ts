export type Workspace = {
  id: string
  name: string
  kind: 'personal' | 'team' | string
  timezone: string
  role: 'owner' | 'builder' | 'reviewer' | 'viewer' | string
}

export type CurrentUser = {
  id: string
  email: string
  display_name: string
}

export type SessionResponse = {
  user: CurrentUser
  current_workspace: Workspace
  workspaces: Workspace[]
}

export type ApiErrorShape = {
  code?: string
  message?: string
  details?: unknown
  request_id?: string
}
