-- 20260815060432 harden — castle wall on the kernel itself + pinned search_path.
-- Idempotent.

begin;

alter table objects enable row level security;
alter table acts enable row level security;
alter table relations enable row level security;
alter table registry enable row level security;
alter table identities enable row level security;
alter table identity_keys enable row level security;

alter function public.reject_act_mutation() set search_path = '';

commit;
