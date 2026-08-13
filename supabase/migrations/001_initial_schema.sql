-- WoundAI Master's Capstone - initial Supabase schema
-- Run in a new Supabase project before using the web application.

create extension if not exists pgcrypto;

create type public.app_role as enum ('participant', 'reviewer', 'researcher', 'admin');
create type public.model_status as enum ('development', 'research', 'approved', 'archived');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  role public.app_role not null default 'participant',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.wound_images (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  storage_path text not null unique,
  original_filename text,
  mime_type text not null,
  file_size_bytes bigint not null check (file_size_bytes > 0),
  created_at timestamptz not null default now()
);

create table public.model_versions (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  version text not null,
  status public.model_status not null default 'development',
  notes text,
  created_at timestamptz not null default now(),
  unique(name, version)
);

create table public.predictions (
  id uuid primary key default gen_random_uuid(),
  wound_image_id uuid not null references public.wound_images(id) on delete cascade,
  model_version_id uuid references public.model_versions(id),
  predicted_class text not null,
  confidence_score double precision not null check (confidence_score >= 0 and confidence_score <= 1),
  is_uncertain boolean not null default false,
  gradcam_storage_path text,
  created_at timestamptz not null default now()
);

create table public.prediction_scores (
  id uuid primary key default gen_random_uuid(),
  prediction_id uuid not null references public.predictions(id) on delete cascade,
  category text not null,
  probability double precision not null check (probability >= 0 and probability <= 1),
  unique(prediction_id, category)
);

create table public.expert_reviews (
  id uuid primary key default gen_random_uuid(),
  prediction_id uuid not null references public.predictions(id) on delete cascade,
  reviewer_id uuid not null references public.profiles(id),
  verified_class text not null,
  is_prediction_correct boolean not null,
  comments text,
  created_at timestamptz not null default now(),
  unique(prediction_id, reviewer_id)
);

create table public.model_metrics (
  id uuid primary key default gen_random_uuid(),
  model_version_id uuid not null references public.model_versions(id) on delete cascade,
  dataset_split text not null default 'test',
  accuracy double precision,
  macro_precision double precision,
  macro_recall double precision,
  macro_f1 double precision,
  inference_ms double precision,
  sample_count integer,
  created_at timestamptz not null default now()
);

create table public.audit_logs (
  id bigint generated always as identity primary key,
  actor_id uuid references public.profiles(id),
  action text not null,
  entity_type text,
  entity_id uuid,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- Automatically create a participant profile after auth signup.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', ''));
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Helper prevents trusting client-supplied roles.
create or replace function public.current_role()
returns public.app_role
language sql
stable
security definer
set search_path = public
as $$
  select role from public.profiles where id = auth.uid()
$$;

alter table public.profiles enable row level security;
alter table public.wound_images enable row level security;
alter table public.model_versions enable row level security;
alter table public.predictions enable row level security;
alter table public.prediction_scores enable row level security;
alter table public.expert_reviews enable row level security;
alter table public.model_metrics enable row level security;
alter table public.audit_logs enable row level security;

-- Profiles
create policy "Users read own profile"
on public.profiles for select
using (
  id = auth.uid()
  or public.current_role() in ('reviewer','researcher','admin')
);

-- Profile writes are intentionally not exposed to participant clients in the MVP.
-- Update names/roles through a trusted administrative workflow, not directly from browser clients.

-- Images
create policy "Users insert own images"
on public.wound_images for insert
with check (user_id = auth.uid());

create policy "Users read own images"
on public.wound_images for select
using (
  user_id = auth.uid()
  or public.current_role() in ('reviewer','researcher','admin')
);

-- Models / metrics readable to authenticated researchers and participants.
create policy "Authenticated read model versions"
on public.model_versions for select
to authenticated
using (true);

-- Model versions are controlled research metadata. Do not allow arbitrary browser inserts.

create policy "Authenticated read model metrics"
on public.model_metrics for select
to authenticated
using (true);

-- Seed the known development model used by the mock inference service.
insert into public.model_versions (name, version, status, notes)
values ('EfficientNet-B0', 'mock-v0.1', 'development', 'Mock inference only; not a trained research model.')
on conflict (name, version) do nothing;

-- Predictions
create policy "Users insert prediction for own image"
on public.predictions for insert
with check (
  exists (
    select 1 from public.wound_images wi
    where wi.id = wound_image_id and wi.user_id = auth.uid()
  )
);

create policy "Users read predictions for own images"
on public.predictions for select
using (
  exists (
    select 1 from public.wound_images wi
    where wi.id = wound_image_id
      and (wi.user_id = auth.uid() or public.current_role() in ('reviewer','researcher','admin'))
  )
);

-- Scores
create policy "Users insert scores for own prediction"
on public.prediction_scores for insert
with check (
  exists (
    select 1
    from public.predictions p
    join public.wound_images wi on wi.id = p.wound_image_id
    where p.id = prediction_id and wi.user_id = auth.uid()
  )
);

create policy "Users read scores for visible prediction"
on public.prediction_scores for select
using (
  exists (
    select 1
    from public.predictions p
    join public.wound_images wi on wi.id = p.wound_image_id
    where p.id = prediction_id
      and (wi.user_id = auth.uid() or public.current_role() in ('reviewer','researcher','admin'))
  )
);

-- Expert review
create policy "Reviewers read reviews"
on public.expert_reviews for select
using (
  reviewer_id = auth.uid()
  or public.current_role() in ('reviewer','researcher','admin')
);

create policy "Reviewers create reviews"
on public.expert_reviews for insert
with check (
  reviewer_id = auth.uid()
  and public.current_role() in ('reviewer','researcher','admin')
);

-- Storage policies. Create private bucket named wound-images first.
create policy "Users upload to own wound folder"
on storage.objects for insert
to authenticated
with check (
  bucket_id = 'wound-images'
  and (storage.foldername(name))[1] = auth.uid()::text
);

create policy "Users read own wound images"
on storage.objects for select
to authenticated
using (
  bucket_id = 'wound-images'
  and (
    (storage.foldername(name))[1] = auth.uid()::text
    or public.current_role() in ('reviewer','researcher','admin')
  )
);


create policy "Users delete own wound images"
on storage.objects for delete
to authenticated
using (
  bucket_id = 'wound-images'
  and (storage.foldername(name))[1] = auth.uid()::text
);

-- Seed no fake metrics. The application must only show measured research results.
