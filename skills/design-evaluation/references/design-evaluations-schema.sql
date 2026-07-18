-- Optional Supabase persistence for versioned design-evaluation batch results.
-- This table stores evidence-aligned rubric evaluations, not award probabilities.

create table if not exists public.design_evaluations (
  id bigint generated always as identity primary key,
  document_id bigint not null
    references public.works(document_id) on delete cascade,
  batch_id text not null,
  snapshot_id text not null,
  idempotency_key text not null,
  input_fingerprint text not null,

  model_name text not null,
  model_version text not null,
  prompt_version text not null,
  rubric_version text not null,
  runner_version text not null,

  maturity text not null
    check (maturity in ('student_concept', 'mature_work')),
  maturity_source text not null default 'user'
    check (maturity_source = 'user'),
  maturity_mapping jsonb not null default '{}'::jsonb,
  maturity_evidence_mismatch boolean not null default false,

  design_score numeric(6,2)
    check (design_score is null or design_score between 0 and 50),
  presentation_score numeric(6,2)
    check (presentation_score is null or presentation_score between 0 and 50),
  total_score numeric(6,2)
    check (total_score is null or total_score between 0 and 100),
  evidence_confidence text
    check (evidence_confidence is null or evidence_confidence in ('High', 'Medium', 'Low')),
  confidence_index numeric(7,4)
    check (confidence_index is null or confidence_index between 0 and 3),
  critical_count integer
    check (critical_count is null or critical_count >= 0),

  payload jsonb not null default '{}'::jsonb,
  result jsonb not null default '{}'::jsonb,
  status text not null default 'queued'
    check (status in ('queued', 'running', 'completed', 'not_evaluable', 'failed')),
  error text,
  attempt_count integer not null default 0
    check (attempt_count >= 0),

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz,

  constraint design_evaluations_idempotency_key unique (idempotency_key),
  constraint design_evaluations_score_sum_check check (
    total_score is null
    or (
      design_score is not null
      and presentation_score is not null
      and total_score = design_score + presentation_score
    )
  ),
  constraint design_evaluations_completed_fields_check check (
    status <> 'completed'
    or (
      design_score is not null
      and presentation_score is not null
      and total_score is not null
      and evidence_confidence is not null
      and confidence_index is not null
      and critical_count is not null
      and completed_at is not null
    )
  ),
  constraint design_evaluations_error_check check (
    status not in ('failed', 'not_evaluable')
    or nullif(btrim(error), '') is not null
  )
);

create index if not exists design_evaluations_document_id_idx
  on public.design_evaluations (document_id);

create index if not exists design_evaluations_batch_status_idx
  on public.design_evaluations (batch_id, status);

create index if not exists design_evaluations_snapshot_track_score_idx
  on public.design_evaluations (snapshot_id, maturity, total_score desc)
  where status = 'completed';

create or replace function public.set_design_evaluations_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists design_evaluations_set_updated_at
  on public.design_evaluations;
create trigger design_evaluations_set_updated_at
before update on public.design_evaluations
for each row execute function public.set_design_evaluations_updated_at();

alter table public.design_evaluations enable row level security;

-- No anon/authenticated policy is created. Batch workers use service_role.
revoke all on table public.design_evaluations from anon, authenticated;
grant select, insert, update, delete on table public.design_evaluations to service_role;
grant usage, select on sequence public.design_evaluations_id_seq to service_role;
