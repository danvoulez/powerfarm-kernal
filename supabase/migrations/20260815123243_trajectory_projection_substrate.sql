begin;

create table if not exists public.trajectory_selectors (
  selector_hash text primary key check (selector_hash ~ '^[0-9a-f]{64}$'),
  name text not null,
  version bigint not null check (version > 0),
  projector_hash text not null references public.registry(hash),
  definition jsonb not null,
  registered_act text references public.acts(hash),
  created_at timestamptz not null default now(),
  unique (name, version),
  check (jsonb_typeof(definition) = 'object')
);

create table if not exists public.trajectory_runs (
  run_hash text primary key check (run_hash ~ '^[0-9a-f]{64}$'),
  selector_hash text not null references public.trajectory_selectors(selector_hash),
  input_cut jsonb not null,
  input_cut_hash text not null check (input_cut_hash ~ '^[0-9a-f]{64}$'),
  status text not null default 'running'
    check (status in ('running', 'complete', 'failed', 'superseded')),
  parameters jsonb not null default '{}'::jsonb,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  error jsonb,
  unique (selector_hash, input_cut_hash, run_hash),
  check (powerfarm_internal.is_hash_array(input_cut)),
  check (jsonb_typeof(parameters) = 'object'),
  check (error is null or jsonb_typeof(error) = 'object'),
  check (finished_at is null or finished_at >= started_at)
);

create table if not exists public.trajectory_nodes (
  run_hash text not null references public.trajectory_runs(run_hash) on delete cascade,
  node_hash text not null check (node_hash ~ '^[0-9a-f]{64}$'),
  ordinal bigint not null check (ordinal >= 0),
  node_role text not null
    check (node_role in ('observed', 'simulated', 'crafted', 'candidate', 'counterfactual')),
  act_hash text references public.acts(hash),
  state_hash text check (state_hash is null or state_hash ~ '^[0-9a-f]{64}$'),
  properties jsonb not null default '{}'::jsonb,
  primary key (run_hash, node_hash),
  unique (run_hash, ordinal),
  check (act_hash is not null or state_hash is not null),
  check (jsonb_typeof(properties) = 'object')
);

create table if not exists public.trajectory_edges (
  run_hash text not null references public.trajectory_runs(run_hash) on delete cascade,
  edge_hash text not null check (edge_hash ~ '^[0-9a-f]{64}$'),
  from_hash text not null check (from_hash ~ '^[0-9a-f]{64}$'),
  to_hash text not null check (to_hash ~ '^[0-9a-f]{64}$'),
  edge_type text not null,
  weight double precision,
  properties jsonb not null default '{}'::jsonb,
  primary key (run_hash, edge_hash),
  foreign key (run_hash, from_hash) references public.trajectory_nodes(run_hash, node_hash),
  foreign key (run_hash, to_hash) references public.trajectory_nodes(run_hash, node_hash),
  check (weight is null or weight = weight),
  check (jsonb_typeof(properties) = 'object')
);

create table if not exists public.trajectory_features (
  run_hash text not null,
  node_hash text not null,
  feature_name text not null,
  feature_version bigint not null default 1 check (feature_version > 0),
  value jsonb not null,
  computed_at timestamptz not null default now(),
  primary key (run_hash, node_hash, feature_name, feature_version),
  foreign key (run_hash, node_hash) references public.trajectory_nodes(run_hash, node_hash)
    on delete cascade
);

create table if not exists public.trajectory_annotations (
  annotation_hash text primary key check (annotation_hash ~ '^[0-9a-f]{64}$'),
  run_hash text not null,
  node_hash text not null,
  annotation_type text not null,
  body jsonb not null,
  author_identity text references public.identities(hash),
  source_act text references public.acts(hash),
  created_at timestamptz not null default now(),
  foreign key (run_hash, node_hash) references public.trajectory_nodes(run_hash, node_hash),
  check (jsonb_typeof(body) = 'object')
);

create index if not exists trajectory_runs_selector_idx
  on public.trajectory_runs (selector_hash, started_at desc);
create index if not exists trajectory_nodes_act_idx
  on public.trajectory_nodes (act_hash) where act_hash is not null;
create index if not exists trajectory_nodes_role_idx
  on public.trajectory_nodes (run_hash, node_role, ordinal);
create index if not exists trajectory_edges_from_idx
  on public.trajectory_edges (run_hash, from_hash, edge_type);
create index if not exists trajectory_edges_to_idx
  on public.trajectory_edges (run_hash, to_hash, edge_type);
create index if not exists trajectory_features_name_idx
  on public.trajectory_features (feature_name, feature_version);

alter table public.trajectory_selectors enable row level security;
alter table public.trajectory_runs enable row level security;
alter table public.trajectory_nodes enable row level security;
alter table public.trajectory_edges enable row level security;
alter table public.trajectory_features enable row level security;
alter table public.trajectory_annotations enable row level security;

revoke all on public.trajectory_selectors, public.trajectory_runs,
  public.trajectory_nodes, public.trajectory_edges, public.trajectory_features,
  public.trajectory_annotations
  from public, anon, authenticated, service_role;

commit;
