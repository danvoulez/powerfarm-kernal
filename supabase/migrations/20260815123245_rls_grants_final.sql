begin;

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'powerfarm_worker') then
    create role powerfarm_worker nologin noinherit;
  end if;
end
$$;

revoke all on schema powerfarm_internal from public, anon, authenticated, service_role;
revoke all on all tables in schema public from anon, authenticated, service_role;
revoke all on all sequences in schema public from anon, authenticated, service_role;
revoke execute on all functions in schema public from public, anon, authenticated, service_role;
revoke execute on all functions in schema powerfarm_internal
  from public, anon, authenticated, service_role;

alter default privileges in schema public
  revoke all on tables from anon, authenticated, service_role;
alter default privileges in schema public
  revoke all on sequences from anon, authenticated, service_role;
alter default privileges in schema public
  revoke execute on functions from public, anon, authenticated, service_role;
alter default privileges in schema powerfarm_internal
  revoke execute on functions from public, anon, authenticated, service_role;

grant usage on schema public, powerfarm_internal to powerfarm_worker;

grant select on public.objects, public.acts, public.relations, public.registry,
  public.identities, public.identity_keys, public.identity_links,
  public.oauth_applications, public.authorization_proofs,
  public.registry_seed_manifest, public.identity_keys_open,
  public.update_packages
  to powerfarm_worker;

grant select, insert on public.remote_ledger_segments to powerfarm_worker;

grant select, insert, update, delete on
  public.projection_runs, public.projection_checkpoints,
  public.proj_graph_nodes, public.proj_graph_edges,
  public.adk_event_envelopes, public.adk_workflow_nodes,
  public.adk_tool_calls, public.adk_artifact_refs,
  public.trajectory_selectors, public.trajectory_runs,
  public.trajectory_nodes, public.trajectory_edges,
  public.trajectory_features, public.trajectory_annotations
  to powerfarm_worker;

grant execute on function powerfarm_internal.identity_keys_at_cut(text, jsonb)
  to powerfarm_worker;
grant execute on function powerfarm_internal.commit_act(
  text, bytea, text, text, text, jsonb, jsonb, text, jsonb, jsonb,
  jsonb, text, text, text
) to powerfarm_worker;

drop policy if exists powerfarm_worker_select on public.objects;
create policy powerfarm_worker_select on public.objects for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_select on public.acts;
create policy powerfarm_worker_select on public.acts for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_select on public.relations;
create policy powerfarm_worker_select on public.relations for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_select on public.registry;
create policy powerfarm_worker_select on public.registry for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_select on public.identities;
create policy powerfarm_worker_select on public.identities for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_select on public.identity_keys;
create policy powerfarm_worker_select on public.identity_keys for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_select on public.identity_links;
create policy powerfarm_worker_select on public.identity_links for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_select on public.oauth_applications;
create policy powerfarm_worker_select on public.oauth_applications for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_select on public.authorization_proofs;
create policy powerfarm_worker_select on public.authorization_proofs for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_select on public.registry_seed_manifest;
create policy powerfarm_worker_select on public.registry_seed_manifest for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_select on public.remote_ledger_segments;
create policy powerfarm_worker_select on public.remote_ledger_segments for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_insert on public.remote_ledger_segments;
create policy powerfarm_worker_insert on public.remote_ledger_segments for insert
  to powerfarm_worker with check (true);
drop policy if exists powerfarm_worker_select on public.update_packages;
create policy powerfarm_worker_select on public.update_packages for select
  to powerfarm_worker using (true);

do $policy$
declare
  table_name text;
begin
  foreach table_name in array array[
    'projection_runs', 'projection_checkpoints', 'proj_graph_nodes',
    'proj_graph_edges', 'adk_event_envelopes', 'adk_workflow_nodes',
    'adk_tool_calls', 'adk_artifact_refs', 'trajectory_selectors',
    'trajectory_runs', 'trajectory_nodes', 'trajectory_edges',
    'trajectory_features', 'trajectory_annotations'
  ] loop
    execute format('drop policy if exists powerfarm_worker_all on public.%I', table_name);
    execute format(
      'create policy powerfarm_worker_all on public.%I for all to powerfarm_worker using (true) with check (true)',
      table_name
    );
  end loop;
end
$policy$;

commit;
