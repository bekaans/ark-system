-- ARK - Migration 005: NocoBase kanban gorunumu icin siralama alani
-- SADECE bu dosyayi SQL Editor'a yapistir, eski scriptleri tekrar calistirma.

alter table leads
  add column if not exists kanban_sort bigint;

update leads set kanban_sort = extract(epoch from created_at)::bigint where kanban_sort is null;
