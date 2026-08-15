begin;

create table if not exists public.projection_runs (
  run_hash text primary key check (run_hash ~ '^[0-9a-f]{64}$'),
  projector_hash text not null references public.registry(hash),
  input_cut jsonb not null,
  input_cut_hash text not null check (input_cut_hash ~ '^[0-9a-f]{64}$'),
  status text not null default 'running'
    check (status in ('running', 'complete', 'failed', 'superseded')),
  high_water_seq bigint not null default 0 check (high_water_seq >= 0),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  error jsonb,
  unique (projector_hash, input_cut_hash),
  check (powerfarm_internal.is_hash_array(input_cut)),
  check (error is null or jsonb_typeof(error) = 'object'),
  check (finished_at is null or finished_at >= started_at)
);

create table if not exists public.projection_checkpoints (
  projector_hash text primary key references public.registry(hash),
  input_cut jsonb not null,
  input_cut_hash text not null check (input_cut_hash ~ '^[0-9a-f]{64}$'),
  high_water_seq bigint not null check (high_water_seq >= 0),
  run_hash text not null references public.projection_runs(run_hash),
  updated_at timestamptz not null default now(),
  check (powerfarm_internal.is_hash_array(input_cut))
);

create table if not exists public.proj_graph_nodes (
  projector_hash text not null references public.registry(hash),
  input_cut_hash text not null check (input_cut_hash ~ '^[0-9a-f]{64}$'),
  node_hash text not null check (node_hash ~ '^[0-9a-f]{64}$'),
  node_kind text not null,
  labels jsonb not null default '[]'::jsonb,
  properties jsonb not null default '{}'::jsonb,
  primary key (projector_hash, input_cut_hash, node_hash),
  foreign key (projector_hash, input_cut_hash)
    references public.projection_runs(projector_hash, input_cut_hash)
    on delete cascade,
  check (jsonb_typeof(labels) = 'array'),
  check (jsonb_typeof(properties) = 'object')
);

create table if not exists public.proj_graph_edges (
  projector_hash text not null references public.registry(hash),
  input_cut_hash text not null check (input_cut_hash ~ '^[0-9a-f]{64}$'),
  edge_hash text not null check (edge_hash ~ '^[0-9a-f]{64}$'),
  from_hash text not null check (from_hash ~ '^[0-9a-f]{64}$'),
  to_hash text not null check (to_hash ~ '^[0-9a-f]{64}$'),
  edge_type text not null,
  properties jsonb not null default '{}'::jsonb,
  primary key (projector_hash, input_cut_hash, edge_hash),
  foreign key (projector_hash, input_cut_hash)
    references public.projection_runs(projector_hash, input_cut_hash)
    on delete cascade,
  check (jsonb_typeof(properties) = 'object')
);

create index if not exists projection_runs_status_idx
  on public.projection_runs (status, started_at);
create index if not exists projection_runs_projector_seq_idx
  on public.projection_runs (projector_hash, high_water_seq desc);
create index if not exists proj_graph_nodes_kind_idx
  on public.proj_graph_nodes (projector_hash, input_cut_hash, node_kind);
create index if not exists proj_graph_edges_from_idx
  on public.proj_graph_edges (projector_hash, input_cut_hash, from_hash, edge_type);
create index if not exists proj_graph_edges_to_idx
  on public.proj_graph_edges (projector_hash, input_cut_hash, to_hash, edge_type);

alter table public.projection_runs enable row level security;
alter table public.projection_checkpoints enable row level security;
alter table public.proj_graph_nodes enable row level security;
alter table public.proj_graph_edges enable row level security;

revoke all on public.projection_runs, public.projection_checkpoints,
  public.proj_graph_nodes, public.proj_graph_edges
  from public, anon, authenticated, service_role;

commit;
