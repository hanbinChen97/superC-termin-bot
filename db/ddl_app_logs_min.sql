create table public.app_logs_min (
  id bigserial not null,
  log_timestamp timestamp with time zone not null,
  level text not null,
  message text not null,
  created_at timestamp with time zone not null default now(),
  schritt text not null default '-'::text,
  constraint app_logs_min_pkey primary key (id),
  constraint app_logs_min_level_check check (
    (
      level = any (
        array[
          'DEBUG'::text,
          'INFO'::text,
          'WARNING'::text,
          'ERROR'::text,
          'CRITICAL'::text
        ]
      )
    )
  )
) TABLESPACE pg_default;

create index IF not exists idx_app_logs_min_timestamp on public.app_logs_min using btree (log_timestamp desc) TABLESPACE pg_default;

create index IF not exists idx_app_logs_min_level on public.app_logs_min using btree (level) TABLESPACE pg_default;