-- ARK - Migration 002: dm-qualifier yanit gecikmesi + sohbet-ici satis tier'i
-- SADECE bu dosyayi SQL Editor'a yapistir, eski scriptleri tekrar calistirma.

alter table leads
  add column if not exists response_stage int not null default 1,
  add column if not exists last_delay_seconds numeric,
  add column if not exists sales_tier text check (sales_tier in ('S','A','B','C','D')),
  add column if not exists sales_tier_score numeric;
