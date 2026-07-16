-- ARK - Migration 004: s1-7 surekli-calisan dongu icin ilerleme takibi
-- SADECE bu dosyayi SQL Editor'a yapistir, eski scriptleri tekrar calistirma.

create table if not exists scrape_progress (
  id uuid primary key default gen_random_uuid(),
  sector_code text not null,
  city text not null,
  status text not null default 'pending' check (status in ('pending','done')),
  scraped_at timestamptz,
  created_at timestamptz not null default now(),
  unique (sector_code, city)
);

alter table scrape_progress enable row level security;
