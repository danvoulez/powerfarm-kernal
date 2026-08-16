-- A credential principal is (issuer, subject). Nothing less identifies it.
--
-- `identity_links` keyed the binding on `supabase_user uuid references
-- auth.users(id)`, which made a Supabase row the ontology of a Powerfarm
-- Identity. Two consequences followed, both wrong: the issuer was structurally
-- absent, so a subject asserted by any issuer resolved the same way; and the
-- subject had to be a UUID, which is a fact about one authorization server
-- rather than about principals.
--
-- Section 5.1 keeps these apart: a platform session is authentication evidence,
-- linked to a stable Powerfarm Identity, and never itself an authority. The
-- binding is therefore between an issuer's subject and an Identity, and both
-- its creation and its revocation are Acts.
--
-- `identity_links` is dropped rather than left beside its replacement: it holds
-- no Acts and no rows, and a second, subtly wrong answer to "who is this?" is
-- worse than none.

begin;

create table if not exists public.principal_bindings (
  issuer text not null check (issuer <> ''),
  subject text not null check (subject <> ''),
  identity_hash text not null references public.identities(hash),
  linked_act text not null references public.acts(hash),
  unlinked_act text references public.acts(hash),
  primary key (issuer, subject, linked_act)
);

-- At most one live binding per credential principal. Revoked ones stay as
-- history: unlinking is an Act, not a delete.
create unique index if not exists principal_bindings_active_idx
  on public.principal_bindings (issuer, subject)
  where unlinked_act is null;

create index if not exists principal_bindings_identity_idx
  on public.principal_bindings (identity_hash)
  where unlinked_act is null;

drop trigger if exists principal_bindings_are_immutable on public.principal_bindings;
create trigger principal_bindings_are_immutable
before delete on public.principal_bindings
for each row execute function powerfarm_internal.reject_ledger_mutation();

alter table public.principal_bindings enable row level security;
revoke all on public.principal_bindings from public, anon, authenticated, service_role;
grant select, insert, update on public.principal_bindings to powerfarm_worker;

drop policy if exists powerfarm_worker_select on public.principal_bindings;
create policy powerfarm_worker_select on public.principal_bindings for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_insert on public.principal_bindings;
create policy powerfarm_worker_insert on public.principal_bindings for insert
  to powerfarm_worker with check (true);
drop policy if exists powerfarm_worker_unlink on public.principal_bindings;
create policy powerfarm_worker_unlink on public.principal_bindings for update
  to powerfarm_worker using (true) with check (true);

drop table if exists public.identity_links;

commit;
