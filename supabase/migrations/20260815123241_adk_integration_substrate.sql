begin;

create table if not exists public.adk_event_envelopes (
  event_hash text primary key check (event_hash ~ '^[0-9a-f]{64}$'),
  session_id text not null,
  invocation_id text not null,
  author text not null,
  event_type text not null,
  occurred_at timestamptz not null,
  linked_act text references public.acts(hash),
  content jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  ingested_at timestamptz not null default now(),
  check (jsonb_typeof(content) in ('object', 'array')),
  check (jsonb_typeof(metadata) = 'object')
);

create table if not exists public.adk_workflow_nodes (
  workflow_hash text not null check (workflow_hash ~ '^[0-9a-f]{64}$'),
  node_id text not null,
  node_kind text not null,
  parent_node_id text,
  agent_name text,
  status text not null default 'pending'
    check (status in ('pending', 'running', 'complete', 'failed', 'cancelled')),
  input_event_hash text references public.adk_event_envelopes(event_hash),
  output_event_hash text references public.adk_event_envelopes(event_hash),
  started_at timestamptz,
  finished_at timestamptz,
  attributes jsonb not null default '{}'::jsonb,
  primary key (workflow_hash, node_id),
  check (jsonb_typeof(attributes) = 'object'),
  check (finished_at is null or started_at is null or finished_at >= started_at)
);

create table if not exists public.adk_tool_calls (
  call_hash text primary key check (call_hash ~ '^[0-9a-f]{64}$'),
  workflow_hash text not null check (workflow_hash ~ '^[0-9a-f]{64}$'),
  node_id text not null,
  tool_name text not null,
  status text not null default 'requested'
    check (status in ('requested', 'running', 'complete', 'failed', 'cancelled')),
  request_event_hash text references public.adk_event_envelopes(event_hash),
  response_event_hash text references public.adk_event_envelopes(event_hash),
  arguments jsonb not null default '{}'::jsonb,
  result jsonb,
  error jsonb,
  requested_at timestamptz not null default now(),
  completed_at timestamptz,
  foreign key (workflow_hash, node_id)
    references public.adk_workflow_nodes(workflow_hash, node_id),
  check (jsonb_typeof(arguments) = 'object'),
  check (error is null or jsonb_typeof(error) = 'object'),
  check (completed_at is null or completed_at >= requested_at)
);

create table if not exists public.adk_artifact_refs (
  artifact_ref_hash text primary key check (artifact_ref_hash ~ '^[0-9a-f]{64}$'),
  workflow_hash text not null check (workflow_hash ~ '^[0-9a-f]{64}$'),
  node_id text not null,
  object_hash text references public.objects(hash),
  storage_bucket text,
  storage_path text,
  media_type text,
  size_bytes bigint check (size_bytes is null or size_bytes >= 0),
  attributes jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  foreign key (workflow_hash, node_id)
    references public.adk_workflow_nodes(workflow_hash, node_id),
  check (object_hash is not null or (storage_bucket is not null and storage_path is not null)),
  check (jsonb_typeof(attributes) = 'object')
);

create index if not exists adk_events_session_idx
  on public.adk_event_envelopes (session_id, occurred_at);
create index if not exists adk_events_invocation_idx
  on public.adk_event_envelopes (invocation_id, occurred_at);
create index if not exists adk_events_linked_act_idx
  on public.adk_event_envelopes (linked_act) where linked_act is not null;
create index if not exists adk_workflow_status_idx
  on public.adk_workflow_nodes (workflow_hash, status);
create index if not exists adk_tool_calls_workflow_idx
  on public.adk_tool_calls (workflow_hash, node_id, requested_at);
create index if not exists adk_artifacts_object_idx
  on public.adk_artifact_refs (object_hash) where object_hash is not null;

alter table public.adk_event_envelopes enable row level security;
alter table public.adk_workflow_nodes enable row level security;
alter table public.adk_tool_calls enable row level security;
alter table public.adk_artifact_refs enable row level security;

revoke all on public.adk_event_envelopes, public.adk_workflow_nodes,
  public.adk_tool_calls, public.adk_artifact_refs
  from public, anon, authenticated, service_role;

commit;
