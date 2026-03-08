-- Run this in Supabase: SQL Editor → New query → paste → Run
-- Then set SUPABASE_URL and SUPABASE_ANON_KEY in landing/.env or landing/.config (see .env.example)

-- 1. Table for signups
create table if not exists public.signups (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  created_at timestamptz not null default now()
);

-- 2. RLS: allow anyone to insert; no direct read (emails stay private)
alter table public.signups enable row level security;

create policy "Allow anonymous insert"
  on public.signups for insert
  to anon
  with check (true);

-- 3. Function so the frontend can get only the count (no access to rows)
create or replace function public.get_signup_count()
returns bigint
language sql
security definer
set search_path = public
as $$
  select count(*)::bigint from public.signups;
$$;

grant execute on function public.get_signup_count() to anon;
